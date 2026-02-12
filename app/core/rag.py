"""
RAG (Retrieval-Augmented Generation) chain implementation.

Provides:
- RAGChain class for generating answers with retrieved context
"""

import os
import logging
import time
import uuid
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError

from app.core.retrieval import RetrievalEngine, SearchResult

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RAGChain:
    """
    RAG Chain for generating answers using retrieved context.

    This class implements a retrieval-augmented generation pipeline:
    1. Retrieve relevant chunks using the retrieval engine
    2. Build context with numbered citations
    3. Generate answer using Chutes.ai chat completions
    4. Return answer with sources, citations, and metrics
    """

    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the RAGChain.

        Args:
            retrieval_engine: Instance of RetrievalEngine for context retrieval.
            model: The model to use for generation. Default: from CHUTES_MODEL env var.
            api_key: API key. If None, reads from CHUTES_API_TOKEN env var.
            base_url: API base URL. If None, reads from CHUTES_API_BASE_URL env var.
        """
        self.retrieval_engine = retrieval_engine
        self.model = model or os.getenv("CHUTES_MODEL", "Qwen/Qwen3-32B")
        self.api_key = api_key or os.getenv("CHUTES_API_TOKEN") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("CHUTES_API_BASE_URL", "https://llm.chutes.ai/v1")

        # DEBUG: Log API key configuration (masked for security)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DEBUG] RAGChain initialized with model: {self.model}")
        logger.info(f"[DEBUG] RAGChain base_url: {self.base_url}")
        if self.api_key:
            masked_key = f"{self.api_key[:10]}...{self.api_key[-4:]}"
            logger.info(f"[DEBUG] RAGChain API key (masked): {masked_key}")
        else:
            logger.warning("[DEBUG] RAGChain API key is NOT SET!")

        if not self.api_key:
            raise ValueError("API key not provided and CHUTES_API_TOKEN/OPENAI_API_KEY environment variable not set.")

        # Chutes.ai requires "Bearer " prefix in the Authorization header
        # The OpenAI client doesn't add this automatically for custom base URLs
        self.bearer_token = f"Bearer {self.api_key}"
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={"Authorization": self.bearer_token}
        )

        # System prompt for the assistant
        self.system_prompt = (
            "You are a helpful customer support assistant. "
            "Use ONLY the provided context to answer questions. "
            "Cite your sources using [1], [2], [3] notation. "
            "If the answer is not in the context, say so clearly."
        )
    
    async def query(self, query_text: str, k: int = 5) -> Dict:
        """
        Query the RAG system and generate an answer.

        Args:
            query_text: The user's question.
            k: Number of context chunks to retrieve. Default: 5.

        Returns:
            Dict: Dictionary containing:
                - answer: The generated answer
                - sources: List of source information
                - citations: List of citation references
                - metrics: Performance metrics (retrieval_time, response_time, etc.)

        Raises:
            ValueError: If query_text is empty.
            Exception: If the OpenAI API call fails.
        """
        if not query_text or not query_text.strip():
            raise ValueError("Query text cannot be empty.")
        
        # Step 1: Retrieve relevant chunks
        retrieval_start = time.time()
        search_results = await self.retrieval_engine.semantic_search(query_text, k)
        retrieval_time = (time.time() - retrieval_start) * 1000  # Convert to milliseconds
        
        # Step 2: Build context with numbered citations
        context_parts = []
        sources = []
        citations = []
        
        for i, result in enumerate(search_results, start=1):
            context_parts.append(f"[{i}] {result.text}")
            sources.append({
                "id": result.id,
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata
            })
            citations.append(f"[{i}]")
        
        context = "\n\n".join(context_parts)
        
        # Step 3: Generate answer using OpenAI
        generation_start = time.time()
        
        logger.info(f"[DEBUG] Sending request to LLM API: model={self.model}, base_url={self.base_url}")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query_text}"
                    }
                ],
                temperature=0.7,
                max_tokens=1024
            )

            answer = response.choices[0].message.content
            logger.info(f"[DEBUG] LLM API response received successfully")

        except APIError as e:
            logger.error(f"[DEBUG] LLM API error: {type(e).__name__}: {e}")
            raise Exception(f"Failed to generate answer: {e}")
        
        generation_time = (time.time() - generation_start) * 1000  # Convert to milliseconds
        
        # Step 4: Return results with metrics
        return {
            "answer": answer,
            "sources": sources,
            "citations": citations,
            "metrics": {
                "retrieval_time_ms": round(retrieval_time, 2),
                "response_time_ms": round(generation_time, 2),
                "total_time_ms": round(retrieval_time + generation_time, 2),
                "num_chunks_retrieved": len(search_results),
                "num_sources": len(sources)
            }
        }
    
    async def query_with_ticket(
        self, 
        query_text: str, 
        k: int = 5,
        ticket_id: Optional[str] = None
    ) -> Dict:
        """
        Query the RAG system with optional ticket association.
        
        Args:
            query_text: The user's question.
            k: Number of context chunks to retrieve. Default: 5.
            ticket_id: Optional ticket ID to associate with the query.
        
        Returns:
            Dict: Dictionary containing answer, sources, citations, and metrics.
        """
        result = await self.query(query_text, k)
        
        # Add ticket_id to result if provided
        if ticket_id:
            result["ticket_id"] = ticket_id
        
        return result
    
    def format_context(self, search_results: List[SearchResult]) -> str:
        """
        Format search results into a context string.
        
        Args:
            search_results: List of SearchResult objects.
        
        Returns:
            str: Formatted context string with numbered citations.
        """
        context_parts = []
        for i, result in enumerate(search_results, start=1):
            context_parts.append(f"[{i}] {result.text}")
        return "\n\n".join(context_parts)
    
    def extract_citations(self, answer: str) -> List[str]:
        """
        Extract citation references from an answer.
        
        Args:
            answer: The generated answer text.
        
        Returns:
            List[str]: List of unique citation references found.
        """
        import re
        citations = re.findall(r'\[\d+\]', answer)
        return list(set(citations))  # Return unique citations
