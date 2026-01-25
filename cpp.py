import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="ND曲轴数据查询系统", layout="centered", page_icon="⚓")

# 自定义 CSS：网页端的报表视图
st.markdown("""
    <style>
    .report-table { width: 100%; border-collapse: collapse; margin-top: 20px; border: 2px solid #000; }
    .report-table td { border: 1px solid #333; padding: 12px; font-size: 16px; line-height: 1.5; }
    .label-col { background-color: #f2f2f2; font-weight: bold; width: 35%; text-align: left; }
    .value-col { width: 65%; background-color: #ffffff; font-weight: 500; color: #000; }
    .ccs-logo-img { height: 35px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心功能函数 ---

def get_image_base64(path):
    """读取图片并转为 Base64，用于在网页 HTML 表格中显示"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_chinese_font(size):
    """解决图片中文乱码"""
    font_paths = [
        "simhei.ttf", 
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", 
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/STHeiti Light.ttc"
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_report_image(row, logo_path):
    """生成证书图片：图标精准定位在“检验机构”行"""
    width, height = 800, 950
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_title = get_chinese_font(32)
    font_text = get_chinese_font(24)

    # 绘制外框
    margin = 25
    draw.rectangle([margin, margin, width - margin, height - margin], outline=(0, 0, 0), width=3)
    draw.text((55, 60), "ND CRANKSHAFT INSPECTION RECORD", fill=(0, 0, 0), font=font_title)

    # 准备数据项
    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
    items = [
        ("名  称", str(row.get('名称', 'N/A'))),
        ("轴  号", str(row.get('轴号', 'N/A'))),
        ("材  质", str(row.get('材质', 'N/A'))),
        ("炉  号", str(row.get('炉号', 'N/A'))),
        ("制造单位", "CRRC ZJ"),
        ("检测方式", "UT  MT"),
        ("船检控制号", str(row.get('船检控制号', 'N/A'))),
        ("检验机构", "LOGO_PLACEHOLDER"), # 特殊标记，用于放图标
        ("船检时间", fmt_date)
    ]

    y_start = 160
    line_height = 80
    
    for label, value in items:
        # 绘制行线
        draw.line([55, y_start + 50, width - 55, y_start + 50], fill=(210, 210, 210), width=1)
        # 绘制左侧标签
        draw.text((70, y_start), f"{label}:", fill=(100, 100, 100), font=font_text)
        
        # 绘制右侧内容
        if value == "LOGO_PLACEHOLDER":
            # 如果是检验机构行，贴上图标
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                # 缩放图标以适应行高
                logo.thumbnail((120, 45))
                # 计算垂直居中位置
                logo_y = y_start - 5 
                img.paste(logo, (280, logo_y), logo)
            else:
                draw.text((280, y_start), "CCS", fill=(0, 0, 0), font=font_text)
        else:
            # 普通文字内容
            draw.text((280, y_start), value, fill=(0, 0, 0), font=font_text)
            
        y_start += line_height

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. 密码验证逻辑 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 内部系统，请输入授权密码")
        st.text_input("授权密码", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), key="password")
        return False
    return st.session_state["password_correct"]

# --- 4. 主程序 ---
if check_password():
    st.title("🚢 ND曲轴证书查询系统")
    st.markdown("---")
    
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            if '船检时间' in df.columns:
                df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except: return None

    df = load_data()
    logo_b64 = get_image_base64("CCS.png")

    if df is not None:
        search_id = st.text_input("🔍 请输入轴号进行查询 (支持模糊搜索):")
        
        if search_id:
            res = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not res.empty:
                for index, row in res.iterrows():
                    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                    ccs_display = f'<img src="data:image/png;base64,{logo_b64}" class="ccs-logo-img">' if logo_b64 else "CCS"
                    
                    # 4.1 网页端显视 (HTML 表格)
                    html = f"""
                    <table class="report-table">
                        <tr><td class="label-col">名称</td><td class="value-col">{row['名称']}</td></tr>
                        <tr><td class="label-col">轴号</td><td class="value-col">{row['轴号']}</td></tr>
                        <tr><td class="label-col">材质</td><td class="value-col">{row['材质']}</td></tr>
                        <tr><td class="label-col">炉号</td><td class="value-col">{row['炉号']}</td></tr>
                        <tr><td class="label-col">制造单位</td><td class="value-col">CRRC ZJ</td></tr>
                        <tr><td class="label-col">检测方式</td><td class="value-col">UT  MT</td></tr>
                        <tr><td class="label-col">船检控制号</td><td class="value-col">{row['船检控制号']}</td></tr>
                        <tr><td class="label-col">检验机构</td><td class="value-col">{ccs_display}</td></tr>
                        <tr><td class="label-col">船检时间</td><td class="value-col"><b>{fmt_date}</b></td></tr>
                    </table>
                    """
                    st.markdown(html, unsafe_allow_html=True)
                    
                    # 4.2 生成并下载图片 (key 确保唯一，文件名以轴号命名)
                    img_data = create_report_image(row, "CCS.png")
                    st.download_button(
                        label=f"💾 下载图片证书：{row['轴号']}.png",
                        data=img_data,
                        file_name=f"{row['轴号']}.png",
                        mime="image/png",
                        key=f"dl_btn_{row['轴号']}_{index}"
                    )
                    st.divider()
            else:
                st.warning("查无记录")