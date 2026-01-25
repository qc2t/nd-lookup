import streamlit as st
import pandas as pd

# 页面配置
st.set_page_config(page_title="ND曲轴查询系统", layout="centered")

# 读取数据
@st.cache_data
def load_data():
    # 这里建议直接使用你的 Excel 文件名
    try:
        df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
        return df
    except:
        # 兼容你上传的 CSV 文件名
        return pd.read_csv("ND曲轴.xlsx - CCS.csv")

df = load_data()

st.title("🚢 ND曲轴 CCS 证书信息查询")
st.info("在下方输入轴号，系统将自动检索 CCS 数据库中的相关记录。")

# 查询输入框
search_id = st.text_input("请输入轴号 (如: 2005L6-366)", placeholder="点击此处输入...")

if search_id:
    # 逻辑查询
    res = df[df['轴号'].str.contains(search_id, na=False)]
    
    if not res.empty:
        # 如果有多条匹配，显示列表
        for index, row in res.iterrows():
            with st.container():
                st.markdown(f"### 🔍 轴号: {row['轴号']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("材质", row['材质'])
                c2.metric("炉号", row['炉号'])
                c3.metric("验船师", row['验船师'])
                
                # 详细信息表格化
                st.table(row[['证件编号', '图号', '船检控制号', '船检时间', '证书返回时间']].to_frame().T)
                st.divider()
    else:
        st.warning("⚠️ 未找到匹配的轴号，请核对。")