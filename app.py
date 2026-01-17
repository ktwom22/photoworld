import streamlit as st
from sqlalchemy import create_engine, text
import os

# Database Config
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
if not db_url: db_url = "sqlite:///local_test.db"
engine = create_engine(db_url)

st.set_page_config(page_title="Client Portal", page_icon="📸")

# Elegant Styling
st.markdown("""
    <style>
    .stProgress > div > div > div > div { background-color: #000; }
    h1, h2 { font-family: 'serif'; }
    </style>
    """, unsafe_allow_html=True)

st.title("Photography Client Portal")
email_input = st.text_input("Enter your email to access your project", placeholder="client@email.com")

if email_input:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM photography_projects WHERE client_email = :email"),
            {"email": email_input.strip()}
        ).mappings().fetchone()

    if result:
        st.subheader(f"Project: {result['project_name']}")

        # Display Progress
        st.metric("Current Stage", result['status'])
        st.progress(result['progress'] / 100)
        st.caption(f"Your project is {result['progress']}% complete.")

        st.divider()

        if result['progress'] >= 100:
            st.success("### Your Gallery is Ready")
            if result['gallery_link']:
                st.link_button("View & Download High-Res Gallery", result['gallery_link'], use_container_width=True)
        else:
            st.info(
                f"We are currently in the **{result['status']}** phase. We'll notify you when the final edits are ready.")
    else:
        st.error("No project found. Please check the email spelling.")