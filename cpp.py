import streamlit as st
import pandas as pd
from io import BytesIO

# 页面设置：设置为宽屏模式，更像专业后台
st.set_page_config(page_title="ND曲轴查询系统", layout="wide", page_icon="🚢")

# --- 1. 安全密码校验 ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["my_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 内部系统，请验证身份")
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码错误，请重试", type="password", on_change=password_entered, key="password")
        st.error("🚫 密码不正确，请联系系统管理员")
        return False
    return True

# --- 2. 核心业务逻辑 ---
if check_password():
    # 界面标题
    st.title("🚢 ND曲轴 CCS 证书查询系统")
    st.markdown("---")

    # 数据加载（带缓存功能，提升速度）
    @st.cache_data
    def load_data():
        try:
            # 优先读取 Excel，备选 CSV
            return pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
        except:
            return pd.read_csv("ND曲轴.xlsx - CCS.csv")

    df = load_data()

    if df is not None:
        # 查询区域
        search_id = st.text_input("🔍 输入轴号进行查询 (支持部分搜索):", placeholder="例如: 2005L6")

        if search_id:
            # 搜索逻辑：忽略大小写，匹配轴号列
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not results.empty:
                st.success(f"找到 {len(results)} 条相关匹配记录")
                
                # --- 卡片式结果显视 ---
                for index, row in results.iterrows():
                    # 为每一条结果创建一个美观的容器
                    with st.expander(f"📋 轴号：{row['轴号']} (详情点击展开)", expanded=True):
                        # 第一行：三个关键指标
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**材质:** `{row.get('材质', 'N/A')}`")
                        c2.markdown(f"**炉号:** `{row.get('炉号', 'N/A')}`")
                        c3.markdown(f"**验船师:** `{row.get('验船师', 'N/A')}`")
                        
                        # 第二行：证书与图纸信息
                        c4, c5, c6 = st.columns(3)
                        c4.write(f"**证件编号:** {row.get('证件编号', 'N/A')}")
                        c5.write(f"**图号:** {row.get('图号', 'N/A')}")
                        c6.write(f"**船检控制号:** {row.get('船检控制号', 'N/A')}")
                        
                        # 第三行：时间节点
                        st.divider()
                        c7, c8, c9 = st.columns(3)
                        c7.info(f"📅 船检时间: {row.get('船检时间', 'N/A')}")
                        c8.info(f"📦 取件时间: {row.get('取件时间', 'N/A')}")
                        c9.info(f"📑 证书返回: {row.get('证书返回时间', 'N/A')}")

                # --- 导出功能 ---
                st.markdown("---")
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    results.to_excel(writer, index=False)
                st.download_button(
                    label="📥 点击下载上方查询结果为 Excel",
                    data=output.getvalue(),
                    file_name=f"查询结果_{search_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("☹️ 未找到该轴号，请检查输入是否有误。")
        else:
            st.info("💡 请在上方输入框输入轴号，系统将自动检索 CCS 数据库。")

# 侧边栏辅助说明
st.sidebar.image("https://www.ccs.org.cn/ccswz/images/logo.png", width=100) # 这里可以换成你公司的LOGO
st.sidebar.title("操作指南")
st.sidebar.info("1. 输入轴号部分关键字即可模糊搜索。\n2. 手机端建议横屏查看以获得最佳效果。")