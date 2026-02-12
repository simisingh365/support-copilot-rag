"""
Embedding generation module using ChromaDB's built-in embedding functions.

Provides:
- Async embedding generation for single text
- Async batch embedding generation
- Cosine similarity calculation
"""

import logging
import os
from typing import List

import numpy as np
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings using ChromaDB's built-in embedding functions.

    This class provides methods to generate embeddings for text using
    ChromaDB's embedding functions with error handling.
    """

    def __init__(self, api_key: str | None = None, model: str = "all-MiniLM-L6-v2", base_url: str | None = None):
        """
        Initialize the EmbeddingGenerator.

        Args:
            api_key: API key (not used for local embeddings).
            model: The embedding model to use. Default: all-MiniLM-L6-v2.
            base_url: Custom base URL (not used for local embeddings).
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("CHUTES_API_BASE_URL")

        # Use ChromaDB's built-in sentence transformer embedding function
        # This is a local model that doesn't require an API call
        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            logger.info(f"Initialized EmbeddingGenerator with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding function: {e}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.

        Args:
            text: The text to generate an embedding for.

        Returns:
            List[float]: The embedding vector.

        Raises:
            ValueError: If text is empty.
            Exception: If the embedding generation fails.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        try:
            logger.info(f"Generating embedding for text: {text[:50]}...")
            embeddings = self.embedding_function([text])
            logger.info("Embedding generated successfully")
            return embeddings[0]
        except Exception as e:
            logger.error(f"Error generating embedding: {type(e).__name__}: {e}")
            raise Exception(f"Failed to generate embedding: {e}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            List[List[float]]: List of embedding vectors.

        Raises:
            ValueError: If texts list is empty.
            Exception: If the embedding generation fails.
        """
        if not texts:
            raise ValueError("Texts list cannot be empty.")

        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided.")

        logger.info(f"Generating embeddings for {len(valid_texts)} texts using model {self.model}")

        try:
            logger.info("Generating embeddings...")
            embeddings = self.embedding_function(valid_texts)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {type(e).__name__}: {e}")
            raise Exception(f"Failed to generate embeddings: {e}")

    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            float: Cosine similarity score between -1 and 1.

        Raises:
            ValueError: If embeddings have different dimensions.
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension.")

        # Convert to numpy arrays for efficient computation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    @staticmethod
    def cosine_similarity_batch(
        query_embedding: List[float],
        embeddings: List[List[float]]
    ) -> List[float]:
        """
        Calculate cosine similarity between a query embedding and multiple embeddings.

        Args:
            query_embedding: The query embedding vector.
            embeddings: List of embedding vectors to compare against.

        Returns:
            List[float]: List of cosine similarity scores.
        """
        return [
            EmbeddingGenerator.cosine_similarity(query_embedding, emb)
            for emb in embeddings
        ]
