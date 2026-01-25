import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# --- 功能函数：图片转 Base64 (用于网页显示) ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- 功能函数：生成结果图片 (用于下载) ---
def create_result_image(row, logo_path):
    # 创建一张白底图片 (宽 800, 高 600)
    img = Image.new('RGB', (800, 700), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 尝试加载中文字体 (Streamlit Cloud 通常有 NotoSansCJK 或 DejaVuSans)
    # 如果本地运行，请确保路径正确，或使用默认字体
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        font_text = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # 绘制边框
    draw.rectangle([20, 20, 780, 680], outline=(0, 0, 0), width=2)
    
    # 标题
    draw.text((40, 50), f"ND Crankshaft Data: {row['轴号']}", fill=(0, 0, 0), font=font_title)
    
    # 绘制表格内容
    y_pos = 120
    data_items = [
        ("Name", row.get('名称', 'N/A')),
        ("Serial No", row.get('轴号', 'N/A')),
        ("Material", row.get('材质', 'N/A')),
        ("Heat No", row.get('炉号', 'N/A')),
        ("Manufacturer", "CRRC ZJ"),
        ("Inspection", "UT  MT"),
        ("Control No", row.get('船检控制号', 'N/A')),
        ("Agency", "CCS"),
        ("Date", row.get('船检时间', 'N/A').strftime('%d-%m-%Y') if pd.notnull(row.get('船检时间')) else 'N/A')
    ]
    
    for label, value in data_items:
        draw.line([40, y_pos + 35, 760, y_pos + 35], fill=(200, 200, 200), width=1)
        draw.text((50, y_pos), f"{label}:", fill=(100, 100, 100), font=font_text)
        draw.text((250, y_pos), str(value), fill=(0, 0, 0), font=font_text)
        y_pos += 50

    # 合成 CCS 图标
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((100, 50)) # 缩放图标
        img.paste(logo, (650, 40), logo)

    # 保存到内存
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# --- 自定义 CSS (网页版表格) ---
st.markdown("""
    <style>
    .result-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 2px solid #333; }
    .result-table td { border: 1px solid #dee2e6; padding: 12px; }
    .label-cell { background-color: #f8f9fa; font-weight: bold; width: 30%; }
    .ccs-logo { height: 35px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 密码保护 (略，同之前) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), key="password")
        return False
    return st.session_state["password_correct"]

# --- 4. 主程序 ---
if check_password():
    st.title("🚢 ND曲轴证书查询 & 图片导出")
    
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            if '船检时间' in df.columns:
                df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except: return None

    df = load_data()
    img_base64 = get_image_base64("CCS.png")

    if df is not None:
        search_id = st.text_input("输入轴号查询:")
        
        if search_id:
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            for _, row in results.iterrows():
                # 网页显示版
                fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                ccs_html = f'<img src="data:image/png;base64,{img_base64}" class="ccs-logo">' if img_base64 else "CCS"
                
                html_table = f"""
                <table class="result-table">
                    <tr><td class="label-cell">名称</td><td>{row['名称']}</td></tr>
                    <tr><td class="label-cell">轴号</td><td>{row['轴号']}</td></tr>
                    <tr><td class="label-cell">炉号</td><td>{row['炉号']}</td></tr>
                    <tr><td class="label-cell">制造单位</td><td>CRRC ZJ</td></tr>
                    <tr><td class="label-cell">检测方式</td><td>UT  MT</td></tr>
                    <tr><td class="label-cell">检验机构</td><td>{ccs_html}</td></tr>
                    <tr><td class="label-cell">船检时间</td><td><b>{fmt_date}</b></td></tr>
                </table>
                """
                st.markdown(html_table, unsafe_allow_html=True)
                
                # --- 图片生成与导出 ---
                img_data = create_result_image(row, "CCS.png")
                st.download_button(
                    label=f"🖼️ 点击下载图片 ({row['轴号']}.png)",
                    data=img_data,
                    file_name=f"{row['轴号']}.png",
                    mime="image/png"
                )
                st.divider()