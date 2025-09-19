#!/bin/bash

# Super Admin Agent API Test Scripts
# This script tests all the agent APIs using curl

# Configuration
BASE_URL="http://localhost:8001"
JWT_TOKEN=""  # Add your JWT token here

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_test() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to make API calls
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local content_type=${4:-"application/json"}
    
    if [ -z "$JWT_TOKEN" ]; then
        print_warning "No JWT token provided. Some tests may fail."
        curl -s -X $method "$BASE_URL$endpoint" \
             -H "Content-Type: $content_type" \
             ${data:+-d "$data"}
    else
        curl -s -X $method "$BASE_URL$endpoint" \
             -H "Authorization: Bearer $JWT_TOKEN" \
             -H "Content-Type: $content_type" \
             ${data:+-d "$data"}
    fi
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=${5:-200}
    
    print_test "$name"
    echo "Request: $method $BASE_URL$endpoint"
    
    if [ -n "$data" ]; then
        echo "Data: $data"
    fi
    
    response=$(make_request $method $endpoint "$data")
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$BASE_URL$endpoint" \
                  ${JWT_TOKEN:+-H "Authorization: Bearer $JWT_TOKEN"} \
                  -H "Content-Type: application/json" \
                  ${data:+-d "$data"})
    
    echo "Response Code: $status_code"
    echo "Response: $response" | jq . 2>/dev/null || echo "$response"
    
    if [ "$status_code" -eq "$expected_status" ]; then
        print_success "Test passed"
    else
        print_error "Test failed - Expected: $expected_status, Got: $status_code"
    fi
    
    echo ""
}

# Check if server is running
print_test "Checking if server is running"
if curl -s "$BASE_URL/" > /dev/null; then
    print_success "Server is running"
else
    print_error "Server is not running. Please start the server with: python -m uvicorn agents.main:app --reload --port 8001"
    exit 1
fi

echo ""

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/health"

# Test 2: System Info
test_endpoint "System Info" "GET" "/info"

# Test 3: Root Endpoint
test_endpoint "Root Endpoint" "GET" "/"

# ===== SUPER ADMIN AGENT TESTS =====

print_test "SUPER ADMIN AGENT TESTS"

# Test 4: Get Super Admin Agent Status
test_endpoint "Super Admin Agent Status" "GET" "/agents/super-admin/status"

# Test 5: Get Super Admin Capabilities
test_endpoint "Super Admin Capabilities" "GET" "/agents/super-admin/capabilities"

# Test 6: Get Platform Stats
test_endpoint "Platform Statistics" "GET" "/agents/super-admin/platform/stats"

# Test 7: Get Platform Analysis
test_endpoint "Platform Analysis" "GET" "/agents/super-admin/platform/analysis"

# Test 8: Create Super Admin Session
SESSION_DATA='{
    "title": "Test Super Admin Session",
    "agent_type": "super_admin",
    "metadata": {"test": true}
}'
test_endpoint "Create Super Admin Session" "POST" "/agents/super-admin/sessions" "$SESSION_DATA"

# Test 9: Chat with Super Admin Agent
CHAT_DATA='{
    "message": "Hello, can you help me understand the platform statistics?",
    "temperature": 0.7,
    "metadata": {"test_chat": true}
}'
test_endpoint "Chat with Super Admin" "POST" "/agents/super-admin/chat" "$CHAT_DATA"

# Test 10: Create Course Assistant via Chat
COURSE_CHAT='{
    "message": "Create a Calculus course for college students. The course should focus on differential and integral calculus with practical applications.",
    "temperature": 0.7
}'
test_endpoint "Create Course via Chat" "POST" "/agents/super-admin/chat" "$COURSE_CHAT"

# ===== COURSE ASSISTANT TESTS =====

print_test "COURSE ASSISTANT TESTS"

# Test 11: Create Course Assistant Directly
COURSE_ASSISTANT_DATA='{
    "name": "Advanced Physics",
    "subject": "Physics",
    "description": "Advanced physics course covering quantum mechanics and relativity",
    "role_instructions": "You are an expert physics instructor. Help students understand complex physics concepts through clear explanations and practical examples.",
    "constraints": "Focus on undergraduate level physics. Use SI units consistently.",
    "temperature": 0.7,
    "metadata": {"level": "advanced", "target_audience": "undergraduate"}
}'
test_endpoint "Create Course Assistant" "POST" "/agents/course-assistants" "$COURSE_ASSISTANT_DATA"

# Test 12: List Course Assistants
test_endpoint "List Course Assistants" "GET" "/agents/course-assistants"

# Test 13: Get Course Assistant Capabilities
test_endpoint "Course Assistant Capabilities" "GET" "/agents/course-assistants/[ASSISTANT_ID]/capabilities" "" 404

# ===== CHAT & SESSION TESTS =====

print_test "CHAT & SESSION TESTS"

# Test 14: List Chat Sessions
test_endpoint "List Chat Sessions" "GET" "/agents/chat/sessions"

# Test 15: Create Chat Session
CHAT_SESSION_DATA='{
    "title": "Test Chat Session",
    "agent_type": "super_admin",
    "metadata": {"test": true}
}'
test_endpoint "Create Chat Session" "POST" "/agents/chat/sessions" "$CHAT_SESSION_DATA"

# Test 16: Universal Chat (Super Admin)
UNIVERSAL_CHAT_DATA='{
    "message": "What are the current platform statistics?",
    "temperature": 0.7
}'
test_endpoint "Universal Chat - Super Admin" "POST" "/agents/chat/universal?agent_type=super_admin" "$UNIVERSAL_CHAT_DATA"

# ===== FILE MANAGEMENT TESTS =====

print_test "FILE MANAGEMENT TESTS"

# Test 17: List Files
test_endpoint "List Files" "GET" "/agents/files"

# Test 18: Get File Statistics
test_endpoint "File Statistics" "GET" "/agents/files/statistics/user"

# Test 19: File Health Check
test_endpoint "File Health Check" "GET" "/agents/files/health"

# Test 20: Chat Health Check
test_endpoint "Chat Health Check" "GET" "/agents/chat/health"

# ===== ERROR HANDLING TESTS =====

print_test "ERROR HANDLING TESTS"

# Test 21: Invalid Endpoint
test_endpoint "Invalid Endpoint" "GET" "/agents/invalid" "" 404

# Test 22: Invalid Course Assistant ID
test_endpoint "Invalid Course Assistant" "GET" "/agents/course-assistants/invalid-id" "" 404

# Test 23: Invalid Session ID
test_endpoint "Invalid Session" "GET" "/agents/chat/sessions/invalid-id" "" 404

# ===== AUTHENTICATION TESTS =====

print_test "AUTHENTICATION TESTS"

# Test without JWT token
OLD_TOKEN=$JWT_TOKEN
JWT_TOKEN=""

# Test 24: Unauthorized Access
test_endpoint "Unauthorized Super Admin" "GET" "/agents/super-admin/status" "" 401

# Test 25: Unauthorized Course Creation
test_endpoint "Unauthorized Course Creation" "POST" "/agents/course-assistants" "$COURSE_ASSISTANT_DATA" 401

# Restore token
JWT_TOKEN=$OLD_TOKEN

# ===== PERFORMANCE TESTS =====

print_test "PERFORMANCE TESTS"

# Test 26: Multiple Concurrent Requests
print_test "Concurrent Health Checks"
for i in {1..5}; do
    make_request "GET" "/health" &
done
wait
print_success "Concurrent requests completed"

# ===== INTEGRATION TESTS =====

print_test "INTEGRATION TESTS"

# Test 27: Complete Course Creation Workflow
print_test "Complete Course Creation Workflow"

# Step 1: Create session
SESSION_RESPONSE=$(make_request "POST" "/agents/super-admin/sessions" "$SESSION_DATA")
echo "1. Session created: $SESSION_RESPONSE"

# Step 2: Chat to create course
COURSE_CREATION_CHAT='{
    "message": "Create a Mathematics course for high school students focusing on algebra and geometry.",
    "temperature": 0.7
}'
CHAT_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$COURSE_CREATION_CHAT")
echo "2. Course creation chat: $CHAT_RESPONSE"

# Step 3: List courses
COURSES_RESPONSE=$(make_request "GET" "/agents/course-assistants")
echo "3. Available courses: $COURSES_RESPONSE"

print_success "Integration test completed"

# ===== SUMMARY =====

print_test "TEST SUMMARY"

if [ -z "$JWT_TOKEN" ]; then
    print_warning "Tests completed without JWT authentication"
    print_warning "To test authenticated endpoints, add your JWT token to the JWT_TOKEN variable"
else
    print_success "Tests completed with JWT authentication"
fi

print_success "All API tests finished!"
print_test "Next Steps:"
echo "1. Review the responses above for any errors"
echo "2. Test file upload functionality with actual files"
echo "3. Test WebSocket connections"
echo "4. Test streaming endpoints"
echo ""
echo "Documentation available at: $BASE_URL/docs"
echo "Alternative docs at: $BASE_URL/redoc"
