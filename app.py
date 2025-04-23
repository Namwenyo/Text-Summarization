from flask import Flask, render_template, request, jsonify
import os
import pdfplumber
import docx
from transformers import pipeline

app = Flask(__name__)

# PDF extraction
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# DOCX extraction
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# BART-based summarization
summarizer = pipeline("summarization", model="t5-small")

def summarize_text(text, max_length=100, min_length=30):
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]["summary_text"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json()
    text = data.get("text", "")
    format_style = data.get("format", "paragraph")

    if not text.strip():
        return jsonify({"error": "No input text provided."}), 400

    try:
        summary = summarize_text(text)
        return jsonify({"summary": summary})
    except Exception as e:
        print("Summarization error:", str(e))
        return jsonify({"error": f"Summarization failed: {str(e)}"}), 500

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filename = file.filename.lower()

    try:
        if filename.endswith(".txt"):
            text = file.read().decode("utf-8")
        elif filename.endswith(".pdf"):
            text = extract_text_from_pdf(file)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(file)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
