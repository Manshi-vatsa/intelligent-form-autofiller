import os
import base64
import io
import traceback
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
import pdfplumber
from docx import Document
from PIL import Image

load_dotenv()
print("API KEY LOADED:", bool(os.getenv("GROQ_API_KEY")))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_text_from_pdf(file_content: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_content: bytes) -> str:
    doc = Document(io.BytesIO(file_content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def convert_image_to_base64(file_content: bytes) -> str:
    image = Image.open(io.BytesIO(file_content))
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


@app.post("/extract")
async def extract_resume_data(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        file_content = await file.read()
        filename = file.filename.lower()
        
        extracted_content = ""
        
        if filename.endswith(".pdf"):
            extracted_content = extract_text_from_pdf(file_content)
        elif filename.endswith(".docx"):
            extracted_content = extract_text_from_docx(file_content)
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            base64_image = convert_image_to_base64(file_content)
            extracted_content = f"[IMAGE_BASE64]{base64_image}[/IMAGE_BASE64]"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, JPG, or PNG.")
        
        prompt = f"""Extract the following information from this resume and return ONLY a valid JSON object, no markdown, no explanation:

full_name, email, phone, location, current_role, total_experience_years, skills (as a list), education (degree and institution), summary (2 lines)

Resume content:
{extracted_content}

Return the JSON object with these exact keys: full_name, email, phone, location, current_role, total_experience_years, skills, education, summary"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        response_text = response.choices[0].message.content.strip()
        
        # Remove any markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        import json
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
