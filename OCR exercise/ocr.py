import base64
import os
import requests
from pathlib import Path

# Read the image file and encode it as base64
image_path = Path(r"/home/liyutong/dhg502-assignment/OCR exercise/hongloumeng.jpeg")
with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Create data URL
data_url = f"data:image/jpeg;base64,{image_data}"

# API configuration - using a vision-capable model
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

url = "https://openrouter.ai/api/v1/chat/completions"

payload = {
    "model": "qwen/qwen3.5-9b",
    "reasoning": {"enabled": False},
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Perform OCR on this page of a classical Chinese novel. "
                    "The text is written vertically: each column reads top to bottom, and columns are ordered right to left. "
                    "Preserve the original Traditional Chinese characters exactly as printed - do NOT convert them to Simplified Chinese. "
                    "Output the transcription one column per line, starting with the rightmost column and moving left, "
                    "reading each column top to bottom. Output only the transcribed text, with no explanations or commentary."
                )},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }
    ],
    "max_tokens": 8192,
    "timeout": 120
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://opencode.ai"
}

response = requests.post(url, json=payload, headers=headers, timeout=120)
response.raise_for_status()

result = response.json()["choices"][0]["message"]["content"]

# Print result to console
print(result)

# Save result to file
output_path = Path("/home/liyutong/dhg502-assignment/OCR exercise/hongloumeng-tc.txt")
output_path.write_text(result, encoding="utf-8")

print(f"\nOCR result saved to {output_path}")
