import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CẤU HÌNH GIAO DIỆN & MÀU SẮC (VÀNG - ĐEN)
st.set_page_config(page_title="Hệ thống Chấm điểm Pro 2026", layout="wide")

st.markdown("""
    <style>
    /* Nền đen toàn bộ */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Màu vàng chủ đạo cho tiêu đề và nút */
    h1, h2, h3 { color: #FFD700 !important; }
    .stButton>button {
        background-color: #FFD700 !important;
        color: black !important;
        border-radius: 10px;
        font-weight: bold;
        border: none;
        width: 100%;
    }
    
    /* Tùy chỉnh thanh trượt Slider */
    .stSlider > div > div > div > div { background-color: #FFD700 !important; }
    
    /* Viền cho các bảng điểm */
    .stDataFrame { border: 1px solid #FFD700; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI GOOGLE SHEETS
# (Lưu ý: Bạn cần cấu hình secrets trên Streamlit Cloud với link Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. LOGIC TÍNH TOÁN (Làm tròn 5 chữ số)
def calculate_score(d1, d2, d3, d4, d5):
    # Công thức trọng số: 10%, 30%, 20%, 20%, 20%
    raw_score = (d1 * 0.1) + (d2 * 0.3) + (d3 * 0.2) + (d4 * 0.2) + (d5 * 0.2)
    return round(raw_score, 5)

# 4. ĐIỀU HƯỚNG
menu = ["Người Chấm Điểm", "Máy Chủ Quản Trị"]
choice = st.sidebar.selectbox("Chế độ", menu)

# --- GIAO DIỆN NGƯỜI CHẤM ---
if choice == "Người Chấm Điểm":
    st.title("🏆 PHẦN MỀM ĐÁNH GIÁ THÍ SINH")
    st.subheader("Vui lòng nhập điểm chính xác (Thang 10)")

    with st.container():
        user = st.text_input("Tên Giám khảo / Người chấm")
        candidate = st.selectbox("Chọn Thí sinh", [f"Thí sinh {i:02d}" for i in range(1, 21)])
        
        col1, col2 = st.columns(2)
        with col1:
            d1 = st.slider("Hình thức (10%)", 0.0, 10.0, 5.0, 0.1)
            d2 = st.slider("Nội dung (30%)", 0.0, 10.0, 5.0, 0.1)
            d3 = st.slider("Bổ trợ (20%)", 0.0, 10.0, 5.0, 0.1)
        with col2:
            d4 = st.slider("Phản biện (20%)", 0.0, 10.0, 5.0, 0.1)
            d5 = st.slider("Trả lời Phản biện (20%)", 0.0, 10.0, 5.0, 0.1)

        total = calculate_score(d1, d2, d3, d4, d5)
        st.info(f"Tổng điểm dự kiến: **{total:.5f}**")

        if st.button("GỬI KẾT QUẢ"):
            if user:
                # Ghi dữ liệu vào Google Sheets
                new_data = pd.DataFrame([{
                    "NguoiCham": user, "ThiSinh": candidate,
                    "HinhThuc": d1, "NoiDung": d2, "BoTro": d3,
                    "PhanBien": d4, "TraLoi": d5, "TongDiem": total
                }])
                # Logic: Đọc cũ + Thêm mới (Appends)
                existing_data = conn.read()
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"Đã lưu điểm cho {candidate} thành công!")
            else:
                st.error("Vui lòng nhập tên người chấm!")

# --- GIAO DIỆN MÁY CHỦ ---
else:
    st.title("📊 BẢNG ĐIỀU KHIỂN QUẢN TRỊ")
    
    # Đọc dữ liệu từ Sheets
    df = conn.read()
    
    if not df.empty:
        # 1. Bảng thống kê tổng hợp (Trung bình cộng)
        summary = df.groupby("ThiSinh")["TongDiem"].mean().reset_index()
        summary["TongDiem"] = summary["TongDiem"].apply(lambda x: f"{x:.5f}")
        
        st.subheader("Xếp hạng Thí sinh")
        st.dataframe(summary.sort_values(by="TongDiem", ascending=False), use_container_width=True)
        
        # 2. Biểu đồ cột
        st.subheader("Biểu đồ trực quan")
        st.bar_chart(summary.set_index("ThiSinh"), color="#FFD700")
        
        # 3. Kiểm tra dữ liệu chi tiết
        with st.expander("Xem chi tiết tất cả đánh giá"):
            st.write(df)
    else:
        st.write("Chưa có dữ liệu.")
