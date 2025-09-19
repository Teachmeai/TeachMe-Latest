"""Vector store utilities for document search and retrieval."""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..utils.openai_client import openai_client
from ..utils.supabase_client import supabase_client
from ..config.settings import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings and similarity search."""
    
    def __init__(self):
        """Initialize Vector Store Service."""
        self.embedding_model = settings.embedding_model
        self.vector_dimension = settings.vector_dimension
        self.similarity_threshold = settings.similarity_threshold
        self.max_results = settings.max_results
    
    async def create_embeddings(
        self,
        texts: List[str],
        metadata: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Create embeddings for a list of texts."""
        try:
            if not texts:
                return []
            
            # Create embeddings using OpenAI
            embeddings = await openai_client.create_embeddings(
                texts=texts,
                model=self.embedding_model
            )
            
            # Combine with metadata
            results = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                result = {
                    "text": text,
                    "embedding": embedding,
                    "metadata": metadata[i] if metadata and i < len(metadata) else {}
                }
                results.append(result)
            
            logger.info(f"Created {len(results)} embeddings")
            return results
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise
    
    async def store_document_chunks(
        self,
        file_id: str,
        chunks: List[Dict[str, Any]],
        assistant_id: str = None,
        vector_store_id: str = None
    ) -> List[str]:
        """Store document chunks with embeddings."""
        try:
            # Extract text content from chunks
            texts = [chunk["content"] for chunk in chunks]
            
            # Prepare metadata for each chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "file_id": file_id,
                    "chunk_id": chunk.get("chunk_id"),
                    "chunk_number": chunk.get("chunk_number", i + 1),
                    "start_index": chunk.get("start_index", 0),
                    "end_index": chunk.get("end_index", len(chunk["content"])),
                    "assistant_id": assistant_id,
                    "vector_store_id": vector_store_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                chunk_metadata.append(metadata)
            
            # Create embeddings
            embeddings_data = await self.create_embeddings(texts, chunk_metadata)
            
            # Store in vector database (placeholder - would use actual vector DB in production)
            stored_ids = []
            for embedding_data in embeddings_data:
                # In production, this would store in a vector database like Pinecone, Weaviate, etc.
                # For now, we'll store in Supabase as JSONB (not optimal for large scale)
                stored_id = await self._store_embedding_record(embedding_data)
                stored_ids.append(stored_id)
            
            logger.info(f"Stored {len(stored_ids)} document chunks with embeddings")
            return stored_ids
            
        except Exception as e:
            logger.error(f"Error storing document chunks: {str(e)}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        assistant_id: str = None,
        vector_store_id: str = None,
        limit: int = None,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Perform similarity search on stored embeddings."""
        try:
            # Create embedding for query
            query_embeddings = await openai_client.create_embeddings(
                texts=[query],
                model=self.embedding_model
            )
            query_embedding = query_embeddings[0]
            
            # Search for similar embeddings
            results = await self._search_similar_embeddings(
                query_embedding=query_embedding,
                assistant_id=assistant_id,
                vector_store_id=vector_store_id,
                limit=limit or self.max_results,
                threshold=threshold or self.similarity_threshold
            )
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            raise
    
    async def delete_document_embeddings(
        self,
        file_id: str
    ) -> bool:
        """Delete all embeddings for a specific document."""
        try:
            # Delete embeddings from vector database
            # This is a placeholder - would use actual vector DB operations
            deleted = await self._delete_embeddings_by_file_id(file_id)
            
            logger.info(f"Deleted embeddings for file: {file_id}")
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting document embeddings: {str(e)}")
            raise
    
    async def get_document_context(
        self,
        query: str,
        assistant_id: str,
        max_context_length: int = 4000
    ) -> str:
        """Get relevant document context for a query."""
        try:
            # Search for relevant documents
            search_results = await self.similarity_search(
                query=query,
                assistant_id=assistant_id,
                limit=10
            )
            
            if not search_results:
                return ""
            
            # Build context from search results
            context_parts = []
            current_length = 0
            
            for result in search_results:
                text = result["text"]
                
                # Check if adding this text would exceed max length
                if current_length + len(text) > max_context_length:
                    # Try to fit partial text
                    remaining_space = max_context_length - current_length
                    if remaining_space > 100:  # Only add if meaningful amount of space
                        text = text[:remaining_space - 3] + "..."
                        context_parts.append(f"[Score: {result['score']:.3f}] {text}")
                    break
                
                context_parts.append(f"[Score: {result['score']:.3f}] {text}")
                current_length += len(text)
            
            context = "\n\n".join(context_parts)
            
            logger.info(f"Built context of {len(context)} characters from {len(context_parts)} documents")
            return context
            
        except Exception as e:
            logger.error(f"Error getting document context: {str(e)}")
            return ""
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    async def _store_embedding_record(
        self,
        embedding_data: Dict[str, Any]
    ) -> str:
        """Store embedding record in database."""
        try:
            # This is a placeholder implementation using Supabase
            # In production, you would use a dedicated vector database
            
            record_data = {
                "text": embedding_data["text"],
                "embedding": embedding_data["embedding"],
                "metadata": embedding_data["metadata"],
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store in a hypothetical embeddings table
            # Note: This would require creating an embeddings table in Supabase
            # For now, we'll return a placeholder ID
            
            import uuid
            record_id = str(uuid.uuid4())
            
            logger.debug(f"Stored embedding record: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Error storing embedding record: {str(e)}")
            raise
    
    async def _search_similar_embeddings(
        self,
        query_embedding: List[float],
        assistant_id: str = None,
        vector_store_id: str = None,
        limit: int = 10,
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings in the database."""
        try:
            # This is a placeholder implementation
            # In production, you would use a vector database with proper indexing
            
            # For now, return empty results
            # In a real implementation, this would:
            # 1. Query the vector database with the query embedding
            # 2. Filter by assistant_id and vector_store_id if provided
            # 3. Return top results above the similarity threshold
            
            results = []
            
            logger.debug(f"Searching embeddings with threshold {threshold}, limit {limit}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {str(e)}")
            raise
    
    async def _delete_embeddings_by_file_id(
        self,
        file_id: str
    ) -> bool:
        """Delete embeddings by file ID."""
        try:
            # This is a placeholder implementation
            # In production, you would delete from the vector database
            
            logger.debug(f"Deleting embeddings for file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            return False
    
    async def get_embedding_statistics(
        self,
        assistant_id: str = None
    ) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            # This would query the vector database for statistics
            # For now, return placeholder data
            
            stats = {
                "total_embeddings": 0,
                "total_documents": 0,
                "average_chunk_size": 0,
                "embedding_dimension": self.vector_dimension,
                "model_used": self.embedding_model,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if assistant_id:
                stats["assistant_id"] = assistant_id
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting embedding statistics: {str(e)}")
            raise
    
    async def update_embeddings_metadata(
        self,
        file_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update metadata for all embeddings of a file."""
        try:
            # This would update metadata in the vector database
            # For now, return success
            
            logger.info(f"Updated metadata for file {file_id}: {metadata_updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating embeddings metadata: {str(e)}")
            return False


# Global instance
vector_store_service = VectorStoreService()
