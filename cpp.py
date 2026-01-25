import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="ND查询-超大字号版", layout="centered", page_icon="⚓")

# CSS：极致字号优化
st.markdown("""
    <style>
    /* 全局背景和间距 */
    .main { background-color: #f9f9f9; }
    
    /* 表格整体：加粗边框 */
    .report-table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 10px; 
        border: 4px solid #000; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    
    /* 单元格：超大字号与超大间距 */
    .report-table td { 
        border: 1px solid #000; 
        padding: 20px 15px; /* 极大的内边距 */
        line-height: 1.2;
    }
    
    /* 左侧标签：高对比度黑底白字 */
    .label-col { 
        background-color: #333333 !important; 
        color: #ffffff !important; 
        font-weight: bold; 
        font-size: 24px !important;
        width: 35%;
        text-align: center;
    }
    
    /* 右侧数值：超大加粗深蓝色 */
    .value-col { 
        background-color: #ffffff; 
        font-weight: 900;   
        font-size: 32px !important; /* 核心字号推到32px */
        color: #003366;    /* 深蓝色更醒目 */
        width: 65%;
    }

    /* CCS 图标调大 */
    .ccs-logo-img { 
        height: 60px; 
        vertical-align: middle; 
    }

    /* 下载按钮：全屏宽度 + 亮橘色 + 巨型字 */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 80px !important;
        font-size: 28px !important;
        font-weight: bold !important;
        background-color: #FF8C00 !important; /* 亮橘色极其醒目 */
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0px 5px 15px rgba(255,140,0,0.4) !important;
    }
    
    /* 搜索框字号调大 */
    input {
        font-size: 26px !important;
        height: 60px !important;
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
    paths = ["simhei.ttf", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "C:/Windows/Fonts/simhei.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_report_image(row, logo_path):
    """生成的图片也同步加粗加大"""
    width, height = 800, 1100 
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_b = get_chinese_font(40) # 图片标题调大
    font_s = get_chinese_font(32) # 图片内容调大

    draw.rectangle([20, 20, 780, 1080], outline=(0, 0, 0), width=5)
    draw.text((50, 50), "ND CRANKSHAFT DATA REPORT", fill=(0, 0, 0), font=font_b)

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

    y = 150
    for label, value in items:
        draw.line([50, y + 65, 750, y + 65], fill=(0, 0, 0), width=2)
        draw.text((60, y), f"{label}:", fill=(0, 0, 0), font=font_s)
        if value == "LOGO_MARK":
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo.thumbnail((180, 70))
                img.paste(logo, (300, y - 5), logo)
            else:
                draw.text((300, y), "CCS", fill=(0, 0, 0), font=font_s)
        else:
            draw.text((300, y), value, fill=(0, 0, 0), font=font_s)
        y += 100 

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. 密码与逻辑 ---
if "password_correct" not in st.session_state:
    st.markdown("<h1 style='text-align:center;'>🔒 授权登录</h1>", unsafe_allow_html=True)
    st.text_input("请输入访问密码", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), key="password")
else:
    st.markdown("<h1 style='color:#003366;'>🚢 ND曲轴证书查询</h1>", unsafe_allow_html=True)
    
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
        search_id = st.text_input("🔍 点击输入轴号搜索:", placeholder="例如: ND2-11")
        if search_id:
            res = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            if not res.empty:
                st.write(f"找到 {len(res)} 条记录")
                for index, row in res.iterrows():
                    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                    ccs_html = f'<img src="data:image/png;base64,{logo_b64}" class="ccs-logo-img">' if logo_b64 else "CCS"
                    
                    st.markdown(f"""
                    <table class="report-table">
                        <tr><td class="label-col">名 称</td><td class="value-col">{row['名称']}</td></tr>
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
                        label=f"📥 点击下载图片：{row['轴号']}.png",
                        data=img_data,
                        file_name=f"{row['轴号']}.png",
                        mime="image/png",
                        key=f"btn_{row['轴号']}_{index}"
                    )
                    st.markdown("<br><br>", unsafe_allow_html=True)
            else:
                st.warning("⚠️ 查无记录，请检查输入")