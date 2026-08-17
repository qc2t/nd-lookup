import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import re
from functools import lru_cache

# --- 1. 页面配置 ---
st.set_page_config(page_title="ND曲轴数据查询", layout="centered", page_icon="⚓")

# CSS：手机端样式与组件隐藏
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton, div[data-testid="stStatusWidget"], [data-testid="stToolbar"] {display: none !important;}

    /* 网页表格样式：深海蓝高对比度 */
    .report-table { width: 100%; border-collapse: collapse; margin-top: 10px; border: 4px solid #004080; }
    .report-table td { border: 1px solid #004080; padding: 18px 12px; line-height: 1.2; }
    .label-col { 
        background-color: #004080 !important; color: #ffffff !important; 
        font-weight: bold; font-size: 22px !important; width: 35%; text-align: center; 
    }
    .value-col { 
        background-color: #ffffff; font-weight: 800; font-size: 26px !important; 
        color: #002b55; width: 65%; word-break: break-all;
    }
    .ccs-logo-img { height: 55px; vertical-align: middle; }

    /* 下载按钮 */
    div.stDownloadButton > button {
        width: 100% !important; height: 75px !important; font-size: 24px !important;
        font-weight: bold !important; background-color: #FF8C00 !important;
        color: white !important; border-radius: 10px !important;
        box-shadow: 0px 4px 12px rgba(255,140,0,0.3) !important;
    }
    
    /* 表单与输入框 */
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    input { font-size: 24px !important; height: 60px !important; border: 2px solid #004080 !important; }
    div[data-testid="stFormSubmitButton"] > button { 
        height: 60px !important; background-color: #004080 !important; 
        color: white !important; font-size: 22px !important; font-weight: bold !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 缓存与功能函数 ---

@lru_cache(maxsize=4)
def get_chinese_font(size: int):
    """内存缓存字体句柄，避免每次循环重复查盘"""
    paths = ["simhei.ttf", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "C:/Windows/Fonts/simhei.ttf"]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

@st.cache_data
def get_logo_assets(logo_path="CCS.png"):
    """缓存 Logo 的 Base64 文本与 PIL 对象"""
    b64_str = None
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode()
    return b64_str

def extract_model(name_str):
    """剔除汉字保留型号代码"""
    if not name_str or pd.isna(name_str):
        return "N/A"
    cleaned = re.sub(r'[\u4e00-\u9fa5]', '', str(name_str))
    return cleaned.strip() or "N/A"

def create_report_image(row, logo_path="CCS.png"):
    """生成证书图片"""
    width, height = 800, 1300 
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_b = get_chinese_font(40)
    font_s = get_chinese_font(30)

    draw.rectangle([20, 20, 780, 1280], outline=(0, 64, 128), width=6)
    draw.text((60, 60), "ND CRANKSHAFT DATA REPORT", fill=(0, 64, 128), font=font_b)

    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
    model_val = extract_model(row.get('名称', ''))

    items = [
        ("名  称", str(row.get('名称', 'N/A'))),
        ("机  型", model_val),
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
                try:
                    logo = Image.open(logo_path).convert("RGBA")
                    logo.thumbnail((200, 80))
                    img.paste(logo, (320, y - 5), logo)
                except Exception:
                    draw.text((320, y), "CCS", fill=(0, 0, 0), font=font_s)
            else:
                draw.text((320, y), "CCS", fill=(0, 0, 0), font=font_s)
        else:
            draw.text((320, y), value, fill=(0, 0, 0), font=font_s)
        y += 100 

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@st.cache_data
def load_data():
    """读取 Excel 数据"""
    if not os.path.exists("ND曲轴.xlsx"):
        return None
    try:
        df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
        if '船检时间' in df.columns:
            df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
        # 预先处理缺失值，提升渲染效率
        df = df.fillna('N/A')
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None

# --- 3. 登录拦截 ---
if "password_correct" not in st.session_state:
    st.markdown("<h2 style='text-align:center;'>⚓ ND查询系统登录</h2>", unsafe_allow_html=True)
    pwd = st.text_input("请输入访问密码", type="password", key="pwd_input")
    if st.button("登录", use_container_width=True):
        if pwd == st.secrets.get("my_password", "123456"):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("密码错误")
    st.stop()

# --- 4. 主干查询业务 ---
df = load_data()
logo_b64 = get_logo_assets("CCS.png")

if df is None:
    st.warning("⚠️ 未找到数据文件 `ND曲轴.xlsx`，请确认文件路径。")
    st.stop()

st.markdown("<h1 style='color:#004080; text-align:center;'>🚢 ND曲轴证书查询</h1>", unsafe_allow_html=True)

# 使用表单保证输入与提交原子触发
with st.form("search_form"):
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        search_id = st.text_input("轴号搜索", placeholder="输入轴号 (如 ND2-11)...", label_visibility="collapsed")
    with col2:
        submit_btn = st.form_submit_button("查询", use_container_width=True)

if submit_btn and search_id.strip():
    kw = search_id.strip()
    res = df[df['轴号'].astype(str).str.contains(kw, case=False, na=False)]
    
    if res.empty:
        st.warning("⚠️ 查无数据，请核对轴号。")
    else:
        total_count = len(res)
        # 限制单次展示数量，防止几百条数据挤爆手机浏览器
        display_df = res.head(30)
        st.success(f"✅ 共匹配到 {total_count} 条记录" + (" (仅展示前 30 条)" if total_count > 30 else ""))

        for index, row in display_df.iterrows():
            fmt_date = row['船检时间'].strftime('%d-%m-%Y') if isinstance(row['船检时间'], pd.Timestamp) else str(row['船检时间'])
            ccs_html = f'<img src="data:image/png;base64,{logo_b64}" class="ccs-logo-img">' if logo_b64 else "CCS"
            current_model = extract_model(row['名称'])
            
            st.markdown(f"""
            <table class="report-table">
                <tr><td class="label-col">名 称</td><td class="value-col">{row.get('名称', 'N/A')}</td></tr>
                <tr><td class="label-col">机 型</td><td class="value-col">{current_model}</td></tr>
                <tr><td class="label-col">图 号</td><td class="value-col">{row.get('图号', 'N/A')}</td></tr>
                <tr><td class="label-col">轴 号</td><td class="value-col">{row.get('轴号', 'N/A')}</td></tr>
                <tr><td class="label-col">材 质</td><td class="value-col">{row.get('材质', 'N/A')}</td></tr>
                <tr><td class="label-col">炉 号</td><td class="value-col">{row.get('炉号', 'N/A')}</td></tr>
                <tr><td class="label-col">制 造</td><td class="value-col">CRRC ZJ</td></tr>
                <tr><td class="label-col">检 测</td><td class="value-col">UT  MT</td></tr>
                <tr><td class="label-col">控 制 号</td><td class="value-col">{row.get('船检控制号', 'N/A')}</td></tr>
                <tr><td class="label-col">机 构</td><td class="value-col">{ccs_html}</td></tr>
                <tr><td class="label-col">时 间</td><td class="value-col">{fmt_date}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            
            # 生成证书图片
            img_data = create_report_image(row, "CCS.png")
            st.download_button(
                label=f"📥 下载图片：{row['轴号']}.png",
                data=img_data,
                file_name=f"{row['轴号']}.png",
                mime="image/png",
                key=f"btn_{row['轴号']}_{index}"
            )
            st.divider()