import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# 自定义网页 CSS 样式 (用于网页端的表格显示)
st.markdown("""
    <style>
    .result-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 2px solid #333; }
    .result-table td { border: 1px solid #dee2e6; padding: 12px; font-size: 16px; }
    .label-cell { background-color: #f8f9fa; font-weight: bold; width: 35%; color: #333; }
    .value-cell { width: 65%; color: #000; font-weight: 500; }
    .ccs-logo { height: 35px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

# --- 函数：读取图片并转为 Base64 ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- 函数：寻找可用中文字体 ---
def get_font(size):
    # 1. 优先尝试仓库中上传的 simhei.ttf
    font_paths = [
        "simhei.ttf", 
        "simsun.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", # Linux/Streamlit Cloud 常用路径
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # 2. 如果都没找到，只能返回默认（中文会乱码）
    st.warning("⚠️ 未检测到中文字体文件，请上传 simhei.ttf 到 GitHub 仓库以修复图片乱码。")
    return ImageFont.load_default()

# --- 函数：生成证书样式的图片 ---
def create_styled_image(row, logo_path):
    img = Image.new('RGB', (800, 850), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 加载字体
    font_b = get_font(30)
    font_s = get_font(24)

    # 绘制外边框
    draw.rectangle([30, 30, 770, 820], outline=(0, 0, 0), width=3)
    
    # 标题
    draw.text((60, 60), "ND CRANKSHAFT DATA REPORT", fill=(0, 0, 0), font=font_b)
    
    # 绘制数据内容
    y = 150
    data = [
        ("名  称", row.get('名称', 'N/A')),
        ("轴  号", row.get('轴号', 'N/A')),
        ("材  质", row.get('材质', 'N/A')),
        ("炉  号", row.get('炉号', 'N/A')),
        ("制造单位", "CRRC ZJ"),
        ("检测方式", "UT  MT"),
        ("船检控制号", row.get('船检控制号', 'N/A')),
        ("检验机构", "CCS"),
        ("船检时间", row.get('船检时间', 'N/A').strftime('%d-%m-%Y') if pd.notnull(row.get('船检时间')) else 'N/A')
    ]

    for label, value in data:
        draw.line([60, y + 45, 740, y + 45], fill=(200, 200, 200), width=1)
        draw.text((70, y), f"{label}:", fill=(100, 100, 100), font=font_s)
        draw.text((280, y), str(value), fill=(0, 0, 0), font=font_s)
        y += 70

    # 合成 CCS 图标
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((120, 60))
        img.paste(logo, (620, 55), logo)

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# --- 密码保护 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("请输入访问密码", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), key="password")
        return False
    return st.session_state["password_correct"]

# --- 主程序 ---
if check_password():
    st.title("🚢 ND曲轴查询 & 自动图片生成")
    
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except: return None

    df = load_data()
    img_b64 = get_image_base64("CCS.png")

    if df is not None:
        search_id = st.text_input("🔍 请输入轴号查询:")
        if search_id:
            results = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            for _, row in results.iterrows():
                # 1. 网页 HTML 预览
                fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                logo_html = f'<img src="data:image/png;base64,{img_b64}" class="ccs-logo">' if img_b64 else "CCS"
                
                table_html = f"""
                <table class="result-table">
                    <tr><td class="label-cell">名称</td><td class="value-cell">{row['名称']}</td></tr>
                    <tr><td class="label-cell">轴号</td><td class="value-cell">{row['轴号']}</td></tr>
                    <tr><td class="label-cell">材质</td><td class="value-cell">{row['材质']}</td></tr>
                    <tr><td class="label-cell">炉号</td><td class="value-cell">{row['炉号']}</td></tr>
                    <tr><td class="label-cell">制造单位</td><td class="value-cell">CRRC ZJ</td></tr>
                    <tr><td class="label-cell">检测方式</td><td class="value-cell">UT  MT</td></tr>
                    <tr><td class="label-cell">船检控制号</td><td class="value-cell">{row['船检控制号']}</td></tr>
                    <tr><td class="label-cell">检验机构</td><td class="value-cell">{logo_html}</td></tr>
                    <tr><td class="label-cell">船检时间</td><td class="value-cell"><b>{fmt_date}</b></td></tr>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
                # 2. 图片导出 (以轴号命名)
                img_bytes = create_styled_image(row, "CCS.png")
                st.download_button(
                    label=f"💾 点击下载证书图片：{row['轴号']}.png",
                    data=img_bytes,
                    file_name=f"{row['轴号']}.png",
                    mime="image/png"
                )
                st.divider()