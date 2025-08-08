import streamlit as st
from utils import (
    extract_text_from_pdf, extract_text_from_docx, compare_keywords, generate_bullet_point_nebius
)
from dotenv import load_dotenv
import os

load_dotenv()
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")

st.set_page_config(page_title="ATS Resume Optimizer", layout="wide")
st.title("📄 ATS Resume Optimizer with Keyword Suggestions")

col1, col2 = st.columns(2)

with col1:
    resume_file = st.file_uploader("Upload Your Resume (PDF/DOCX)", type=["pdf", "docx"])

with col2:
    jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

if resume_file and jd_file:
    # Extract text
    if resume_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(resume_file)
    else:
        resume_text = extract_text_from_docx(resume_file)

    if jd_file.type == "application/pdf":
        jd_text = extract_text_from_pdf(jd_file)
    elif jd_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        jd_text = extract_text_from_docx(jd_file)
    else:
        jd_text = jd_file.read().decode("utf-8")

    # Compare keywords
    missing_keywords = compare_keywords(resume_text, jd_text)

    st.subheader("🔍 Missing Keywords")
    if missing_keywords:
        for keyword in missing_keywords:
            if st.button(f"Generate Bullet for '{keyword}'"):
                bullet = generate_bullet_point_nebius(keyword, NEBIUS_API_KEY)
                st.success(bullet)
    else:
        st.success("Your resume contains all major keywords from the job description ✅")
