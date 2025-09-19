"""OpenAI client wrapper for agent operations."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from openai.types import FileObject
from openai.types.beta import Assistant, VectorStore, Thread
from openai.types.beta.threads import Message, Run

from ..config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIClientWrapper:
    """Wrapper for OpenAI client with agent-specific functionality."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
    
    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str = None,
        tools: List[Dict[str, Any]] = None,
        vector_store_ids: List[str] = None,
        metadata: Dict[str, str] = None
    ) -> Assistant:
        """Create a new assistant."""
        try:
            tools = tools or [{"type": "file_search"}]
            if vector_store_ids:
                tools.append({
                    "type": "file_search",
                    "file_search": {
                        "vector_store_ids": vector_store_ids
                    }
                })
            
            assistant = await self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model or settings.text_model,
                tools=tools,
                metadata=metadata or {}
            )
            
            logger.info(f"Created assistant: {assistant.id}")
            return assistant
            
        except Exception as e:
            logger.error(f"Error creating assistant: {str(e)}")
            raise
    
    async def update_assistant(
        self,
        assistant_id: str,
        name: str = None,
        instructions: str = None,
        model: str = None,
        tools: List[Dict[str, Any]] = None,
        vector_store_ids: List[str] = None,
        metadata: Dict[str, str] = None
    ) -> Assistant:
        """Update an existing assistant."""
        try:
            update_data = {}
            
            if name is not None:
                update_data["name"] = name
            if instructions is not None:
                update_data["instructions"] = instructions
            if model is not None:
                update_data["model"] = model
            if metadata is not None:
                update_data["metadata"] = metadata
            
            if tools is not None or vector_store_ids is not None:
                tools = tools or [{"type": "file_search"}]
                if vector_store_ids:
                    tools.append({
                        "type": "file_search",
                        "file_search": {
                            "vector_store_ids": vector_store_ids
                        }
                    })
                update_data["tools"] = tools
            
            assistant = await self.client.beta.assistants.update(
                assistant_id=assistant_id,
                **update_data
            )
            
            logger.info(f"Updated assistant: {assistant_id}")
            return assistant
            
        except Exception as e:
            logger.error(f"Error updating assistant {assistant_id}: {str(e)}")
            raise
    
    async def delete_assistant(self, assistant_id: str) -> bool:
        """Delete an assistant."""
        try:
            await self.client.beta.assistants.delete(assistant_id)
            logger.info(f"Deleted assistant: {assistant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting assistant {assistant_id}: {str(e)}")
            raise
    
    async def get_assistant(self, assistant_id: str) -> Assistant:
        """Get assistant details."""
        try:
            assistant = await self.client.beta.assistants.retrieve(assistant_id)
            return assistant
            
        except Exception as e:
            logger.error(f"Error retrieving assistant {assistant_id}: {str(e)}")
            raise
    
    async def create_vector_store(
        self,
        name: str,
        file_ids: List[str] = None,
        metadata: Dict[str, str] = None
    ) -> VectorStore:
        """Create a vector store."""
        try:
            vector_store = await self.client.beta.vector_stores.create(
                name=name,
                file_ids=file_ids or [],
                metadata=metadata or {}
            )
            
            logger.info(f"Created vector store: {vector_store.id}")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    async def add_files_to_vector_store(
        self,
        vector_store_id: str,
        file_ids: List[str]
    ) -> None:
        """Add files to a vector store."""
        try:
            for file_id in file_ids:
                await self.client.beta.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
            
            logger.info(f"Added {len(file_ids)} files to vector store: {vector_store_id}")
            
        except Exception as e:
            logger.error(f"Error adding files to vector store {vector_store_id}: {str(e)}")
            raise
    
    async def upload_file(
        self,
        file_path: str,
        purpose: str = "assistants"
    ) -> FileObject:
        """Upload a file to OpenAI."""
        try:
            with open(file_path, "rb") as file:
                uploaded_file = await self.client.files.create(
                    file=file,
                    purpose=purpose
                )
            
            logger.info(f"Uploaded file: {uploaded_file.id}")
            return uploaded_file
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from OpenAI."""
        try:
            await self.client.files.delete(file_id)
            logger.info(f"Deleted file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise
    
    async def create_thread(self, metadata: Dict[str, str] = None) -> Thread:
        """Create a new thread."""
        try:
            thread = await self.client.beta.threads.create(
                metadata=metadata or {}
            )
            
            logger.info(f"Created thread: {thread.id}")
            return thread
            
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise
    
    async def add_message_to_thread(
        self,
        thread_id: str,
        content: str,
        role: str = "user",
        file_ids: List[str] = None,
        metadata: Dict[str, str] = None
    ) -> Message:
        """Add a message to a thread."""
        try:
            message = await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content,
                attachments=[{"file_id": fid, "tools": [{"type": "file_search"}]} for fid in (file_ids or [])],
                metadata=metadata or {}
            )
            
            logger.info(f"Added message to thread: {thread_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error adding message to thread {thread_id}: {str(e)}")
            raise
    
    async def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: str = None,
        additional_instructions: str = None,
        temperature: float = None,
        max_prompt_tokens: int = None,
        max_completion_tokens: int = None,
        metadata: Dict[str, str] = None
    ) -> Run:
        """Run an assistant on a thread."""
        try:
            run_kwargs = {
                "thread_id": thread_id,
                "assistant_id": assistant_id,
                "metadata": metadata or {}
            }
            
            if instructions:
                run_kwargs["instructions"] = instructions
            if additional_instructions:
                run_kwargs["additional_instructions"] = additional_instructions
            if temperature is not None:
                run_kwargs["temperature"] = temperature
            if max_prompt_tokens:
                run_kwargs["max_prompt_tokens"] = max_prompt_tokens
            if max_completion_tokens:
                run_kwargs["max_completion_tokens"] = max_completion_tokens
            
            run = await self.client.beta.threads.runs.create(**run_kwargs)
            
            logger.info(f"Started run: {run.id} on thread: {thread_id}")
            return run
            
        except Exception as e:
            logger.error(f"Error running assistant on thread {thread_id}: {str(e)}")
            raise
    
    async def wait_for_run_completion(
        self,
        thread_id: str,
        run_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0
    ) -> Run:
        """Wait for a run to complete."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            while True:
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status in ["completed", "failed", "cancelled", "expired"]:
                    logger.info(f"Run {run_id} completed with status: {run.status}")
                    return run
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.error(f"Run {run_id} timed out after {timeout} seconds")
                    raise TimeoutError(f"Run timed out after {timeout} seconds")
                
                await asyncio.sleep(poll_interval)
                
        except Exception as e:
            logger.error(f"Error waiting for run completion {run_id}: {str(e)}")
            raise
    
    async def get_thread_messages(
        self,
        thread_id: str,
        limit: int = 20,
        order: str = "desc"
    ) -> List[Message]:
        """Get messages from a thread."""
        try:
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit,
                order=order
            )
            
            return list(messages.data)
            
        except Exception as e:
            logger.error(f"Error getting messages from thread {thread_id}: {str(e)}")
            raise
    
    async def create_embeddings(
        self,
        texts: List[str],
        model: str = None
    ) -> List[List[float]]:
        """Create embeddings for texts."""
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=model or settings.embedding_model
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Created embeddings for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        model: str = None,
        language: str = None,
        prompt: str = None,
        temperature: float = 0.0
    ) -> str:
        """Transcribe audio using Whisper."""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=model or settings.voice_model,
                    file=audio_file,
                    language=language,
                    prompt=prompt,
                    temperature=temperature
                )
            
            logger.info(f"Transcribed audio file: {audio_file_path}")
            return transcript.text
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_file_path}: {str(e)}")
            raise
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None,
        metadata: Dict[str, str] = None
    ) -> Any:
        """Create a chat completion."""
        try:
            completion_kwargs = {
                "model": model or settings.text_model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
            
            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens
            if tools:
                completion_kwargs["tools"] = tools
            if metadata:
                completion_kwargs["metadata"] = metadata
            
            if stream:
                return await self.client.chat.completions.create(**completion_kwargs)
            else:
                completion = await self.client.chat.completions.create(**completion_kwargs)
                logger.info(f"Created chat completion with {len(messages)} messages")
                return completion
                
        except Exception as e:
            logger.error(f"Error creating chat completion: {str(e)}")
            raise
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion."""
        try:
            stream = await self.client.chat.completions.create(
                model=model or settings.text_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming chat completion: {str(e)}")
            raise


# Global client instance
openai_client = OpenAIClientWrapper()
