import streamlit as st
import pandas as pd
from io import BytesIO

# --- 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询系统", layout="centered", page_icon="⚓")

# --- 1. 密码保护逻辑 ---
def check_password():
    """验证成功返回 True，否则显示输入框并返回 False"""
    def password_entered():
        # 优先从 Secrets 读取，如果没有设置则默认 123456
        if st.session_state["password"] == st.secrets.get("my_password", "123456"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 内部系统，请输入授权密码")
        st.text_input("授权密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码错误，请重新输入", type="password", on_change=password_entered, key="password")
        st.error("🚫 验证失败")
        return False
    return True

# --- 2. 主程序入口 ---
if check_password():
    st.title("🚢 ND曲轴 CCS 证书数据查询")
    st.markdown("---")

    # 数据加载函数
    @st.cache_data
    def load_data():
        try:
            # 读取 Excel 工作表 CCS
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
        except Exception:
            try:
                # 兼容备份 CSV 文件
                df = pd.read_csv("ND曲轴.xlsx - CCS.csv")
            except Exception:
                st.error("❌ 错误：未找到数据库文件 'ND曲轴.xlsx'。请确保文件已上传至 GitHub 仓库。")
                return None
        
        # 预处理：将船检时间转换为日期对象，便于后续格式化
        if '船检时间' in df.columns:
            df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
        return df

    df = load_data()

    if df is not None:
        # 搜索输入
        search_id = st.text_input("请输入轴号进行查询 (支持模糊搜索):", placeholder="例如: 2005L6")
        
        if search_id:
            # 在‘轴号’列执行部分匹配 (不区分大小写)
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not results.empty:
                st.success(f"✅ 查询成功：找到 {len(results)} 条匹配记录")
                
                # 遍历结果并按模版显示
                for _, row in results.iterrows():
                    with st.container():
                        st.markdown(f"### 📋 轴号：{row['轴号']}")
                        
                        # --- 按照指定顺序显视字段 ---
                        st.markdown(f"**名称：** {row.get('名称', 'N/A')}")
                        st.markdown(f"**轴号：** {row.get('轴号', 'N/A')}")
                        st.markdown(f"**材质：** {row.get('材质', 'N/A')}")
                        st.markdown(f"**炉号：** {row.get('炉号', 'N/A')}")
                        
                        # 插入固定行
                        st.markdown("**CRRC ZJ**")
                        st.markdown("**UT  MT**")
                        
                        st.markdown(f"**船检控制号：** {row.get('船检控制号', 'N/A')}")
                        
                        # 船检时间上加入 CCS
                        st.markdown("**CCS**")
                        
                        # 处理日期显示：日-月-年 (DD-MM-YYYY)
                        raw_date = row.get('船检时间', None)
                        if pd.notnull(raw_date):
                            formatted_date = raw_date.strftime('%d-%m-%Y')
                        else:
                            formatted_date = 'N/A'
                            
                        st.markdown(f"**船检时间：** {formatted_date}")
                        
                        st.divider() # 分割线
                
                # 结果导出功能
                towrite = BytesIO()
                results.to_excel(towrite, index=False, engine='openpyxl')
                towrite.seek(0)
                st.download_button(
                    label="📥 导出当前查询结果为 Excel",
                    data=towrite,
                    file_name=f"ND_{search_id}_Results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning(f"⚠️ 未找到包含 '{search_id}' 的轴号，请检查输入。")
        else:
            st.info("💡 请在输入框中输入轴号开始检索。")

# 侧边栏版权信息
st.sidebar.markdown("---")
st.sidebar.caption("ND曲轴管理系统 | 内部专用")