import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="ND曲轴数据查询系统", layout="centered", page_icon="⚓")

# 自定义 CSS：实现带边框的报表视图
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
    """读取图片并转为 Base64，用于在 HTML 表格中显示"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_chinese_font(size):
    """解决图片中文乱码：自动寻找可用的中文字体"""
    font_paths = [
        "simhei.ttf",  # 优先使用您上传到 GitHub 仓库的字体
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", # Streamlit Cloud 默认中文字体
        "C:/Windows/Fonts/simhei.ttf", # Windows 开发环境路径
        "/System/Library/Fonts/STHeiti Light.ttc" # Mac 开发环境路径
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_report_image(row, logo_path):
    """将查询结果生成为证书样式的图片"""
    # 创建画布 (宽 800, 高 900)
    img = Image.new('RGB', (800, 900), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = get_chinese_font(32)
    font_text = get_chinese_font(24)

    # 绘制外框
    draw.rectangle([20, 20, 780, 880], outline=(0, 0, 0), width=3)
    draw.text((50, 50), "ND CRANKSHAFT INSPECTION RECORD", fill=(0, 0, 0), font=font_title)

    # 格式化日期
    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
    
    # 定义要绘制的数据项 (对应您的模板顺序)
    items = [
        ("名  称", str(row.get('名称', 'N/A'))),
        ("轴  号", str(row.get('轴号', 'N/A'))),
        ("材  质", str(row.get('材质', 'N/A'))),
        ("炉  号", str(row.get('炉号', 'N/A'))),
        ("制造单位", "CRRC ZJ"),
        ("检测方式", "UT  MT"),
        ("船检控制号", str(row.get('船检控制号', 'N/A'))),
        ("检验机构", "CCS"),
        ("船检时间", fmt_date)
    ]

    y = 150
    for label, value in items:
        # 绘制行分隔线
        draw.line([50, y+45, 750, y+45], fill=(200, 200, 200), width=1)
        # 绘制标签和数值
        draw.text((60, y), f"{label}:", fill=(100, 100, 100), font=font_text)
        draw.text((280, y), value, fill=(0, 0, 0), font=font_text)
        y += 75

    # 合成 CCS 图标到图片右上角
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((150, 60))
        img.paste(logo, (600, 50), logo)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. 密码验证逻辑 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 内部系统，请输入授权密码")
        st.text_input(
            "授权密码", 
            type="password", 
            on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets.get("my_password", "123456")}), 
            key="password"
        )
        return False
    return st.session_state["password_correct"]

# --- 4. 主程序入口 ---
if check_password():
    st.title("🚢 ND曲轴证书查询 & 图片导出")
    st.markdown("---")
    
    # 加载数据
    @st.cache_data
    def load_data():
        try:
            # 读取 Excel 工作表 CCS
            df = pd.read_excel("ND曲轴.xlsx", sheet_name="CCS")
            # 预处理日期格式
            if '船检时间' in df.columns:
                df['船检时间'] = pd.to_datetime(df['船检时间'], errors='coerce')
            return df
        except Exception as e:
            st.error(f"❌ 数据加载失败: {e}")
            return None

    df = load_data()
    logo_b64 = get_image_base64("CCS.png")

    if df is not None:
        # 查询输入
        search_id = st.text_input("🔍 请输入轴号进行查询 (支持模糊搜索):", placeholder="例如: 2005L6")
        
        if search_id:
            # 执行模糊搜索
            res = df[df['轴号'].astype(str).str.contains(search_id, case=False, na=False)]
            
            if not res.empty:
                st.info(f"为您找到 {len(res)} 条匹配记录")
                
                # 遍历结果（使用 index 确保按钮 ID 唯一）
                for index, row in res.iterrows():
                    fmt_date = row['船检时间'].strftime('%d-%m-%Y') if pd.notnull(row['船检时间']) else 'N/A'
                    ccs_display = f'<img src="data:image/png;base64,{logo_b64}" class="ccs-logo-img">' if logo_b64 else "CCS"
                    
                    # 4.1 网页端显示：美化表格版
                    html_table = f"""
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
                    st.markdown(html_table, unsafe_allow_html=True)
                    
                    # 4.2 图片导出功能：以轴号命名
                    # 生成图片数据
                    img_data = create_report_image(row, "CCS.png")
                    
                    # 下载按钮 (增加唯一 key 修复报错)
                    st.download_button(
                        label=f"💾 下载图片：{row['轴号']}.png",
                        data=img_data,
                        file_name=f"{row['轴号']}.png",
                        mime="image/png",
                        key=f"dl_btn_{row['轴号']}_{index}" 
                    )
                    st.divider()
            else:
                st.warning("☹️ 未找到匹配记录，请尝试其他关键词。")
        else:
            st.info("💡 请在输入框中输入轴号。")

# 侧边栏
st.sidebar.markdown("---")
st.sidebar.caption("ND曲轴管理系统 | 内部专用")