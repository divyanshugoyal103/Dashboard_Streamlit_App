import os
import openai

openai.api_key = os.getenv("NEBIUS_API_KEY")

def generate_xyz_bullet(keyword):
    prompt = f"Write a professional resume bullet point using the XYZ strategy that includes the keyword: {keyword}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60
    )
    return response.choices[0].message["content"].strip()
