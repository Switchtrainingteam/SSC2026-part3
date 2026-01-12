import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="SSC 2026 Dashboard", layout="wide")

# --- Helper Function to Parse Data ---
def load_data(file_path):
    """
    Parses the CSV file which contains multiple tables separated by empty rows.
    Returns a dictionary of DataFrames.
    """
    try:
        # Read the raw file without header to detect blocks
        raw_df = pd.read_csv(file_path, header=None)
        
        tables = {}
        current_block = []
        
        # Iterate through rows to split by empty lines
        for index, row in raw_df.iterrows():
            # Check if row is effectively empty (all NaN or empty strings)
            if row.isnull().all():
                if current_block:
                    tables = process_block(current_block, tables)
                    current_block = []
            else:
                current_block.append(row.values)
        
        # Process the last block if exists
        if current_block:
            tables = process_block(current_block, tables)
            
        return tables
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def process_block(block_data, tables_dict):
    """Helper to convert a list of rows into a named DataFrame"""
    if not block_data:
        return tables_dict
        
    df = pd.DataFrame(block_data)
    header = df.iloc[0]
    df = df[1:].copy()
    df.columns = header
    
    # Identify table type based on first column name
    first_col = str(header[0]).strip()
    
    if "Result" in first_col:
        tables_dict["Product_Data"] = df
    elif "Region" in first_col:
        tables_dict["Region_Data"] = df
    elif "Outlet" in first_col:
        tables_dict["Outlet_Data"] = df
        
    return tables_dict

# --- Sidebar (Column 1) ---
with st.sidebar:
    st.title("Dashboard Controls")
    
    # File Selection
    level_choice = st.selectbox(
        "Select Data Level",
        ["Level 1", "Level 2", "Level 3"]
    )
    
    # Map selection to filename
    file_map = {
        "Level 1": "SSC 2026 Data.xlsx - Level 1.csv",
        "Level 2": "SSC 2026 Data.xlsx - Level 2.csv",
        "Level 3": "SSC 2026 Data.xlsx - Level 3.csv"
    }
    
    selected_file = file_map[level_choice]
    
    st.info(f"Loaded: {selected_file}")
    st.markdown("---")
    st.markdown("**Instructions:**\nSelect a level to view the performance metrics.")

# --- Main Content (Column 2) ---

# Load Data
data_tables = load_data(selected_file)

if data_tables and "Region_Data" in data_tables:
    region_df = data_tables["Region_Data"]
    
    # Data Cleaning for Region Table
    # Ensure numeric columns are actually numeric
    cols_to_numeric = ['Pass', 'Fail', 'Total Headcount']
    for col in cols_to_numeric:
        if col in region_df.columns:
            region_df[col] = pd.to_numeric(region_df[col], errors='coerce').fillna(0)

    # --- Row 1: Data Cards ---
    st.markdown("### 📊 Key Performance Indicators")
    
    # Calculate Metrics
    total_pass = int(region_df['Pass'].sum())
    total_fail = int(region_df['Fail'].sum())
    total_headcount = int(region_df['Total Headcount'].sum())
    pass_rate = (total_pass / total_headcount * 100) if total_headcount > 0 else 0
    
    # Layout 3 cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Pass", value=f"{total_pass:,}")
        
    with col2:
        st.metric(label="Total Fail", value=f"{total_fail:,}")
        
    with col3:
        st.metric(label="Overall Pass Rate", value=f"{pass_rate:.1f}%")
        
    st.markdown("---")

    # --- Row 2: Graphs ---
    st.markdown("### 📈 Visual Analysis")
    
    # Create 2 columns for graphs if we have product data (Level 1), otherwise 1
    graph_col1, graph_col2 = st.columns([2, 1])
    
    with graph_col1:
        # Stacked Bar Chart for Region Pass/Fail
        # Melt data for plotly
        melted_region = region_df.melt(id_vars=['Region'], value_vars=['Pass', 'Fail'], 
                                     var_name='Status', value_name='Count')
        
        fig_region = px.bar(
            melted_region, 
            x='Region', 
            y='Count', 
            color='Status', 
            title=f"Pass vs Fail by Region ({level_choice})",
            text_auto=True,
            color_discrete_map={'Pass': '#4CAF50', 'Fail': '#FF5252'},
            barmode='group'
        )
        st.plotly_chart(fig_region, use_container_width=True)

    with graph_col2:
        # Pie chart for overall distribution
        fig_pie = px.pie(
            names=['Pass', 'Fail'], 
            values=[total_pass, total_fail],
            title="Overall Status Distribution",
            color=['Pass', 'Fail'],
            color_discrete_map={'Pass': '#4CAF50', 'Fail': '#FF5252'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Extra Graph for Product Data (Only available in Level 1)
    if "Product_Data" in data_tables:
        st.subheader("Product Performance (Level 1 Specific)")
        prod_df = data_tables["Product_Data"]
        
        # Simple processing for visualization: Pivot longer
        # The structure is Result (Product+Status) | Central | Northern ...
        # We'll just show the raw table in an interactive way or a heatmap
        
        # Clean numeric columns in Product Data
        region_cols = [c for c in prod_df.columns if c != 'Result']
        for c in region_cols:
            prod_df[c] = pd.to_numeric(prod_df[c], errors='coerce').fillna(0)
            
        # Add a total column for sorting
        prod_df['Total'] = prod_df[region_cols].sum(axis=1)
        
        fig_prod = px.bar(
            prod_df.sort_values('Total', ascending=True), 
            x='Total', 
            y='Result', 
            orientation='h',
            title="Total Counts by Product/Status Category",
            text_auto=True
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    st.markdown("---")

    # --- Row 3: Data Table ---
    st.markdown("### 📋 Detailed Data View")
    
    # Use tabs to organize multiple tables
    tab_names = ["Region Summary", "Outlet Summary"]
    if "Product_Data" in data_tables:
        tab_names.insert(0, "Product Results")
        
    tabs = st.tabs(tab_names)
    
    if "Product_Data" in data_tables:
        with tabs[0]:
            st.dataframe(data_tables["Product_Data"], use_container_width=True)
            # Remove from list to handle indices correctly for others
            tab_names.pop(0) 
            # Note: This logic depends on the specific insertion order, simpler to check keys directly
            
    # Display Region Data
    # Find the tab index for Region Summary. If Product Data exists, Region is index 1, else 0.
    region_tab_idx = 1 if "Product_Data" in data_tables else 0
    with tabs[region_tab_idx]:
        st.dataframe(region_df, use_container_width=True)
        
    # Display Outlet Data
    outlet_tab_idx = 2 if "Product_Data" in data_tables else 1
    if "Outlet_Data" in data_tables:
        with tabs[outlet_tab_idx]:
            st.dataframe(data_tables["Outlet_Data"], use_container_width=True)

else:
    st.warning("Data not found or could not be parsed. Please check the CSV files.")
