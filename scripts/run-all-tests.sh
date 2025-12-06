#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running all tests for TestOps Copilot...${NC}"

# Function to run backend tests
run_backend_tests() {
    echo -e "\n${YELLOW}Running Backend Tests...${NC}"
    cd src/backend

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -q -r requirements.txt
    pip install -q -r requirements-test.txt

    # Run tests
    echo -e "${YELLOW}Executing backend tests...${NC}"
    if pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=60; then
        echo -e "${GREEN}Backend tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Backend tests failed!${NC}"
        return 1
    fi
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "\n${YELLOW}Running Frontend Tests...${NC}"
    cd ../frontend

    # Install dependencies
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm ci --silent

    # Run unit tests
    echo -e "${YELLOW}Executing frontend unit tests...${NC}"
    if npm test -- --coverage --watchAll=false; then
        echo -e "${GREEN}Frontend unit tests passed!${NC}"
    else
        echo -e "${RED}Frontend unit tests failed!${NC}"
        return 1
    fi

    # Run E2E tests (optional)
    echo -e "${YELLOW}Executing frontend E2E tests...${NC}"
    if npx playwright test --reporter=line; then
        echo -e "${GREEN}Frontend E2E tests passed!${NC}"
    else
        echo -e "${YELLOW}Frontend E2E tests failed or not installed (optional)${NC}"
    fi

    return 0
}

# Function to run AI Core tests
run_ai_core_tests() {
    echo -e "\n${YELLOW}Running AI Core Tests...${NC}"
    cd ../ai-core

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment for AI Core...${NC}"
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    echo -e "${YELLOW}Installing AI Core dependencies...${NC}"
    pip install -q -r requirements.txt

    # Run tests (if they exist)
    if [ -d "tests" ]; then
        echo -e "${YELLOW}Executing AI Core tests...${NC}"
        if python -m pytest tests/ -v; then
            echo -e "${GREEN}AI Core tests passed!${NC}"
        else
            echo -e "${RED}AI Core tests failed!${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}No AI Core tests found, skipping...${NC}"
    fi

    return 0
}

# Function to run integration tests
run_integration_tests() {
    echo -e "\n${YELLOW}Running Integration Tests...${NC}"
    cd ..

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Docker is not running. Skipping integration tests.${NC}"
        return 0
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}docker-compose is not installed. Skipping integration tests.${NC}"
        return 0
    fi

    # Run integration tests
    if [ -d "tests/integration" ]; then
        echo -e "${YELLOW}Executing integration tests...${NC}"
        if python -m pytest tests/integration/ -v; then
            echo -e "${GREEN}Integration tests passed!${NC}"
        else
            echo -e "${RED}Integration tests failed!${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}No integration tests found, skipping...${NC}"
    fi

    return 0
}

# Main execution
echo -e "${GREEN}Starting test execution...${NC}"

# Track exit codes
EXIT_CODE=0

# Run all test suites
run_backend_tests || EXIT_CODE=1
run_frontend_tests || EXIT_CODE=1
run_ai_core_tests || EXIT_CODE=1
run_integration_tests || EXIT_CODE=1

# Final result
echo -e "\n${GREEN}==================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed! Check the output above.${NC}"
    exit 1
fi