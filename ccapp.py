import streamlit as st
from docx import Document
import pandas as pd
from PIL import Image
import requests
import tempfile
import os
import cv2  # For camera

# Setup folders 
os.makedirs("saved_documents/uploaded_files", exist_ok=True)
os.makedirs("saved_documents/extracted_text", exist_ok=True)

# Streamlit config
st.set_page_config(page_title="Customer Clearance App", layout="wide")

# Header
st.markdown("""
    <style>
        .main-title {
            text-align: center;
            color: navy;
            font-size: 36px;
            font-weight: bold;
        }
        .subtitle {
            text-align: center;
            color: gray;
            font-size: 18px;
        }
        .section {
            background-color: #f1f3f6;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
    </style>
    <div class="main-title">📑 Customer Clearance System</div>
    <div class="subtitle">Upload Files or Use Camera to Extract and Save Text Locally</div>
""", unsafe_allow_html=True)

# Upload file section
with st.container():
    st.markdown("### 📂 Upload a File")
    st.markdown('<div class="section">', unsafe_allow_html=True)

    file = st.file_uploader("Choose a file (PDF, DOCX, CSV, TXT, JPG, PNG)", type=["pdf", "docx", "csv", "txt", "jpg", "jpeg", "png"])

    def save_file(file):
        path = os.path.join("saved_documents/uploaded_files", file.name)
        with open(path, "wb") as f:
            f.write(file.read())
        return path

    def extract_text_via_ocr(image_path):
        with open(image_path, 'rb') as img:
            result = requests.post(
                "https://api.ocr.space/parse/image",
                files={"filename": img},
                data={"apikey": "K83406522288957", "language": "eng"},
            )
            result_json = result.json()
            try:
                return result_json["ParsedResults"][0]["ParsedText"]
            except (KeyError, IndexError):
                return "❌ OCR failed to extract text."

    def extract_text(file_path, ext):
        text = ""
        if ext == "pdf":
            # No pdfplumber import - fallback to OCR or you can add pdfplumber import and usage
            # Here, fallback to OCR for PDF pages converted to images could be done, but that is complex.
            # So simple fallback:
            text = extract_text_via_ocr(file_path)
        elif ext == "docx":
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext == "csv":
            df = pd.read_csv(file_path)
            text = df.to_string()
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif ext in ["jpg", "jpeg", "png"]:
            text = extract_text_via_ocr(file_path)
        else:
            text = "Unsupported file type for text extraction."
        return text

    def save_text(text, filename):
        path = os.path.join("saved_documents/extracted_text", filename + ".txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    if file:
        file_size = round(len(file.read()) / (1024 * 1024), 2)
        file.seek(0)  # Reset pointer
        ext = file.name.split('.')[-1].lower()
        file_type = file.type

        st.success("✅ File uploaded successfully!")
        st.markdown(f"**📄 File Name:** `{file.name}`")
        st.markdown(f"**💾 File Size:** `{file_size} MB`")
        st.markdown(f"**📁 File Type:** `{file_type}`")

        doc_type = st.selectbox("📌 Select Document Type", [
            "Commercial Invoice",
            "Bill of Lading",
            "Packing List",
            "Certificate of Origin",
            "Other"
        ])

        file_path = save_file(file)
        text = extract_text(file_path, ext)
        text_path = save_text(text, file.name.split('.')[0])

        metadata_path = os.path.join("saved_documents/extracted_text", file.name.split('.')[0] + "_meta.txt")
        with open(metadata_path, "w", encoding="utf-8") as meta:
            meta.write(f"File Name: {file.name}\n")
            meta.write(f"File Size: {file_size} MB\n")
            meta.write(f"File Type: {file_type}\n")
            meta.write(f"Document Type: {doc_type}\n")

        st.text_area("📝 Extracted Text", text, height=300)
        st.info(f"💾 Text saved at: `{text_path}`")
        st.success(f"📌 Document Type: {doc_type}")

    st.markdown('</div>', unsafe_allow_html=True)

# Camera section
with st.container():
    st.markdown("### 📸 Capture from Camera")
    st.markdown('<div class="section">', unsafe_allow_html=True)

    if st.button("📷 Take Photo and Extract Text"):
        st.info("Activating webcam...")
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            st.error("❌ Camera not available or permission denied.")
        else:
            ret, frame = camera.read()
            camera.release()
            if ret:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                cv2.imwrite(temp_file.name, frame)

                st.image(temp_file.name, caption="📷 Captured Image", use_container_width=True)

                extracted_text = extract_text_via_ocr(temp_file.name)
                text_path = save_text(extracted_text, "camera_capture")
                st.text_area("📝 Extracted Text from Camera", extracted_text, height=300)
                st.success(f"💾 Text saved at: `{text_path}`")
            else:
                st.error("❌ Failed to capture image.")

    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<h6 style='text-align: center; color: gray;'>🔐 Your files and extracted data are securely saved locally.</h6>", unsafe_allow_html=True)
