# Super Admin Agent System

A comprehensive AI agent system for educational platform management using OpenAI's Agent SDK.

## 🚀 Quick Start

1. **Run the setup script:**
   ```bash
   python agents/setup.py
   ```

2. **Start the server:**
   ```bash
   python agents/start_agent_server.py
   ```

3. **Test the APIs:**
   ```bash
   cd agents/tests
   ./test_apis.sh
   ```

4. **Access documentation:**
   - API Docs: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

## Architecture

```
agents/
├── main.py                 # FastAPI application entry point
├── config/
│   └── settings.py         # Configuration management
├── models/
│   ├── schemas.py          # Pydantic models for API payloads
│   └── database.py         # Database models and connections
├── services/
│   ├── super_admin_agent.py    # Core Super Admin Agent logic
│   ├── course_agent.py         # Course Assistant management
│   ├── chat_service.py         # Chat session management
│   ├── file_service.py         # File upload and processing
│   └── vector_store.py         # Vector embeddings and retrieval
├── api/
│   ├── __init__.py
│   ├── super_admin.py          # Super Admin Agent endpoints
│   ├── course_agents.py        # Course Assistant endpoints
│   ├── chat.py                 # Chat and messaging endpoints
│   └── files.py                # File upload endpoints
├── utils/
│   ├── auth.py                 # Authentication utilities
│   ├── openai_client.py        # OpenAI SDK wrapper
│   └── supabase_client.py      # Supabase integration
├── tests/
│   └── test_apis.sh            # Curl test scripts
└── requirements.txt            # Python dependencies
```

## Key Features

- **Super Admin Agent**: Orchestration agent for platform management
- **Course Assistant Creation**: Dynamic creation of subject-specific AI tutors
- **File Processing**: PDF, DOCX, PPT, CSV, image ingestion with vector storage
- **Chat Sessions**: Thread-based conversations with persistent history
- **Role-Based Security**: Integration with existing auth system
- **Vector Search**: Context-aware responses using uploaded documents

## API Endpoints

### Super Admin Agent
- `POST /agents/super-admin/chat` - Chat with Super Admin Agent
- `GET /agents/super-admin/sessions` - List chat sessions
- `POST /agents/super-admin/sessions` - Create new session
- `DELETE /agents/super-admin/sessions/{session_id}` - Delete session

### Course Assistants
- `POST /agents/course-assistants` - Create course assistant
- `GET /agents/course-assistants` - List course assistants
- `PUT /agents/course-assistants/{assistant_id}` - Update assistant
- `DELETE /agents/course-assistants/{assistant_id}` - Delete assistant
- `POST /agents/course-assistants/{assistant_id}/chat` - Chat with course assistant

### File Management
- `POST /agents/files/upload` - Upload files for vector ingestion
- `GET /agents/files` - List uploaded files
- `DELETE /agents/files/{file_id}` - Delete file

## Usage

1. Start the agent server: `python -m uvicorn agents.main:app --reload --port 8001`
2. Test with curl scripts in `tests/test_apis.sh`
3. Integrate with existing frontend via HTTP/WebSocket APIs

## Models

- **Text Model**: GPT-4o Mini for cost-effective responses
- **Voice Model**: Whisper v1 Base for audio transcription
- **Embeddings**: text-embedding-3-small for vector storage
