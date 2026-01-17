import streamlit as st
from sqlalchemy import create_engine, text
import os

# --- DATABASE SETUP ---
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
if not db_url: db_url = "sqlite:///local_test.db"
engine = create_engine(db_url)


def init_db():
    with engine.connect() as conn:
        # Projects Table
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
        # NEW: Photos Table for Proofing
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project_photos (
                id SERIAL PRIMARY KEY,
                client_email TEXT,
                image_data TEXT,
                is_favorite BOOLEAN DEFAULT FALSE
            );
        """))
        conn.commit()


init_db()

# --- UI STYLING ---
st.set_page_config(page_title="Client Portal", page_icon="📸", layout="wide")
st.markdown("""
    <style>
    .stProgress > div > div > div > div { background-color: #000; }
    h1, h2, h3 { font-family: 'serif'; }
    .thumb-container { border: 1px solid #eee; padding: 10px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("Photography Client Portal")
email_input = st.text_input("Enter your email to access your project", placeholder="client@email.com")

if email_input:
    email = email_input.strip()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM photography_projects WHERE client_email = :email"),
            {"email": email}
        ).mappings().fetchone()

    if result:
        # 1. Status Section
        st.subheader(f"Project: {result['project_name']}")
        col1, col2 = st.columns([1, 2])
        col1.metric("Current Stage", result['status'])
        col2.write(f"**Overall Progress: {result['progress']}%**")
        col2.progress(result['progress'] / 100)

        # 2. Final Gallery Section
        if result['progress'] >= 100:
            st.success("### ✨ Your Final Gallery is Ready")
            if result['gallery_link']:
                st.link_button("Download High-Res Images", result['gallery_link'], use_container_width=True)

        st.divider()

        # 3. PROOFING SECTION (Favorites)
        st.header("Photo Proofs")
        st.write("Select the ❤️ on images you would like me to retouch.")

        with engine.connect() as conn:
            photos = conn.execute(
                text("SELECT id, image_data, is_favorite FROM project_photos WHERE client_email = :e"),
                {"e": email}
            ).mappings().fetchall()

        if photos:
            # Display photos in a 4-column grid
            cols = st.columns(4)
            for idx, photo in enumerate(photos):
                with cols[idx % 4]:
                    st.image(f"data:image/jpeg;base64,{photo['image_data']}", use_container_width=True)

                    # Heart Button Logic
                    btn_label = "❤️ Favorited" if photo['is_favorite'] else "🤍 Favorite"
                    if st.button(btn_label, key=f"photo_{photo['id']}"):
                        new_fav = not photo['is_favorite']
                        with engine.connect() as conn:
                            conn.execute(
                                text("UPDATE project_photos SET is_favorite = :f WHERE id = :id"),
                                {"f": new_fav, "id": photo['id']}
                            )
                            conn.commit()
                        st.rerun()
        else:
            st.info("No proofs have been uploaded for your session yet.")
    else:
        st.error("No project found for that email.")