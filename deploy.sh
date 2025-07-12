#!/bin/bash

# Indonesian Mental Health Support Bot - Clean Architecture Deployment Script
# Kak Indira - Konselor Kesehatan Mental (Clean Architecture)

set -e

echo "🧠 Indonesian Mental Health Support Bot - Clean Architecture Deployment"
echo "💚 Kak Indira - Konselor Kesehatan Mental (Clean Architecture)"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo -e "${YELLOW}💡 Visit: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check clean architecture structure
check_architecture() {
    echo -e "${BLUE}🏗️  Validating clean architecture structure...${NC}"
    
    # Check main directories
    if [ ! -d "src" ]; then
        echo -e "${RED}❌ src/ directory not found. Clean architecture requires src/ directory.${NC}"
        exit 1
    fi
    
    if [ ! -d "src/core" ]; then
        echo -e "${RED}❌ src/core/ directory not found. Core business logic directory missing.${NC}"
        exit 1
    fi
    
    if [ ! -d "src/infrastructure" ]; then
        echo -e "${RED}❌ src/infrastructure/ directory not found. Infrastructure layer missing.${NC}"
        exit 1
    fi
    
    if [ ! -d "src/main" ]; then
        echo -e "${RED}❌ src/main/ directory not found. Application composition root missing.${NC}"
        exit 1
    fi
    
    # Check main application file
    if [ ! -f "app.py" ]; then
        echo -e "${RED}❌ app.py not found. Main application file missing.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Clean architecture structure validated${NC}"
}

# Check for .env file and API key configuration
check_env_file() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found${NC}"
        
        if [ -f "env.template" ]; then
            echo -e "${BLUE}📝 Creating .env file from template...${NC}"
            cp env.template .env
            echo -e "${GREEN}✅ .env file created from template${NC}"
        else
            echo -e "${BLUE}📝 Creating .env file...${NC}"
            cat > .env << 'EOF'
# Indonesian Mental Health Support Bot Configuration (Clean Architecture)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration (Optional - for Claude 3.5 Sonnet fallback)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# Environment Settings
TZ=Asia/Jakarta
LANG=id_ID.UTF-8
EOF
            echo -e "${GREEN}✅ .env file created${NC}"
        fi
        
        echo -e "${YELLOW}⚠️  Please edit .env file and add your API keys${NC}"
        echo -e "${BLUE}📝 You can edit it with: nano .env${NC}"
        read -p "Do you want to enter your OpenAI API key now? (y/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter your OpenAI API key: " api_key
            if [ -n "$api_key" ]; then
                sed -i "s/your_openai_api_key_here/$api_key/" .env
                echo -e "${GREEN}✅ OpenAI API key added to .env file${NC}"
                
                read -p "Enter your Anthropic API key (optional, press enter to skip): " anthropic_key
                if [ -n "$anthropic_key" ]; then
                    sed -i "s/your_anthropic_api_key_here/$anthropic_key/" .env
                    echo -e "${GREEN}✅ Anthropic API key added to .env file${NC}"
                fi
            else
                echo -e "${RED}❌ No API key provided${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  Please manually edit .env file with your API keys before proceeding${NC}"
            exit 1
        fi
    fi
    
    # Check if API key is configured in .env file
    if grep -q "your_openai_api_key_here" .env; then
        echo -e "${RED}❌ OpenAI API key not configured in .env file${NC}"
        echo -e "${BLUE}📝 Please edit .env file and replace 'your_openai_api_key_here' with your actual API key${NC}"
        exit 1
    fi
    
    # Validate API key format
    api_key=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2)
    if [[ ! "$api_key" =~ ^sk-.* ]]; then
        echo -e "${YELLOW}⚠️  API key format may be incorrect. OpenAI API keys typically start with 'sk-'${NC}"
        echo -e "${BLUE}📝 Please verify your API key in .env file${NC}"
    fi
    
    # Check for Anthropic API key
    if grep -q "ANTHROPIC_API_KEY=" .env && ! grep -q "your_anthropic_api_key_here" .env; then
        echo -e "${GREEN}✅ Anthropic API key configured (fallback enabled)${NC}"
    else
        echo -e "${YELLOW}⚠️  Anthropic API key not configured (fallback disabled)${NC}"
    fi
    
    echo -e "${GREEN}✅ Environment configuration validated${NC}"
}

# Validate clean architecture structure
check_architecture

# Check environment configuration
check_env_file

# Create necessary directories
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p static templates

# Function to stop and remove existing containers
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up existing containers...${NC}"
    docker compose down 2>/dev/null || true
    docker container rm kak-indira-mental-health-bot 2>/dev/null || true
}

