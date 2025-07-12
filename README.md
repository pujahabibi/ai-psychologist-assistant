# Indonesian Mental Health Support Bot

A culturally sensitive, therapeutic-grade voice chatbot designed specifically for Indonesian users, featuring real-time speech processing, intent analysis, and comprehensive safety mechanisms.

## 🚀 Key Features

- **Voice-First Interface**: Real-time speech-to-text and text-to-speech
- **Cultural Sensitivity**: Deep understanding of Indonesian culture, language, and values
- **Advanced AI Models**: GPT-4.1 with Claude 3.5 Sonnet fallback for reliability
- **Safety Mechanisms**: Comprehensive crisis detection and intervention protocols
- **Therapeutic Techniques**: CBT, mindfulness, cultural validation, and spiritual integration
- **Islamic Counseling**: Integration of Islamic values and spiritual support
- **Family Dynamics**: Understanding of Indonesian family structures and hierarchies

## 🤖 AI Model Integration

### Primary Model: GPT-4.1
- Main therapeutic response generation
- Indonesian language optimization
- Cultural context understanding

### Fallback Model: Claude 3.5 Sonnet
- Automatic fallback when GPT-4.1 is unavailable
- Model validation and comparison capabilities
- Enhanced reliability and uptime

### Model Usage
```python
# Automatic fallback (default behavior)
response = bot._get_therapeutic_response(user_input, session_id)

# Compare responses from both models
validation = bot._get_therapeutic_response_with_validation(user_input, session_id)
```

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.8+
- Docker (optional)
- OpenAI API key (required)
- Anthropic API key (optional, for Claude fallback)

### Environment Configuration
Copy `env.template` to `.env` and configure:

```bash
# OpenAI API Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration (Optional - for Claude 3.5 Sonnet fallback)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 📊 API Endpoints

### Core Endpoints
- `POST /voice-therapy` - Complete voice therapy interaction
- `POST /therapeutic-response` - Text-based therapeutic response
- `POST /text-to-speech` - Convert text to speech
- `POST /speech-to-text` - Convert speech to text

### Model Management Endpoints
- `POST /therapeutic-response-validation` - Get responses from both models
- `GET /claude-status` - Check Claude availability

### Utility Endpoints
- `GET /tts-performance-stats` - TTS performance metrics
- `GET /crisis-resources` - Emergency contacts and resources
- `GET /sessions` - List active sessions

## 🔧 Advanced Features

### Parallel Text-to-Speech
Intelligent text chunking with parallel processing for faster audio generation:
- ≤150 chars: Parallel processing (8 workers)
- \>150 chars: Extended parallel processing (8 workers)

### Model Fallback Logic
1. **Primary**: Attempt GPT-4.1 response
2. **Fallback**: Use Claude 3.5 Sonnet if GPT-4.1 fails
3. **Error Handling**: Graceful degradation with user-friendly messages

### Safety Mechanisms
- 4-tier alert system (GREEN/YELLOW/ORANGE/RED)
- Crisis keyword detection
- Professional referral triggers
- Emergency contact integration

## 🧠 Cultural Integration

### Indonesian Context
- Family hierarchy respect
- Islamic values integration
- Traditional healing approaches
- Community-based support systems

### Therapeutic Approaches
- Javanese harmony principles
- Islamic counseling techniques
- Family-centered therapy
- Spiritual wellness integration

## 📈 Monitoring and Analytics

### Session Analysis
- Conversation tracking
- Performance metrics
- Error rate monitoring

## 🛡️ Safety and Ethics

- Professional boundaries maintenance
- Crisis intervention protocols
- Emergency hotline integration
- Data protection compliance

## 📱 Usage Examples

### Basic Therapy Session
```python
from infer import IndonesianMentalHealthBot

bot = IndonesianMentalHealthBot()
session_id = "user_session_123"

# Text-based interaction
response = bot._get_therapeutic_response(
    "Saya merasa cemas tentang masa depan", 
    session_id
)

# Voice-based interaction (requires audio data)
result = bot.listen_and_respond(session_id)
```

### Model Validation
```python
# Compare responses from both models
validation = bot._get_therapeutic_response_with_validation(
    "Saya merasa sedih hari ini",
    session_id
)

print(f"GPT-4.1: {validation['gpt_response']}")
print(f"Claude: {validation['claude_response']}")
print(f"Primary: {validation['primary_response']}")
```

## 🎯 Target Users

- Indonesian mental health support seekers
- Mental health professionals
- Researchers in AI-assisted therapy
- Cultural sensitivity advocates

## 🔮 Future Enhancements

- Multi-language support (Indonesian dialects)
- Advanced emotion recognition
- Integration with professional networks
- Mobile application development

## 📞 Emergency Resources

- Suicide Prevention: 119
- Medical Emergency: 118
- Mental Health Crisis: 500-454
- Women Crisis Center: 021-7270005

## 🤝 Contributing

We welcome contributions to improve cultural sensitivity, therapeutic techniques, and technical capabilities.

## 📄 License

This project is designed for mental health support and research purposes.

---

**Disclaimer**: This AI chatbot is not a replacement for professional mental health treatment. In case of emergency, please contact local emergency services or mental health professionals. 