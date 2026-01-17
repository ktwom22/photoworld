import streamlit as st
from sqlalchemy import create_engine, text
import os

# --- 1. DATABASE CONFIGURATION ---
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if not db_url:
    db_url = "sqlite:///local_test.db"

engine = create_engine(db_url)


# --- 2. DATABASE INITIALIZATION ---
def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS photography_projects (
                id SERIAL PRIMARY KEY,
                client_email TEXT UNIQUE,
                project_name TEXT,
                status TEXT,
                progress INT,
                gallery_link TEXT
            );
        """))
        conn.commit()


init_db()

# --- 3. ELEGANT UI STYLING ---
st.set_page_config(page_title="Portfolio | Client Portal", page_icon="📸", layout="centered")

# Custom CSS for a clean, editorial look
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    .stProgress > div > div > div > div { background-color: #1a1a1a; }
    h1 { font-family: 'serif'; font-weight: 400; color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CLIENT DASHBOARD LOGIC ---
st.title("Photography Client Portal")
st.write("Welcome back. Please sign in to view your project status.")

# Clean Login Interface
with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        email_input = st.text_input("Client Email Address", placeholder="hello@yourname.com")

if email_input:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM photography_projects WHERE client_email = :email"),
            {"email": email_input.strip()}
        ).mappings().fetchone()

    if result:
        st.divider()
        st.markdown(f"### {result['project_name']}")

        # Professional Metric Display
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Current Stage", result['status'])
        with m2:
            st.metric("Completion", f"{result['progress']}%")

        st.progress(result['progress'] / 100)

        st.write("---")

        # Action Center
        if result['progress'] >= 100:
            st.balloons()
            st.success("### Your Collection is Ready")
            st.write("We've finished the final retouches. Your high-resolution gallery is now live.")
            if result['gallery_link']:
                st.link_button("View Final Gallery", result['gallery_link'], use_container_width=True)
            else:
                st.info("Your gallery link is being generated. Please check back in a few moments.")
        else:
            st.info(
                f"**Update:** We are currently in the **{result['status']}** phase. You will receive an email once the final gallery is ready for download.")

    else:
        st.error("No active project found for this email. Please verify with your photographer.")

# --- 5. DISCRETE ADMIN PANEL ---
st.sidebar.markdown("---")
with st.sidebar.expander("✨ Photographer Admin"):
    st.write("Update client progress here.")
    with st.form("admin_form", clear_on_submit=True):
        adm_email = st.text_input("Client Email")
        adm_name = st.text_input("Project Name")
        adm_status = st.selectbox("Current Status", ["Pre-Production", "Sorting", "Initial Edits", "Final Retouching",
                                                     "Ready for Delivery"])
        adm_progress = st.slider("Progress %", 0, 100, 10)
        adm_link = st.text_input("Gallery Link (Dropbox/Pic-Time URL)")

        if st.form_submit_button("Save Project Changes"):
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO photography_projects (client_email, project_name, status, progress, gallery_link) 
                        VALUES (:e, :n, :s, :p, :l) 
                        ON CONFLICT (client_email) DO UPDATE 
                        SET status = EXCLUDED.status, 
                            progress = EXCLUDED.progress, 
                            gallery_link = EXCLUDED.gallery_link,
                            project_name = EXCLUDED.project_name
                    """),
                    {"e": adm_email.strip(), "n": adm_name, "s": adm_status, "p": adm_progress, "l": adm_link}
                )
                conn.commit()
            st.success("Client data synced.")
            st.rerun()

# --- 6. FOOTER ---
st.markdown(
    "<br><br><p style='text-align: center; color: #aaa; font-size: 0.8em;'>© 2026 Portsmouth Photography Studio</p>",
    unsafe_allow_html=True)