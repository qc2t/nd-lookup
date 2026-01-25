import streamlit as st
import pandas as pd
from io import BytesIO

# 页面基础设置
st.set_page_config(page_title="ND曲轴CCS查询系统", layout="wide")

# --- 1. 密码验证逻辑 ---
def check_password():
    def password_entered():
        # 这里对应你在 Streamlit 后台 Secrets 设置的键值
        if st.session_state["password"] == st.secrets["my_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码错误，请重试", type="password", on_change=password_entered, key="password")
        st.error("🚫 鉴权失败")
        return False
    return True

# --- 2. 主程序 ---
if check_password():
    st.title("🚢 ND曲轴 CCS 证书数据查询系统")
    
    # 缓存数据读取
    @st.cache_data
    def load_data():
        # 自动识别文件名，建议在仓库里文件名统一为 ND曲轴.xlsx
        try:
            return pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
        except Exception as e:
            st.error(f"无法读取文件: {e}")
            return None

    df = load_data()

    if df is not None:
        # 查询界面
        search_id = st.text_input("🔍 输入轴号搜索 (支持部分输入)", placeholder="例如: 2005L6")

        if search_id:
            # 过滤数据
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not results.empty:
                st.success(f"共找到 {len(results)} 条相关记录")
                
                # 展示表格
                st.dataframe(results, use_container_width=True)
                
                # 导出功能
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    results.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 下载查询结果为 Excel",
                    data=output.getvalue(),
                    file_name=f"查询结果_{search_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("未匹配到任何数据，请检查轴号是否正确。")
        else:
            st.info("💡 请在上方输入框输入轴号开始查询。")