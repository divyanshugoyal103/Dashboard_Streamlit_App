import re

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return set(words)

def find_missing_keywords(resume_keywords, jd_keywords):
    return list(jd_keywords - resume_keywords)
