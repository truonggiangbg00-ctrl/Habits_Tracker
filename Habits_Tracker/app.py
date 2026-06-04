import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
import os
import plotly.express as px

# Cấu hình giao diện hỗ trợ hiển thị biểu đồ rộng rãi
st.set_page_config(page_title="Habit Tracker Pro", page_icon="💪", layout="centered")

BASE_DIR = r"C:\Users\Zeng\CamChiu\Habits_Tracker"
BASE_FILE = os.path.join(BASE_DIR, "Tracker.csv")

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

def get_file_path(year, month):
    return os.path.join(BASE_DIR, f"Tracker_{year}_{month:02d}.csv")

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

# --- SIDEBAR: QUẢN LÝ ---
st.sidebar.title("📅 Quản Lý Thời Gian")
current_year = datetime.now().year
current_month = datetime.now().month

sel_year = st.sidebar.selectbox("Chọn Năm:", range(current_year - 1, current_year + 3), index=1)
sel_month = st.sidebar.selectbox("Chọn Tháng:", range(1, 13), index=current_month - 1)

df = load_data(sel_year, sel_month)
total_days = df.shape[1] - 3
total_col_idx = df.shape[1] - 1
last_row_idx = len(df) - 1

# Phân chia các Tabs chức năng
tab1, tab2, tab3 = st.tabs(["📝 Nhật Ký", "📊 Phân Tích Tuần", "⚙️ Thiết Lập"])

# TAB 1: THEO DÕI HÀNG NGÀY
with tab1:
    st.subheader(f"Cập nhật ngày trong tháng {sel_month}/{sel_year}")
    today = datetime.now().day
    selected_day = st.selectbox(
        "Chọn ngày:", 
        range(1, total_days + 1), 
        index=(today - 1) if 1 <= today <= total_days else 0
    )
    col_index = selected_day + 1
    day_of_week = df.iloc[3, col_index]
    st.info(f"Thứ {day_of_week} — Ngày {selected_day:02d}/{sel_month:02d}/{sel_year}")
    
    with st.form("habit_form"):
        new_values = {}
        for i in range(4, last_row_idx):
            stt = df.iloc[i, 0]
            habit_name = df.iloc[i, 1]
            if pd.isna(habit_name) or str(habit_name).strip() == "": continue
            
            current_val = str(df.iloc[i, col_index]).strip().upper() == 'TRUE'
            is_done = st.checkbox(f"{stt}. {habit_name}", value=current_val)
            new_values[i] = 'TRUE' if is_done else 'FALSE'
            
        submit_btn = st.form_submit_button("Lưu dữ liệu ngày này", use_container_width=True)
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
            st.success("Đã ghi nhận dữ liệu thành công!")
            st.rerun()

# TAB 2: ĐÁNH GIÁ TUẦN (BẢN GIAO DIỆN ĐẸP)
with tab2:
    st.markdown("### 📈 Báo Cáo Hiệu Suất Thói Quen")
    
    weeks = {
        "Tuần 1 (01-07)": list(range(1, 8)),
        "Tuần 2 (08-14)": list(range(8, 15)),
        "Tuần 3 (15-21)": list(range(15, 22)),
        "Tuần 4 (22-28)": list(range(22, 29)),
    }
    if total_days > 28:
        weeks[f"Tuần 5 (29-{total_days:02d})"] = list(range(29, total_days + 1))
        
    # Tính số lượng thói quen hoàn thành trung bình
    completion_data = []
    total_habits_count = last_row_idx - 4
    
    for w_name, days in weeks.items():
        completed_counts = []
        for d in days:
            c_idx = d + 1
            val = df.iloc[last_row_idx, c_idx]
            completed_counts.append(int(val) if pd.notna(val) else 0)
        avg_completed = np.mean(completed_counts)
        completion_data.append({"Tuần": w_name, "Thói quen / Ngày": round(avg_completed, 1)})
        
    df_chart1 = pd.DataFrame(completion_data)
    
    # 1. Biểu đồ đường mịn xu hướng phát triển qua các tuần
    fig1 = px.line(df_chart1, x="Tuần", y="Thói quen / Ngày", markers=True, text="Thói quen / Ngày",
                   title="Xu hướng hoàn thành thói quen trung bình mỗi ngày")
    fig1.update_traces(line_shape="spline", line_color="#00CC96", marker=dict(size=8, color="#636EFA"))
    fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300, hovermode="x")
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    
    # 2. Chi tiết từng thói quen trong tuần cụ thể
    selected_week = st.selectbox("Chọn tuần để phân tích sâu:", list(weeks.keys()))
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
        # Tính phần trăm tỷ lệ hoàn thành
        pct = int((done_count / max_possible_days) * 100)
        habit_perf.append({"Thói quen": h_name, "Số ngày đạt": done_count, "Tỷ lệ (%)": pct})
        
    df_chart2 = pd.DataFrame(habit_perf)
    
    # Thẻ điểm tổng quan (Metric Card) của tuần
    avg_week_pct = int(df_chart2["Tỷ lệ (%)"].mean())
    st.metric(label=f"🔥 Tỷ lệ kỷ luật chung của {selected_week}", value=f"{avg_week_pct}%", 
              delta="Tốt" if avg_week_pct >= 70 else "Cần cố gắng thêm")
    
    # Biểu đồ cột ngang phân tích từng mục thói quen (Rất hợp với màn hình dọc điện thoại)
    fig2 = px.bar(df_chart2, x="Số ngày đạt", y="Thói quen", orientation='h', text="Số ngày đạt",
                  title=f"Số ngày hoàn thành trong {selected_week}",
                  color="Tỷ lệ (%)", color_continuous_scale=px.colors.sequential.Tealgrn)
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=40, b=20), height=350)
    fig2.update_traces(textposition="inside")
    st.plotly_chart(fig2, use_container_width=True)

# TAB 3: THAY ĐỔI THÓI QUEN
with tab3:
    st.subheader("➕ Thêm thói quen mới")
    new_habit = st.text_input("Nhập tên thói quen cần bổ sung:")
    if st.button("Thêm vào danh sách theo dõi", use_container_width=True):
        if new_habit.strip() != "":
            new_stt = str(last_row_idx - 3)
            new_row = [new_stt, new_habit.strip()] + ["FALSE"] * total_days + [0]
            
            df_list = df.values.tolist()
            df_list.insert(last_row_idx, new_row)
            
            df = pd.DataFrame(df_list)
            save_data(df, sel_year, sel_month)
            st.success(f"Đã thêm thành công thói quen: '{new_habit}'")
            st.rerun()
            
    st.markdown("---")
    st.subheader("❌ Xóa thói quen hiện tại")
    current_habits = []
    habit_row_indices = {}
    for i in range(4, last_row_idx):
        h_name = df.iloc[i, 1]
        if pd.notna(h_name) and str(h_name).strip() != "":
            item_label = f"{df.iloc[i,0]}. {h_name}"
            current_habits.append(item_label)
            habit_row_indices[item_label] = i
            
    if current_habits:
        to_delete = st.selectbox("Chọn thói quen cần xóa:", current_habits)
        if st.button("Xóa mục này khỏi danh sách", use_container_width=True):
            target_idx = habit_row_indices[to_delete]
            df_list = df.values.tolist()
            df_list.pop(target_idx)
            
            for i in range(4, len(df_list) - 1):
                df_list[i][0] = str(i - 3)
                
            df = pd.DataFrame(df_list)
            save_data(df, sel_year, sel_month)
            st.success("Đã loại bỏ mục chọn thành công!")
            st.rerun()
            