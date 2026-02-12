"""
Retrieval engine using ChromaDB for semantic search.

Provides:
- SearchResult class for search results
- RetrievalEngine class for semantic search and document management
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.errors import ChromaError

from app.core.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    Represents a search result from the retrieval engine.
    
    Attributes:
        id: Unique identifier for the result.
        text: The text content of the result.
        score: Relevance score (higher is more relevant).
        metadata: Additional metadata about the result.
    """
    id: str
    text: str
    score: float
    metadata: dict
    
    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}


class RetrievalEngine:
    """
    Retrieval engine using ChromaDB for semantic search.
    
    This class provides methods to:
    - Perform semantic search on the knowledge base
    - Add documents to the vector store
    - Manage the ChromaDB collection
    """
    
    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        collection_name: str = "knowledge_base",
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Initialize the RetrievalEngine.

        Args:
            embedding_generator: Instance of EmbeddingGenerator for creating embeddings.
            collection_name: Name of the ChromaDB collection. Default: "knowledge_base".
            host: ChromaDB host. If None, uses CHROMA_HOST env var or localhost.
            port: ChromaDB port. If None, uses CHROMA_PORT env var or 8000.
        """
        self.embedding_generator = embedding_generator
        self.collection_name = collection_name
        self.host = host or os.getenv("CHROMA_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMA_PORT", "8000"))

        logger.info(f"Initializing RetrievalEngine with ChromaDB at {self.host}:{self.port}")

        # Initialize ChromaDB client
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"Successfully connected to ChromaDB at {self.host}:{self.port}")
        except ChromaError as e:
            logger.error(f"Failed to connect to ChromaDB at {self.host}:{self.port}: {e}")
            raise ChromaError(f"Failed to connect to ChromaDB at {self.host}:{self.port}: {e}")

        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Knowledge base for RAG system"}
            )
            logger.info(f"Successfully got/created collection '{self.collection_name}'")
        except ChromaError as e:
            logger.error(f"Failed to get or create collection '{self.collection_name}': {e}")
            raise ChromaError(f"Failed to get or create collection '{self.collection_name}': {e}")
    
    async def semantic_search(self, query: str, k: int = 5) -> List[SearchResult]:
        """
        Perform semantic search on the knowledge base.

        Args:
            query: The search query text.
            k: Number of results to return. Default: 5.

        Returns:
            List[SearchResult]: List of search results sorted by relevance.

        Raises:
            ValueError: If query is empty or k is invalid.
            ChromaError: If the search operation fails.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if k <= 0:
            raise ValueError("k must be greater than 0.")

        logger.info(f"Performing semantic search for query: {query[:100]}... (k={k})")

        try:
            # Generate embedding for the query
            logger.info("Generating query embedding...")
            query_embedding = await self.embedding_generator.generate_embedding(query)
            logger.info("Query embedding generated successfully")

            # Query ChromaDB
            logger.info(f"Querying ChromaDB collection '{self.collection_name}'...")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            logger.info(f"ChromaDB query returned {len(results.get('ids', [[]])[0])} results")

            # Convert to SearchResult objects
            search_results = []
            if results and results.get("ids") and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    text = results["documents"][0][i] if results.get("documents") else ""
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}

                    # Calculate score based on rank (ChromaDB doesn't return scores by default)
                    # Higher rank = higher score
                    score = 1.0 - (i / k) if k > 0 else 0.0

                    search_result = SearchResult(
                        id=doc_id,
                        text=text,
                        score=score,
                        metadata=metadata
                    )
                    search_results.append(search_result)

            logger.info(f"Returning {len(search_results)} search results")
            return search_results

        except ChromaError as e:
            logger.error(f"ChromaError in semantic search: {e}")
            raise ChromaError(f"Semantic search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in semantic search: {type(e).__name__}: {e}")
            raise ChromaError(f"Unexpected error during semantic search: {e}")
    
    async def add_documents(
        self,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[dict]] = None
    ) -> None:
        """
        Add documents to the ChromaDB collection.

        Args:
            documents: List of document texts to add.
            ids: Optional list of document IDs. If None, generates UUIDs.
            metadatas: Optional list of metadata dictionaries for each document.

        Raises:
            ValueError: If documents list is empty or lengths don't match.
            ChromaError: If the add operation fails.
        """
        if not documents:
            raise ValueError("Documents list cannot be empty.")

        if ids is not None and len(ids) != len(documents):
            raise ValueError("Length of ids must match length of documents.")

        if metadatas is not None and len(metadatas) != len(documents):
            raise ValueError("Length of metadatas must match length of documents.")

        logger.info(f"Adding {len(documents)} documents to ChromaDB collection '{self.collection_name}'")

        try:
            # Generate embeddings for all documents
            logger.info("Generating embeddings for documents...")
            embeddings = await self.embedding_generator.generate_embeddings(documents)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
                logger.info(f"Generated {len(ids)} new document IDs")

            # Ensure metadatas is a list
            if metadatas is None:
                metadatas = [{} for _ in documents]

            # Add to ChromaDB
            logger.info("Adding documents to ChromaDB...")
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(documents)} documents to ChromaDB")

        except ChromaError as e:
            logger.error(f"ChromaError adding documents: {e}")
            raise ChromaError(f"Failed to add documents to ChromaDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error adding documents: {type(e).__name__}: {e}")
            raise ChromaError(f"Unexpected error adding documents: {e}")
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents from the ChromaDB collection.
        
        Args:
            ids: List of document IDs to delete.
        
        Raises:
            ValueError: If ids list is empty.
            ChromaError: If the delete operation fails.
        """
        if not ids:
            raise ValueError("IDs list cannot be empty.")
        
        try:
            self.collection.delete(ids=ids)
        except ChromaError as e:
            raise ChromaError(f"Failed to delete documents from ChromaDB: {e}")
    
    def get_collection_count(self) -> int:
        """
        Get the number of documents in the collection.
        
        Returns:
            int: Number of documents in the collection.
        """
        try:
            return self.collection.count()
        except ChromaError as e:
            raise ChromaError(f"Failed to get collection count: {e}")
    
    def clear_collection(self) -> None:
        """
        Clear all documents from the collection.
        
        Warning: This will delete all data in the collection.
        
        Raises:
            ChromaError: If the clear operation fails.
        """
        try:
            # Delete all documents by getting all IDs
            all_data = self.collection.get()
            if all_data and all_data.get("ids"):
                self.delete_documents(all_data["ids"])
        except ChromaError as e:
            raise ChromaError(f"Failed to clear collection: {e}")
