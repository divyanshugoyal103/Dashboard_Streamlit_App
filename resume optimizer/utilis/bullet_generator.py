import os
import openai

openai.api_key = os.getenv("eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJnaXRodWJ8Njc0OTQ4MzEiLCJzY29wZSI6Im9wZW5pZCBvZmZsaW5lX2FjY2VzcyIsImlzcyI6ImFwaV9rZXlfaXNzdWVyIiwiYXVkIjpbImh0dHBzOi8vbmViaXVzLWluZmVyZW5jZS5ldS5hdXRoMC5jb20vYXBpL3YyLyJdLCJleHAiOjE5MTIzMDIwMTIsInV1aWQiOiIxMjQ0MDE5MC03NzE5LTQyMzktYTI2MS01YzY3MmM3NDk5ZjkiLCJuYW1lIjoicmVzdW1lIiwiZXhwaXJlc19hdCI6IjIwMzAtMDgtMDdUMDM6MDA6MTIrMDAwMCJ9.K5YvXPdqxsNB-HSLUCcfHLYigZcl7Q2Iwr9ZCdU1GgY")

def generate_xyz_bullet(keyword):
    prompt = f"Write a professional resume bullet point using the XYZ strategy that includes the keyword: {keyword}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60
    )
    return response.choices[0].message["content"].strip()
