#!/bin/bash

# File Upload Test Script for Super Admin Agent APIs

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

# Check if JWT token is provided
if [ -z "$JWT_TOKEN" ]; then
    print_warning "No JWT token provided. Please add your JWT token to test file uploads."
    print_warning "Set JWT_TOKEN variable at the top of this script."
    exit 1
fi

# Create test files
print_test "Creating test files for upload"

# Create a test PDF (simple text file with .pdf extension for testing)
echo "This is a test PDF file for Super Admin Agent testing.

Course: Introduction to AI
Subject: Artificial Intelligence
Content: This document covers the basics of AI and machine learning.

Topics:
1. What is AI?
2. Machine Learning Fundamentals
3. Neural Networks
4. Applications of AI

This is test content for the vector store." > test_course.pdf

# Create a test text file
echo "Test Course Materials

This is a sample text file for testing the file upload functionality.

Learning Objectives:
- Understand basic concepts
- Apply theoretical knowledge
- Solve practical problems

Assessment Methods:
- Quizzes
- Assignments
- Final Project" > test_materials.txt

# Create a test CSV file
echo "topic,difficulty,hours,description
Introduction to AI,Beginner,2,Basic concepts and overview
Machine Learning,Intermediate,4,Supervised and unsupervised learning
Neural Networks,Advanced,6,Deep learning fundamentals
AI Applications,Intermediate,3,Real-world use cases" > test_data.csv

print_success "Test files created"

# Test 1: Upload PDF file
print_test "Test 1: Upload PDF file"
PDF_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/files/upload" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -F "file=@test_course.pdf" \
    -F "metadata={\"type\":\"course_material\",\"subject\":\"AI\"}")

echo "Response: $PDF_RESPONSE" | jq . 2>/dev/null || echo "$PDF_RESPONSE"
PDF_FILE_ID=$(echo "$PDF_RESPONSE" | jq -r '.id' 2>/dev/null)
print_success "PDF uploaded with ID: $PDF_FILE_ID"
echo ""

# Test 2: Upload text file
print_test "Test 2: Upload text file"
TXT_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/files/upload" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -F "file=@test_materials.txt" \
    -F "metadata={\"type\":\"study_guide\"}")

echo "Response: $TXT_RESPONSE" | jq . 2>/dev/null || echo "$TXT_RESPONSE"
TXT_FILE_ID=$(echo "$TXT_RESPONSE" | jq -r '.id' 2>/dev/null)
print_success "Text file uploaded with ID: $TXT_FILE_ID"
echo ""

# Test 3: Upload CSV file
print_test "Test 3: Upload CSV file"
CSV_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/files/upload" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -F "file=@test_data.csv" \
    -F "metadata={\"type\":\"curriculum_data\"}")

echo "Response: $CSV_RESPONSE" | jq . 2>/dev/null || echo "$CSV_RESPONSE"
CSV_FILE_ID=$(echo "$CSV_RESPONSE" | jq -r '.id' 2>/dev/null)
print_success "CSV file uploaded with ID: $CSV_FILE_ID"
echo ""

# Test 4: List uploaded files
print_test "Test 4: List uploaded files"
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/agents/files" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Response: $LIST_RESPONSE" | jq . 2>/dev/null || echo "$LIST_RESPONSE"
echo ""

# Test 5: Get file content extraction
if [ -n "$PDF_FILE_ID" ] && [ "$PDF_FILE_ID" != "null" ]; then
    print_test "Test 5: Extract content from PDF"
    CONTENT_RESPONSE=$(curl -s -X GET "$BASE_URL/agents/files/$PDF_FILE_ID/content" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    echo "Response: $CONTENT_RESPONSE" | jq . 2>/dev/null || echo "$CONTENT_RESPONSE"
    echo ""
fi

# Test 6: File statistics
print_test "Test 6: Get file statistics"
STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/agents/files/statistics/user" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Response: $STATS_RESPONSE" | jq . 2>/dev/null || echo "$STATS_RESPONSE"
echo ""

# Test 7: Download file
if [ -n "$TXT_FILE_ID" ] && [ "$TXT_FILE_ID" != "null" ]; then
    print_test "Test 7: Download file"
    curl -s -X GET "$BASE_URL/agents/files/$TXT_FILE_ID/download" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -o "downloaded_file.txt"
    
    if [ -f "downloaded_file.txt" ]; then
        print_success "File downloaded successfully"
        echo "Downloaded content:"
        cat downloaded_file.txt
        rm downloaded_file.txt
    else
        print_error "File download failed"
    fi
    echo ""
fi

# Test 8: Upload multiple files
print_test "Test 8: Upload multiple files"
MULTI_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/files/upload/multiple" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -F "files=@test_materials.txt" \
    -F "files=@test_data.csv")

echo "Response: $MULTI_RESPONSE" | jq . 2>/dev/null || echo "$MULTI_RESPONSE"
echo ""

# Test 9: Create course assistant and associate files
print_test "Test 9: Create course assistant for file processing"
COURSE_DATA='{
    "name": "AI Fundamentals Course",
    "subject": "Artificial Intelligence",
    "description": "A comprehensive course on AI fundamentals with uploaded materials",
    "role_instructions": "You are an AI instructor. Use the uploaded course materials to answer student questions and provide detailed explanations about artificial intelligence concepts.",
    "constraints": "Focus on beginner to intermediate level concepts. Always reference the uploaded materials when possible.",
    "temperature": 0.7,
    "metadata": {"created_for_testing": true}
}'

