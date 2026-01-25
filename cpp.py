import streamlit as st
import pandas as pd
from io import BytesIO
import base64
import os

# --- 页面配置 ---
st.set_page_config(page_title="ND曲轴查询系统", layout="centered", page_icon="⚓")

# 读取图片并转换为 Base64 (为了在 HTML 表格中稳定显示)
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# 自定义 CSS 样式
st.markdown("""
    <style>
    .result-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    .result-table td { border: 1px solid #dee2e6; padding: 12px; vertical-align: middle; }
    .label-cell { background-color: #f8f9fa; font-weight: bold; width: 30%; color: #333; }
    .value-cell { width: 70%; color: #000; }
    .ccs-logo { height: 30px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 密码保护 ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets.get("my_password", "123456"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码错误", type="password", on_change=password_entered, key="password")
        st.error("🚫 验证失败")
        return False
    return True

# --- 2. 主程序 ---
if check_password():
    st.title("🚢 ND曲轴 CCS 数据查询")
    
    # 获取 CCS 图标
    img_base64 = get_image_base64("CCS.png")
    if img_base64:
        ccs_display = f'<img src="data:image/png;base64,{img_base64}" class="ccs-logo">'
    else:
        ccs_display = "CCS (未找到图标)"

    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            if '船检时间' in df.columns:
                df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except:
            return None

    df = load_data()

    if df is not None:
        search_id = st.text_input("输入轴号查询:", placeholder="例如: 2005L6")
        
        if search_id:
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not results.empty:
                for _, row in results.iterrows():
                    raw_date = row.get('船检时间', None)
                    fmt_date = raw_date.strftime('%d-%m-%Y') if pd.notnull(raw_date) else 'N/A'
                    
                    # 构造表格，其中检验机构一行使用图标
                    html_table = f"""
                    <table class="result-table">
                        <tr><td class="label-cell">名称</td><td class="value-cell">{row.get('名称', 'N/A')}</td></tr>
                        <tr><td class="label-cell">轴号</td><td class="value-cell">{row.get('轴号', 'N/A')}</td></tr>
                        <tr><td class="label-cell">材质</td><td class="value-cell">{row.get('材质', 'N/A')}</td></tr>
                        <tr><td class="label-cell">炉号</td><td class="value-cell">{row.get('炉号', 'N/A')}</td></tr>
                        <tr><td class="label-cell">制造单位</td><td class="value-cell">CRRC ZJ</td></tr>
                        <tr><td class="label-cell">检测方式</td><td class="value-cell">UT  MT</td></tr>
                        <tr><td class="label-cell">船检控制号</td><td class="value-cell">{row.get('船检控制号', 'N/A')}</td></tr>
                        <tr><td class="label-cell">检验机构</td><td class="value-cell">{ccs_display}</td></tr>
                        <tr><td class="label-cell">船检时间</td><td class="value-cell"><b>{fmt_date}</b></td></tr>
                    </table>
                    """
                    st.markdown(html_table, unsafe_allow_html=True)
                
                # 导出按钮
                output = BytesIO()
                results.to_excel(output, index=False, engine='openpyxl')
                st.download_button("📥 导出结果", output.getvalue(), f"Result_{search_id}.xlsx")
            else:
                st.warning("查无数据。")