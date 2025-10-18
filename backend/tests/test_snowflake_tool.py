import sys
import os
import json
from pathlib import Path

# Add parent directory (backend) to path to import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from tool_snowflake import SnowflakeTools

def test_tools():
    tools = SnowflakeTools()
    
    print("Testing sales metrics:")
    sales = tools.get_sales_metrics(30)
    print(json.dumps(sales, indent=2))
    
    print("\nTesting sales trend:")
    trend = tools.get_sales_trend(30)
    print(json.dumps(trend, indent=2))
    
    print("\nTesting revenue by category:")
    categories = tools.get_revenue_by_category()
    print(json.dumps(categories, indent=2))
    
    print("\nTesting monthly comparison:")
    monthly = tools.get_monthly_comparison(6)
    print(json.dumps(monthly, indent=2))
    
    print("\nTesting top products:")
    products = tools.get_top_products(5)
    print(json.dumps(products, indent=2))
    
    print("\nTesting customer segments:")
    segments = tools.get_customer_segments()
    print(json.dumps(segments, indent=2))

if __name__ == "__main__":
    test_tools()