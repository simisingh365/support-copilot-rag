"""
ChromaDB Server Launcher

This script starts the ChromaDB server for the RAG system.
Run this script to start the ChromaDB server before running the main application.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable ChromaDB telemetry to avoid Posthog compatibility issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Get ChromaDB configuration from environment
HOST = os.getenv("CHROMA_HOST", "localhost")
PORT = int(os.getenv("CHROMA_PORT", "8001"))

if __name__ == "__main__":
    print(f"Starting ChromaDB server on {HOST}:{PORT}...")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        # Run ChromaDB server using Python module
        # This is the correct way for ChromaDB 0.4.18
        subprocess.run(
            [sys.executable, "-m", "chromadb.cli.cli", "run", "--host", HOST, "--port", str(PORT)],
            check=True
        )

    except KeyboardInterrupt:
        print("\nChromaDB server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting ChromaDB server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
