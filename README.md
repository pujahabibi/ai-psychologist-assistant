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

## 🏗️ Clean Architecture Implementation

This project has been refactored using **Clean Architecture** principles for improved maintainability, testability, and scalability.

### 🗂️ Project Structure

```
speech/
├── src/
│   ├── core/
│   │   ├── entities/               # Domain models
│   │   │   ├── therapeutic_session.py
│   │   │   ├── audio_data.py
│   │   │   └── therapeutic_response.py
│   │   ├── use_cases/              # Business logic
│   │   │   └── therapy_interaction.py
│   │   └── interfaces/             # Contracts/Ports
│   │       ├── ai_service.py
│   │       ├── audio_service.py
│   │       └── session_service.py
│   ├── infrastructure/             # External services
│   │   ├── ai_services/
│   │   │   ├── gpt_service.py
│   │   │   ├── claude_service.py
│   │   │   └── ai_orchestrator.py
│   │   ├── audio_services/
│   │   │   └── audio_service.py
│   │   ├── session_services/
│   │   │   └── session_manager.py
│   │   └── config/
│   │       └── settings.py
│   └── main/
│       └── app.py                  # Dependency injection
├── app.py                          # FastAPI application (Clean Architecture)
├── app_legacy.py                   # Original monolithic app (backup)
├── infer_legacy.py                 # Original monolithic logic (backup)
├── test_clean_architecture.py      # Clean architecture tests
└── templates/
    └── index.html
```

### 🔧 Architecture Benefits

- **Separation of Concerns**: Each layer has a specific responsibility
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Testability**: Easy to mock dependencies and unit test components
- **Maintainability**: Changes in one layer don't affect others
- **Scalability**: Easy to add new features or replace components

### 📚 Layer Descriptions

#### 1. **Core Layer** (Business Logic)
- **Entities**: Domain models (`TherapeuticSession`, `AudioData`, `TherapeuticResponse`)
- **Use Cases**: Business logic orchestration (`TherapyInteractionUseCase`)
- **Interfaces**: Contracts for external dependencies

#### 2. **Infrastructure Layer** (External Services)
- **AI Services**: GPT and Claude API integrations with fallback logic
- **Audio Services**: Speech-to-text and text-to-speech processing
- **Session Services**: Session management and consent handling
- **Configuration**: Settings management with preserved original values

#### 3. **Presentation Layer** (API Endpoints)
- **FastAPI Application**: RESTful API endpoints
- **Request/Response Models**: Pydantic models for data validation

## 🤖 AI Model Integration

### Primary Model: GPT-4.1
- Main therapeutic response generation
- Indonesian language optimization
- Cultural context understanding
- **Preserved hyperparameters**:
  - Temperature: 0.3
  - Max tokens: 1024
  - Presence penalty: 0.1
  - Frequency penalty: 0.1

### Fallback Model: Claude 3.5 Sonnet
- Automatic fallback when GPT-4.1 is unavailable
- Model validation and comparison capabilities
- Enhanced reliability and uptime

### Original System Prompt
The complete therapeutic system prompt has been **preserved exactly** as in the original implementation, maintaining all cultural sensitivity, safety mechanisms, and therapeutic techniques.

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

# Test clean architecture
python test_clean_architecture.py

# Run the application
python app.py
```

## 📊 API Endpoints

### Core Endpoints
- `POST /voice-therapy` - Complete voice therapy interaction
- `POST /therapeutic-response` - Text-based therapeutic response
- `POST /text-to-speech` - Convert text to speech (always parallel)
- `POST /speech-to-text` - Convert speech to text

### Clean Architecture Endpoints
- `GET /service-status` - Get service status and configuration
- `POST /therapeutic-response-validation` - Get responses from both models
- `GET /claude-status` - Check Claude availability

### Session Management
- `GET /session-info/{session_id}` - Get session information
- `DELETE /session/{session_id}` - Delete session
- `GET /sessions` - List active sessions
- `GET /session-analysis/{session_id}` - Get session analysis

### Utility Endpoints
- `GET /tts-performance-stats` - TTS performance metrics
- `GET /crisis-resources` - Emergency contacts and resources
- `GET /health` - Health check with architecture info

## 🔧 Advanced Features

### Parallel Text-to-Speech
Intelligent text chunking with parallel processing for faster audio generation:
- **Always uses parallel processing** (per user preference)
- Smart worker allocation (8 workers by default)
- **MP3 format** (per user preference)
- Performance metrics and monitoring

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

## 📈 Testing and Validation

### Clean Architecture Testing
```bash
# Run clean architecture tests
python test_clean_architecture.py
```

### Test Coverage
- Entity creation and validation
- Use case business logic
- Service availability
- Session management
- Configuration loading
- API integration

## 🛡️ Safety and Ethics

- Professional boundaries maintenance
- Crisis intervention protocols
- Emergency hotline integration
- Data protection compliance

## 📱 Usage Examples

### Basic Therapy Session (Clean Architecture)
```python
from src.main.app import app
from src.core.entities.audio_data import AudioData

# Get use case
therapy_use_case = app.get_therapy_use_case()

# Text-based interaction
result = await therapy_use_case.process_text_therapy(
    "Saya merasa cemas tentang masa depan",
    session_id="user_session_123"
)

# Voice-based interaction
audio_data = AudioData(audio_bytes=audio_bytes, format="mp3")
result = await therapy_use_case.process_voice_therapy(audio_data, session_id)
```

### Model Validation
```python
# Compare responses from both models
validation = await therapy_use_case.get_validated_response(
    "Saya merasa sedih hari ini",
    session_id
)

print(f"GPT-4.1: {validation.gpt_response.content}")
print(f"Claude: {validation.claude_response.content}")
print(f"Primary: {validation.get_primary_or_fallback().content}")
```

## 🔄 Migration from Legacy

### File Changes
- `app.py` → `app_legacy.py` (backup)
- `infer.py` → `infer_legacy.py` (backup)
- New `app.py` uses clean architecture
- Added `src/` directory with clean architecture components

### Preserved Elements
- **System prompt**: Exactly as in original
- **Model names**: gpt-4.1 and claude-3-5-sonnet-20241022
- **Hyperparameters**: temperature=0.3, max_tokens=1024, etc.
- **API endpoints**: All original endpoints maintained
- **User preferences**: Parallel TTS, MP3 format

### Breaking Changes
- None - all original functionality preserved
- API responses may include additional metadata
- Better error handling and logging

## 🎯 Target Users

- Indonesian mental health support seekers
- Mental health professionals
- Developers working with clean architecture
- Researchers in AI-assisted therapy
- Cultural sensitivity advocates

## 🔮 Future Enhancements

- Advanced emotion recognition
- Integration with professional networks
- Mobile application development
- Multi-language support (Indonesian dialects)
- Enhanced testing coverage
- Performance optimizations

## 📞 Emergency Resources

- Suicide Prevention: 119
- Medical Emergency: 118
- Mental Health Crisis: 500-454
- Women Crisis Center: 021-7270005

## 🤝 Contributing

We welcome contributions to improve cultural sensitivity, therapeutic techniques, and technical capabilities. Please ensure clean architecture principles are followed.

## 📄 License

This project is designed for mental health support and research purposes.

---

**Disclaimer**: This AI chatbot is not a replacement for professional mental health treatment. In case of emergency, please contact local emergency services or mental health professionals. 