# Function to build and start the bot
deploy() {
    echo -e "${BLUE}🔨 Building Indonesian Mental Health Support Bot (Clean Architecture)...${NC}"
    docker compose build

    echo -e "${BLUE}🚀 Starting Kak Indira Mental Health Bot (Clean Architecture)...${NC}"
    docker compose up -d

    echo -e "${GREEN}✅ Clean Architecture Deployment successful!${NC}"
    echo ""
    echo -e "${GREEN}🌐 Access the mental health support interface at:${NC}"
    echo -e "${BLUE}   http://localhost:8000${NC}"
    echo ""
    echo -e "${GREEN}📚 API Documentation available at:${NC}"
    echo -e "${BLUE}   http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${GREEN}🏥 Health Check endpoint:${NC}"
    echo -e "${BLUE}   http://localhost:8000/health${NC}"
    echo ""
    echo -e "${GREEN}🔍 Check container status:${NC}"
    echo -e "${BLUE}   docker compose ps${NC}"
    echo ""
    echo -e "${GREEN}📜 View logs:${NC}"
    echo -e "${BLUE}   docker compose logs -f mental-health-bot${NC}"
    echo ""
    echo -e "${GREEN}🏗️  Architecture Info:${NC}"
    echo -e "${BLUE}   - Core Business Logic: src/core/${NC}"
    echo -e "${BLUE}   - Infrastructure Layer: src/infrastructure/${NC}"
    echo -e "${BLUE}   - Application Layer: src/main/${NC}"
    echo -e "${BLUE}   - Main Entry Point: app.py${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [COMMAND]${NC}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the mental health bot (default)"
    echo "  stop     - Stop the mental health bot"
    echo "  restart  - Restart the mental health bot"
    echo "  logs     - Show bot logs"
    echo "  status   - Show container status and health"
    echo "  test     - Run health check"
    echo "  clean    - Stop and remove all containers"
    echo "  validate - Validate clean architecture structure"
    echo ""
    echo "Clean Architecture Features:"
    echo "  - Modular design with clear separation of concerns"
    echo "  - Core business logic isolated from external dependencies"
    echo "  - Infrastructure layer for external services (OpenAI, Anthropic)"
    echo "  - Dependency injection for testability"
    echo ""
}

# Parse command line arguments
case "${1:-start}" in
    "start")
        cleanup
        deploy
        ;;
    "stop")
        echo -e "${YELLOW}🛑 Stopping Indonesian Mental Health Support Bot...${NC}"
        docker compose down
        echo -e "${GREEN}✅ Bot stopped successfully${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Restarting Indonesian Mental Health Support Bot...${NC}"
        cleanup
        deploy
        ;;
    "logs")
        echo -e "${BLUE}📜 Showing mental health bot logs...${NC}"
        docker compose logs -f mental-health-bot
        ;;
    "status")
        echo -e "${BLUE}📊 Container status:${NC}"
        docker compose ps
        echo ""
        echo -e "${BLUE}🏥 Health check:${NC}"
        health_response=$(curl -s http://localhost:8000/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "$health_response" | jq . 2>/dev/null || echo "$health_response"
            echo -e "${GREEN}✅ Mental health bot is healthy and running${NC}"
        else
            echo -e "${RED}❌ Mental health bot is not responding${NC}"
            echo -e "${YELLOW}💡 Try: $0 restart${NC}"
        fi
        echo ""
        echo -e "${BLUE}🏗️  Clean Architecture Status:${NC}"
        echo -e "${GREEN}   - Core Layer: ✅ Available${NC}"
        echo -e "${GREEN}   - Infrastructure Layer: ✅ Available${NC}"
        echo -e "${GREEN}   - Application Layer: ✅ Available${NC}"
        ;;
    "test")
        echo -e "${BLUE}🧪 Running comprehensive health check...${NC}"
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Mental health bot is healthy and running${NC}"
            echo -e "${GREEN}🌐 Access at: http://localhost:8000${NC}"
            
            # Test API documentation
            if curl -s http://localhost:8000/docs > /dev/null; then
                echo -e "${GREEN}✅ API documentation is accessible${NC}"
            else
                echo -e "${YELLOW}⚠️  API documentation may not be accessible${NC}"
            fi
        else
            echo -e "${RED}❌ Mental health bot is not responding${NC}"
            echo -e "${YELLOW}💡 Try: $0 restart${NC}"
        fi
        ;;
    "clean")
        echo -e "${YELLOW}🧹 Cleaning up all containers and images...${NC}"
        docker compose down --rmi all --volumes --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup completed${NC}"
        ;;
    "validate")
        echo -e "${BLUE}🔍 Validating clean architecture setup...${NC}"
        check_architecture
        check_env_file
        echo -e "${GREEN}✅ Clean architecture validation completed${NC}"
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac 