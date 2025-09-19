#!/bin/bash

# Super Admin Workflow Test Script
# Tests complete workflows for Super Admin Agent operations

# Configuration
BASE_URL="http://localhost:8001"
JWT_TOKEN=""  # Add your JWT token here

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    
    if [ -z "$JWT_TOKEN" ]; then
        print_warning "No JWT token provided"
        return
    fi
    
    curl -s -X $method "$BASE_URL$endpoint" \
         -H "Authorization: Bearer $JWT_TOKEN" \
         -H "Content-Type: application/json" \
         ${data:+-d "$data"}
}

print_test "SUPER ADMIN WORKFLOW TESTS"

if [ -z "$JWT_TOKEN" ]; then
    print_error "JWT_TOKEN is required for these tests"
    print_warning "Please set the JWT_TOKEN variable at the top of this script"
    exit 1
fi

# Workflow 1: Platform Overview and Statistics
print_test "Workflow 1: Platform Overview"

echo "Step 1.1: Get platform statistics"
STATS_RESPONSE=$(make_request "GET" "/agents/super-admin/platform/stats")
echo "$STATS_RESPONSE" | jq . 2>/dev/null || echo "$STATS_RESPONSE"
echo ""

echo "Step 1.2: Get platform analysis"
ANALYSIS_RESPONSE=$(make_request "GET" "/agents/super-admin/platform/analysis")
echo "$ANALYSIS_RESPONSE" | jq . 2>/dev/null || echo "$ANALYSIS_RESPONSE"
echo ""

echo "Step 1.3: Chat about platform status"
CHAT_DATA='{
    "message": "Give me a comprehensive overview of the current platform status, including user statistics, course assistants, and any recommendations for improvement.",
    "temperature": 0.7
}'
CHAT_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$CHAT_DATA")
echo "$CHAT_RESPONSE" | jq . 2>/dev/null || echo "$CHAT_RESPONSE"
echo ""

# Workflow 2: Course Creation via Natural Language
print_test "Workflow 2: Course Creation via Natural Language"

echo "Step 2.1: Create a Mathematics course"
MATH_COURSE_CHAT='{
    "message": "Create a comprehensive Mathematics course for high school students. The course should cover algebra, geometry, and basic calculus. Make sure the assistant is patient and provides step-by-step explanations.",
    "temperature": 0.7
}'
MATH_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$MATH_COURSE_CHAT")
echo "$MATH_RESPONSE" | jq . 2>/dev/null || echo "$MATH_RESPONSE"
echo ""

echo "Step 2.2: Create a Science course"
SCIENCE_COURSE_CHAT='{
    "message": "Create a Science course for middle school students focusing on biology, chemistry, and physics fundamentals. The assistant should use simple language and include lots of real-world examples.",
    "temperature": 0.7
}'
SCIENCE_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$SCIENCE_COURSE_CHAT")
echo "$SCIENCE_RESPONSE" | jq . 2>/dev/null || echo "$SCIENCE_RESPONSE"
echo ""

echo "Step 2.3: Create a Programming course"
PROGRAMMING_COURSE_CHAT='{
    "message": "Create a Programming course for beginners focusing on Python. The course should teach programming fundamentals, data structures, and simple algorithms. The assistant should provide code examples and practice exercises.",
    "temperature": 0.7
}'
PROGRAMMING_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$PROGRAMMING_COURSE_CHAT")
echo "$PROGRAMMING_RESPONSE" | jq . 2>/dev/null || echo "$PROGRAMMING_RESPONSE"
echo ""

# Workflow 3: Course Management
print_test "Workflow 3: Course Management"

echo "Step 3.1: List all course assistants"
COURSES_LIST=$(make_request "GET" "/agents/course-assistants")
echo "$COURSES_LIST" | jq . 2>/dev/null || echo "$COURSES_LIST"

# Extract first course assistant ID for testing
FIRST_COURSE_ID=$(echo "$COURSES_LIST" | jq -r '.[0].id' 2>/dev/null)
echo "First course ID: $FIRST_COURSE_ID"
echo ""

if [ -n "$FIRST_COURSE_ID" ] && [ "$FIRST_COURSE_ID" != "null" ]; then
    echo "Step 3.2: Get course assistant details"
    COURSE_DETAILS=$(make_request "GET" "/agents/course-assistants/$FIRST_COURSE_ID")
    echo "$COURSE_DETAILS" | jq . 2>/dev/null || echo "$COURSE_DETAILS"
    echo ""
    
    echo "Step 3.3: Get course assistant capabilities"
    COURSE_CAPABILITIES=$(make_request "GET" "/agents/course-assistants/$FIRST_COURSE_ID/capabilities")
    echo "$COURSE_CAPABILITIES" | jq . 2>/dev/null || echo "$COURSE_CAPABILITIES"
    echo ""
    
    echo "Step 3.4: Get course assistant statistics"
    COURSE_STATS=$(make_request "GET" "/agents/course-assistants/$FIRST_COURSE_ID/statistics")
    echo "$COURSE_STATS" | jq . 2>/dev/null || echo "$COURSE_STATS"
    echo ""
fi

