#!/bin/bash

# Indonesian Mental Health Support Bot - Docker Deployment Script
# Kak Indira - Konselor Kesehatan Mental

set -e

echo "🧠 Indonesian Mental Health Support Bot - Docker Deployment"
echo "💚 Kak Indira - Konselor Kesehatan Mental"
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

# Check for .env file and OpenAI API key configuration
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
# Indonesian Mental Health Support Bot Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Optional settings
TZ=Asia/Jakarta
LANG=id_ID.UTF-8
EOF
            echo -e "${GREEN}✅ .env file created${NC}"
        fi
        
        echo -e "${YELLOW}⚠️  Please edit .env file and add your OpenAI API key${NC}"
        echo -e "${BLUE}📝 You can edit it with: nano .env${NC}"
        read -p "Do you want to enter your API key now? (y/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter your OpenAI API key: " api_key
            if [ -n "$api_key" ]; then
                sed -i "s/your_openai_api_key_here/$api_key/" .env
                echo -e "${GREEN}✅ API key added to .env file${NC}"
            else
                echo -e "${RED}❌ No API key provided${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  Please manually edit .env file with your API key before proceeding${NC}"
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
    
    echo -e "${GREEN}✅ .env file configured${NC}"
}

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
    echo -e "${BLUE}🔨 Building Indonesian Mental Health Support Bot...${NC}"
    docker compose build

    echo -e "${BLUE}🚀 Starting Kak Indira Mental Health Bot...${NC}"
    docker compose up -d

    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo -e "${GREEN}🌐 Access the mental health support interface at:${NC}"
    echo -e "${BLUE}   http://localhost:8000${NC}"
    echo ""
    echo -e "${GREEN}📚 API Documentation available at:${NC}"
    echo -e "${BLUE}   http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${GREEN}🔍 Check container status:${NC}"
    echo -e "${BLUE}   docker compose ps${NC}"
    echo ""
    echo -e "${GREEN}📜 View logs:${NC}"
    echo -e "${BLUE}   docker compose logs -f mental-health-bot${NC}"
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
    echo "  status   - Show container status"
    echo "  test     - Run health check"
    echo "  clean    - Stop and remove all containers"
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
        curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health || echo "Service not accessible"
        ;;
    "test")
        echo -e "${BLUE}🧪 Running health check...${NC}"
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Mental health bot is healthy and running${NC}"
            echo -e "${GREEN}🌐 Access at: http://localhost:8000${NC}"
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
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac 