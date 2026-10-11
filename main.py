
import os

from flask import Flask, render_template, request
from google import genai
from google.genai import types
try:
    import pymupdf as fitz  # PyMuPDF (newer versions)
except ImportError:
    import fitz  # PyMuPDF (older versions)
from docx import Document

app = Flask(__name__)

# --- CONFIGURATION ---
# The API key is read from an environment variable (never hardcode it).
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def extract_text_from_pdf(file):
    """Read an uploaded PDF as a byte stream and return its text layer."""
    text = ""
    try:
        file_bytes = file.read()
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        return f"PDF Error: {str(e)}"
    return text


def extract_text_from_docx(file):
    """Return the text of every paragraph in an uploaded DOCX file."""
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"DOCX Error: {str(e)}"


@app.route("/", methods=["GET", "POST"])
def index():
    simplified = ""
    original = ""

    if request.method == "POST":
        file = request.files.get("file")

        # Priority 1: File upload
        if file and file.filename != "":
            name = file.filename.lower()
            if name.endswith(".pdf"):
                original = extract_text_from_pdf(file)
            elif name.endswith(".docx"):
                original = extract_text_from_docx(file)
        # Priority 2: Text box
        else:
            original = request.form.get("content", "")

        if original and original.strip():
            if client is None:
                simplified = ("AI Error: GEMINI_API_KEY is not set. "
                              "See the README for setup steps.")
            else:
                prompt = ("Simplify this text for a 6th grader. "
                          "Use plain text only, no markdown: \n\n" + original)
                try:
                    response = client.models.generate_content(
                        model=MODEL_ID,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.1),
                    )
                    simplified = response.text
                except Exception as e:
                    simplified = f"AI Error: {str(e)}"

    return render_template("index.html", original=original, simplified=simplified)


if __name__ == "__main__":
    app.run(debug=True)
