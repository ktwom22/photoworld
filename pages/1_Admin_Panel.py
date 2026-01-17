import streamlit as st
from sqlalchemy import create_engine, text
import os
import base64

# DB Config (same as app.py)
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
if not db_url: db_url = "sqlite:///local_test.db"
engine = create_engine(db_url)

st.title("✨ Photographer Admin")

# STAGE CONFIGURATION
STAGES = {
    "Booking/Deposit": 10,
    "Shoot Scheduled": 25,
    "Culling/Sorting": 40,
    "Initial Proofs Ready": 60,
    "Client Retouching Selection": 75,
    "Final Editing": 90,
    "Delivered": 100
}

tab1, tab2 = st.tabs(["Client Management", "Upload Proofs"])

with tab1:
    with st.form("client_form"):
        st.subheader("Create or Update Project")
        email = st.text_input("Client Email")
        p_name = st.text_input("Project Name")
        status = st.selectbox("Project Stage", list(STAGES.keys()))
        g_link = st.text_input("Final Gallery URL (Dropbox/Pic-Time)")

        if st.form_submit_button("Save Changes"):
            progress = STAGES[status]  # Auto-set percentage
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO photography_projects (client_email, project_name, status, progress, gallery_link)
                        VALUES (:e, :n, :s, :p, :l)
                        ON CONFLICT (client_email) DO UPDATE 
                        SET status = EXCLUDED.status, progress = EXCLUDED.progress, gallery_link = EXCLUDED.gallery_link
                    """),
                    {"e": email.strip(), "n": p_name, "s": status, "p": progress, "l": g_link}
                )
                conn.commit()
            st.success("Project updated!")

with tab2:
    st.subheader("Upload Proofing Images")
    target_email = st.text_input("Upload for which client (Email)?")
    files = st.file_uploader("Select Images", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

    if st.button("Start Upload") and files and target_email:
        with engine.connect() as conn:
            for f in files:
                # Encode image to Base64 to store in DB
                encoded = base64.b64encode(f.read()).decode()
                conn.execute(
                    text("INSERT INTO project_photos (client_email, image_data) VALUES (:e, :d)"),
                    {"e": target_email.strip(), "d": encoded}
                )
                conn.commit()
        st.success(f"Successfully uploaded {len(files)} photos.")