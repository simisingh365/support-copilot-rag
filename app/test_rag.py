"""
Test script for the RAG Customer Support System.

Tests:
- Database initialization
- Document ingestion
- RAG query
- Knowledge listing
- Ticket creation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = "http://localhost:8000"

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_test(test_name):
    """Print test name."""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}TEST: {test_name}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")


def print_pass(message):
    """Print pass message."""
    print(f"{GREEN}✓ PASS: {message}{RESET}")


def print_fail(message):
    """Print fail message."""
    print(f"{RED}✗ FAIL: {message}{RESET}")


def test_api_health():
    """Test API health check."""
    print_test("API Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print_pass("API is healthy")
            return True
        else:
            print_fail(f"API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Could not connect to API: {e}")
        return False


def test_rag_health():
    """Test RAG API health check."""
    print_test("RAG API Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/rag/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"RAG API is healthy - Collection: {data.get('collection_name')}, Count: {data.get('collection_count')}")
            return True
        else:
            print_fail(f"RAG API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Could not connect to RAG API: {e}")
        return False


def test_ingest_document():
    """Test document ingestion."""
    print_test("Document Ingestion")
    
    sample_document = {
        "title": "Test Document",
        "content": "This is a test document for the RAG system. It contains information about refunds. Our refund policy allows returns within 30 days of purchase. Customers can request refunds through the account settings.",
        "category": "Test",
        "tags": ["test", "refund"],
        "chunking_strategy": "fixed_size"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/knowledge/ingest",
            json=sample_document,
            timeout=60
        )
        
        if response.status_code == 201:
            data = response.json()
            print_pass(f"Document ingested successfully - ID: {data.get('document_id')}, Chunks: {data.get('chunks_count')}")
            return data.get('document_id')
        else:
            print_fail(f"Document ingestion failed: {response.json()}")
            return None
    except Exception as e:
        print_fail(f"Error ingesting document: {e}")
        return None


def test_list_documents():
    """Test listing documents."""
    print_test("List Documents")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/knowledge/documents", timeout=10)
        
        if response.status_code == 200:
            documents = response.json()
            print_pass(f"Found {len(documents)} documents")
            for doc in documents:
                print(f"  - {doc['title']} ({doc['chunk_count']} chunks)")
            return True
        else:
            print_fail(f"Failed to list documents: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Error listing documents: {e}")
        return False


def test_rag_query():
    """Test RAG query."""
    print_test("RAG Query")
    
    query_request = {
        "query": "What is the refund policy?",
        "k": 3
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/rag/query",
            json=query_request,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if "answer" not in data:
                print_fail("Response missing 'answer' field")
                return False
            
            if "sources" not in data:
                print_fail("Response missing 'sources' field")
                return False
            
            if "metrics" not in data:
                print_fail("Response missing 'metrics' field")
                return False
            
            # Verify metrics have reasonable values
            metrics = data["metrics"]
            if metrics.get("retrieval_time_ms", 0) < 0:
                print_fail("Invalid retrieval time")
                return False
            
            if metrics.get("response_time_ms", 0) < 0:
                print_fail("Invalid response time")
                return False
            
            print_pass(f"Query successful - Answer length: {len(data['answer'])} chars")
            print(f"  Sources: {len(data['sources'])}")
            print(f"  Retrieval Time: {metrics.get('retrieval_time_ms', 0):.2f} ms")
            print(f"  Response Time: {metrics.get('response_time_ms', 0):.2f} ms")
            print(f"  Total Time: {metrics.get('total_time_ms', 0):.2f} ms")
            return True
        else:
            print_fail(f"RAG query failed: {response.json()}")
            return False
    except Exception as e:
        print_fail(f"Error querying RAG: {e}")
        return False


def test_create_ticket():
    """Test ticket creation."""
    print_test("Create Ticket")
    
    ticket_request = {
        "subject": "Test Ticket",
        "content": "This is a test ticket created by the test script.",
        "priority": "MEDIUM",
        "customer_id": "test_customer_123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/tickets/",
            json=ticket_request,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print_pass(f"Ticket created successfully - ID: {data['id']}")
            return data['id']
        else:
            print_fail(f"Ticket creation failed: {response.json()}")
            return None
    except Exception as e:
        print_fail(f"Error creating ticket: {e}")
        return None


def test_list_tickets():
    """Test listing tickets."""
    print_test("List Tickets")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/tickets/", timeout=10)
        
        if response.status_code == 200:
            tickets = response.json()
            print_pass(f"Found {len(tickets)} tickets")
            for ticket in tickets:
                print(f"  - {ticket['subject']} ({ticket['status']})")
            return True
        else:
            print_fail(f"Failed to list tickets: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Error listing tickets: {e}")
        return False


def test_analytics():
    """Test analytics endpoint."""
    print_test("Analytics Overview")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/overview", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ["total_queries", "avg_retrieval_time_ms", "avg_response_time_ms"]
            for field in required_fields:
                if field not in data:
                    print_fail(f"Response missing '{field}' field")
                    return False
            
            print_pass(f"Analytics retrieved successfully")
            print(f"  Total Queries: {data['total_queries']}")
            print(f"  Avg Retrieval Time: {data['avg_retrieval_time_ms']:.2f} ms")
            print(f"  Avg Response Time: {data['avg_response_time_ms']:.2f} ms")
            return True
        else:
            print_fail(f"Analytics request failed: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Error getting analytics: {e}")
        return False


def test_system_stats():
    """Test system statistics endpoint."""
    print_test("System Statistics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print_pass("System statistics retrieved")
            print(f"  Tickets: {stats.get('tickets', 0)}")
            print(f"  Messages: {stats.get('messages', 0)}")
            print(f"  Documents: {stats.get('documents', 0)}")
            print(f"  Chunks: {stats.get('chunks', 0)}")
            print(f"  Queries: {stats.get('queries', 0)}")
            return True
        else:
            print_fail(f"System stats request failed: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Error getting system stats: {e}")
        return False


def main():
    """Run all tests."""
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}RAG Customer Support System - Test Suite{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    
    # Check if API is running
    print(f"\n{YELLOW}Checking if API is running at {API_BASE_URL}...{RESET}")
    
    if not test_api_health():
        print(f"\n{RED}ERROR: API is not running. Please start the API first:{RESET}")
        print(f"  python app/main.py")
        return
    
    # Run tests
    results = []
    
    results.append(("API Health", test_api_health()))
    results.append(("RAG Health", test_rag_health()))
    results.append(("Document Ingestion", test_ingest_document() is not None))
    results.append(("List Documents", test_list_documents()))
    results.append(("RAG Query", test_rag_query()))
    results.append(("Create Ticket", test_create_ticket() is not None))
    results.append(("List Tickets", test_list_tickets()))
    results.append(("Analytics", test_analytics()))
    results.append(("System Stats", test_system_stats()))
    
    # Print summary
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}TEST SUMMARY{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{GREEN}{'='*60}{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}All tests passed!{RESET}\n")
    else:
        print(f"{RED}Some tests failed. Please review the output above.{RESET}\n")


if __name__ == "__main__":
    main()
