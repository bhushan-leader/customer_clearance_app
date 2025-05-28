import streamlit as st
import fitz  # PyMuPDF
import os
import requests
from PIL import Image
from docx import Document
from datetime import datetime

# API key for OCR.space
OCR_API_KEY = "K83406522288957"

# Create folders
os.makedirs("extracted_docs", exist_ok=True)
os.makedirs("extracted_texts", exist_ok=True)

# Function to call OCR.space for image text extraction
def extract_text_from_image_api(image_file):
    url = "https://api.ocr.space/parse/image"
    files = {"file": image_file}
    data = {"apikey": OCR_API_KEY, "language": "eng", "isOverlayRequired": False}

    response = requests.post(url, files=files, data=data)
    result = response.json()

    if result.get("IsErroredOnProcessing"):
        return "❌ OCR failed: " + result.get("ErrorMessage", ["Unknown error"])[0]

    return result["ParsedResults"][0]["ParsedText"]

# General extraction function
def extract_text(file):
    text = ""
    file_type = file.name.lower()

    if file_type.endswith(".docx"):
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])

    elif file_type.endswith(".pdf"):
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf:
            text += page.get_text()

    elif file_type.endswith((".png", ".jpg", ".jpeg")):
        text = extract_text_from_image_api(file)

    return text.strip()

# Save function
def save_file_and_text(file, text, source="upload"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if source == "camera":
        base_name = "camera"
        file_path = os.path.join("extracted_docs", f"{timestamp}_{base_name}.jpg")
        text_path = os.path.join("extracted_texts", f"{timestamp}_{base_name}.txt")
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
    else:
        base_name = os.path.splitext(file.name)[0]
        file_path = os.path.join("extracted_docs", f"{timestamp}_{file.name}")
        file.seek(0)
        with open(file_path, "wb") as f:
            f.write(file.read())
        text_path = os.path.join("extracted_texts", f"{timestamp}_{base_name}.txt")

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)
    st.success(f"✅ {source.capitalize()} file and extracted text saved!")

# Streamlit UI
st.set_page_config(page_title="Document Extractor", layout="centered")
st.title("📄 Document Text Extractor & Saver")

# Upload Section
uploaded_file = st.file_uploader("📂 Upload Word, PDF, or Image", type=["docx", "pdf", "png", "jpg", "jpeg"])
if uploaded_file:
    extracted = extract_text(uploaded_file)
    st.text_area("📋 Extracted Text", extracted, height=300)
    if st.button("💾 Save Uploaded File and Text"):
        save_file_and_text(uploaded_file, extracted, source="upload")

# Camera Section
st.markdown("---")
st.header("📷 Capture Document via Camera")
camera_photo = st.camera_input("Take a photo")

if camera_photo:
    extracted_text = extract_text_from_image_api(camera_photo)
    st.text_area("📋 Extracted Text from Camera", extracted_text, height=300)
    if st.button("💾 Save Camera Image and Text"):
        save_file_and_text(camera_photo, extracted_text, source="camera")
