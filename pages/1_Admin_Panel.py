import streamlit as st
from sqlalchemy import create_engine, text
import os

# Database Config
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
if not db_url: db_url = "sqlite:///local_test.db"
engine = create_engine(db_url)

st.title("✨ Studio Management")

# Define Stages and their Percentages
STAGES = {
    "Discovery": 10,
    "Shoot Scheduled": 25,
    "Post-Production: Sorting": 50,
    "Post-Production: Editing": 75,
    "Final Review": 90,
    "Delivered": 100
}

with st.form("admin_control"):
    st.subheader("Update or Create Client")
    c_email = st.text_input("Client Email")
    c_name = st.text_input("Project Name")

    # Selecting the stage automatically sets the percentage
    selected_stage = st.selectbox("Current Stage", list(STAGES.keys()))
    c_link = st.text_input("Gallery Link (Dropbox/Pic-Time/Google Drive)")

    if st.form_submit_button("Sync to Portal"):
        # Map the stage to the percentage
        c_progress = STAGES[selected_stage]

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
                {"e": c_email, "n": c_name, "s": selected_stage, "p": c_progress, "l": c_link}
            )
            conn.commit()
        st.success(f"Project for {c_email} updated to {c_progress}%!")