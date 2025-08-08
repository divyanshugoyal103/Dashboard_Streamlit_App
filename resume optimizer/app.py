import re
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9\s]", "", text).lower()

def extract_keywords(text):
    words = clean_text(text).split()
    return set([w for w in words if len(w) > 2])  # remove short words

def compare_keywords(resume_text, jd_text):
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)
    missing_keywords = jd_keywords - resume_keywords
    return sorted(list(missing_keywords))

def generate_bullet_point_nebius(keyword, api_key):
    import requests
    url = "https://api.studio.nebius.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert resume writer specializing in ATS optimization using the XYZ strategy."},
            {"role": "user", "content": f"Write one bullet point for my resume using the XYZ strategy that incorporates the keyword '{keyword}' and makes it ATS-friendly."}
        ],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Error generating bullet point: {response.text}"
