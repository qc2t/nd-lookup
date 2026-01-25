import streamlit as st
import pandas as pd
from io import BytesIO

# 页面配置
st.set_page_config(page_title="ND曲轴数据查询", layout="wide")

# --- 1. 密码保护 (从 Secrets 读取) ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["my_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码不正确", type="password", on_change=password_entered, key="password")
        st.error("🔒 权限不足")
        return False
    return True

# --- 2. 查询逻辑 ---
if check_password():
    st.title("🔍 ND曲轴 CCS 证书查询视图")
    
    @st.cache_data
    def load_data():
        try:
            # 兼容你上传的文件名
            return pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
        except:
            return pd.read_csv("ND曲轴.xlsx - CCS.csv")

    df = load_data()

    if df is not None:
        search_id = st.text_input("请输入轴号（支持部分匹配）:", placeholder="输入后按回车...")

        if search_id:
            # 过滤结果
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not results.empty:
                st.info(f"为您找到 {len(results)} 条记录")
                
                for _, row in results.iterrows():
                    # --- 核心：复刻图中的表单展示格式 ---
                    with st.container():
                        # 使用 HTML 装饰一下标题
                        st.markdown(f"### 📋 轴号：{row['轴号']}")
                        
                        # 第一行
                        r1_c1 = st.columns(1)
                        r1_c1.markdown(f"**名称：** {row.get('名称', 'N/A')}")
                        # 第二行
                        r2_c1 = st.columns(1)
                        r2_c1.markdown(f"**轴号：** {row.get('轴号', 'N/A')}")
                        # 第三行
                        r3_c1 = st.columns(1)
                         r3_c1.markdown(f"**材质：** {row.get('材质', 'N/A')}")
                        # 第四行
                        r4_c1 = st.columns(1)
                        r4_c1.markdown(f"**炉号：** {row.get('炉号', 'N/A')}")
                        # 第五行
                        r5_c1 = st.columns(1) 
                        r5_c1.markdown(f"**船检控制号：** {row.get('船检控制号', 'N/A')}")
                        # 第六行
                        r6_c1 = st.columns(1) 
                        r6_c1.markdown(f"**船检时间：** {row.get('船检时间', 'N/A')}")
                     
                        st.divider() # 分割线，区分多条结果
                
                # 导出按钮
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    results.to_excel(writer, index=False)
                st.download_button("📥 导出当前查询结果", output.getvalue(), f"{search_id}.xlsx")
            else:
                st.warning("查无数据。")