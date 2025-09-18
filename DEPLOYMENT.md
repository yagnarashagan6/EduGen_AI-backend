# Deployment Guide for EduGen AI Python Backend

## Quick Deployment on Render

### Step 1: Prepare Your Repository

1. Make sure all files are in the `Python-backend` folder:
   - `app.py` (main Flask application)
   - `requirements.txt` (Python dependencies)
   - `runtime.txt` (Python version)
   - `Procfile` (process configuration)
   - `render.yaml` (Render configuration)
   - `.env.example` (environment template)

### Step 2: Deploy on Render

1. Go to [Render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `edugen-python-backend`
   - **Root Directory**: `Python-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

### Step 3: Set Environment Variables

In Render dashboard, add these environment variables:

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `FLASK_ENV`: `production`

### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Test your endpoints using the provided URL

## API Endpoints After Deployment

Your backend will be available at: `https://your-service-name.onrender.com`

### Available Endpoints:

- `GET /api/health` - Health check
- `POST /api/chat` - AI chat
- `POST /api/generate-quiz` - Quiz generation
- `POST /api/speech-to-text` - Speech to text (Talk Mode)
- `POST /api/text-to-speech` - Text to speech (Talk Mode)

## Frontend Integration

Update your frontend to use the new Python backend URL:

```javascript
const API_BASE_URL = "https://your-service-name.onrender.com";
```

## Talk Mode Features

The Python backend includes full talk mode support:

### Speech-to-Text

- Accepts audio files via FormData
- Supports WebM format (browser default)
- Uses Google Speech Recognition
- Returns transcribed text

### Text-to-Speech

- Accepts JSON with text
- Returns base64 encoded MP3 audio
- Configurable speech rate and volume

## Testing

1. **Local Testing**: Run `python test_backend.py` (requires running server)
2. **Production Testing**: Update test script URL to your Render URL

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are in requirements.txt
2. **Audio Issues**: Ensure proper audio format and permissions
3. **API Failures**: Check OpenRouter API key and quotas
4. **Rate Limiting**: Respect the 2 requests per 15 seconds limit

### Checking Logs:

- In Render dashboard, go to your service
- Click "Logs" tab to see real-time logs
- Look for error messages and API responses

## Security Notes

- Never commit `.env` files with real API keys
- Use Render's environment variables for secrets
- API keys are automatically secured in production
- CORS is configured for your frontend domains

## Performance

- Configured for 1 worker (suitable for free tier)
- 120-second timeout for AI requests
- Rate limiting prevents abuse
- Optimized for educational workloads

## Monitoring

Monitor your deployment:

- Check `/api/health` endpoint regularly
- Monitor Render dashboard for errors
- Track API usage in OpenRouter dashboard
