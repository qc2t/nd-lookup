import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# CSS：专门针对手机端大幅调大字号
st.markdown("""
    <style>
    /* 整体表格样式 */
    .report-table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 15px; 
        border: 3px solid #000; /* 加粗外边框 */
    }
    .report-table td { 
        border: 1px solid #444; 
        padding: 15px;      /* 增加内边距 */
        font-size: 22px;    /* 手机端核心：大幅增加字号 */
        line-height: 1.4;
    }
    /* 左侧标签列 */
    .label-col { 
        background-color: #f2f2f2; 
        font-weight: bold; 
        width: 40%;         /* 调整比例适配手机 */
        color: #000;
    }
    /* 右侧内容列 */
    .value-col { 
        width: 60%; 
        background-color: #ffffff; 
        font-weight: 600;   /* 文字加粗 */
        color: #000;
    }
    /* CCS 图标缩放 */
    .ccs-logo-img { 
        height: 45px;       /* 图标调大 */
        vertical-align: middle; 
    }
    /* 调整 Streamlit 默认按钮样式，使其在手机上更好点 */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 60px !important;
        font-size: 20px !important;
        background-color: #007bff !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心函数 ---

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_chinese_font(size):
    """自动寻找中文字体，解决图片乱码"""
    paths = ["simhei.ttf", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "C:/Windows/Fonts/simhei.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_report_image(row, logo_path):
    """生成证书图片：图标精准定位在检验机构行"""
    width, height = 800, 1000 # 增加高度
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_b = get_chinese_font(36) # 图片字体也同步调大
    font_s = get_chinese_font(28)

    draw.rectangle([25, 25, 775, 975], outline=(0, 0, 0), width=4)
    draw.text((55, 60), "ND CRANKSHAFT INSPECTION RECORD", fill=(0, 0, 0), font=font_b)

    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
    items = [
        ("名  称", str(row.get('名称', 'N/A'))),
        ("轴  号", str(row.get('轴号', 'N/A'))),
        ("材  质", str(row.get('材质', 'N/A'))),
        ("炉  号", str(row.get('炉号', 'N/A'))),
        ("制造单位", "CRRC ZJ"),
        ("检测方式", "UT  MT"),
        ("船检控制号", str(row.get('船检控制号', 'N/A'))),
        ("检验机构", "LOGO_MARK"), 
        ("船检时间", fmt_date)
    ]

    y = 160
    for label, value in items:
        draw.line([55, y + 55, 745, y + 55], fill=(200, 200, 200), width=1)
        draw.text((70, y), f"{label}:", fill=(100, 100, 100), font=font_s)
        if value == "LOGO_MARK":
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo.thumbnail((150, 55))
                img.paste(logo, (300, y - 5), logo)
            else:
                draw.text((300, y), "CCS", fill=(0, 0, 0), font=font_s)
        else:
            draw.text((300, y), value, fill=(0, 0, 0), font=font_s)
        y += 85 # 行间距拉大

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. 密码与主逻辑 ---
if "password_correct" not in st.session_state:
    st.markdown("## 🔒 授权查询系统")
    st.text_input("请输入访问密码", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), key="password")
else:
    st.title("🚢 ND曲轴证书查询 (手机版)")
    
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except: return None

    df = load_data()
    logo_b64 = get_image_base64("CCS.png")

    if df is not None:
        search_id = st.text_input("🔍 轴号搜索:", placeholder="输入轴号...")
        if search_id:
            res = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            if not res.empty:
                for index, row in res.iterrows():
                    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                    ccs_html = f'<img src="data:image/png;base64,{logo_b64}" class="ccs-logo-img">' if logo_b64 else "CCS"
                    
                    st.markdown(f"""
                    <table class="report-table">
                        <tr><td class="label-col">名称</td><td class="value-col">{row['名称']}</td></tr>
                        <tr><td class="label-col">轴号</td><td class="value-col">{row['轴号']}</td></tr>
                        <tr><td class="label-col">材质</td><td class="value-col">{row['材质']}</td></tr>
                        <tr><td class="label-col">炉号</td><td class="value-col">{row['炉号']}</td></tr>
                        <tr><td class="label-col">制造单位</td><td class="value-col">CRRC ZJ</td></tr>
                        <tr><td class="label-col">检测方式</td><td class="value-col">UT  MT</td></tr>
                        <tr><td class="label-col">船检控制号</td><td class="value-col">{row['船检控制号']}</td></tr>
                        <tr><td class="label-col">检验机构</td><td class="value-col">{ccs_html}</td></tr>
                        <tr><td class="label-col">船检时间</td><td class="value-col"><b>{fmt_date}</b></td></tr>
                    </table>
                    """, unsafe_allow_html=True)
                    
                    img_data = create_report_image(row, "CCS.png")
                    st.download_button(
                        label=f"💾 下载图片：{row['轴号']}.png",
                        data=img_data,
                        file_name=f"{row['轴号']}.png",
                        mime="image/png",
                        key=f"btn_{row['轴号']}_{index}"
                    )
                    st.divider()
            else:
                st.warning("查无记录")