from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
import io
import base64
import random
from datetime import datetime
import google.generativeai as genai

# Document processing imports
# Make sure to install these: pip install PyPDF2 python-docx
try:
    import PyPDF2
    from docx import Document
    DOCUMENT_PROCESSING_ENABLED = True
except ImportError:
    DOCUMENT_PROCESSING_ENABLED = False
    print("WARNING: PyPDF2 or python-docx not found. PDF/DOCX features will be disabled.")
    print("Install them with: pip install PyPDF2 python-docx")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# --- Google Gemini API Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Error: GOOGLE_API_KEY environment variable is not set.")

genai.configure(api_key=GOOGLE_API_KEY)

try:
    # Using gemini-1.5-flash as it's fast and capable for these tasks.
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    raise RuntimeError(f"Error initializing Gemini model: {e}")


# --- Prompts ---
# This prompt provides general instructions for the AI's persona.
GENERAL_CHAT_PROMPT = """
You are EduGen AI, a helpful and knowledgeable assistant.
Your goal is to provide concise, informative answers (2-4 sentences).
Use markdown for emphasis (e.g., **bolding**).
When providing links, YOU MUST use Markdown format: [Link Text](URL).
Your tone should be helpful and encouraging.
"""

# This prompt is used specifically for analyzing resumes.
RESUME_ANALYSIS_PROMPT = """
You are an expert ATS (Applicant Tracking System) and professional career coach. A user has uploaded their resume for analysis. Provide a comprehensive and professional review.

Follow this structure strictly:
1.  **📊 ATS Compatibility Score:** Give a score out of 100. Justify it briefly based on clarity, keyword optimization, and standard formatting.
2.  **👍 Strengths:** Identify 2-3 of the strongest aspects of the resume (e.g., quantifiable achievements, strong action verbs, clear structure).
3.  **💡 Areas for Improvement:** Provide 2-3 specific, actionable suggestions for improvement. Be constructive.
4.  **💬 Summary:** Briefly summarize the candidate's professional profile based on the resume.
"""

# This prompt is used for answering questions about a general document.
GENERAL_DOC_PROMPT = """
You are an intelligent assistant, EduGen AI. A user has uploaded a document and asked a question about it.
Your task is to answer the user's question accurately based *only* on the provided document text.
If the answer cannot be found in the text, clearly state that the information is not in the provided document.

--- DOCUMENT CONTEXT ---
{document_text}
--- END CONTEXT ---

**User's Question:** {user_question}
"""

# --- App Configuration ---
# CORS configuration to allow requests from your frontend
CORS(app, origins=["https://edugen-ai-zeta.vercel.app", "http://localhost:3000"],
     methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# Rate limiting to prevent abuse
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])


# --- Helper Functions ---
def extract_text_from_file(file_data, filename):
    """Extracts text from a base64 encoded PDF or DOCX file."""
    if not DOCUMENT_PROCESSING_ENABLED:
        return None, "Document processing libraries are not installed on the server."

    try:
        # The frontend sends a data URL (e.g., "data:application/pdf;base64,JVBERi..."), we need to strip the header.
        if ',' not in file_data:
            return None, "Invalid base64 file data."
        header, encoded = file_data.split(",", 1)
        decoded_data = base64.b64decode(encoded)
        file_stream = io.BytesIO(decoded_data)

        if filename.lower().endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file_stream)
            return "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text()), None
        elif filename.lower().endswith('.docx'):
            doc = Document(file_stream)
            return "\n".join(para.text for para in doc.paragraphs if para.text), None
        else:
            return None, "Unsupported file type. Please upload a PDF or DOCX file."
    except PyPDF2.errors.PdfReadError:
        return None, "Could not read the PDF file. It may be corrupted or encrypted."
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None, f"An unexpected error occurred while processing the file."

