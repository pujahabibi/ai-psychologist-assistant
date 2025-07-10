# Indonesian Mental Health Support Bot (Kak Indira)

A culturally-sensitive Indonesian mental health chatbot with voice capabilities, built with FastAPI, OpenAI APIs, and modern web technologies.

## Features

- **Voice-First Interface**: Real-time speech-to-text and text-to-speech in Indonesian
- **Cultural Sensitivity**: Designed specifically for Indonesian culture and values
- **Mental Health Support**: Therapeutic conversations with empathetic responses
- **Islamic Values Integration**: Respectful of religious and cultural contexts
- **Real-time Processing**: Seamless voice conversations with minimal latency
- **Modern UI**: Beautiful, responsive web interface with status indicators

## Quick Start

### 1. Configuration

Create a `.env` file from the template:

```bash
cp env.template .env
```

Edit the `.env` file with your OpenAI API key:

```bash
# Indonesian Mental Health Support Bot Configuration
OPENAI_API_KEY=your_actual_openai_api_key_here

# Optional settings
TZ=Asia/Jakarta
LANG=id_ID.UTF-8
```

**Important**: Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### 2. Docker Deployment (Recommended)

```bash
# Option 1: Using automated deployment script
./deploy.sh start

# Option 2: Manual Docker Compose
docker-compose up --build

# Option 3: Background deployment
docker-compose up -d --build
```

#### Pre-deployment Validation

```bash
# Check if system is ready for deployment
./docker-check.sh

# The script will validate:
# - Docker installation
# - .env file configuration
# - Required files and directories
# - Port availability
```

#### Deployment Management

```bash
# Start the bot
./deploy.sh start

# Stop the bot
./deploy.sh stop

# Restart the bot
./deploy.sh restart

# View real-time logs
./deploy.sh logs

# Check container status and health
./deploy.sh status

# Run health check
./deploy.sh test

# Clean up all containers and images
./deploy.sh clean
```

### 3. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Application

Open your browser and go to: `http://localhost:8000`

## Usage

1. **First Visit**: Click the speaker icon (🔊) to activate audio
2. **Welcome Message**: The bot will automatically greet you in Indonesian
3. **Voice Conversation**: Click the microphone (🎤) to start speaking
4. **Real-time Response**: The bot will automatically respond with voice

## Technical Stack

- **Backend**: Python 3.10, FastAPI, OpenAI GPT-4, Whisper, TTS
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Audio**: PyAudio, Web Audio API
- **Infrastructure**: Docker, Docker Compose
- **Database**: In-memory conversation management

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | None |
| `TZ` | Timezone | `Asia/Jakarta` |
| `LANG` | Language locale | `id_ID.UTF-8` |

### OpenAI Models Used

- **Chat**: `gpt-4.1-nano` for therapeutic conversations
- **Speech-to-Text**: `whisper-1` for Indonesian voice recognition
- **Text-to-Speech**: `gpt-4o-mini-tts` for natural voice synthesis

## Security

- ✅ API keys stored in `.env` file (never committed to git)
- ✅ Conversation data stored in memory only
- ✅ No persistent user data collection
- ✅ HTTPS-ready for production deployment

## Cultural Considerations

The bot (Kak Indira) is designed with deep understanding of:

- Indonesian family structures and social hierarchies
- Islamic values and religious sensitivity
- Mental health stigma in Indonesian society
- Therapeutic approaches suitable for Indonesian culture
- Bahasa Indonesia natural language patterns

## Development

### File Structure

```
speech/
├── main.py              # FastAPI application
├── infer.py             # Voice assistant core logic
├── templates/           # HTML templates
│   └── index.html       # Main web interface
├── static/              # Static assets
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── env.template        # Environment template
└── README.md           # This file
```

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.template .env
# Edit .env with your OpenAI API key

# Run development server
uvicorn main:app --reload
```

## Troubleshooting

### Common Issues

1. **No audio playback**: Check browser audio permissions
2. **API errors**: Verify OpenAI API key in `.env` file
3. **Docker build fails**: Ensure Docker is running and has internet access
4. **Voice not recognized**: Check microphone permissions in browser

### Docker Issues

```bash
# Quick diagnosis
./docker-check.sh

# Restart the bot
./deploy.sh restart

# Check logs
./deploy.sh logs

# Clean rebuild
./deploy.sh clean
./deploy.sh start

# Manual troubleshooting
docker-compose down
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is intended for educational and therapeutic support purposes. Please use responsibly and ensure compliance with local healthcare regulations.

## Support

For issues or questions:
- Check the troubleshooting section
- Review Docker logs
- Ensure proper .env configuration
- Verify OpenAI API key validity

---

**Disclaimer**: This is an AI-powered tool and should not replace professional mental health care. Always consult qualified healthcare providers for serious mental health concerns. 