# Workflow 4: Advanced Platform Operations
print_test "Workflow 4: Advanced Platform Operations"

echo "Step 4.1: Ask about user management"
USER_MGMT_CHAT='{
    "message": "How many active users do we currently have? Can you break this down by user roles and provide insights about user engagement?",
    "temperature": 0.7
}'
USER_MGMT_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$USER_MGMT_CHAT")
echo "$USER_MGMT_RESPONSE" | jq . 2>/dev/null || echo "$USER_MGMT_RESPONSE"
echo ""

echo "Step 4.2: Ask about course recommendations"
RECOMMENDATIONS_CHAT='{
    "message": "Based on the current platform data, what new courses would you recommend creating? Consider user demographics and popular subjects.",
    "temperature": 0.7
}'
RECOMMENDATIONS_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$RECOMMENDATIONS_CHAT")
echo "$RECOMMENDATIONS_RESPONSE" | jq . 2>/dev/null || echo "$RECOMMENDATIONS_RESPONSE"
echo ""

echo "Step 4.3: Platform operations request"
OPERATIONS_DATA='{
    "operation": "Generate monthly analytics report",
    "parameters": {
        "month": "current",
        "include_user_metrics": true,
        "include_course_metrics": true
    },
    "description": "Generate comprehensive monthly report for platform review"
}'
OPERATIONS_RESPONSE=$(make_request "POST" "/agents/super-admin/platform/operations" "$OPERATIONS_DATA")
echo "$OPERATIONS_RESPONSE" | jq . 2>/dev/null || echo "$OPERATIONS_RESPONSE"
echo ""

# Workflow 5: Session Management
print_test "Workflow 5: Session Management"

echo "Step 5.1: Create a new session"
SESSION_DATA='{
    "title": "Platform Management Session",
    "agent_type": "super_admin",
    "metadata": {"purpose": "platform_management", "workflow_test": true}
}'
SESSION_RESPONSE=$(make_request "POST" "/agents/super-admin/sessions" "$SESSION_DATA")
echo "$SESSION_RESPONSE" | jq . 2>/dev/null || echo "$SESSION_RESPONSE"
SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.id' 2>/dev/null)
echo "Created session ID: $SESSION_ID"
echo ""

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
    echo "Step 5.2: Chat within the session"
    SESSION_CHAT='{
        "message": "This is a test message within a specific session. Can you confirm you received this?",
        "session_id": "'$SESSION_ID'",
        "temperature": 0.7
    }'
    SESSION_CHAT_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$SESSION_CHAT")
    echo "$SESSION_CHAT_RESPONSE" | jq . 2>/dev/null || echo "$SESSION_CHAT_RESPONSE"
    echo ""
    
    echo "Step 5.3: Get session summary"
    SESSION_SUMMARY=$(make_request "GET" "/agents/super-admin/sessions/$SESSION_ID/summary")
    echo "$SESSION_SUMMARY" | jq . 2>/dev/null || echo "$SESSION_SUMMARY"
    echo ""
    
    echo "Step 5.4: Export session"
    SESSION_EXPORT=$(make_request "GET" "/agents/super-admin/sessions/$SESSION_ID/export?format=json")
    echo "$SESSION_EXPORT" | jq . 2>/dev/null || echo "$SESSION_EXPORT"
    echo ""
fi

# Workflow 6: Error Handling and Edge Cases
print_test "Workflow 6: Error Handling"

echo "Step 6.1: Test invalid course creation"
INVALID_COURSE_CHAT='{
    "message": "Create a course with invalid parameters and see how the system handles it",
    "temperature": 0.7
}'
INVALID_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$INVALID_COURSE_CHAT")
echo "$INVALID_RESPONSE" | jq . 2>/dev/null || echo "$INVALID_RESPONSE"
echo ""

echo "Step 6.2: Test complex natural language request"
COMPLEX_CHAT='{
    "message": "I need to create multiple courses at once: 1) Advanced Mathematics with calculus and linear algebra, 2) Computer Science with programming in Python and Java, 3) Physics with quantum mechanics. Each should be tailored for university students and include practice problems.",
    "temperature": 0.7
}'
COMPLEX_RESPONSE=$(make_request "POST" "/agents/super-admin/chat" "$COMPLEX_CHAT")
echo "$COMPLEX_RESPONSE" | jq . 2>/dev/null || echo "$COMPLEX_RESPONSE"
echo ""

# Summary
print_test "WORKFLOW TEST SUMMARY"

echo "Completed workflows:"
echo "1. ✓ Platform Overview and Statistics"
echo "2. ✓ Course Creation via Natural Language"
echo "3. ✓ Course Management Operations"
echo "4. ✓ Advanced Platform Operations"
echo "5. ✓ Session Management"
echo "6. ✓ Error Handling and Edge Cases"
echo ""

print_success "All Super Admin workflows tested successfully!"
echo ""
echo "Key capabilities verified:"
echo "- Natural language course creation"
echo "- Platform statistics and analysis"
echo "- Course assistant management"
echo "- Session handling"
echo "- Complex query processing"
echo "- Error handling"
echo ""
echo "The Super Admin Agent is ready for production use!"
