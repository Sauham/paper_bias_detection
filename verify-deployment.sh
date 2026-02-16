#!/bin/bash

# Deployment Verification Script
# Usage: ./verify-deployment.sh <backend-url>

set -e

BACKEND_URL=${1:-"http://localhost:8000"}
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Verifying deployment at: $BACKEND_URL"
echo "----------------------------------------"

# Test 1: Health Check
echo -n "Testing health endpoint... "
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [ "$HEALTH_RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED (HTTP $HEALTH_RESPONSE)${NC}"
    exit 1
fi

# Test 2: API Response Format
echo -n "Testing health response format... "
HEALTH_DATA=$(curl -s "$BACKEND_URL/health")
if echo "$HEALTH_DATA" | grep -q "\"status\""; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED (Invalid response format)${NC}"
    echo "Response: $HEALTH_DATA"
    exit 1
fi

# Test 3: CORS Headers (if frontend URL provided)
if [ ! -z "$2" ]; then
    echo -n "Testing CORS headers... "
    CORS_RESPONSE=$(curl -s -I -H "Origin: $2" "$BACKEND_URL/health" | grep -i "access-control-allow-origin")
    if [ ! -z "$CORS_RESPONSE" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
    else
        echo -e "${YELLOW}⚠ WARNING (CORS headers not found)${NC}"
    fi
fi

# Test 4: Response Time
echo -n "Testing response time... "
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$BACKEND_URL/health")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
if (( $(echo "$RESPONSE_TIME < 2" | bc -l) )); then
    echo -e "${GREEN}✓ PASSED${NC} (${RESPONSE_TIME_MS}ms)"
else
    echo -e "${YELLOW}⚠ SLOW${NC} (${RESPONSE_TIME_MS}ms)"
fi

echo "----------------------------------------"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "1. Test PDF upload from frontend"
echo "2. Verify Gemini API integration"
echo "3. Check logs for any errors"
echo "4. Monitor performance metrics"
