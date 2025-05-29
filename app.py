# 📁 app.py (เพิ่ม dropdown filter กรองตาม Sub_id2 + ช่องสรุปด้านบน + กรองตามวันที่ + กรอง Validity)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Affiliate Profit Dashboard", layout="wide")
st.title("📊 Affiliate Profit Dashboard V1.1")

# ===================== CSS =====================
st.markdown("""
    <style>
    section[data-testid="stFileUploader"] div[data-testid="stFileDropzone"]:nth-of-type(1) {
        background-color: #fff5e6; padding: 10px; border-radius: 8px;
    }
    section[data-testid="stFileUploader"] div[data-testid="stFileDropzone"]:nth-of-type(2) {
        background-color: #f5e6ff; padding: 10px; border-radius: 8px;
    }
    section[data-testid="stFileUploader"] div[data-testid="stFileDropzone"]:nth-of-type(3) {
        background-color: #e6f0ff; padding: 10px; border-radius: 8px;
    }
    th, td { text-align: center; }
    
    /* Custom metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1.2em;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# ===================== FILE UPLOAD =====================
st.sidebar.header("📁 Upload Files")
commission_file = st.sidebar.file_uploader("Shopee Commission Report (CSV or Excel)", type=["csv", "xlsx"])
lzd_file = st.sidebar.file_uploader("Lazada Commission Report (Excel)", type=["xlsx"])
ads_file = st.sidebar.file_uploader("Ads Report (CSV or Excel)", type=["csv", "xlsx"])

def read_file(file):
    return pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

df_shopee = df_lazada = df_ads = summary = pd.DataFrame()

# ===================== Shopee =====================
if commission_file:
    df_shopee = read_file(commission_file)
    if not df_shopee.empty:
        df_shopee = df_shopee.dropna(subset=['Sub_id4', 'คอมมิชชั่นสินค้าโดยรวม(฿)', 'รหัสการสั่งซื้อ'])

# ===================== Lazada =====================
if lzd_file:
    df_lazada = read_file(lzd_file)
    if not df_lazada.empty:
        df_lazada['Sub_id4'] = df_lazada['Sub ID 3'].fillna(df_lazada['Sub ID 1'])
        df_lazada = df_lazada.dropna(subset=['Sub_id4', 'Payout'])
        df_lazada = df_lazada[df_lazada['Sub_id4'] != 'paris']

# ===================== Ads Data =====================
if ads_file:
    df_ads = read_file(ads_file)
    if not df_ads.empty:
        df_ads = df_ads.dropna(subset=['Ad name', 'Amount spent (THB)', 'Unique link clicks'])

# ===================== FILTER OPTIONS SECTION =====================
st.markdown("### 🔍 Filter Options")

col_filter1, col_filter2 = st.columns(2)

# Platform filter
with col_filter1:
    shopee_platforms = df_shopee['Sub_id2'].dropna().unique().tolist() if not df_shopee.empty and 'Sub_id2' in df_shopee.columns else []
    lazada_platforms = df_lazada['Sub ID 2'].dropna().unique().tolist() if not df_lazada.empty and 'Sub ID 2' in df_lazada.columns else []
    platform_options = list(set(shopee_platforms + lazada_platforms))
    selected_platform = st.selectbox("🔎 กรองตามแพลตฟอร์ม (Sub_id2):", ['ทั้งหมด'] + platform_options)

# Validity filter (Lazada only)
with col_filter2:
    if not df_lazada.empty and 'Validity' in df_lazada.columns:
        validity_options = df_lazada['Validity'].dropna().unique().tolist()
        selected_validity = st.selectbox("✅ กรอง Validity (Lazada):", ['ทั้งหมด'] + validity_options)
    else:
        selected_validity = 'ทั้งหมด'
        st.selectbox("✅ กรอง Validity (Lazada):", ['ทั้งหมด'], disabled=True, help="ไม่มีข้อมูล Lazada หรือไม่มีคอลัมน์ Validity")

# Date filter section
st.markdown("#### 📅 Date Filter")
use_date_filter = st.checkbox("🔍 กรองตามวันที่", value=False)

date_start = date_end = None
if use_date_filter:
    col_date1, col_date2 = st.columns(2)
    
    with col_date1:
        # กำหนดค่า default เป็น 30 วันย้อนหลัง
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=30)
        
        date_start = st.date_input(
            "📅 วันที่เริ่มต้น:", 
            value=default_start,
            help="เลือกวันที่เริ่มต้นสำหรับการกรองข้อมูล"
        )
    
    with col_date2:
        date_end = st.date_input(
            "📅 วันที่สิ้นสุด:", 
            value=default_end,
            help="เลือกวันที่สิ้นสุดสำหรับการกรองข้อมูล"
        )
    
    # ตรวจสอบว่าวันที่เริ่มต้นไม่เกินวันที่สิ้นสุด
    if date_start > date_end:
        st.error("⚠️ วันที่เริ่มต้นต้องไม่เกินวันที่สิ้นสุด")
        date_start = date_end

# ===================== APPLY FILTERS =====================
# Create copies for filtering
df_shopee_filtered = df_shopee.copy() if not df_shopee.empty else pd.DataFrame()
df_lazada_filtered = df_lazada.copy() if not df_lazada.empty else pd.DataFrame()
df_ads_filtered = df_ads.copy() if not df_ads.empty else pd.DataFrame()

# กรองตามวันที่สำหรับ Shopee
if not df_shopee_filtered.empty:
    if use_date_filter and date_start and date_end:
        if 'เวลาที่สั่งซื้อ' in df_shopee_filtered.columns:
            df_shopee_filtered['เวลาที่สั่งซื้อ'] = pd.to_datetime(df_shopee_filtered['เวลาที่สั่งซื้อ'], errors='coerce')
            df_shopee_filtered = df_shopee_filtered[
                (df_shopee_filtered['เวลาที่สั่งซื้อ'].dt.date >= date_start) & 
                (df_shopee_filtered['เวลาที่สั่งซื้อ'].dt.date <= date_end)
            ]
    
    df_shopee_grouped = df_shopee_filtered.groupby('Sub_id4').agg({
        'คอมมิชชั่นสินค้าโดยรวม(฿)': 'sum',
        'รหัสการสั่งซื้อ': 'nunique'
    }).reset_index().rename(columns={
        'คอมมิชชั่นสินค้าโดยรวม(฿)': 'Shopee Com',
        'รหัสการสั่งซื้อ': 'Order Count'
    })
else:
    df_shopee_grouped = pd.DataFrame(columns=['Sub_id4', 'Shopee Com', 'Order Count'])

# กรองตามวันที่และ Validity สำหรับ Lazada
if not df_lazada_filtered.empty:
    # กรองตาม Validity
    if selected_validity != 'ทั้งหมด':
        df_lazada_filtered = df_lazada_filtered[df_lazada_filtered['Validity'] == selected_validity]
    
    # กรองตามวันที่
    if use_date_filter and date_start and date_end:
        if 'Conversion Time' in df_lazada_filtered.columns:
            df_lazada_filtered['Conversion Time'] = pd.to_datetime(df_lazada_filtered['Conversion Time'], errors='coerce')
            df_lazada_filtered = df_lazada_filtered[
                (df_lazada_filtered['Conversion Time'].dt.date >= date_start) & 
                (df_lazada_filtered['Conversion Time'].dt.date <= date_end)
            ]
    
    df_lazada_grouped = df_lazada_filtered.groupby('Sub_id4').agg({
        'Payout': 'sum',
        'Order Amount': 'sum'
    }).reset_index().rename(columns={
        'Payout': 'Lazada Com',
        'Order Amount': 'LZD Order Amount'
    })
else:
    df_lazada_grouped = pd.DataFrame(columns=['Sub_id4', 'Lazada Com', 'LZD Order Amount'])

# กรองตามวันที่สำหรับ Ads
if not df_ads_filtered.empty:
    if use_date_filter and date_start and date_end:
        if 'Day' in df_ads_filtered.columns:
            df_ads_filtered['Day'] = pd.to_datetime(df_ads_filtered['Day'], errors='coerce')
            df_ads_filtered = df_ads_filtered[
                (df_ads_filtered['Day'].dt.date >= date_start) & 
                (df_ads_filtered['Day'].dt.date <= date_end)
            ]

# ===================== Merge Shopee + Lazada =====================
if not df_shopee_grouped.empty and not df_lazada_grouped.empty:
    summary = pd.merge(df_shopee_grouped, df_lazada_grouped, on='Sub_id4', how='outer').fillna(0)
elif not df_shopee_grouped.empty:
    summary = df_shopee_grouped.copy()
    summary['Lazada Com'] = 0
    summary['LZD Order Amount'] = 0
elif not df_lazada_grouped.empty:
    summary = df_lazada_grouped.copy()
    summary['Shopee Com'] = 0
    summary['Order Count'] = 0

# ===================== คำนวณรวมคอมมิชชั่น =====================
if not summary.empty:
    summary['Total Com'] = summary.get('Shopee Com', 0) + summary.get('Lazada Com', 0)

    if not df_ads_filtered.empty:
        ad_costs, clicks = [], []
        for sub_id in summary['Sub_id4']:
            matched = df_ads_filtered[df_ads_filtered['Ad name'].str.contains(sub_id, na=False)]
            ad_costs.append(matched['Amount spent (THB)'].sum())
            clicks.append(matched['Unique link clicks'].sum())
        summary['Ad Cost'] = ad_costs
        summary['Link Click'] = clicks
    else:
        summary['Ad Cost'] = 0
        summary['Link Click'] = 0

    summary['Profit'] = summary['Total Com'] - summary['Ad Cost']
    summary['ROI (%)'] = (summary['Profit'] / summary['Ad Cost'].replace(0, pd.NA)) * 100
    summary['CPC(Link)'] = summary['Ad Cost'] / summary['Link Click'].replace(0, pd.NA)
    summary['Cost Per Order(Shopee)'] = summary['Ad Cost'] / summary['Order Count'].replace(0, pd.NA)
    summary['Amount Per AdCost(LZD)'] = summary['LZD Order Amount'] / summary['Ad Cost'].replace(0, pd.NA)

    # ===== แสดงข่วงวันที่และตัวกรองที่เลือก =====
    filter_info = []
    if use_date_filter and date_start and date_end:
        filter_info.append(f"📅 ช่วงวันที่: {date_start.strftime('%d/%m/%Y')} ถึง {date_end.strftime('%d/%m/%Y')}")
    if selected_platform != 'ทั้งหมด':
        filter_info.append(f"🔎 แพลตฟอร์ม: {selected_platform}")
    if selected_validity != 'ทั้งหมด':
        filter_info.append(f"✅ Validity: {selected_validity}")
    
    if filter_info:
        st.info(" | ".join(filter_info))

    # ===== กรอง Sub_id2 =====
    if selected_platform != 'ทั้งหมด':
        shopee_match = df_shopee_filtered[df_shopee_filtered['Sub_id2'] == selected_platform]['Sub_id4'].unique() if not df_shopee_filtered.empty and 'Sub_id2' in df_shopee_filtered.columns else []
        lazada_match = df_lazada_filtered[df_lazada_filtered['Sub ID 2'] == selected_platform]['Sub_id4'].unique() if not df_lazada_filtered.empty and 'Sub ID 2' in df_lazada_filtered.columns else []
        matched_subid4 = set(shopee_match).union(set(lazada_match))
        summary = summary[summary['Sub_id4'].isin(matched_subid4)]

    # ===================== SUMMARY METRICS =====================
    # คำนวณค่ารวมสำหรับแสดงในช่องสรุป
    total_ad_cost = summary['Ad Cost'].sum()
    total_shopee_com = summary['Shopee Com'].sum()
    total_lazada_com = summary['Lazada Com'].sum()
    total_com = summary['Total Com'].sum()
    total_profit = summary['Profit'].sum()
    total_roi = (total_profit / total_ad_cost * 100) if total_ad_cost > 0 else 0

    # แสดงช่องสรุปด้านบนในรูปแบบ 3 คอลัมน์ x 2 แถว
    st.markdown("### 📊 สรุปภาพรวมทั้งหมด")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Ad Cost",
            value=f"฿{total_ad_cost:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="🛒 Shopee Commission",
            value=f"฿{total_shopee_com:,.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="🛍️ Lazada Commission", 
            value=f"฿{total_lazada_com:,.2f}",
            delta=None
        )

    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric(
            label="💎 Total Commission",
            value=f"฿{total_com:,.2f}",
            delta=None
        )
    
    with col5:
        profit_color = "normal" if total_profit >= 0 else "inverse"
        st.metric(
            label="📈 Total Profit",
            value=f"฿{total_profit:,.2f}",
            delta=f"{'กำไร' if total_profit >= 0 else 'ขาดทุน'}"
        )
    
    with col6:
        roi_color = "normal" if total_roi >= 0 else "inverse" 
        st.metric(
            label="📊 ROI (%)",
            value=f"{total_roi:.2f}%",
            delta=f"{'บวก' if total_roi >= 0 else 'ลบ'}"
        )

    st.markdown("---")  # เส้นแบ่ง

    # ===================== จัดเรียงคอลัมน์และเตรียมข้อมูล =====================
    desired_order = ['Sub_id4', 'Ad Cost', 'Link Click', 'Order Count', 'Shopee Com',
                     'Lazada Com', 'LZD Order Amount', 'Total Com', 'Profit', 'ROI (%)',
                     'CPC(Link)', 'Cost Per Order(Shopee)', 'Amount Per AdCost(LZD)']
    summary = summary[desired_order]

    # เก็บข้อมูลดิบไว้สำหรับการเรียงลำดับ
    summary_for_display = summary.copy()

    # รวมบรรทัดรวมทั้งหมด (สำหรับแสดงแยกต่างหาก)
    numeric_cols = ['Ad Cost', 'Link Click', 'Order Count', 'Shopee Com', 'Lazada Com',
                    'LZD Order Amount', 'Total Com', 'Profit', 'ROI (%)',
                    'CPC(Link)', 'Cost Per Order(Shopee)', 'Amount Per AdCost(LZD)']
    
    total_row_data = summary[numeric_cols].sum()
    
    # ตัวเลือกการเรียงลำดับ
    st.markdown("### 📋 สรุปกำไรต่อ Sub_id4")
    
    col_sort1, col_sort2 = st.columns([1, 3])
    with col_sort1:
        sort_column = st.selectbox(
            "🔄 เรียงตาม:",
            options=['Sub_id4'] + numeric_cols,
            index=0
        )
    with col_sort2:
        sort_order = st.radio(
            "ลำดับ:",
            options=['น้อยไปมาก (Ascending)', 'มากไปน้อย (Descending)'],
            horizontal=True,
            index=1
        )
    
    # เรียงข้อมูล
    ascending = sort_order == 'น้อยไปมาก (Ascending)'
    summary_sorted = summary_for_display.sort_values(by=sort_column, ascending=ascending)

    # จัดรูปแบบตัวเลขสำหรับแสดงผล
    summary_display = summary_sorted.copy()
    for col in numeric_cols:
        summary_display[col] = summary_display[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) and x != 0 else "0.00")

    # แสดงตารางแบบ interactive
    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sub_id4": st.column_config.TextColumn("Sub ID", width="medium"),
            "Ad Cost": st.column_config.TextColumn("💰 Ad Cost", width="medium"),
            "Link Click": st.column_config.TextColumn("👆 Link Click", width="medium"),
            "Order Count": st.column_config.TextColumn("📦 Order Count", width="medium"),
            "Shopee Com": st.column_config.TextColumn("🛒 Shopee Com", width="medium"),
            "Lazada Com": st.column_config.TextColumn("🛍️ Lazada Com", width="medium"),
            "LZD Order Amount": st.column_config.TextColumn("💵 LZD Order Amount", width="medium"),
            "Total Com": st.column_config.TextColumn("💎 Total Com", width="medium"),
            "Profit": st.column_config.TextColumn("📈 Profit", width="medium"),
            "ROI (%)": st.column_config.TextColumn("📊 ROI (%)", width="medium"),
            "CPC(Link)": st.column_config.TextColumn("💲 CPC(Link)", width="medium"),
            "Cost Per Order(Shopee)": st.column_config.TextColumn("📋 Cost/Order(SPE)", width="medium"),
            "Amount Per AdCost(LZD)": st.column_config.TextColumn("📊 Amount/AdCost(LZD)", width="medium")
        }
    )
    
    # แสดงแถวรวมแยกต่างหาก
    st.markdown("#### 📊 สรุปรวมทั้งหมด:")
    total_summary = pd.DataFrame([{
        'รายการ': 'รวมทั้งหมด',
        'Ad Cost': f"฿{total_row_data['Ad Cost']:,.2f}",
        'Shopee Com': f"฿{total_row_data['Shopee Com']:,.2f}",
        'Lazada Com': f"฿{total_row_data['Lazada Com']:,.2f}",
        'Total Com': f"฿{total_row_data['Total Com']:,.2f}",
        'Profit': f"฿{total_row_data['Profit']:,.2f}",
        'ROI (%)': f"{(total_row_data['Profit']/total_row_data['Ad Cost']*100 if total_row_data['Ad Cost'] > 0 else 0):,.2f}%"
    }])
    
    st.dataframe(
        total_summary,
        use_container_width=True,
        hide_index=True
    )

    # ===================== TOP 10 สินค้า ค่าคอมสูงสุด =====================
    st.markdown("### 🏆 สินค้าที่ค่าคอมสูงสุด (Top 10 Products)")

    # เตรียมข้อมูล Shopee
    top_shopee = pd.DataFrame()
    if not df_shopee_filtered.empty and 'ชื่อรายการสินค้า' in df_shopee_filtered.columns:
        top_shopee = df_shopee_filtered.groupby('ชื่อรายการสินค้า').agg({
            'คอมมิชชั่นสินค้าโดยรวม(฿)': 'sum',
            'มูลค่าซื้อ(฿)': 'sum'
        }).reset_index().rename(columns={
            'ชื่อรายการสินค้า': 'Product Name',
            'คอมมิชชั่นสินค้าโดยรวม(฿)': 'Commission',
            'มูลค่าซื้อ(฿)': 'Order Amount'
        })
        top_shopee['Platform'] = '🛍️ Shopee'  # เพิ่มคอลัมน์แพลตฟอร์ม

    # เตรียมข้อมูล Lazada
    top_lazada = pd.DataFrame()
    if not df_lazada_filtered.empty and 'Product Name' in df_lazada_filtered.columns:
        top_lazada = df_lazada_filtered.groupby('Product Name').agg({
            'Payout': 'sum',
            'Order Amount': 'sum'
        }).reset_index().rename(columns={
            'Product Name': 'Product Name',
            'Payout': 'Commission',
            'Order Amount': 'Order Amount'
        })
        top_lazada['Platform'] = '🛒 Lazada'  # เพิ่มคอลัมน์แพลตฟอร์ม

    # รวมข้อมูล Shopee + Lazada
    top_products = pd.concat([top_shopee, top_lazada], axis=0, ignore_index=True)
    if not top_products.empty:
        # จัดเรียงตามค่าคอมมิชชั่นโดยไม่รวมสินค้าที่ชื่อเหมือนกัน (เพื่อดูแยกแพลตฟอร์ม)
        top_products = top_products.sort_values(by='Commission', ascending=False).head(10)
        
        # แสดงผล
        top_products_display = top_products.copy()
        top_products_display['Commission'] = top_products_display['Commission'].apply(lambda x: f"฿{x:,.2f}")
        top_products_display['Order Amount'] = top_products_display['Order Amount'].apply(lambda x: f"{int(x)}")

        st.dataframe(
            top_products_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Product Name": st.column_config.TextColumn("📦 ชื่อสินค้า", width="large"),
                "Commission": st.column_config.TextColumn("💰 ค่าคอมมิชชั่นรวม", width="medium"),
                "Order Amount": st.column_config.TextColumn("📊 ยอดขาย", width="medium"),
                "Platform": st.column_config.TextColumn("🏪 แพลตฟอร์ม", width="small")
            }
        )
        
        # แสดงสถิติสรุป
        platform_counts = top_products['Platform'].value_counts()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            shopee_count = platform_counts.get('🛍️ Shopee', 0)
            st.metric("🛍️ Shopee ใน Top 10", shopee_count)
        with col2:
            lazada_count = platform_counts.get('🛒 Lazada', 0)
            st.metric("🛒 Lazada ใน Top 10", lazada_count)
        with col3:
            total_commission = top_products['Commission'].sum()
            st.metric("💰 ค่าคอมรวม Top 10", f"฿{total_commission:,.2f}")

    else:
        st.info("ไม่มีข้อมูลสินค้าเพียงพอสำหรับการจัดอันดับค่าคอมสูงสุด")

    # ===================== กราฟรายวัน: Ad Cost, Shopee Com, Lazada Com, Profit =====================
    st.markdown("### 📈 กราฟรายวัน: Ad Cost, Total Commission และ Profit")

    try:
        import matplotlib.pyplot as plt

        # เตรียมข้อมูล Ads รายวัน
        if not df_ads.empty:
            df_ads['Day'] = pd.to_datetime(df_ads['Day'], errors='coerce')
            ads_daily = df_ads.groupby('Day').agg({'Amount spent (THB)': 'sum'}).reset_index()
            ads_daily.rename(columns={'Day': 'Date', 'Amount spent (THB)': 'Ad Cost'}, inplace=True)
        else:
            ads_daily = pd.DataFrame(columns=['Date', 'Ad Cost'])

        # เตรียมข้อมูล Shopee รายวัน
        if not df_shopee.empty:
            df_shopee['เวลาที่สั่งซื้อ'] = pd.to_datetime(df_shopee['เวลาที่สั่งซื้อ'], errors='coerce')
            shopee_daily = df_shopee.groupby(df_shopee['เวลาที่สั่งซื้อ'].dt.date).agg({'คอมมิชชั่นสินค้าโดยรวม(฿)': 'sum'}).reset_index()
            shopee_daily.rename(columns={'เวลาที่สั่งซื้อ': 'Date', 'คอมมิชชั่นสินค้าโดยรวม(฿)': 'Shopee Com'}, inplace=True)
            shopee_daily['Date'] = pd.to_datetime(shopee_daily['Date'])
        else:
            shopee_daily = pd.DataFrame(columns=['Date', 'Shopee Com'])

        # เตรียมข้อมูล Lazada รายวัน
        if not df_lazada.empty and 'Conversion Time' in df_lazada.columns:
            df_lazada['Conversion Time'] = pd.to_datetime(df_lazada['Conversion Time'], errors='coerce')
            lazada_daily = df_lazada.groupby(df_lazada['Conversion Time'].dt.date).agg({'Payout': 'sum'}).reset_index()
            lazada_daily.rename(columns={'Conversion Time': 'Date', 'Payout': 'Lazada Com'}, inplace=True)
            lazada_daily['Date'] = pd.to_datetime(lazada_daily['Date'])
        else:
            lazada_daily = pd.DataFrame(columns=['Date', 'Lazada Com'])

        # รวมข้อมูลทั้งหมด
        daily = pd.merge(ads_daily, shopee_daily, on='Date', how='outer')
        daily = pd.merge(daily, lazada_daily, on='Date', how='outer')
        daily = daily.fillna(0)

        # คำนวณ Total Com และ Profit
        daily['Total Com'] = daily['Shopee Com'] + daily['Lazada Com']
        daily['Profit'] = daily['Total Com'] - daily['Ad Cost']

        # เรียงลำดับตามวันที่
        daily = daily.sort_values('Date')

        if not daily.empty:
            # วาดกราฟ
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(daily['Date'], daily['Ad Cost'], label='Ad Cost', marker='o', linewidth=2)
            ax.plot(daily['Date'], daily['Total Com'], label='Total Commission', marker='s', linewidth=2)
            ax.plot(daily['Date'], daily['Profit'], label='Profit', marker='^', linewidth=2)
            ax.set_xlabel('วันที่')
            ax.set_ylabel('จำนวนเงิน (บาท)')
            ax.set_title("📊 รายวัน: Ad Cost vs Total Com vs Profit")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # ปรับแกน x ให้แสดงวันที่อย่างชัดเจน
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # แสดงตารางข้อมูลรายวัน
            st.markdown("#### 📋 ข้อมูลรายวัน:")
            daily_display = daily.copy()
            daily_display['Date'] = daily_display['Date'].dt.strftime('%d/%m/%Y')
            for col in ['Ad Cost', 'Shopee Com', 'Lazada Com', 'Total Com', 'Profit']:
                daily_display[col] = daily_display[col].apply(lambda x: f"฿{x:,.2f}")
            
            st.dataframe(
                daily_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("📅 วันที่", width="medium"),
                    "Ad Cost": st.column_config.TextColumn("💰 Ad Cost", width="medium"),
                    "Shopee Com": st.column_config.TextColumn("🛒 Shopee Com", width="medium"),
                    "Lazada Com": st.column_config.TextColumn("🛍️ Lazada Com", width="medium"),
                    "Total Com": st.column_config.TextColumn("💎 Total Com", width="medium"),
                    "Profit": st.column_config.TextColumn("📈 Profit", width="medium")
                }
            )
            
            # เพิ่มแถวรวมยอดสำหรับตารางรายวัน
            st.markdown("#### 📊 สรุปรวม (รายวัน):")
            daily_total = pd.DataFrame([{
                'รายการ': 'รวมทั้งหมด',
                'Ad Cost': f"฿{daily['Ad Cost'].sum():,.2f}",
                'Shopee Com': f"฿{daily['Shopee Com'].sum():,.2f}",
                'Lazada Com': f"฿{daily['Lazada Com'].sum():,.2f}",
                'Total Com': f"฿{daily['Total Com'].sum():,.2f}",
                'Profit': f"฿{daily['Profit'].sum():,.2f}"
            }])
            
            st.dataframe(
                daily_total,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "รายการ": st.column_config.TextColumn("📋 รายการ", width="medium"),
                    "Ad Cost": st.column_config.TextColumn("💰 Ad Cost", width="medium"),
                    "Shopee Com": st.column_config.TextColumn("🛒 Shopee Com", width="medium"),
                    "Lazada Com": st.column_config.TextColumn("🛍️ Lazada Com", width="medium"),
                    "Total Com": st.column_config.TextColumn("💎 Total Com", width="medium"),
                    "Profit": st.column_config.TextColumn("📈 Profit", width="medium")
                }
            )
        else:
            st.info("ไม่มีข้อมูลรายวันเพื่อแสดงกราฟ")

    except Exception as e:
        st.warning(f"ไม่สามารถแสดงกราฟรายวันได้: {e}")

else:
    st.info("กรุณาอัปโหลดไฟล์อย่างน้อย Shopee หรือ Lazada Commission เพื่อเริ่มต้นการคำนวณ")
