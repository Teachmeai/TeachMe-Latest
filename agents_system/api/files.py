"""File management API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import os

from ..models.schemas import (
    FileUploadResponse,
    FileResponse as FileResponseSchema,
    FileProcessRequest,
    ErrorResponse
)
from ..utils.auth import get_current_user, require_super_admin
from ..services.file_service import file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/files", tags=["File Management"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    assistant_id: Optional[str] = Form(None, description="Associate with specific course assistant"),
    metadata: Optional[str] = Form(None, description="JSON metadata for the file"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> FileUploadResponse:
    """
    Upload a file for processing and vector storage.
    
    Supported file types:
    - PDF documents
    - Word documents (DOCX)
    - PowerPoint presentations (PPTX)
    - CSV files
    - Text files
    - Images (JPEG, PNG, GIF)
    """
    try:
        user_id = current_user["user_id"]
        
        # Read file content
        file_content = await file.read()
        
        # Parse metadata if provided
        file_metadata = {}
        if metadata:
            import json
            try:
                file_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid metadata JSON"
                )
        
        # Verify assistant exists if provided
        if assistant_id:
            from ..services.course_agent import course_agent_service
            try:
                await course_agent_service.get_course_assistant(assistant_id, user_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course assistant not found"
                )
        
        uploaded_file = await file_service.upload_file(
            file_content=file_content,
            filename=file.filename or "unnamed_file",
            content_type=file.content_type or "application/octet-stream",
            user_id=user_id,
            assistant_id=assistant_id,
            metadata=file_metadata
        )
        
        return uploaded_file
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/upload/multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Multiple files to upload"),
    assistant_id: Optional[str] = Form(None, description="Associate with specific course assistant"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[FileUploadResponse]:
    """Upload multiple files at once."""
    try:
        user_id = current_user["user_id"]
        
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 files per upload"
            )
        
        uploaded_files = []
        
        for file in files:
            try:
                file_content = await file.read()
                
                uploaded_file = await file_service.upload_file(
                    file_content=file_content,
                    filename=file.filename or "unnamed_file",
                    content_type=file.content_type or "application/octet-stream",
                    user_id=user_id,
                    assistant_id=assistant_id
                )
                
                uploaded_files.append(uploaded_file)
                
            except Exception as e:
                logger.error(f"Error uploading file {file.filename}: {str(e)}")
                # Continue with other files even if one fails
        
        return uploaded_files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading multiple files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multiple file upload failed: {str(e)}"
        )


@router.get("", response_model=List[FileResponseSchema])
async def list_files(
    assistant_id: Optional[str] = Query(None, description="Filter by course assistant"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[FileResponseSchema]:
    """Get list of uploaded files for the current user."""
    try:
        user_id = current_user["user_id"]
        
        files = await file_service.get_user_files(
            user_id=user_id,
            assistant_id=assistant_id,
            limit=limit
        )
        
        return files
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve files: {str(e)}"
        )


@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> FileResponseSchema:
    """Get details of a specific file."""
    try:
        user_id = current_user["user_id"]
        
        files = await file_service.get_user_files(user_id)
        file_record = None
        
        for f in files:
            if f.id == file_id:
                file_record = f
                break
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return file_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file: {str(e)}"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Delete a file."""
    try:
        user_id = current_user["user_id"]
        
        success = await file_service.delete_file(
            file_id=file_id,
            user_id=user_id
        )
        
        if success:
            return JSONResponse(
                content={"message": "File deleted successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.post("/process", response_model=Dict[str, Any])
async def process_files_for_assistant(
    process_request: FileProcessRequest,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """
    Process files for a course assistant's vector store.
    
    This endpoint uploads files to OpenAI and associates them with a course assistant.
    Only Super Admins can perform this operation.
    """
    try:
        user_id = current_user["user_id"]
        
        result = await file_service.process_files_for_assistant(
            request=process_request,
            user_id=user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> FileResponse:
    """Download a file."""
    try:
        user_id = current_user["user_id"]
        
        # Get file record
        files = await file_service.get_user_files(user_id)
        file_record = None
        
        for f in files:
            if f.id == file_id:
                file_record = f
                break
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if file exists on disk
        if not os.path.exists(file_record.upload_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        return FileResponse(
            path=file_record.upload_path,
            filename=file_record.original_filename,
            media_type=file_record.file_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File download failed: {str(e)}"
        )


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    chunk_size: int = Query(1000, ge=100, le=5000, description="Text chunk size"),
    chunk_overlap: int = Query(200, ge=0, le=1000, description="Chunk overlap"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Extract and return text content from a file."""
    try:
        user_id = current_user["user_id"]
        
        # Get file record
        files = await file_service.get_user_files(user_id)
        file_record = None
        
        for f in files:
            if f.id == file_id:
                file_record = f
                break
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Extract text content
        chunks = await file_service.extract_text_content(
            file_path=file_record.upload_path,
            file_type=file_record.file_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Combine chunks for full text
        full_text = "\n".join(chunk["content"] for chunk in chunks)
        
        return {
            "file_id": file_id,
            "filename": file_record.original_filename,
            "file_type": file_record.file_type,
            "full_text": full_text,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "total_characters": len(full_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting file content {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content extraction failed: {str(e)}"
        )


@router.get("/statistics/user")
async def get_user_file_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get file upload statistics for the current user."""
    try:
        user_id = current_user["user_id"]
        
        stats = await file_service.get_file_statistics(user_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting file statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Audio language (optional)"),
    prompt: Optional[str] = Form(None, description="Transcription prompt (optional)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Transcribe audio file using Whisper.
    
    Supported audio formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate audio file type
        audio_types = ["audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "audio/m4a"]
        if audio_file.content_type not in audio_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio type: {audio_file.content_type}"
            )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using OpenAI Whisper
            from ..utils.openai_client import openai_client
            
            transcript = await openai_client.transcribe_audio(
                audio_file_path=temp_file_path,
                language=language,
                prompt=prompt
            )
            
            # Optionally save transcript as a file
            transcript_content = f"Audio Transcription\nFile: {audio_file.filename}\nTranscript:\n\n{transcript}"
            
            uploaded_file = await file_service.upload_file(
                file_content=transcript_content.encode('utf-8'),
                filename=f"{os.path.splitext(audio_file.filename)[0]}_transcript.txt",
                content_type="text/plain",
                user_id=user_id,
                metadata={
                    "original_audio_file": audio_file.filename,
                    "transcription": True,
                    "language": language,
                    "audio_content_type": audio_file.content_type
                }
            )
            
            return {
                "transcript": transcript,
                "original_filename": audio_file.filename,
                "language": language,
                "transcript_file": {
                    "id": uploaded_file.id,
                    "filename": uploaded_file.filename
                }
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}"
        )


@router.get("/health")
async def file_health_check() -> Dict[str, Any]:
    """Health check endpoint for file services."""
    try:
        # Check upload directory
        upload_dir_exists = os.path.exists(file_service.upload_dir)
        upload_dir_writable = os.access(file_service.upload_dir, os.W_OK) if upload_dir_exists else False
        
        return {
            "status": "healthy" if upload_dir_exists and upload_dir_writable else "degraded",
            "upload_directory": {
                "path": file_service.upload_dir,
                "exists": upload_dir_exists,
                "writable": upload_dir_writable
            },
            "supported_types": file_service.supported_types,
            "max_file_size_mb": file_service.max_file_size / (1024 * 1024),
            "features": {
                "file_upload": True,
                "text_extraction": True,
                "audio_transcription": True,
                "multiple_uploads": True,
                "vector_processing": True
            }
        }
        
    except Exception as e:
        logger.error(f"File health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File service unhealthy"
        )
