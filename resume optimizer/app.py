import streamlit as st
from utils.keyword_matcher import extract_keywords, find_missing_keywords
from utils.bullet_generator import generate_xyz_bullet
import os

st.set_page_config(page_title="Resume Optimizer", layout="wide")

st.title("📄 Resume Optimizer for ATS")

# Upload resume and job description
resume_text = st.text_area("Paste your resume text here")
job_description = st.text_area("Paste the job description here")

if st.button("Analyze Resume"):
    if resume_text and job_description:
        resume_keywords = extract_keywords(resume_text)
        jd_keywords = extract_keywords(job_description)
        missing_keywords = find_missing_keywords(resume_keywords, jd_keywords)
        
        if missing_keywords:
            st.subheader("Missing Keywords")
            for keyword in missing_keywords:
                if st.button(f"Generate bullet for '{keyword}'"):
                    bullet = generate_xyz_bullet(keyword)
                    st.write(f"- {bullet}")
        else:
            st.success("Your resume contains all the relevant keywords!")
    else:
        st.error("Please paste both your resume and the job description.")
