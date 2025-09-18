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
# CORRECTED: Removed redundant 'import time' and 'import datetime' as they are handled by specific imports
import random
from datetime import datetime # This is the correct import to use
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
    # Using Gemini Flash model for fast responses
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    exit(1)

# CORRECTED: Made the Talk Mode prompt much stricter for shorter, more casual replies.
TALK_MODE_PROMPT = """
You are a friendly and casual AI assistant. Your goal is to provide a very short and direct answer.
**Strictly limit your response to 1-2 sentences maximum.**
Do NOT use any special formatting like bolding or lists.
Do NOT provide detailed explanations. Get straight to the point in a conversational way.
"""


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

GENERAL_DOC_PROMPT = """
You are a helpful assistant. Use the provided document context to give a short and sweet answer to the user's question. Be direct and concise.

--- DOCUMENT CONTEXT ---
{document_text}
--- END CONTEXT ---

User's Question: {user_question}
"""

# CORS configuration
allowed_origins = [
    "https://edugen-ai-zeta.vercel.app",
    "http://localhost:3000",
    "https://edugen-backend.onrender.com",
]

CORS(app, origins=allowed_origins, methods=["GET", "POST", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization"])

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize speech engine (if available)
if AUDIO_ENABLED:
    try:
        tts_engine = pyttsx3.init()
        speech_recognizer = sr.Recognizer()
    except Exception as e:
        print(f"Audio initialization failed: {e}")
        AUDIO_ENABLED = False
else:
    tts_engine = None
    speech_recognizer = None

def extract_text_from_file(file_data, filename):
    """Extracts text from PDF or DOCX file data."""
    if not DOCUMENT_PROCESSING_ENABLED:
        return None
        
    try:
        # Assumes file_data is a base64 string
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
    """Fetches response from Gemini API with exponential backoff."""
    max_retries = 5
    base_delay = 1
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Added a short sleep even for non-429 errors to prevent hammering
            import time
            time.sleep(1)
            if "429" in str(e) and attempt < max_retries - 1:
                delay = (base_delay * 2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit exceeded. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                print(f"Gemini API error: {e}")
                return "Sorry, an error occurred while processing your request."
    return "The service is currently busy. Please try again in a moment."

# Rate limit for chat and quiz endpoints
@limiter.limit("5 per 15 seconds") # Increased limit slightly
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.5",
        "timestamp": datetime.now().isoformat(),
        "model": "gemini-1.5-flash",
        "audio_features": AUDIO_ENABLED,
        "document_processing": DOCUMENT_PROCESSING_ENABLED
    })

@limiter.limit("5 per 15 seconds") # Increased limit slightly
@app.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint with support for document analysis and casual talk mode"""
    try:
        data = request.get_json()
        message = data.get("message", "")
        file_data = data.get("fileData")
        filename = data.get("filename")
        talk_mode = data.get("talkMode", False)
        
        if not message and not (file_data and filename):
            return jsonify({"error": "No message or file provided."}), 400

        # Handle document processing if file is provided
        if file_data and filename:
            if not DOCUMENT_PROCESSING_ENABLED:
                return jsonify({
                    "error": "Document processing not available",
                    "message": "PDF/DOCX processing is disabled on this server"
                }), 503
                
            extracted_text = extract_text_from_file(file_data, filename)
            if not extracted_text:
                return jsonify({"response": "Sorry, I could not read the content of the document."})
            
            classification_prompt = f"Is the following text a resume or CV? Answer with only 'yes' or 'no'.\n\n{extracted_text[:1000]}"
            is_resume_response = get_gemini_response(classification_prompt).strip().lower()

            if 'yes' in is_resume_response:
                if message:
                    final_prompt = GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=message)
                else:
                    final_prompt = f"{RESUME_ANALYSIS_PROMPT}\n\n--- RESUME CONTENT ---\n{extracted_text}"
            else:
                final_prompt = GENERAL_DOC_PROMPT.format(document_text=extracted_text, user_question=message)
            
            reply = get_gemini_response(final_prompt)
            return jsonify({"response": reply})

        # Handle regular chat
        if "time" in message.lower() or "date" in message.lower():
            # CORRECTED: Changed from datetime.datetime.now() to datetime.now()
            now = datetime.now()
            response_text = f"The current date and time is {now.strftime('%A, %B %d, %Y, %I:%M %p')}."
            return jsonify({"response": response_text})

        if talk_mode:
            # Casual talk mode using the new, stricter prompt
            final_prompt = f"{TALK_MODE_PROMPT}\n\nUser's question: {message}"
            reply = get_gemini_response(final_prompt)
        else:
            # Educational mode - detailed explanations
            prompt = f"""You are EduGen AI 🎓, a comprehensive educational assistant for students. When explaining topics, follow these guidelines:

📚 CONTENT DEPTH: Provide detailed, thorough explanations that cover:
• Key concepts and definitions
• Step-by-step breakdowns when applicable
• Multiple perspectives or approaches
• Important connections to related topics

🌍 REAL-WORLD EXAMPLES: Always include:
• Practical, everyday examples students can relate to
• Current events or modern applications
• Industry use cases and career connections
• Historical context when relevant

💡 CLARITY & UNDERSTANDING: Make content accessible by:
• Using simple language with clear explanations
• Breaking complex ideas into digestible parts
• Providing analogies and metaphors
• Including visual descriptions where helpful

📺 EDUCATIONAL RESOURCES: When appropriate, suggest:
• YouTube channels and specific video recommendations for visual learning
• Educational articles and research papers for deeper reading
• Interactive websites and tools for hands-on practice
• Free online courses (Khan Academy, Coursera, edX) for structured learning
• Documentaries and educational content for broader understanding

🔗 RESOURCE FORMAT: Present resources as:
📺 **YouTube Videos:**
• [Video Title] - Channel Name
• Search terms: 'specific keywords for finding videos'

📖 **Articles & Reading:**
• Article/website suggestions with brief descriptions
• Search terms for finding quality articles

📍 STRUCTURE: Organize responses with:
• Clear headings using emojis (🧮 math, 🧪 science, 📖 literature, etc.)
• Bullet points and numbered lists
• Key takeaways highlighted with ✨
• Practical tips marked with 💡
• Resource recommendations marked with 🔗

Always aim for comprehensive yet understandable explanations that help students truly grasp the material, see its relevance in the real world, and provide pathways for further learning through quality educational resources.

Student's question: {message}"""

            reply = get_gemini_response(prompt)
        
        return jsonify({"response": reply})
        
    except Exception as e:
        print(f"Chat API Error: {str(e)}")
        return jsonify({
            "error": "Failed to get response from AI",
            "message": str(e)
        }), 500

# The rest of your file (quiz, speech-to-text, etc.) remains the same as it was correct.
# I'm including it here for completeness.

@limiter.limit("2 per 15 seconds")
@app.route("/api/generate-quiz", methods=["POST"])
def generate_quiz():
    """Quiz generation endpoint"""
    try:
        data = request.get_json()
        topic = data.get("topic")
        count = data.get("count")

        if not topic or not isinstance(topic, str) or not topic.strip():
            return jsonify({
                "error": "Invalid input",
                "message": "Please provide a valid topic for the quiz"
            }), 400

        try:
            question_count = int(count)
            if question_count < 3 or question_count > 10:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                "error": "Invalid input",
                "message": "Please request between 3 and 10 questions"
            }), 400

        prompt = f"""Generate exactly {question_count} multiple choice quiz questions on the topic "{topic}". Follow these strict rules:
1. Each question must have:
   - A clear question text
   - Exactly 4 options (A, B, C, D)
   - One correct answer (must match exactly one option)
2. Format each question as JSON with:
   - "text": The question
   - "options": Array of 4 options (prefix with A), B), etc.)
   - "correctAnswer": The full correct option text
3. Return only a valid JSON array with no extra text

Example:
[
  {{
    "text": "What is the capital of France?",
    "options": ["A) London", "B) Paris", "C) Berlin", "D) Madrid"],
    "correctAnswer": "B) Paris"
  }}
]

Now generate {question_count} questions about "{topic}":"""

        gemini_prompt = f"""You are a quiz generator 📝. Generate engaging quiz questions using subject-relevant emojis in the question text (e.g., 🧮 for math, 🧪 for science, 🌍 for geography, etc.). Return only valid JSON arrays with quiz questions in the exact specified format. Do not include any additional text or explanations. Format the questions with emojis where appropriate, but ensure the options remain clearly marked with A), B), C), D).

{prompt}"""

        content = get_gemini_response(gemini_prompt)

        if not content or "sorry" in content.lower():
            raise Exception("Failed to get valid response from Gemini")

        content = content.replace("```json\n", "").replace("\n```", "").strip()
        
        try:
            questions = json.loads(content)
            if not isinstance(questions, list):
                raise ValueError("Response is not a valid array")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}, Raw content: {content}")
            raise Exception("Failed to parse quiz data")

        validated_questions = []
        for i, q in enumerate(questions):
            if not q.get("text") or not isinstance(q["text"], str):
                raise Exception(f"Question {i + 1} missing text")
            if not q.get("options") or not isinstance(q["options"], list) or len(q["options"]) != 4:
                raise Exception(f"Question {i + 1} must have exactly 4 options")
            if not q.get("correctAnswer") or not isinstance(q["correctAnswer"], str):
                raise Exception(f"Question {i + 1} missing correctAnswer")
            if q["correctAnswer"] not in q["options"]:
                raise Exception(f"Question {i + 1} correctAnswer doesn't match any option")
            
            validated_questions.append({
                "text": q["text"].strip(),
                "options": [opt.strip() for opt in q["options"]],
                "correctAnswer": q["correctAnswer"].strip()
            })

        if len(validated_questions) != question_count:
            raise Exception(f"Expected {question_count} questions, got {len(validated_questions)}")

        return jsonify({"questions": validated_questions})

    except Exception as e:
        print(f"Quiz generation error: {str(e)}")
        return jsonify({
            "error": "Failed to generate quiz",
            "message": str(e)
        }), 500

