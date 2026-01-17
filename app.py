import streamlit as st
from sqlalchemy import create_engine, text
import os

# 1. Database Connection & URL Fix
db_url = os.getenv("DATABASE_URL")

# --- CRITICAL FIX FOR RAILWAY/SQLALCHEMY ---
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Fallback for local testing
if not db_url:
    db_url = "postgresql://postgres:password@localhost:5432/railway"

engine = create_engine(db_url)


# 2. AUTO-INIT: Create table if it doesn't exist
# We wrap this in a function to keep it clean
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

# --- STREAMLIT UI ---
st.set_page_config(page_title="Photo Client Portal", layout="wide")
st.title("📸 Photo Client Portal")

# Sidebar for Login
with st.sidebar:
    st.header("Client Login")
    email_input = st.text_input("Enter your email")

if email_input:
    with engine.connect() as conn:
        # Use .mappings() so you can access columns by name (result.status)
        result = conn.execute(
            text("SELECT * FROM photography_projects WHERE client_email = :email"),
            {"email": email_input}
        ).mappings().fetchone()

    if result:
        st.header(f"Project: {result['project_name']}")

        # Display Progress
        col1, col2 = st.columns(2)
        col1.metric("Status", result['status'])
        col2.metric("Progress", f"{result['progress']}%")

        st.progress(result['progress'] / 100)

        if result['progress'] >= 100:
            st.success("🎉 Your photos are ready!")
            st.link_button("Download Gallery", result['gallery_link'])
        else:
            st.info("We're still working our magic on your photos! Check back soon.")
    else:
        st.info("No project found for that email. Contact your photographer.")

# --- ADMIN SECTION ---
st.divider()
with st.expander("Admin: Manage Clients"):
    with st.form("add_client"):
        c_email = st.text_input("Client Email")
        c_name = st.text_input("Project Name")
        c_status = st.selectbox("Initial Status", ["Sorting", "Editing", "Final Review"])
        c_progress = st.slider("Initial Progress", 0, 100, 10)

        if st.form_submit_button("Create/Update Project"):
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO photography_projects (client_email, project_name, status, progress) 
                        VALUES (:e, :n, :s, :p) 
                        ON CONFLICT (client_email) DO UPDATE 
                        SET status = EXCLUDED.status, progress = EXCLUDED.progress
                    """),
                    {"e": c_email, "n": c_name, "s": c_status, "p": c_progress}
                )
                conn.commit()
            st.success(f"Project for {c_email} updated!")