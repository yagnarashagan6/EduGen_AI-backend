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
    # Using a fast and capable model for these tasks.
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    raise RuntimeError(f"Error initializing Gemini model: {e}")


# --- Prompts ---
# This prompt provides general instructions for the AI's persona.
GENERAL_CHAT_PROMPT = """
You are EduGen AI, a helpful and knowledgeable assistant.
Your goal is to provide well-structured, informative answers.

📋 **FORMATTING REQUIREMENTS:**
• Always use bullet points (•) for lists and information
• Use relevant emojis at the start of each section or point
• Use markdown for emphasis (e.g., **bolding**, *italics*)
• Structure your response with clear headings when appropriate
• When providing links, use Markdown format: [Link Text](URL)

🎯 **RESPONSE STYLE:**
• Be concise but comprehensive (2-5 sentences per point)
• Use a helpful and encouraging tone
• Break down complex information into digestible bullet points
• Include relevant emojis to make responses engaging and easy to scan
"""

# --- CORRECTED & IMPROVED PROMPT ---
# This prompt from your original chatbot.py is more direct and structured.
RESUME_ANALYSIS_PROMPT = """
You are an expert HR hiring manager. Analyze the following resume.
Provide a very "short and sweet" analysis. Be direct and use concise language.

**📄 ATS Score & Feedback:**
Give a score out of 100 and a brief, one-sentence explanation.

**👍 Strengths:**
List 2 key strengths in a bulleted list.

**👎 Weaknesses:**
List 2 major weaknesses in a bulleted list.

**💡 Recommendations:**
Provide 2 actionable recommendations in a bulleted list.
"""

# This prompt is used for answering questions about a general document.
GENERAL_DOC_PROMPT = """
You are an intelligent assistant, EduGen AI. A user has uploaded a document and asked a question about it.
Your task is to answer the user's question accurately based *only* on the provided document text.

📋 **FORMATTING REQUIREMENTS:**
• Structure your response with clear bullet points
• Use relevant emojis for each section or key point
• Use markdown formatting for emphasis
• If the answer cannot be found, clearly state: "❌ This information is not available in the provided document."

--- DOCUMENT CONTEXT ---
{document_text}
--- END CONTEXT ---

**❓ User's Question:** {user_question}

**📝 Answer:**
"""

# --- App Configuration ---
CORS(app, origins=["https://edugen-ai-zeta.vercel.app", "http://localhost:3000"],
     methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])


# --- Helper Functions ---
def extract_text_from_file(file_data, filename):
    """Extracts text from a base64 encoded PDF or DOCX file."""
    if not DOCUMENT_PROCESSING_ENABLED:
        return None, "Document processing libraries are not installed on the server."

    try:
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
            return response.text
        except Exception as e:
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

        # --- CORRECTED File Processing Logic ---
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
                # If the document is identified as a resume, always use the analysis prompt.
                # This ensures a structured review is given, which is the primary goal.
                final_prompt = f"{RESUME_ANALYSIS_PROMPT}\n\n--- RESUME CONTENT ---\n{extracted_text}"
            else:
                # For any other document, answer the user's question using the text as context.
                # If no question is asked, provide a summary as a default action.
                user_question = message if message else "Summarize this document."
                final_prompt = GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=user_question)

            reply = get_gemini_response(final_prompt)
            return jsonify({"response": reply})

        # --- Standard Chat Logic (No File) ---
        final_prompt = f"{GENERAL_CHAT_PROMPT}\n\nUser's question: {message}"
        reply = get_gemini_response(final_prompt)
        return jsonify({"response": reply})

    except Exception as e:
        print(f"An unexpected error occurred in /api/chat: {str(e)}")
        return jsonify({"error": "An internal server error occurred.", "message": str(e)}), 500

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)