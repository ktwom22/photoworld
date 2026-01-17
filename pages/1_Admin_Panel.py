import streamlit as st
from sqlalchemy import create_engine, text
from PIL import Image
from datetime import datetime
import os

# --- DATABASE CONNECTION ---
engine = create_engine("sqlite:///local_test.db")

st.set_page_config(page_title="Studio Management", layout="wide", initial_sidebar_state="collapsed")

# --- LIGHTFOLIO DESIGN SYSTEM ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f5f7; }
    header { visibility: hidden; }

    /* Metrics & Cards */
    .dash-card {
        background: white; border-radius: 8px; padding: 24px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03); height: 100%;
        border: 1px solid #eef0f2; margin-bottom: 20px;
    }
    .card-label { color: #8c9196; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; }

    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 40px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { font-size: 12px; letter-spacing: 1px; text-transform: uppercase; }

    /* Hide Widget Labels */
    label[data-testid="stWidgetLabel"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---
def get_projects():
    with engine.connect() as conn:
        return conn.execute(text("SELECT * FROM photography_projects ORDER BY rowid DESC")).mappings().fetchall()


# --- HEADER ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<h1 style="font-size: 28px; margin-bottom:0;">Studio Command</h1>', unsafe_allow_html=True)
    st.caption(f"Manage Projects & Galleries")

with col_h2:
    if st.button("Refresh Dashboard"):
        st.experimental_rerun()

# --- MAIN NAVIGATION ---
tab_dash, tab_projects, tab_upload = st.tabs(["📊 Dashboard", "📁 Project Manager", "📤 Gallery Uploader"])

projects = get_projects()

# --- TAB 1: DASHBOARD (Overview) ---
with tab_dash:
    c1, c2, c3 = st.columns(3)
    total_rev = sum(p['total_price'] for p in projects)
    total_paid = sum(p['amount_paid'] for p in projects)

    c1.markdown(
        f'<div class="dash-card"><p class="card-label">Revenue</p><h2 style="margin:0">${total_rev:,.2f}</h2></div>',
        unsafe_allow_html=True)
    c2.markdown(
        f'<div class="dash-card"><p class="card-label">Collected</p><h2 style="margin:0">${total_paid:,.2f}</h2></div>',
        unsafe_allow_html=True)
    c3.markdown(
        f'<div class="dash-card"><p class="card-label">Due</p><h2 style="margin:0; color:#d93025">${total_rev - total_paid:,.2f}</h2></div>',
        unsafe_allow_html=True)

# --- TAB 2: PROJECT MANAGER (Edit Projects) ---
with tab_projects:
    if not projects:
        st.info("No projects created yet.")
    else:
        for p in projects:
            with st.expander(f"⚙️ MANAGE: {p['project_name'].upper()} ({p['client_email']})"):
                with st.form(f"edit_form_{p['client_email']}"):
                    col1, col2 = st.columns(2)

                    # Edit Project Info
                    new_name = col1.text_input("Project Name", value=p['project_name'])
                    new_status = col1.selectbox("Stage",
                                                ["Inquiry", "Booked", "Post-Production", "Proofing", "Delivered"],
                                                index=["Inquiry", "Booked", "Post-Production", "Proofing",
                                                       "Delivered"].index(p['status']) if p['status'] in ["Inquiry",
                                                                                                          "Booked",
                                                                                                          "Post-Production",
                                                                                                          "Proofing",
                                                                                                          "Delivered"] else 0)

                    # Edit Finances
                    new_total = col2.number_input("Total Contract ($)", value=float(p['total_price']))
                    new_paid = col2.number_input("Total Paid ($)", value=float(p['amount_paid']))

                    if st.form_submit_button("Save Changes"):
                        with engine.connect() as conn:
                            conn.execute(text("""
                                UPDATE photography_projects 
                                SET project_name=:n, status=:s, total_price=:t, amount_paid=:a 
                                WHERE client_email=:e
                            """), {"n": new_name, "s": new_status, "t": new_total, "a": new_paid,
                                   "e": p['client_email']})
                            conn.commit()
                        st.success("Project updated.")
                        st.experimental_rerun()

# --- TAB 3: GALLERY UPLOADER (Upload Photos) ---
with tab_upload:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown('<p class="card-label">Upload Assets to Gallery</p>', unsafe_allow_html=True)

    if projects:
        # Select which project to upload to
        target_email = st.selectbox("Select Project Gallery", [p['client_email'] for p in projects])

        # Multi-file uploader
        uploaded_files = st.file_uploader("Select Photos (JPG/PNG)", accept_multiple_files=True,
                                          type=['jpg', 'jpeg', 'png'])

        if st.button("Execute Upload") and uploaded_files:
            # Create static folder if not exists
            if not os.path.exists("static"):
                os.makedirs("static")

            with engine.connect() as conn:
                progress_bar = st.progress(0)
                for i, f in enumerate(uploaded_files):
                    # Save file locally
                    file_name = f"{target_email.replace('@', '_')}_{f.name}"
                    file_path = os.path.join("static", file_name)

                    with open(file_path, "wb") as img_file:
                        img_file.write(f.getbuffer())

                    # Record in Database
                    conn.execute(
                        text("INSERT INTO project_photos (client_email, file_path, is_favorite) VALUES (:e, :p, 0)"),
                        {"e": target_email, "p": file_path})
                    conn.commit()

                    # Update progress
                    progress_bar.progress((i + 1) / len(uploaded_files))

            st.success(f"Successfully uploaded {len(uploaded_files)} photos to {target_email}")
    else:
        st.warning("Create a project first to enable uploads.")
    st.markdown('</div>', unsafe_allow_html=True)