def get_gemini_response(prompt):
    """Sends a prompt to the Gemini API with retry logic for rate limiting."""
    max_retries = 3
    base_delay = 1
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            # Accessing the text safely
            return response.text
        except Exception as e:
            # Check for rate limit error (often indicated by a 429 status code in underlying API calls)
            if "429" in str(e) and attempt < max_retries - 1:
                import time
                delay = (base_delay * 2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit exceeded. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                print(f"Gemini API error: {e}")
                return "Sorry, an error occurred while connecting to the AI service."
    return "The service is currently busy. Please try again in a moment."


# --- API Routes ---
@app.route("/api/health", methods=["GET"])
def health_check():
    """Provides a simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "document_processing": DOCUMENT_PROCESSING_ENABLED
        }
    })

@limiter.limit("10 per minute")
@app.route("/api/chat", methods=["POST"])
def chat():
    """Handles chat messages, including file uploads for analysis."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input."}), 400

        message = data.get("message", "").strip()
        file_data = data.get("fileData")
        filename = data.get("filename")

        if not message and not (file_data and filename):
            return jsonify({"error": "No message or file was provided."}), 400

        # --- File Processing Logic ---
        if file_data and filename:
            extracted_text, error = extract_text_from_file(file_data, filename)
            if error:
                return jsonify({"response": error}), 400
            if not extracted_text:
                return jsonify({"response": "Sorry, I could not extract any text from the document. It might be empty or an image-based file."})

            # Use the LLM to classify the document
            classification_prompt = f"Is the following text a resume or CV? Answer with only 'yes' or 'no'.\n\n{extracted_text[:1000]}"
            is_resume_response = get_gemini_response(classification_prompt).strip().lower()

            if 'yes' in is_resume_response:
                # If it's a resume and the user just wants a review, use the analysis prompt
                if not message or "review" in message.lower() or "analyze" in message.lower():
                    final_prompt = f"{RESUME_ANALYSIS_PROMPT}\n\n--- RESUME CONTENT ---\n{extracted_text}"
                # If they ask a specific question, answer it using the resume as context
                else:
                    final_prompt = GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=message)
            else:
                # For any other document, answer the user's question using the text as context
                if not message:
                    message = "Summarize this document." # Default action if no question is asked
                final_prompt = GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=message)

            reply = get_gemini_response(final_prompt)
            return jsonify({"response": reply})

        # --- Standard Chat Logic (No File) ---
        final_prompt = f"{GENERAL_CHAT_PROMPT}\n\nUser's question: {message}"
        reply = get_gemini_response(final_prompt)
        return jsonify({"response": reply})

    except Exception as e:
        print(f"An unexpected error occurred in /api/chat: {str(e)}")
        return jsonify({"error": "An internal server error occurred.", "message": str(e)}), 500

# The generate_quiz route and error handlers remain unchanged...
@limiter.limit("5 per minute")
@app.route("/api/generate-quiz", methods=["POST"])
def generate_quiz():
    try:
        data = request.get_json()
        topic = data.get("topic")
        count = data.get("count")
        if not topic or not isinstance(topic, str) or not topic.strip():
            return jsonify({"error": "Invalid input", "message": "Please provide a valid topic for the quiz"}), 400
        try:
            question_count = int(count)
            if not 3 <= question_count <= 10: raise ValueError()
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid input", "message": "Please request between 3 and 10 questions"}), 400
        
        prompt = f"""Generate exactly {question_count} multiple choice quiz questions on the topic "{topic}". 
        
        Follow these strict rules:
        1. Each question must have: "text", "options" (an array of 4 strings), and "correctAnswer" (the full string of the correct option).
        2. Return ONLY a valid JSON array. Do not include any introductory text, explanations, or markdown fences like ```json.
        
        Example:
        [
          {{"text": "What is the capital of France?", "options": ["A) London", "B) Paris", "C) Berlin", "D) Madrid"], "correctAnswer": "B) Paris"}}
        ]
        
        Now generate the quiz."""

        gemini_prompt = f"You are a quiz generator. Generate engaging quiz questions using subject-relevant emojis in the question text. {prompt}"
        
        content = get_gemini_response(gemini_prompt)
        if not content: raise Exception("Failed to get a valid response from the AI model.")
        
        # Clean the response to ensure it's valid JSON
        content = content.strip()
        
        try:
            questions = json.loads(content)
            if not isinstance(questions, list): raise ValueError("Response is not a valid JSON array.")
        except json.JSONDecodeError:
            raise Exception(f"Failed to parse quiz data from the model's response.")
            
        return jsonify({"questions": questions})
        
    except Exception as e:
        print(f"Quiz generation error: {str(e)}")
        return jsonify({"error": "Failed to generate quiz", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({"error": "Too many requests, please wait and try again."}), 429

if __name__ == "__main__":
    # It's recommended to use a production-ready WSGI server like Gunicorn instead of app.run in production
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
