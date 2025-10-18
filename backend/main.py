from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from langgraph_agents import EcommerceAgents
from tool_snowflake import SnowflakeTools
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="E-commerce AI Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agents = EcommerceAgents()
tools = SnowflakeTools()
executor = ThreadPoolExecutor(max_workers=4)

class AnalysisRequest(BaseModel):
    query: str

class QuickInsight(BaseModel):
    metric: str
    value: str
    trend: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ecommerce-ai-agents"}

@app.get("/quick-insights")
async def get_quick_insights():
    def get_insights():
        sales = tools.get_sales_metrics(30)
        products = tools.get_top_products(3)
        segments = tools.get_customer_segments()
        
        return [
            QuickInsight(
                metric="Total Revenue (30 days)",
                value=f"${sales['total_revenue']:,.2f}",
                trend=f"{sales['total_orders']} orders"
            ),
            QuickInsight(
                metric="Top Product",
                value=products['top_products'][0]['product_name'] if products['top_products'] else "N/A",
                trend=f"${products['top_products'][0]['total_revenue']:,.2f}" if products['top_products'] else "N/A"
            ),
            QuickInsight(
                metric="Active Customers",
                value=str(sum(seg['customer_count'] for seg in segments['customer_segments'])),
                trend="Across all segments"
            )
        ]
    
    loop = asyncio.get_event_loop()
    insights = await loop.run_in_executor(executor, get_insights)
    return {"insights": insights}

@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    def run_analysis():
        return agents.analyze(request.query)
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_analysis)
    
    print(f"DEBUG: Charts in result: {result.get('charts', [])}")
    
    return {
        "analysis_id": "temp_id",
        "query": result["query"],
        "status": "completed",
        "results": {
            "data": result["data"],
            "analysis": result["analysis"],
            "recommendations": result["recommendations"],
            "charts": result.get("charts", [])
        }
    }
    
@app.get("/analyze/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    return {"analysis_id": analysis_id, "status": "completed"}

if __name__ == "__main__":
    print("Starting E-commerce AI Agents API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)