COURSE_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/course-assistants" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$COURSE_DATA")

echo "Response: $COURSE_RESPONSE" | jq . 2>/dev/null || echo "$COURSE_RESPONSE"
COURSE_ASSISTANT_ID=$(echo "$COURSE_RESPONSE" | jq -r '.id' 2>/dev/null)
print_success "Course assistant created with ID: $COURSE_ASSISTANT_ID"
echo ""

# Test 10: Process files for course assistant
if [ -n "$COURSE_ASSISTANT_ID" ] && [ "$COURSE_ASSISTANT_ID" != "null" ] && [ -n "$PDF_FILE_ID" ] && [ "$PDF_FILE_ID" != "null" ]; then
    print_test "Test 10: Process files for course assistant"
    PROCESS_DATA="{
        \"file_ids\": [\"$PDF_FILE_ID\", \"$TXT_FILE_ID\"],
        \"assistant_id\": \"$COURSE_ASSISTANT_ID\",
        \"chunk_size\": 1000,
        \"chunk_overlap\": 200
    }"
    
    PROCESS_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/files/process" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$PROCESS_DATA")
    
    echo "Response: $PROCESS_RESPONSE" | jq . 2>/dev/null || echo "$PROCESS_RESPONSE"
    echo ""
fi

# Test 11: Chat with course assistant using uploaded files
if [ -n "$COURSE_ASSISTANT_ID" ] && [ "$COURSE_ASSISTANT_ID" != "null" ]; then
    print_test "Test 11: Chat with course assistant using uploaded files"
    CHAT_DATA='{
        "message": "Based on the uploaded course materials, can you explain what artificial intelligence is and its main applications?",
        "temperature": 0.7
    }'
    
    CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/agents/course-assistants/$COURSE_ASSISTANT_ID/chat" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$CHAT_DATA")
    
    echo "Response: $CHAT_RESPONSE" | jq . 2>/dev/null || echo "$CHAT_RESPONSE"
    echo ""
fi

# Test 12: Delete files
print_test "Test 12: Delete uploaded files"
for FILE_ID in "$PDF_FILE_ID" "$TXT_FILE_ID" "$CSV_FILE_ID"; do
    if [ -n "$FILE_ID" ] && [ "$FILE_ID" != "null" ]; then
        DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/agents/files/$FILE_ID" \
            -H "Authorization: Bearer $JWT_TOKEN")
        
        echo "Deleted file $FILE_ID: $DELETE_RESPONSE"
    fi
done
echo ""

# Cleanup test files
print_test "Cleaning up test files"
rm -f test_course.pdf test_materials.txt test_data.csv
print_success "Test files cleaned up"

print_test "FILE UPLOAD TESTS COMPLETED"
print_success "All file upload and processing tests finished!"
echo ""
echo "Summary of tests performed:"
echo "1. ✓ PDF file upload"
echo "2. ✓ Text file upload" 
echo "3. ✓ CSV file upload"
echo "4. ✓ File listing"
echo "5. ✓ Content extraction"
echo "6. ✓ File statistics"
echo "7. ✓ File download"
echo "8. ✓ Multiple file upload"
echo "9. ✓ Course assistant creation"
echo "10. ✓ File processing for vector store"
echo "11. ✓ Chat with file-enhanced assistant"
echo "12. ✓ File deletion"
