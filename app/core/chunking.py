"""
Text chunking strategies for document processing.

Provides:
- Chunk base class
- FixedSizeChunker: Fixed-size chunks with overlap
- SemanticChunker: Paragraph-based semantic chunks
"""

import re
import uuid
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Chunk:
    """
    Represents a chunk of text with metadata.
    
    Attributes:
        id: Unique identifier for the chunk.
        text: The chunk content.
        metadata: Additional metadata about the chunk.
    """
    id: str
    text: str
    metadata: dict
    
    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}


class Chunker:
    """
    Base class for text chunking strategies.
    
    Subclasses should implement the chunk method.
    """
    
    def chunk(self, text: str) -> List[Chunk]:
        """
        Split text into chunks.
        
        Args:
            text: The text to chunk.
        
        Returns:
            List[Chunk]: List of chunks.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement chunk method.")


class FixedSizeChunker(Chunker):
    """
    Chunker that splits text into fixed-size chunks with overlap.
    
    This chunker splits text into chunks of approximately equal size
    with a configurable overlap between consecutive chunks.
    """
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize the FixedSizeChunker.
        
        Args:
            chunk_size: Target size of each chunk in characters. Default: 512.
            overlap: Number of characters to overlap between chunks. Default: 50.
        
        Raises:
            ValueError: If chunk_size <= 0 or overlap >= chunk_size.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if overlap < 0:
            raise ValueError("overlap must be non-negative.")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size.")
        
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str) -> List[Chunk]:
        """
        Split text into fixed-size chunks with overlap.
        
        Args:
            text: The text to chunk.
        
        Returns:
            List[Chunk]: List of chunks with metadata.
        """
        if not text or not text.strip():
            return []
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a word boundary
            if end < len(text):
                # Find the last space before the end
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    text=chunk_text,
                    metadata={
                        "chunk_index": chunk_index,
                        "chunk_type": "fixed_size",
                        "start_pos": start,
                        "end_pos": end,
                        "chunk_size": len(chunk_text)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.overlap
            if start < 0:
                start = 0
        
        return chunks


class SemanticChunker(Chunker):
    """
    Chunker that splits text at paragraph boundaries.
    
    This chunker preserves semantic coherence by splitting at paragraph
    boundaries (double newlines). Each paragraph becomes a separate chunk.
    """
    
    def __init__(self, min_chunk_size: int = 50):
        """
        Initialize the SemanticChunker.
        
        Args:
            min_chunk_size: Minimum size for a chunk to be included. Default: 50.
        
        Raises:
            ValueError: If min_chunk_size <= 0.
        """
        if min_chunk_size <= 0:
            raise ValueError("min_chunk_size must be greater than 0.")
        
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, text: str) -> List[Chunk]:
        """
        Split text into semantic chunks at paragraph boundaries.
        
        Args:
            text: The text to chunk.
        
        Returns:
            List[Chunk]: List of chunks with metadata.
        """
        if not text or not text.strip():
            return []
        
        # Split by paragraph boundaries (double newlines)
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        chunks = []
        chunk_index = 0
        
        for paragraph in paragraphs:
            # Clean up the paragraph
            paragraph = re.sub(r'\s+', ' ', paragraph.strip())
            
            # Skip if too short
            if len(paragraph) < self.min_chunk_size:
                continue
            
            chunk = Chunk(
                id=str(uuid.uuid4()),
                text=paragraph,
                metadata={
                    "chunk_index": chunk_index,
                    "chunk_type": "semantic",
                    "paragraph": True,
                    "chunk_size": len(paragraph)
                }
            )
            chunks.append(chunk)
            chunk_index += 1
        
        return chunks


def get_chunker(strategy: str, **kwargs) -> Chunker:
    """
    Factory function to get a chunker by strategy name.
    
    Args:
        strategy: The chunking strategy ("fixed_size" or "semantic").
        **kwargs: Additional arguments for the chunker.
    
    Returns:
        Chunker: The configured chunker instance.
    
    Raises:
        ValueError: If strategy is not recognized.
    """
    strategy = strategy.lower()
    
    if strategy == "fixed_size":
        return FixedSizeChunker(
            chunk_size=kwargs.get("chunk_size", 512),
            overlap=kwargs.get("overlap", 50)
        )
    elif strategy == "semantic":
        return SemanticChunker(
            min_chunk_size=kwargs.get("min_chunk_size", 50)
        )
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Use 'fixed_size' or 'semantic'.")
