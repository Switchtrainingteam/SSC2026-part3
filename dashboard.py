import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration to wide mode
st.set_page_config(page_title="SSC 2026 Dashboard", layout="wide")

# Function to parse the complex CSV structure
def load_and_parse_data(file_path):
    # Read the file without header to detect blocks
    try:
        df_raw = pd.read_csv(file_path, header=None)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}. Please ensure the CSV files are in the same directory.")
        return None, None

    # Container for parsed tables
    tables = {}
    
    # 1. Find and parse Region Table
    # Look for the row containing "Region" in the first column
    region_start = df_raw[df_raw[0] == 'Region'].index
    if not region_start.empty:
        start_idx = region_start[0]
        # Find the next empty row to define the block
        next_empty = df_raw.index[df_raw[0].isna()].tolist()
        next_empty = [x for x in next_empty if x > start_idx]
        end_idx = next_empty[0] if next_empty else len(df_raw)
        
        # Extract and clean
        region_df = df_raw.iloc[start_idx+1:end_idx].copy()
        region_df.columns = df_raw.iloc[start_idx]
        region_df = region_df.reset_index(drop=True)
        
        # Convert numeric columns
        for col in ['Pass', 'Fail', 'Total Headcount']:
            if col in region_df.columns:
                region_df[col] = pd.to_numeric(region_df[col], errors='coerce').fillna(0)
        
        tables['region'] = region_df

    # 2. Find and parse Product Table (Only in Level 1)
    # Look for row containing "Result"
    product_start = df_raw[df_raw[0] == 'Result'].index
    if not product_start.empty:
        start_idx = product_start[0]
        # Find next empty
        next_empty = df_raw.index[df_raw[0].isna()].tolist()
        next_empty = [x for x in next_empty if x > start_idx]
        end_idx = next_empty[0] if next_empty else len(df_raw)
        
        product_df = df_raw.iloc[start_idx+1:end_idx].copy()
        product_df.columns = df_raw.iloc[start_idx]
        tables['product'] = product_df

    return tables

# --- LAYOUT SETUP ---

# 1. Sidebar
with st.sidebar:
    st.header("Dashboard Controls")
    # Map friendly names to actual filenames
    # NOTE: Update these filenames if yours are different
    file_map = {
        "Level 1": "SSC 2026 Data.xlsx - Level 1.csv",
        "Level 2": "SSC 2026 Data.xlsx - Level 2.csv",
        "Level 3": "SSC 2026 Data.xlsx - Level 3.csv"
    }
    
    selected_level = st.selectbox("Select Level", list(file_map.keys()))
    st.info(f"Viewing data for: {selected_level}")

# Load data for selected level
data_tables = load_and_parse_data(file_map[selected_level])

if data_tables and 'region' in data_tables:
    df_region = data_tables['region']
    
    # --- SECOND COLUMN (Main Area) ---
    
    # Row 1: Data Cards
    st.subheader("Key Performance Indicators")
    
    # Calculate Metrics
    total_headcount = df_region['Total Headcount'].sum()
    total_pass = df_region['Pass'].sum()
    total_fail = df_region['Fail'].sum()
    pass_rate = (total_pass / total_headcount * 100) if total_headcount > 0 else 0
    
    # Display Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Headcount", f"{int(total_headcount)}")
    col2.metric("Total Pass", f"{int(total_pass)}")
    col3.metric("Total Fail", f"{int(total_fail)}")
    col4.metric("Pass Rate", f"{pass_rate:.1f}%")
    
    st.markdown("---")

    # Row 2: Graphs
    st.subheader("Visualizations")
    
    # Create a layout for graphs
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Bar Chart: Pass vs Fail by Region
        fig_region = px.bar(
            df_region, 
            x='Region', 
            y=['Pass', 'Fail'], 
            title="Pass vs Fail by Region",
            barmode='group',
            text_auto=True
        )
        st.plotly_chart(fig_region, use_container_width=True)
        
    with chart_col2:
        # Pie Chart: Overall Pass vs Fail
        pie_data = pd.DataFrame({
            'Status': ['Pass', 'Fail'],
            'Count': [total_pass, total_fail]
        })
        fig_pie = px.pie(pie_data, values='Count', names='Status', title="Overall Pass vs Fail Distribution",
                         color='Status', color_discrete_map={'Pass':'lightgreen', 'Fail':'salmon'})
        st.plotly_chart(fig_pie, use_container_width=True)

    # Optional: Product Breakdown for Level 1
    if 'product' in data_tables:
        st.subheader("Product Breakdown")
        df_prod = data_tables['product']
        # Simple cleanup for display
        st.dataframe(df_prod, use_container_width=True)

    st.markdown("---")

    # Row 3: Data Table
    st.subheader("Detailed Regional Data")
    st.dataframe(df_region, use_container_width=True)
