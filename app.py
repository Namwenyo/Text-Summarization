from flask import Flask, render_template, request, jsonify
from transformers import T5ForConditionalGeneration, T5Tokenizer
import os
import re
import docx2txt
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load model and tokenizer (replace with your fine-tuned model if needed)
model = T5ForConditionalGeneration.from_pretrained("t5-small")
tokenizer = T5Tokenizer.from_pretrained("t5-small")

# ----------- Utility Functions -----------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    ext = file_path.rsplit(".", 1)[1].lower()

    if ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == "pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return " ".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif ext in ["doc", "docx"]:
        return docx2txt.process(file_path)
    else:
        return ""

def preprocess_text(text):
    return re.sub(r"\s+", " ", text).strip()

def capitalize_sentences(text):
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    return ' '.join(s.capitalize() for s in sentences)

def summarize(text):
    input_text = "summarize: " + text
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=150,
        min_length=30,
        num_beams=4,
        early_stopping=True
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return capitalize_sentences(summary)

def format_summary(summary, fmt):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', summary) if s.strip()]
    
    if fmt == "bullets":
        return "\n".join(f"• {s}" for s in sentences)
    elif fmt == "numbered":
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    else:
        return " ".join(sentences)

# ----------- Routes -----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/summarize", methods=["POST"])
def summarize_api():
    data = request.get_json()
    text = data.get("text", "")
    fmt = data.get("format", "paragraph")

    if not text:
        return jsonify({"error": "No input text provided"}), 400

    try:
        clean_text = preprocess_text(text)
        summary = summarize(clean_text)
        formatted_summary = format_summary(summary, fmt)
        return jsonify({"summary": formatted_summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        try:
            text = extract_text_from_file(file_path)
            if not text.strip():
                return jsonify({"error": "Failed to extract text from file."}), 400
            return jsonify({"text": text})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Unsupported file type"}), 400

# ----------- Main -----------

if __name__ == "__main__":
    app.run(debug=True)