@app.route("/api/speech-to-text", methods=["POST"])
def speech_to_text():
    """Convert speech to text for talk mode"""
    if not AUDIO_ENABLED:
        return jsonify({
            "error": "Audio processing not available",
            "message": "Speech-to-text functionality is disabled on this server"
        }), 503
    
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400

        filename = secure_filename(f"{uuid.uuid4().hex}.webm")
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        audio_file.save(temp_path)

        try:
            audio = AudioSegment.from_file(temp_path)
            wav_path = temp_path.replace('.webm', '.wav')
            audio.export(wav_path, format="wav")

            with sr.AudioFile(wav_path) as source:
                audio_data = speech_recognizer.record(source)
                text = speech_recognizer.recognize_google(audio_data)

            os.remove(temp_path)
            os.remove(wav_path)

            return jsonify({"text": text})

        except sr.UnknownValueError:
            return jsonify({"error": "Could not understand audio"}), 400
        except sr.RequestError as e:
            return jsonify({"error": f"Speech recognition error: {str(e)}"}), 500
        finally:
            for path in [temp_path, wav_path]:
                if os.path.exists(path):
                    os.remove(path)

    except Exception as e:
        print(f"Speech-to-text error: {str(e)}")
        return jsonify({"error": f"Speech recognition failed: {str(e)}"}), 500

@app.route("/api/text-to-speech", methods=["POST"])
def text_to_speech():
    """Convert text to speech for talk mode"""
    if not AUDIO_ENABLED:
        return jsonify({
            "error": "Audio processing not available",
            "message": "Text-to-speech functionality is disabled on this server"
        }), 503
    
    try:
        data = request.get_json()
        text = data.get("text")
        
        if not text:
            return jsonify({"error": "Text is required"}), 400

        filename = f"{uuid.uuid4().hex}.mp3"
        temp_path = os.path.join(tempfile.gettempdir(), filename)

        tts_engine.setProperty('rate', 150)
        tts_engine.setProperty('volume', 0.9)
        
        tts_engine.save_to_file(text, temp_path)
        tts_engine.runAndWait()

        with open(temp_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        os.remove(temp_path)

        return jsonify({
            "audio": audio_base64,
            "format": "mp3"
        })

    except Exception as e:
        print(f"Text-to-speech error: {str(e)}")
        return jsonify({"error": f"Text-to-speech failed: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(e):
    """404 handler"""
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(429)
def rate_limit_handler(e):
    """Rate limit handler"""
    return jsonify({"error": "Too many requests, please wait and try again."}), 429

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)