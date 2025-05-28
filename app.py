# 📁 app.py (เพิ่ม dropdown filter กรองตาม Sub_id2 + ช่องสรุปด้านบน)

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Affiliate Profit Dashboard", layout="wide")
st.title("📊 Affiliate Profit Dashboard")

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
    df_shopee = df_shopee.dropna(subset=['Sub_id4', 'คอมมิชชั่นสินค้าโดยรวม(฿)', 'รหัสการสั่งซื้อ'])
    df_shopee_grouped = df_shopee.groupby('Sub_id4').agg({
        'คอมมิชชั่นสินค้าโดยรวม(฿)': 'sum',
        'รหัสการสั่งซื้อ': 'nunique'
    }).reset_index().rename(columns={
        'คอมมิชชั่นสินค้าโดยรวม(฿)': 'Shopee Com',
        'รหัสการสั่งซื้อ': 'Order Count'
    })
else:
    df_shopee_grouped = pd.DataFrame(columns=['Sub_id4', 'Shopee Com', 'Order Count'])

# ===================== Lazada =====================
if lzd_file:
    df_lazada = read_file(lzd_file)
    df_lazada['Sub_id4'] = df_lazada['Sub ID 3'].fillna(df_lazada['Sub ID 1'])
    df_lazada = df_lazada.dropna(subset=['Sub_id4', 'Payout'])
    df_lazada = df_lazada[df_lazada['Sub_id4'] != 'paris']
    df_lazada_grouped = df_lazada.groupby('Sub_id4').agg({
        'Payout': 'sum',
        'Order Amount': 'sum'
    }).reset_index().rename(columns={
        'Payout': 'Lazada Com',
        'Order Amount': 'LZD Order Amount'
    })
else:
    df_lazada_grouped = pd.DataFrame(columns=['Sub_id4', 'Lazada Com', 'LZD Order Amount'])

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

    if ads_file:
        df_ads = read_file(ads_file)
        df_ads = df_ads.dropna(subset=['Ad name', 'Amount spent (THB)', 'Unique link clicks'])
        ad_costs, clicks = [], []
        for sub_id in summary['Sub_id4']:
            matched = df_ads[df_ads['Ad name'].str.contains(sub_id, na=False)]
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

    # ===== กรอง Sub_id2 =====
    shopee_platforms = df_shopee['Sub_id2'].dropna().unique().tolist() if not df_shopee.empty else []
    lazada_platforms = df_lazada['Sub ID 2'].dropna().unique().tolist() if not df_lazada.empty else []
    platform_options = list(set(shopee_platforms + lazada_platforms))
    selected_platform = st.selectbox("🔎 กรองตามแพลตฟอร์ม (Sub_id2):", ['ทั้งหมด'] + platform_options)

    if selected_platform != 'ทั้งหมด':
        shopee_match = df_shopee[df_shopee['Sub_id2'] == selected_platform]['Sub_id4'].unique() if not df_shopee.empty else []
        lazada_match = df_lazada[df_lazada['Sub ID 2'] == selected_platform]['Sub_id4'].unique() if not df_lazada.empty else []
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
    if sort_column != 'Sub_id4':
        summary_sorted = summary_for_display.sort_values(by=sort_column, ascending=ascending)
    else:
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

    # วาดกราฟ
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(daily['Date'], daily['Ad Cost'], label='Ad Cost', marker='o')
    ax.plot(daily['Date'], daily['Total Com'], label='Total Commission', marker='s')
    ax.plot(daily['Date'], daily['Profit'], label='Profit', marker='^')
    ax.set_xlabel('วันที่')
    ax.set_ylabel('จำนวนเงิน (บาท)')
    ax.set_title("📊 รายวัน: Ad Cost vs Total Com vs Profit")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

except Exception as e:
    st.warning(f"ไม่สามารถแสดงกราฟรายวันได้: {e}")

else:
    st.info("กรุณาอัปโหลดไฟล์อย่างน้อย Shopee หรือ Lazada Commission เพื่อเริ่มต้นการคำนวณ.")