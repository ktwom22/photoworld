import streamlit as st
from sqlalchemy import create_engine, text
import os, base64

# --- DATABASE SETUP ---
engine = create_engine("sqlite:///local_test.db")
st.set_page_config(page_title="The Private Collection", layout="wide")

# --- HIGH-FASHION CSS (1.12 COMPATIBLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;1,300&family=Montserrat:wght@200;400&display=swap');

    /* Global Styling */
    .stApp { background-color: #ffffff; }
    header { visibility: hidden; }

    /* Typography */
    h1 { font-family: 'Cormorant Garamond', serif !important; color: #1a1a1a; font-weight: 300 !important; font-size: 4rem !important; margin-bottom: 0; }
    p, span, label { font-family: 'Montserrat', sans-serif !important; letter-spacing: 2px; color: #666; font-size: 10px; text-transform: uppercase; }

    /* Hide Standard Widget Labels for Glamour */
    label[data-testid="stWidgetLabel"] { display: none !important; }

    /* Hero Section */
    .hero-container { text-align: center; padding: 100px 0 60px 0; border-bottom: 1px solid #f2f2f2; margin-bottom: 50px; }

    /* Luxury Gallery Cards */
    .img-card { 
        width: 100%; aspect-ratio: 4/5; object-fit: cover; 
        transition: all 0.8s cubic-bezier(0.2, 1, 0.3, 1);
        margin-bottom: 20px;
    }
    .not-selected { filter: grayscale(100%); opacity: 0.2; transform: scale(0.98); }
    .selected { filter: grayscale(0%); opacity: 1; border-bottom: 2px solid #1a1a1a; }

    /* Minimalist Ghost Buttons */
    .stButton>button {
        border: none !important; background: transparent !important;
        color: #1a1a1a !important; text-decoration: underline;
        text-underline-offset: 6px; font-size: 9px !important;
        letter-spacing: 2px; padding: 0 !important; transition: 0.3s;
    }
    .stButton>button:hover { color: #888 !important; letter-spacing: 4px; }

    /* Floating Selection Bar */
    .selection-footer {
        position: fixed; bottom: 0; left: 0; width: 100%; background: white;
        padding: 20px; border-top: 1px solid #eee; text-align: center; z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)


def get_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None


# --- APP LOGIC ---
if 'logged_in' not in st.session_state:
    st.markdown("<div class='hero-container'><p>Private Access</p><h1>The Collection</h1></div>",
                unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        # Placeholder acts as the label for a cleaner look
        email = st.text_input("Access Code", placeholder="ENTER YOUR EMAIL").strip()
        if st.button("OPEN GALLERY") and email:
            st.session_state.logged_in = email
            st.experimental_rerun()  # FIXED FOR 1.12
else:
    email = st.session_state.logged_in
    with engine.connect() as conn:
        project = conn.execute(text("SELECT * FROM photography_projects WHERE client_email = :e"),
                               {"e": email}).mappings().fetchone()
        photos = conn.execute(text("SELECT * FROM project_photos WHERE client_email = :e"),
                              {"e": email}).mappings().fetchall()

    if project:
        # Immersive Header
        st.markdown(f"""
            <div class='hero-container'>
                <p>{project['status']} &nbsp; // &nbsp; {project['project_name']}</p>
                <h1>Selections</h1>
                <p style='margin-top: 20px;'>Balance Due: ${project['total_price'] - project['amount_paid']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

        # 2-Column Luxury Grid
        if photos:
            cols = st.columns(2)
            for i, row in enumerate(photos):
                with cols[i % 2]:
                    img_b64 = get_base64(row['file_path'])
                    if img_b64:
                        is_fav = row['is_favorite']
                        css_class = "selected" if is_fav else "not-selected"
                        st.markdown(f"<img src='data:image/jpeg;base64,{img_b64}' class='img-card {css_class}'>",
                                    unsafe_allow_html=True)

                        btn_label = "— REMOVE FROM SELECTION" if is_fav else "+ ADD TO SELECTION"
                        # Key must be unique; using rowid if id column is missing
                        if st.button(btn_label, key=f"btn_{i}"):
                            with engine.connect() as conn:
                                conn.execute(text("UPDATE project_photos SET is_favorite = :f WHERE file_path = :p"),
                                             {"f": not is_fav, "p": row['file_path']})
                                conn.commit()
                            st.experimental_rerun()  # FIXED FOR 1.12

        # Bottom selection count
        fav_count = sum(1 for r in photos if r['is_favorite'])
        st.markdown(f"<div class='selection-footer'>{fav_count} IMAGES COLLECTED</div>", unsafe_allow_html=True)
    else:
        st.error("Project not found.")
        if st.button("LOGOUT"):
            del st.session_state.logged_in
            st.experimental_rerun()