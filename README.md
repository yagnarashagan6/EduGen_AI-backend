# EduGen AI Python Backend

This Python Flask backend provides API endpoints for the EduGen AI application, including talk mode functionality with speech-to-text and text-to-speech capabilities. **Now powered by Google Gemini API!**

## Features

- **Chat API**: AI-powered educational chat using Google Gemini API
- **Quiz Generation**: Dynamic quiz creation based on topics using Gemini
- **Talk Mode**: Speech-to-text and text-to-speech functionality
- **Rate Limiting**: Prevents API abuse
- **CORS Support**: Cross-origin request handling

## API Endpoints

### Chat

- `POST /api/chat` - Send messages to AI assistant
- Body: `{"message": "your question"}`
- Response: `{"response": "AI response"}`

### Quiz Generation

- `POST /api/generate-quiz` - Generate quiz questions
- Body: `{"topic": "subject", "count": 5}`
- Response: `{"questions": [...]}`

### Talk Mode

- `POST /api/speech-to-text` - Convert audio to text
- Form data with audio file
- Response: `{"text": "transcribed text"}`

- `POST /api/text-to-speech` - Convert text to audio
- Body: `{"text": "text to speak"}`
- Response: `{"audio": "base64_audio_data", "format": "mp3"}`

### Health Check

- `GET /api/health` - Server status
- Response: Server status and configuration info

## Environment Variables

Create a `.env` file with:

```
# Google Gemini API Configuration
GOOGLE_API_KEY=your_google_api_key_here
PORT=10000
FLASK_ENV=production
```

### Getting Your Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key and add it to your `.env` file

## Dependencies

All required packages are listed in `requirements.txt`:

- Flask (web framework)
- Flask-CORS (cross-origin support)
- Flask-Limiter (rate limiting)
- SpeechRecognition (speech-to-text)
- pyttsx3 (text-to-speech)
- pydub (audio processing)
- requests (HTTP client)
- python-dotenv (environment variables)
- gunicorn (WSGI server)
- **google-generativeai** (Google Gemini API client)

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the root directory to `Python-backend`
4. Render will automatically detect the `render.yaml` configuration
5. Set your environment variables in Render dashboard:
   - `GOOGLE_API_KEY`: Your Google Gemini API key

## Testing

1. Run the Gemini API connection test:

   ```bash
   python test_gemini.py
   ```

2. Run the full backend test suite:
   ```bash
   python test_backend.py
   ```

## Local Development

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file with your API keys

3. Run the application:
   ```bash
   python app.py
   ```

The server will start on `http://localhost:10000`

## Talk Mode Requirements

For talk mode to work properly, ensure:

- Audio input is in WebM format (browser default)
- Internet connection for Google Speech Recognition
- Proper microphone permissions in browser

## Rate Limiting

- Chat and Quiz endpoints: 2 requests per 15 seconds
- Other endpoints: 200 requests per day, 50 per hour

## Error Handling

The API includes comprehensive error handling for:

- Invalid requests
- API failures
- Audio processing errors
- Rate limit exceeded
- Server errors
