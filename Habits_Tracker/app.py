import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
import os
import plotly.express as px

# 1. Cấu hình trang - Chế độ "wide" và thu gọn lề
st.set_page_config(page_title="Habit Tracker", page_icon="💪", layout="wide")

# 2. Can thiệp CSS (Tối ưu riêng cho màn hình điện thoại)
st.markdown("""
    <style>
    /* Giảm lề 2 bên và phía trên để tận dụng tối đa màn hình điện thoại */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    /* Làm to và bo góc các nút bấm để dễ chạm (Touch-friendly) */
    .stButton > button {
        min-height: 50px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 16px;
    }
    /* Ẩn hoàn toàn menu mặc định của Streamlit và watermark để trông giống App thật */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Quản lý đường dẫn (Tuyệt đối an toàn trên Cloud)
BASE_DIR = os.path.dirname(__file__) 
# LƯU Ý QUAN TRỌNG: Hãy đảm bảo file trên GitHub của bạn tên chính xác là "Tracker.csv" (chữ T viết hoa)
BASE_FILE = os.path.join(BASE_DIR, "Tracker.csv")

def get_file_path(year, month):
    return os.path.join(BASE_DIR, f"Tracker_{year}_{month:02d}.csv")

@st.cache_data(ttl=0)
def load_data(year, month):
    path = get_file_path(year, month)
    if not os.path.exists(path):
        template_df = pd.read_csv(BASE_FILE, header=None)
        _, num_days = calendar.monthrange(year, month)
        vi_weekdays = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}
        
        habits = []
        for i in range(4, len(template_df) - 1):
            name = template_df.iloc[i, 1]
            if pd.notna(name) and str(name).strip() != "":
                habits.append(str(name).strip())
        
        new_rows = [
            ["Năm", year] + [""] * (num_days + 1),
            ["Tháng", month] + [""] * (num_days + 1),
            ["STT", "Ngày"] + [f"{d:02d}" for d in range(1, num_days + 1)] + ["Tổng"],
            ["", "Thứ"] + [vi_weekdays[calendar.weekday(year, month, d)] for d in range(1, num_days + 1)] + [""]
        ]
        for idx, h in enumerate(habits, 1):
            new_rows.append([str(idx), h] + ["FALSE"] * num_days + [0])
        new_rows.append(["", "Hoàn thành"] + [0] * num_days + [""])
        
        df = pd.DataFrame(new_rows)
        df.to_csv(path, index=False, header=False)
        return df
    return pd.read_csv(path, header=None)

def save_data(df, year, month):
    path = get_file_path(year, month)
    df.to_csv(path, index=False, header=False)
    df.to_csv(BASE_FILE, index=False, header=False)

# --- KHÔNG DÙNG SIDEBAR NỮA - ĐƯA LÊN MÀN HÌNH CHÍNH CHO MOBILE ---
st.markdown("### 🎯 Quản Lý Thói Quen")

current_year = datetime.now().year
current_month = datetime.now().month

# Chia làm 2 cột nhỏ trên cùng 1 hàng để tiết kiệm diện tích
colA, colB = st.columns(2)
with colA:
    sel_month = st.selectbox("Tháng", range(1, 13), index=current_month - 1)
with colB:
    sel_year = st.selectbox("Năm", range(current_year - 1, current_year + 3), index=1)

df = load_data(sel_year, sel_month)
total_days = df.shape[1] - 3
total_col_idx = df.shape[1] - 1
last_row_idx = len(df) - 1

# Rút gọn tên Tab để hiển thị vừa vặn trên 1 hàng dọc của điện thoại
tab1, tab2, tab3 = st.tabs(["📝 Ngày", "📊 Tuần", "⚙️ Cài đặt"])

# TAB 1: NGÀY
with tab1:
    today = datetime.now().day
    selected_day = st.selectbox(
        "📅 Chọn ngày chấm điểm:", 
        range(1, total_days + 1), 
        index=(today - 1) if 1 <= today <= total_days else 0
    )
    col_index = selected_day + 1
    day_of_week = df.iloc[3, col_index]
    st.info(f"**Thứ {day_of_week} — {selected_day:02d}/{sel_month:02d}/{sel_year}**")
    
    with st.form("habit_form"):
        new_values = {}
        for i in range(4, last_row_idx):
            stt = df.iloc[i, 0]
            habit_name = df.iloc[i, 1]
            if pd.isna(habit_name) or str(habit_name).strip() == "": continue
            
            current_val = str(df.iloc[i, col_index]).strip().upper() == 'TRUE'
            is_done = st.checkbox(f"{stt}. {habit_name}", value=current_val)
            new_values[i] = 'TRUE' if is_done else 'FALSE'
            
        submit_btn = st.form_submit_button("Lưu ngày này", use_container_width=True)
        if submit_btn:
            for row_idx, val in new_values.items():
                df.iloc[row_idx, col_index] = val
            
            for i in range(4, last_row_idx):
                row_data = df.iloc[i, 2:total_col_idx].astype(str).str.strip().str.upper()
                df.iloc[i, total_col_idx] = (row_data == 'TRUE').sum()
            
            for c in range(2, total_col_idx):
                day_data = df.iloc[4:last_row_idx, c].astype(str).str.strip().str.upper()
                df.iloc[last_row_idx, c] = (day_data == 'TRUE').sum()
                
            save_data(df, sel_year, sel_month)
            st.success("✅ Đã lưu!")
            st.rerun()

# TAB 2: TUẦN
with tab2:
    weeks = {
        "Tuần 1 (01-07)": list(range(1, 8)),
        "Tuần 2 (08-14)": list(range(8, 15)),
        "Tuần 3 (15-21)": list(range(15, 22)),
        "Tuần 4 (22-28)": list(range(22, 29)),
    }
    if total_days > 28:
        weeks[f"Tuần 5 (29-{total_days:02d})"] = list(range(29, total_days + 1))
        
    completion_data = []
    for w_name, days in weeks.items():
        completed_counts = []
        for d in days:
            c_idx = d + 1
            val = df.iloc[last_row_idx, c_idx]
            completed_counts.append(int(val) if pd.notna(val) else 0)
        avg_completed = np.mean(completed_counts)
        completion_data.append({"Tuần": w_name.split()[0:2], "Hiệu suất": round(avg_completed, 1)}) # Rút gọn tên tuần cho đt
        
    df_chart1 = pd.DataFrame(completion_data)
    df_chart1["Tuần"] = df_chart1["Tuần"].apply(lambda x: " ".join(x))
    
    st.markdown("**Xu hướng (Mục/Ngày)**")
    fig1 = px.line(df_chart1, x="Tuần", y="Hiệu suất", markers=True, text="Hiệu suất")
    fig1.update_traces(line_shape="spline", line_color="#00CC96", textposition="top center")
    fig1.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=250, hovermode="x")
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False}) # Tắt thanh công cụ thừa trên đt
    
    st.markdown("---")
    
    selected_week = st.selectbox("🎯 Phân tích chi tiết:", list(weeks.keys()))
    target_days = weeks[selected_week]
    max_possible_days = len(target_days)
    
    habit_perf = []
    for i in range(4, last_row_idx):
        h_name = df.iloc[i, 1]
        if pd.isna(h_name): continue
        
        done_count = 0
        for d in target_days:
            c_idx = d + 1
            if str(df.iloc[i, c_idx]).strip().upper() == 'TRUE':
                done_count += 1
        pct = int((done_count / max_possible_days) * 100)
        habit_perf.append({"Thói quen": str(h_name)[:15] + "..." if len(str(h_name)) > 15 else str(h_name), "Tỷ lệ (%)": pct}) # Cắt ngắn tên quá dài
        
    df_chart2 = pd.DataFrame(habit_perf)
    avg_week_pct = int(df_chart2["Tỷ lệ (%)"].mean())
    st.metric(label="🔥 Tỷ lệ kỷ luật chung", value=f"{avg_week_pct}%")
    
    fig2 = px.bar(df_chart2, x="Tỷ lệ (%)", y="Thói quen", orientation='h', text="Tỷ lệ (%)",
                  color="Tỷ lệ (%)", color_continuous_scale=px.colors.sequential.Tealgrn)
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=10, b=0), height=350, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# TAB 3: CÀI ĐẶT
with tab3:
    st.markdown("**➕ Thêm mới**")
    new_habit = st.text_input("Nhập tên thói quen:", placeholder="Vd: Đọc sách 30p...")
    if st.button("Thêm vào danh sách", use_container_width=True):
        if new_habit.strip() != "":
            new_stt = str(last_row_idx - 3)
            new_row = [new_stt, new_habit.strip()] + ["FALSE"] * total_days + [0]
            
            df_list = df.values.tolist()
            df_list.insert(last_row_idx, new_row)
            
            df = pd.DataFrame(df_list)
            save_data(df, sel_year, sel_month)
            st.success(f"Đã thêm: '{new_habit}'")
            st.rerun()
            
    st.markdown("---")
    st.markdown("**❌ Xóa mục**")
    current_habits = []
    habit_row_indices = {}
    for i in range(4, last_row_idx):
        h_name = df.iloc[i, 1]
        if pd.notna(h_name) and str(h_name).strip() != "":
            item_label = f"{df.iloc[i,0]}. {h_name}"
            current_habits.append(item_label)
            habit_row_indices[item_label] = i
            
    if current_habits:
        to_delete = st.selectbox("Chọn mục cần xóa:", current_habits)
        if st.button("Xóa mục này", type="primary", use_container_width=True): # Đổi màu nút xóa
            target_idx = habit_row_indices[to_delete]
            df_list = df.values.tolist()
            df_list.pop(target_idx)
            
            for i in range(4, len(df_list) - 1):
                df_list[i][0] = str(i - 3)
                
            df = pd.DataFrame(df_list)
            save_data(df, sel_year, sel_month)
            st.success("Đã xóa!")
            st.rerun()