#!/bin/bash

# Indonesian Mental Health Support Bot - Docker Setup Validation
# Quick check to ensure everything is ready for deployment

echo "🧠 Indonesian Mental Health Support Bot - Docker Setup Check"
echo "💚 Validating deployment requirements..."
echo "============================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check and report
check_requirement() {
    local name="$1"
    local command="$2"
    
    echo -n "Checking $name... "
    
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ MISSING${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Check Docker
check_requirement "Docker" "docker --version"

# Check Docker Compose
if ! check_requirement "Docker Compose (v2)" "docker compose version"; then
    check_requirement "Docker Compose (v1)" "docker compose --version"
fi

# Check if ports are available
echo -n "Checking port 8000 availability... "
if netstat -ln 2>/dev/null | grep -q ":8000 "; then
    echo -e "${YELLOW}⚠️  PORT IN USE${NC}"
    echo -e "${BLUE}   💡 Port 8000 is being used. You may need to stop other services.${NC}"
    ((CHECKS_FAILED++))
else
    echo -e "${GREEN}✅ AVAILABLE${NC}"
    ((CHECKS_PASSED++))
fi

# Check .env file and OpenAI API Key configuration
echo -n "Checking .env file... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ EXISTS${NC}"
    ((CHECKS_PASSED++))
    
    # Check if API key is configured in .env file
    echo -n "Checking OpenAI API Key in .env... "
    if grep -q "^OPENAI_API_KEY=" .env; then
        api_key=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2)
        
        if [ "$api_key" = "your_openai_api_key_here" ]; then
            echo -e "${RED}❌ NOT CONFIGURED${NC}"
            echo -e "${BLUE}   💡 Please edit .env file and replace 'your_openai_api_key_here' with your actual API key${NC}"
            ((CHECKS_FAILED++))
        elif [[ "$api_key" == sk-* ]]; then
            echo -e "${GREEN}✅ CONFIGURED${NC}"
            ((CHECKS_PASSED++))
        else
            echo -e "${YELLOW}⚠️  FORMAT ISSUE${NC}"
            echo -e "${BLUE}   💡 API key should start with 'sk-'${NC}"
            ((CHECKS_FAILED++))
        fi
    else
        echo -e "${RED}❌ NOT FOUND${NC}"
        echo -e "${BLUE}   💡 Add 'OPENAI_API_KEY=your-key-here' to .env file${NC}"
        ((CHECKS_FAILED++))
    fi
else
    echo -e "${RED}❌ MISSING${NC}"
    echo -e "${BLUE}   💡 Create .env file with: cp env.template .env${NC}"
    ((CHECKS_FAILED++))
    
    # Check if template exists
    echo -n "Checking env.template... "
    if [ -f "env.template" ]; then
        echo -e "${GREEN}✅ AVAILABLE${NC}"
        echo -e "${BLUE}   💡 You can create .env with: cp env.template .env${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  TEMPLATE MISSING${NC}"
        echo -e "${BLUE}   💡 Create .env file manually with your OpenAI API key${NC}"
        ((CHECKS_FAILED++))
    fi
fi

# Check required files
for file in "Dockerfile" "docker-compose.yml" "app.py" "infer.py" "requirements.txt" "env.template"; do
    check_requirement "File: $file" "test -f $file"
done

# Check directories
for dir in "templates" "static"; do
    check_requirement "Directory: $dir" "test -d $dir"
done

# Check if deploy script is executable
check_requirement "Deploy script permissions" "test -x deploy.sh"

echo ""
echo "============================================================"
echo -e "${GREEN}✅ Checks Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}❌ Checks Failed: $CHECKS_FAILED${NC}"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo -e "${GREEN}Your system is ready to deploy the Indonesian Mental Health Support Bot!${NC}"
    echo ""
    echo -e "${BLUE}To deploy now, run:${NC}"
    echo -e "${BLUE}   ./deploy.sh start${NC}"
    echo ""
    echo -e "${BLUE}If you need to configure your API key first:${NC}"
    echo -e "${BLUE}   1. Copy template: cp env.template .env${NC}"
    echo -e "${BLUE}   2. Edit .env file: nano .env${NC}"
    echo -e "${BLUE}   3. Add your API key, then run: ./deploy.sh start${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  SOME CHECKS FAILED${NC}"
    echo -e "${YELLOW}Please resolve the issues above before deploying.${NC}"
    echo ""
    echo -e "${BLUE}Common solutions:${NC}"
    echo -e "${BLUE}• Install Docker: https://docs.docker.com/get-docker/${NC}"
    echo -e "${BLUE}• Configure API key: cp env.template .env && nano .env${NC}"
    echo -e "${BLUE}• Stop services using port 8000${NC}"
    exit 1
fi 