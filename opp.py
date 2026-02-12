import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# --- 2. CSS 样式 (保留原版优秀设计) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none !important;}
    div[data-testid="stStatusWidget"] {display:none !important;}
    
    .report-table { 
        width: 100%; border-collapse: collapse; margin-top: 10px; border: 4px solid #004080; 
    }
    .report-table td { 
        border: 1px solid #004080; padding: 15px 10px; line-height: 1.2;
    }
    .label-col { 
        background-color: #004080 !important; color: #ffffff !important; 
        font-weight: bold; font-size: 20px !important; width: 35%; text-align: center;
    }
    .value-col { 
        background-color: #ffffff; font-weight: 900; font-size: 24px !important; 
        color: #002b55; width: 65%;
    }
    .ccs-logo-img { height: 50px; vertical-align: middle; }

    /* 下载按钮优化 */
    div.stDownloadButton > button {
        width: 100% !important; height: 70px !important; font-size: 24px !important;
        background-color: #FF8C00 !important; color: white !important;
        border-radius: 12px !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心工具函数 ---

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_font(size):
    """关键修改：优先加载上传的字体，如果没有则回退到默认（虽然默认不支持中文，但至少不报错）"""
    # 请务必去下载一个 simhei.ttf 放到 GitHub 仓库根目录！
    font_files = ["simhei.ttf", "SimHei.ttf", "msyh.ttf"] 
    for f in font_files:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default() # 如果没字体，这里会显示方框，但程序不会崩

def create_report_image(row, logo_path):
    width, height = 800, 1150 
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 获取字体
    font_b = get_font(40)
    font_s = get_font(32)

    # 画框
    draw.rectangle([20, 20, 780, 1130], outline=(0, 64, 128), width=6)
    draw.text((60, 60), "ND CRANKSHAFT DATA REPORT", fill=(0, 64, 128), font=font_b)

    fmt_date = str(row.get('船检时间', 'N/A'))
    try:
        # 尝试格式化日期，如果格式不对就原样显示
        fmt_date = pd.to_datetime(fmt_date).strftime('%d-%m-%Y')
    except:
        pass

    items = [
        ("名  称", str(row.get('名称', 'N/A'))),
        ("型号", str(row.get('图号', 'N/A'))),
        ("图  号", str(row.get('轴号', 'N/A'))),
        ("轴  号", str(row.get('轴号', 'N/A'))),
        ("材  质", str(row.get('材质', 'N/A'))),
        ("炉  号", str(row.get('炉号', 'N/A'))),
        ("制造单位", "CRRC ZJ"),
        ("检测方式", "UT  MT"),
        ("船检控制号", str(row.get('船检控制号', 'N/A'))),
        ("检验机构", "CCS"), 
        ("船检时间", fmt_date)
    ]

    y = 160
    for label, value in items:
        draw.line([60, y + 70, 740, y + 70], fill=(200, 200, 200), width=2)
        # 如果没有中文字体，label（如"名称"）会显示乱码
        draw.text((80, y), f"{label}:", fill=(100, 100, 100), font=font_s)
        
        if value == "CCS" and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo.thumbnail((200, 80))
                img.paste(logo, (320, y - 5), logo)
            except:
                draw.text((320, y), value, fill=(0, 0, 0), font=font_s)
        else:
            draw.text((320, y), value, fill=(0, 0, 0), font=font_s)
        y += 105 

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 4. 智能数据加载 ---
@st.cache_data
def load_data_smart():
    # 优先找 qzmx.xlsx，其次找 ND曲轴.xlsx
    files = ["qzmx.xlsx", "ND曲轴.xlsx", "data.xlsx"]
    for f in files:
        if os.path.exists(f):
            try:
                # 尝试读取，处理乱码
                if f.endswith('.csv'):
                    df = pd.read_csv(f, encoding='gbk')
                else:
                    # 尝试读取 CCS 表，如果不存在则读取第一个表
                    try:
                        df = pd.read_excel(f, sheet_name="CCS")
                    except:
                        df = pd.read_excel(f)
                
                # 统一列名：去除空格
                df.columns = df.columns.astype(str).str.replace(' ', '')
                return df
            except:
                continue
    return None

# --- 5. 主程序逻辑 ---
if "password_correct" not in st.session_state:
    st.markdown("<h2 style='text-align:center;'>⚓ 内部系统登录</h2>", unsafe_allow_html=True)
    pwd = st.text_input("请输入访问密码", type="password")
    if st.