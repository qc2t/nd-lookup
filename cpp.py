import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import re

# --- 1. 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# CSS：手机端极致醒目优化
st.markdown("""
    <style>
    /* 彻底隐藏管理按钮、浮动小人、页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none !important;}
    div[data-testid="stStatusWidget"] {display:none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}

    /* 网页表格样式：深海蓝高对比度 */
    .report-table { width: 100%; border-collapse: collapse; margin-top: 10px; border: 4px solid #004080; }
    .report-table td { border: 1px solid #004080; padding: 22px 15px; line-height: 1.2; }
    .label-col { 
        background-color: #004080 !important; color: #ffffff !important; 
        font-weight: bold; font-size: 24px !important; width: 35%; text-align: center; 
    }
    .value-col { 
        background-color: #ffffff; font-weight: 900; font-size: 34px !important; 
        color: #002b55; width: 65%; 
    }
    .ccs-logo-img { height: 65px; vertical-align: middle; }

    /* 下载按钮：亮橙色巨型按钮 */
    div.stDownloadButton > button {
        width: 100% !important; height: 85px !important; font-size: 28px !important;
        font-weight: bold !important; background-color: #FF8C00 !important;
        color: white !important; border-radius: 12px !important;
        box-shadow: 0px 5px 15px rgba(255,140,0,0.4) !important;
    }
    
    /* 输入框与查询按钮 */
    input { font-size: 28px !important; height: 65px !important; border: 2px solid #004080 !important; }
    div[data-testid="column"] button { 
        height: 65px !important; background-color: #004080 !important; 
        color: white !important; font-size: 24px !important; font-weight: bold !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心功能函数 ---

def extract_model(name_str):
    """提取除汉字以外的部分 (只保留字母、数字、点、横杠)"""
    if not name_str or pd.isna(name_str):
        return "N/A"
    # 使用正则移除所有中文字符 [\u4e00-\u9fa5]
    cleaned = re.sub(r'[\u4e00-\u9fa5]', '', str(name_str))
    # 去除首尾空格
    return cleaned.strip()

def get_chinese_font(size):
    paths = ["simhei.ttf", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "C:/Windows/Fonts/simhei.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_report_image(row, logo_path):
    """生成证书图片：增加机型(提取)和图号"""
    width, height = 800, 1300 
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_b = get_chinese_font(40)
    font_s = get_chinese_font(30)

    # 绘制外框