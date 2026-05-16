import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(page_title="Inventory Dashboard", page_icon="📦", layout="wide")

# Custom CSS for Premium Design
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Metrics / KPIs */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #00f2fe;
        font-weight: 700;
        text-shadow: 0px 0px 10px rgba(0, 242, 254, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        color: #a0aec0;
        font-weight: 500;
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #1a202c, #2d3748);
        border: 1px solid #4a5568;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 25px rgba(0, 242, 254, 0.2);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #f7fafc;
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Data Loading
@st.cache_data
def load_data():
    file_path = "4.INVENTORY 30 APRIL-2026 updated.xlsm"
    try:
        # Load the two main sheets
        df_master = pd.read_excel(file_path, sheet_name="MASTER_SHEET", engine="openpyxl")
        df_issuance = pd.read_excel(file_path, sheet_name="ISSUANCE_HISTORY", engine="openpyxl")
        return df_master, df_issuance
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_master, df_issuance = load_data()

if df_master.empty:
    st.warning("No data found or failed to load. Please ensure the Excel file is in the same directory.")
    st.stop()

# Clean up column names (remove leading/trailing spaces)
df_master.columns = df_master.columns.str.strip()
df_issuance.columns = df_issuance.columns.str.strip()

# Fix PyArrow serialization issues by converting mixed-type columns to string
for col in df_master.columns:
    if df_master[col].dtype == 'object':
        df_master[col] = df_master[col].astype(str)
        
for col in df_issuance.columns:
    if df_issuance[col].dtype == 'object':
        df_issuance[col] = df_issuance[col].astype(str)

# Sidebar Navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3214/3214764.png", width=100)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard Overview", "Issuance Analysis", "Raw Data Explorer"])

st.sidebar.markdown("---")
st.sidebar.info("Data loaded from: `4.INVENTORY 30 APRIL-2026 updated.xlsm`")

# ==================== PAGE: DASHBOARD OVERVIEW ====================
if page == "Dashboard Overview":
    st.title("📦 Inventory Overview Dashboard")
    st.markdown("A high-level view of current stock, values, and status.")
    
    # Calculate KPIs
    total_items = len(df_master)
    total_value = df_master['Closing Balance Value'].sum()
    total_issued_value = df_master['Issued Value'].sum()
    
    # Low stock calculation (Closing Qty <= Min ReOrder Qty)
    # Ensure columns are numeric
    df_master['Closing Balance Qty'] = pd.to_numeric(df_master['Closing Balance Qty'], errors='coerce').fillna(0)
    df_master['Minimum ReOrder Quantity'] = pd.to_numeric(df_master['Minimum ReOrder Quantity'], errors='coerce').fillna(0)
    low_stock_items = df_master[df_master['Closing Balance Qty'] <= df_master['Minimum ReOrder Quantity']]
    num_low_stock = len(low_stock_items[low_stock_items['Minimum ReOrder Quantity'] > 0]) # Only count items that actually have a min reorder qty

    # KPI Layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items Tracked", f"{total_items:,}")
    with col2:
        st.metric("Total Inventory Value", f"${total_value:,.2f}")
    with col3:
        st.metric("Total Issued Value", f"${total_issued_value:,.2f}")
    with col4:
        st.metric("Low Stock Alerts", f"{num_low_stock}")
        
    st.markdown("---")
    
    # Charts Layout
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Inventory Value by Category")
        cat_value = df_master.groupby('Category')['Closing Balance Value'].sum().reset_index()
        cat_value = cat_value[cat_value['Closing Balance Value'] > 0]
        fig_pie = px.pie(cat_value, values='Closing Balance Value', names='Category', 
                         hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma)
        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Top 10 Items by Value in Stock")
        top_items = df_master.nlargest(10, 'Closing Balance Value')
        fig_bar = px.bar(top_items, x='Closing Balance Value', y='Description', orientation='h',
                         color='Closing Balance Value', color_continuous_scale='Blues')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.subheader("⚠️ Low Stock Alert Items")
    if num_low_stock > 0:
        st.dataframe(low_stock_items[['Item Code', 'Description', 'Category', 'Closing Balance Qty', 'Minimum ReOrder Quantity']], use_container_width=True)
    else:
        st.success("All items are well stocked!")

# ==================== PAGE: ISSUANCE ANALYSIS ====================
elif page == "Issuance Analysis":
    st.title("📤 Issuance Trends & Analysis")
    st.markdown("Track what is being issued, to whom, and where.")
    
    if df_issuance.empty:
        st.warning("No issuance data found.")
    else:
        # Convert date column
        if 'Issue Date' in df_issuance.columns:
            df_issuance['Issue Date'] = pd.to_datetime(df_issuance['Issue Date'], errors='coerce')
            
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Issuance Value by Department")
            dept_value = df_issuance.groupby('DEPARTMENT')['Issued Value'].sum().reset_index()
            fig_dept = px.bar(dept_value, x='DEPARTMENT', y='Issued Value', color='Issued Value', color_continuous_scale='Teal')
            fig_dept.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", xaxis_tickangle=-45)
            st.plotly_chart(fig_dept, use_container_width=True)
            
        with c2:
            st.subheader("Issuance by Location")
            loc_value = df_issuance.groupby('Location')['Issued Value'].sum().reset_index()
            fig_loc = px.pie(loc_value, values='Issued Value', names='Location', hole=0.3, color_discrete_sequence=px.colors.sequential.Viridis)
            fig_loc.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_loc, use_container_width=True)
            
        st.subheader("Recent Issuance History")
        st.dataframe(df_issuance.sort_values(by='Issue Date', ascending=False).head(50), use_container_width=True)

# ==================== PAGE: RAW DATA EXPLORER ====================
elif page == "Raw Data Explorer":
    st.title("🔍 Raw Data Explorer")
    st.markdown("Filter and search through the raw inventory data.")
    
    sheet_sel = st.selectbox("Select Data Source", ["MASTER SHEET", "ISSUANCE HISTORY"])
    
    if sheet_sel == "MASTER SHEET":
        # Add basic filters
        categories = ["All"] + list(df_master['Category'].dropna().unique())
        cat_filter = st.selectbox("Filter by Category", categories)
        
        search_term = st.text_input("Search by Description or Item Code", "")
        
        filtered_df = df_master.copy()
        if cat_filter != "All":
            filtered_df = filtered_df[filtered_df['Category'] == cat_filter]
            
        if search_term:
            search_term = str(search_term).lower()
            filtered_df = filtered_df[
                filtered_df['Description'].str.lower().str.contains(search_term, na=False) |
                filtered_df['Item Code'].astype(str).str.lower().str.contains(search_term, na=False)
            ]
            
        st.dataframe(filtered_df, use_container_width=True, height=600)
        
    else:
        st.dataframe(df_issuance, use_container_width=True, height=600)

