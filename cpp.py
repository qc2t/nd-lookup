import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import re  # 导入正则模块用于提取型号

# --- 1. 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# CSS：手机端极致优化
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none !important;}
    div[data-testid="stStatusWidget"] {display:none !important;}
    
    .report-table { width: 100%; border-collapse: collapse; margin-top: 10px; border: 4px solid #004080; }
    .report-table td { border: 1px solid #004080; padding: 22px 15px; line-height: 1.2; }
    .label-col { background-color: #004080 !important; color: #ffffff !important; font-weight: bold; font-size: 24px !important; width: 35%; text-align: center; }
    .value-col { background-color: #ffffff; font-weight: 900; font-size: 34px !important; color: #002b55; width: 65%; }
    .ccs-logo-img { height: 65px; vertical-align: middle; }

    div.stDownloadButton > button {
        width: 100% !important; height: 85px !important; font-size: 28px !important;
        font-weight: bold !important; background-color: #FF8C00 !important;
        color: white !important; border-radius: 12px !important;
    }
    input { font-size: 28px !important; height: 65px !important; border: 2px solid #004080 !important; }
    div[data-testid="column"] button { height: 65px !important; background-color: #004080 !important; color: white !important; font-size: 24px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 辅助函数 ---

def extract_model(name_str):
    """从名称中提取数字和字母部分 (例如: 宁波中策6NL30曲轴 -> 6NL30)"""
    match = re.search(r'[A-Za-z0-9]+', str(name_str))
    return match.group(0) if match else "N/A"

def get_chinese_font(size):
    paths = ["simhei.ttf", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "C:/Windows/Fonts/simhei.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_report_image(row, logo_path):
    """图片生成：型号动态提取"""
    width, height = 800, 1300
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_b = get_chinese_font(40)
    font_s = get_chinese_font(30)

    # 获取提取后的型号
    model_val = extract_model(row.get('名称', ''))

    draw.rectangle([20, 20, 780, 1280], outline=(0, 64, 128), width=6)
    draw.text((60, 60), "ND CRANKSHAFT DATA REPORT", fill=(0, 64, 128), font=font_b)

    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
    
    items = [
        ("名  称", str(row.get('名称', 'N/A'))),
        ("机  型", model_val),  # 动态型号
        ("图  号", str(row.get('图号', 'N/A'))),
        ("轴  号", str(row.get('轴号', 'N/A'))),
        ("材  质", str(row.get('材质', 'N/A'))),
        ("炉  号", str(row.get('炉号', 'N/A'))),
        ("制造单位", "CRRC ZJ"),
        ("检测方式", "UT  MT"),
        ("船检控制号", str(row.get('船检控制号', 'N/A'))),
        ("检验机构", "LOGO_MARK"), 
        ("船检时间", fmt_date)
    ]

    y = 155
    for label, value in items:
        draw.line([60, y + 75, 740, y + 75], fill=(200, 200, 200), width=2)
        draw.text((80, y), f"{label}:", fill=(100, 100, 100), font=font_s)
        if value == "LOGO_MARK":
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo.thumbnail((200, 80))
                img.paste(logo, (320, y - 5), logo)
            else:
                draw.text((320, y), "CCS", fill=(0, 0, 0), font=font_s)
        else:
            draw.text((320, y), value, fill=(0, 0, 0), font=font_s)
        y += 100 

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. 查询逻辑 ---
if "password_correct" not in st.session_state:
    st.text_input("授权密码", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), key="password")
else:
    @st.cache_data
    def load_data(v="1.2"): 
        try:
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            if '船检时间' in df.columns:
                df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except: return None

    df = load_data()
    
    logo_b64 = None
    if os.path.exists("CCS.png"):
        with open("CCS.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    if df is not None:
        st.markdown("<h1 style='color:#004080; text-align:center;'>🚢 ND曲轴证书查询</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([0.75, 0.25])
        with col1: search_id = st.text_input("", placeholder="输入轴号...", label_visibility="collapsed", key="search_input")
        with col2: search_clicked = st.button("查询", use_container_width=True)

        if search_id or search_clicked:
            if search_id:
                res = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
                if not res.empty:
                    for index, row in res.iterrows():
                        fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                        ccs_html = f'<img src="data:image/png;base64,{logo_b64}" class="ccs-logo-img">' if logo_b64 else "CCS"
                        
                        # 动态提取机型
                        current_model = extract_model(row['名称'])
                        
                        st.markdown(f"""
                        <table class="report-table">
                            <tr><td class="label-col">名 称</td><td class="value-col">{row['名称']}</td></tr>
                            <tr><td class="label-col">机 型</td><td class="value-col">{current_model}</td></tr>
                            <tr><td class="label-col">图 号</td><td class="value-col">{row.get('图号', 'N/A')}</td></tr>
                            <tr><td class="label-col">轴 号</td><td class="value-col">{row['轴号']}</td></tr>
                            <tr><td class="label-col">材 质</td><td class="value-col">{row['材质']}</td></tr>
                            <tr><td class="label-col">炉 号</td><td class="value-col">{row['炉号']}</td></tr>
                            <tr><td class="label-col">制 造</td><td class="value-col">CRRC ZJ</td></tr>
                            <tr><td class="label-col">检 测</td><td class="value-col">UT  MT</td></tr>
                            <tr><td class="label-col">控 制 号</td><td class="value-col">{row['船检控制号']}</td></tr>
                            <tr><td class="label-col">机 构</td><td class="value-col">{ccs_html}</td></tr>
                            <tr><td class="label-col">时 间</td><td class="value-col">{fmt_date}</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                        
                        img_data = create_report_image(row, "CCS.png")
                        st.download_button(
                            label=f"📥 下载图片：{row['轴号']}.png",
                            data=img_data,
                            file_name=f"{row['轴号']}.png",
                            mime="image/png",
                            key=f"btn_{row['轴号']}_{index}"
                        )
                        st.divider()