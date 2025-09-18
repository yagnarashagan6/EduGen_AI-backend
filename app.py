from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
import json
import io
import base64
import sys
import random
from datetime import datetime
import tempfile
import uuid
from werkzeug.utils import secure_filename
import google.generativeai as genai

# Optional imports for audio processing
try:
    import speech_recognition as sr
    import pyttsx3
    from pydub import AudioSegment
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False
    print("Audio processing libraries not available. Speech features disabled.")

# Document processing imports
try:
    import PyPDF2
    from docx import Document
    DOCUMENT_PROCESSING_ENABLED = True
except ImportError:
    DOCUMENT_PROCESSING_ENABLED = False
    print("Document processing libraries not available. PDF/DOCX features disabled.")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

try:
    model = genai.GenerativeModel('gemini-1.5-flash') # Using 1.5-flash for potential improvements
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    exit(1)

# --- PROMPTS ---

# --- CORRECTED PROMPT ---
# This prompt now strictly enforces Markdown for links.
GENERAL_CHAT_PROMPT = """
You are a helpful and knowledgeable AI assistant named EduGen.
Your goal is to provide concise but informative answers, typically 2-4 sentences long.
Use markdown formatting like bolding to emphasize key points for better readability.
When providing links to online resources, you MUST use Markdown format, like this: [Link Text](URL).
For example: [Learn about Python on GeeksforGeeks](https://www.geeksforgeeks.org/python-programming-language/). This is not optional.
If the user asks for a link to a specific website, YouTube channel, or any online resource, provide the direct URL or construct the most likely URL based on the information given.
Your tone should be helpful and encouraging.
"""

RESUME_ANALYSIS_PROMPT = """
You are an expert HR hiring manager. Analyze the following resume.
Provide a very "short and sweet" analysis. Be direct and use concise language.
**ATS Score & Feedback:**
Give a score out of 100 and a brief, one-sentence explanation.
**Strengths:**
List 2 key strengths in a bulleted list.
**Weaknesses:**
List 2 major weaknesses in a bulleted list.
**Recommendations:**
Provide 2 actionable recommendations in a bulleted list.
"""

GENERAL_DOC_PROMPT = """
You are a helpful assistant. Use the provided document context to give a short and sweet answer to the user's question. Be direct and concise.
--- DOCUMENT CONTEXT ---
{document_text}
--- END CONTEXT ---
User's Question: {user_question}
"""

# Copied and adapted from chatbot.py to guide the model on providing links
RESOURCE_LINKS = """
You can provide links to any legitimate online resources. Some common examples include:
- GeeksforGeeks: https://www.geeksforgeeks.org/
- W3Schools: https://www.w3schools.com/
- YouTube: https://www.youtube.com/
- Instagram: https://www.instagram.com/
For YouTube channels, construct URLs like: https://www.youtube.com/@channelname or https://www.youtube.com/c/channelname
"""


# CORS configuration
CORS(app, origins=["https://edugen-ai-zeta.vercel.app", "http://localhost:3000", "https://edugen-backend.onrender.com"],
     methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

def extract_text_from_file(file_data, filename):
    if not DOCUMENT_PROCESSING_ENABLED: return None
    try:
        decoded_data = base64.b64decode(file_data.split(',')[1])
        if filename.endswith('.pdf'):
            pdf_file = io.BytesIO(decoded_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return "".join(page.extract_text() + "\n" for page in pdf_reader.pages)
        elif filename.endswith('.docx'):
            docx_file = io.BytesIO(decoded_data)
            doc = Document(docx_file)
            return "".join(para.text + "\n" for para in doc.paragraphs)
        return None
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def get_gemini_response(prompt):
    max_retries = 5
    base_delay = 1
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            import time
            if "429" in str(e) and attempt < max_retries - 1:
                delay = (base_delay * 2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit exceeded. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                print(f"Gemini API error: {e}")
                return "Sorry, an error occurred while processing your request."
    return "The service is currently busy. Please try again in a moment."

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "version": "1.0.9", "timestamp": datetime.now().isoformat()})

@limiter.limit("5 per 15 seconds")
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message", "")
        file_data = data.get("fileData")
        filename = data.get("filename")

        if not message and not (file_data and filename):
            return jsonify({"error": "No message or file provided."}), 400

        # Handle document processing
        if file_data and filename:
            extracted_text = extract_text_from_file(file_data, filename)
            if not extracted_text:
                return jsonify({"response": "Sorry, I could not read the content of the document."})

            classification_prompt = f"Is the following text a resume or CV? Answer with only 'yes' or 'no'.\n\n{extracted_text[:1000]}"
            is_resume_response = get_gemini_response(classification_prompt).strip().lower()

            if 'yes' in is_resume_response:
                final_prompt = f"{RESUME_ANALYSIS_PROMPT}\n\n--- RESUME CONTENT ---\n{extracted_text}" if not message else GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=message)
            else:
                final_prompt = GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=message)

            reply = get_gemini_response(final_prompt)
            return jsonify({"response": reply})

        # --- UPDATED LOGIC ---
        # The prompt now includes the resource links and specific instructions from chatbot.py
        final_prompt = f"{GENERAL_CHAT_PROMPT}\n\n{RESOURCE_LINKS}\n\nUser's question: {message}"
        reply = get_gemini_response(final_prompt)

        return jsonify({"response": reply})

    except Exception as e:
        print(f"Chat API Error: {str(e)}")
        return jsonify({"error": "Failed to get response from AI", "message": str(e)}), 500

@limiter.limit("2 per 15 seconds")
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
            if question_count < 3 or question_count > 10: raise ValueError()
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid input", "message": "Please request between 3 and 10 questions"}), 400
        prompt = f"""Generate exactly {question_count} multiple choice quiz questions on the topic "{topic}". Follow these strict rules:
1. Each question must have: "text", "options" (Array of 4), and "correctAnswer".
2. Return only a valid JSON array with no extra text.
Example: [{{"text": "What is the capital of France?", "options": ["A) London", "B) Paris", "C) Berlin", "D) Madrid"], "correctAnswer": "B) Paris"}}]
Now generate {question_count} questions about "{topic}":"""
        gemini_prompt = f"""You are a quiz generator. Generate engaging quiz questions using subject-relevant emojis in the question text. Return only valid JSON arrays in the exact specified format. Do not include any additional text or explanations.
{prompt}"""
        content = get_gemini_response(gemini_prompt)
        if not content or "sorry" in content.lower(): raise Exception("Failed to get valid response from Gemini")
        content = content.replace("```json\n", "").replace("\n```", "").strip()
        try:
            questions = json.loads(content)
            if not isinstance(questions, list): raise ValueError("Response is not a valid array")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}, Raw content: {content}")
            raise Exception("Failed to parse quiz data")
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
    app.run(host="0.0.0.0", port=port, debug=False)
