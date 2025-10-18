import sys
import os
import json
from pathlib import Path

# Add parent directory (backend) to path to import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from langgraph_agents import EcommerceAgents

def test_agents():
    """Test the agents with various queries"""
    agents = EcommerceAgents()
    
    # Test 1: Simple sales query
    print("=" * 50)
    print("Test 1: Sales Query")
    print("=" * 50)
    result = agents.analyze("What are the sales trends for the last 30 days?")
    
    print(f"Query: {result['query']}")
    print(f"Data fetched: {list(result['data'].keys())}")
    print(f"Analysis: {result['analysis'][:500]}...")
    print(f"Recommendations: {result['recommendations'][:500]}...")
    
    # Test 2: Complex query that might need multiple data sources
    print("\n" + "=" * 50)
    print("Test 2: Complex Query")
    print("=" * 50)
    result = agents.analyze("How are our top products performing and what customer segments are buying them?")
    
    print(f"Query: {result['query']}")
    print(f"Data fetched: {list(result['data'].keys())}")
    print(f"Analysis: {result['analysis'][:500]}...")

if __name__ == "__main__":
    test_agents()