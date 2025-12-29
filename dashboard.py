import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & DATA LOADING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SSC 2026 Dashboard", layout="wide")

# CSS to style the metrics cards to look like a "Row"
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #d6d6d6;
        padding: 10px;
        border-radius: 5px;
        overflow-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA (Embedded for reliability) ---
# You can replace these with pd.read_csv('your_file.csv') in production

# 1. Regional Data
df_regional = pd.DataFrame({
    'Region': ['Central', 'Northern', 'Southern', 'East Coast', 'Sabah', 'Sarawak'],
    'Pass': [73, 48, 49, 55, 42, 36],
    'Fail': [25, 16, 13, 12, 8, 14],
    'Total Headcount': [98, 64, 62, 67, 50, 50]
})

# 2. Outlet Data
df_outlet = pd.DataFrame({
    'Outlet': ['MT', 'PY', 'EV', 'MF'],
    'Pass': [4, 5, 3, 1],
    'Fail': [2, 3, 2, 4]
})

# 3. LOB Data
df_lob = pd.DataFrame({
    'Result': [
        'iPhone (Pass)', 'iPhone (Fail)', 'Mac (Pass)', 'Mac (Fail)',
        'iPad (Pass)', 'iPad (Fail)', 'Apple Watch (Pass)', 'Apple Watch (Fail)'
    ],
    'Central': [20, 45, 12, 24, 23, 12, 11, 7],
    'Northern': [45, 56, 9, 11, 11, 8, 45, 3],
    'Sarawak': [23, 12, 56, 7, 44, 4, 67, 99],
    'Sabah': [12, 54, 34, 6, 8, 22, 5, 66]
})

# Helper to process LOB data for charts
def process_lob_data(df):
    # Melt to long format
    df_long = df.melt(id_vars=['Result'], var_name='Region', value_name='Count')
    # Extract Status (Pass/Fail)
    df_long['Status'] = df_long['Result'].apply(lambda x: 'Pass' if '(Pass)' in x else 'Fail')
    # Extract Product
    df_long['Product'] = df_long['Result'].apply(lambda x: x.split(' (')[0])
    return df_long

# -----------------------------------------------------------------------------
# 2. COLUMN 1: SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Dashboard Settings")
    
    # User selects which view to see
    selected_view = st.radio(
        "Select Data View:",
        ["Regional Comparison", "Outlet Comparison", "LOB Analysis"]
    )
    
    st.markdown("---")
    st.write("Use this sidebar to toggle between different datasets from your Excel file.")

# -----------------------------------------------------------------------------
# 3. COLUMN 2: MAIN DASHBOARD AREA (3 ROWS)
# -----------------------------------------------------------------------------

st.title(f"📊 {selected_view}")

# --- PREPARE DATA BASED ON SELECTION ---
if selected_view == "Regional Comparison":
    main_df = df_regional
    
    # Calculate KPIs
    total_pass = main_df['Pass'].sum()
    total_fail = main_df['Fail'].sum()
    total_hc = main_df['Total Headcount'].sum()
    pass_rate = (total_pass / total_hc) * 100
    
    # Prepare Chart
    # Melt for grouped bar chart
    chart_df = main_df.melt(id_vars=['Region'], value_vars=['Pass', 'Fail'], var_name='Status', value_name='Count')
    fig = px.bar(chart_df, x='Region', y='Count', color='Status', barmode='group',
                 color_discrete_map={'Pass': '#2ecc71', 'Fail': '#e74c3c'}, text_auto=True)

elif selected_view == "Outlet Comparison":
    main_df = df_outlet
    
    # Calculate KPIs
    total_pass = main_df['Pass'].sum()
    total_fail = main_df['Fail'].sum()
    total_hc = total_pass + total_fail
    pass_rate = (total_pass / total_hc) * 100
    
    # Prepare Chart
    chart_df = main_df.melt(id_vars=['Outlet'], value_vars=['Pass', 'Fail'], var_name='Status', value_name='Count')
    fig = px.bar(chart_df, x='Outlet', y='Count', color='Status', barmode='group',
                 color_discrete_map={'Pass': '#2ecc71', 'Fail': '#e74c3c'}, text_auto=True)

elif selected_view == "LOB Analysis":
    main_df = df_lob
    processed_lob = process_lob_data(df_lob)
    
    # Calculate KPIs
    total_pass = processed_lob[processed_lob['Status'] == 'Pass']['Count'].sum()
    total_fail = processed_lob[processed_lob['Status'] == 'Fail']['Count'].sum()
    total_hc = total_pass + total_fail
    pass_rate = (total_pass / total_hc) * 100
    
    # Prepare Chart (Stacked bar by Product)
    fig = px.bar(processed_lob, x='Product', y='Count', color='Status', 
                 color_discrete_map={'Pass': '#2ecc71', 'Fail': '#e74c3c'}, 
                 facet_col='Region', title="Product Performance by Region")


# --- ROW 1: DATA CARDS (KPIs) ---
st.subheader("1. Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Headcount/Volume", f"{total_hc}")
col2.metric("Total Pass", f"{total_pass}")
col3.metric("Total Fail", f"{total_fail}")
col4.metric("Pass Rate", f"{pass_rate:.1f}%", delta_color="normal")

st.markdown("---")

# --- ROW 2: GRAPHS ---
st.subheader("2. Visualization")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- ROW 3: DATA TABLE ---
st.subheader("3. Detailed Data")
st.dataframe(main_df, use_container_width=True)