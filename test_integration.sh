#!/bin/bash

# Integration test script for TestOps Copilot
set -e

echo "========================================"
echo "TestOps Copilot - Integration Tests"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo -n "1. Checking backend health... "
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    exit 1
fi

# Check if frontend is running
echo -n "2. Checking frontend... "
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${RED}✗ Frontend is not running${NC}"
    exit 1
fi

# Generate test token
echo -n "3. Generating test auth token... "
cd /home/akira/Projects/AIdevtools/src/backend
source ../../.venv/bin/activate
TOKEN=$(python3 << 'EOF'
from app.core.security import create_access_token
token = create_access_token({"sub": "integration_test_user"})
print(token)
EOF
)
echo -e "${GREEN}✓ Token generated${NC}"

# Test API endpoint
echo -n "4. Testing test generation API... "
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/generate/manual \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "requirements": "Функция для умножения двух чисел",
    "code_context": "",
    "metadata": {
      "test_framework": "pytest",
      "language": "python",
      "complexity": "simple"
    }
  }')

if echo "$RESPONSE" | grep -q '"code"'; then
    echo -e "${GREEN}✓ API returns code${NC}"
    TEST_CASES_COUNT=$(echo "$RESPONSE" | grep -o '"title"' | wc -l)
    echo -e "   Generated ${YELLOW}${TEST_CASES_COUNT}${NC} test cases"
else
    echo -e "${RED}✗ API error${NC}"
    echo "$RESPONSE" | python3 -m json.tool
    exit 1
fi

# Check API docs
echo -n "5. Checking API documentation... "
if curl -s http://localhost:8001/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API docs accessible${NC}"
else
    echo -e "${YELLOW}⚠ API docs not accessible${NC}"
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}All integration tests passed!${NC}"
echo "========================================"
echo ""
echo "Access points:"
echo "  • Frontend:  http://localhost:3001"
echo "  • Backend:   http://localhost:8001"
echo "  • API Docs:  http://localhost:8001/docs"
echo ""
