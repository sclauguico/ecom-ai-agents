from pydantic import BaseModel, Field
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from tool_snowflake import SnowflakeTools
import json
import os
from dotenv import load_dotenv
import logging

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisState(BaseModel):
    """State model for the analysis workflow using Pydantic"""
    query: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    analysis: str = ""
    recommendations: str = ""
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    needs_more_data: bool = False
    data_requests: List[str] = Field(default_factory=list)
    iteration_count: int = 0
    
    class Config:
        arbitrary_types_allowed = True

class EcommerceAgents:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.tools = SnowflakeTools()
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def data_extractor(self, state: AnalysisState) -> Dict[str, Any]:
        """Extract data from Snowflake based on query analysis"""
        print("\n[DATA EXTRACTOR AGENT]")
        
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.dict()
        existing_data = state_dict.get("data", {})
        
        if state_dict.get("data_requests"):
            context = f"Additional data requested: {', '.join(state_dict['data_requests'])}"
        else:
            context = f"Initial query: {state_dict['query']}"
        
        prompt = f"""
        {context}
        
        Available data functions:
        - get_sales_metrics(days): Revenue, orders, avg order value
        - get_top_products(limit): Top products by revenue
        - get_customer_segments(): Customer segmentation
        - get_sales_trend(days): Daily sales data for LINE CHARTS
        - get_revenue_by_category(): Revenue breakdown by category for PIE/BAR CHARTS
        - get_monthly_comparison(months): Monthly revenue comparison for BAR CHARTS
        - get_customer_lifetime_value(limit): Top customers by LTV
        
        Current data: {list(existing_data.keys())}
        
        Determine what data to fetch. Be specific about parameters.
        For chart queries, fetch the appropriate chart data sources.
        """
        
        try:
            response = self.llm.invoke(prompt)
            decision = response.content.lower()
            
            logger.info(f"Data extractor decision: {decision}")
            
            # Parse decision and fetch data
            if "sales" in decision or "revenue" in decision or "metrics" in decision:
                days = 30
                if "90" in decision or "ninety" in decision:
                    days = 90
                elif "60" in decision or "sixty" in decision:
                    days = 60
                elif "7" in decision or "seven" in decision or "week" in decision:
                    days = 7
                
                if "sales_metrics" not in existing_data:
                    existing_data["sales_metrics"] = self.tools.get_sales_metrics(days)
                    logger.info(f"Fetched sales metrics for {days} days")
            
            if "trend" in decision or "line" in decision or "time series" in decision or "daily" in decision:
                days = 30
                if "90" in decision: days = 90
                elif "60" in decision: days = 60
                elif "7" in decision: days = 7
                
                if "sales_trend" not in existing_data:
                    existing_data["sales_trend"] = self.tools.get_sales_trend(days)
                    logger.info(f"Fetched sales trend for {days} days")
            
            if "product" in decision or "top" in decision:
                limit = 10
                if "20" in decision or "twenty" in decision:
                    limit = 20
                elif "5" in decision or "five" in decision:
                    limit = 5
                
                if "top_products" not in existing_data:
                    existing_data["top_products"] = self.tools.get_top_products(limit)
                    logger.info(f"Fetched top {limit} products")
            
            if "category" in decision or "categories" in decision or "breakdown" in decision:
                if "revenue_by_category" not in existing_data:
                    existing_data["revenue_by_category"] = self.tools.get_revenue_by_category()
                    logger.info("Fetched revenue by category")
            
            if "monthly" in decision or "month" in decision or "comparison" in decision:
                months = 6
                if "12" in decision: months = 12
                elif "3" in decision: months = 3
                
                if "monthly_comparison" not in existing_data:
                    existing_data["monthly_comparison"] = self.tools.get_monthly_comparison(months)
                    logger.info(f"Fetched monthly comparison for {months} months")
            
            if "customer" in decision and "segment" in decision:
                if "customer_segments" not in existing_data:
                    existing_data["customer_segments"] = self.tools.get_customer_segments()
                    logger.info("Fetched customer segments")
            
            if "lifetime" in decision or "ltv" in decision or "top customer" in decision:
                limit = 10
                if "20" in decision: limit = 20
                elif "5" in decision: limit = 5
                
                if "customer_lifetime_value" not in existing_data:
                    existing_data["customer_lifetime_value"] = self.tools.get_customer_lifetime_value(limit)
                    logger.info(f"Fetched top {limit} customers by LTV")
            
            # Default data if nothing fetched
            if not existing_data and state_dict.get("iteration_count", 0) == 0:
                logger.info("No specific data requested, fetching default dataset with chart data")
                existing_data = {
                    "sales_metrics": self.tools.get_sales_metrics(30),
                    "top_products": self.tools.get_top_products(10),
                    "sales_trend": self.tools.get_sales_trend(30)
                }
            
        except Exception as e:
            logger.error(f"Error in data_extractor: {str(e)}")
            if not existing_data:
                existing_data = {
                    "sales_metrics": self.tools.get_sales_metrics(30),
                    "sales_trend": self.tools.get_sales_trend(30)
                }
        
        # Return dict updates for LangGraph
        return {
            "data": existing_data,
            "data_requests": [],
            "iteration_count": state_dict.get("iteration_count", 0) + 1
        }
    
    def analyst(self, state: AnalysisState) -> Dict[str, Any]:
        """Analyze data and determine if more data is needed"""
        print("\n[ANALYST AGENT]")
        
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.dict()
        data_str = json.dumps(state_dict["data"], indent=2, default=str)
        
        prompt = f"""
        Query: {state_dict["query"]}
        
        Available Data Structure:
        {data_str}
        
        IMPORTANT: The data keys are at the top level (e.g., "top_products", "sales_trend", "customer_segments").
        Do NOT use nested paths like "top_products.top_products" - use only the top-level key name.
        
        Your tasks:
        1. Determine if you have enough data to answer the query
        2. Provide comprehensive analysis
        3. Recommend appropriate chart visualizations
        
        Available chart types:
        - line: For trends over time
        - bar: For vertical comparisons
        - pie: For proportions/percentages
        - horizontal_bar: For horizontal ranking comparisons
        
        Response format:
        SUFFICIENT: YES or NO
        
        If NO:
        NEEDED: [specific data points needed]
        
        If YES:
        ANALYSIS: [your comprehensive analysis]
        CHARTS: [JSON array of chart configs]
        
        CRITICAL CHART CONFIG RULES:
        1. data_key: Use ONLY the top-level key name from the data (e.g., "top_products", NOT "top_products.top_products")
        2. x_field: ALWAYS the categorical/label field name (e.g., "product_name", "date", "segment")
        3. y_fields: ALWAYS array of numeric field names (e.g., ["total_revenue"], ["customer_count"])
        4. For pie charts: use name_field and value_field instead of x_field and y_fields
        
        Chart Examples:
        {{
            "type": "horizontal_bar",
            "title": "Top Products by Revenue",
            "data_key": "top_products",
            "x_field": "product_name",
            "y_fields": ["total_revenue"],
            "description": "Revenue ranking"
        }}
        
        {{
            "type": "pie",
            "title": "Revenue by Category",
            "data_key": "revenue_by_category",
            "name_field": "category",
            "value_field": "revenue",
            "description": "Category distribution"
        }}
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content
            
            logger.info(f"Analyst response preview: {content[:200]}...")
            
            updates = {}
            
            if "SUFFICIENT: NO" in content:
                updates["needs_more_data"] = True
                if "NEEDED:" in content:
                    needed_section = content.split("NEEDED:")[1]
                    if "ANALYSIS:" in needed_section:
                        needed_section = needed_section.split("ANALYSIS:")[0]
                    
                    data_requests = [line.strip().lstrip("- •").strip() 
                                for line in needed_section.split("\n") 
                                if line.strip() and not line.startswith("SUFFICIENT")]
                    updates["data_requests"] = data_requests
                    logger.info(f"Analyst requesting more data: {data_requests}")
                
                updates["analysis"] = "Gathering additional data based on analysis needs..."
                updates["charts"] = []
            else:
                updates["needs_more_data"] = False
                updates["data_requests"] = []
                
                # Extract analysis
                if "ANALYSIS:" in content:
                    analysis_part = content.split("ANALYSIS:")[1]
                    if "CHARTS:" in analysis_part:
                        updates["analysis"] = analysis_part.split("CHARTS:")[0].strip()
                    else:
                        updates["analysis"] = analysis_part.strip()
                else:
                    updates["analysis"] = content.replace("SUFFICIENT: YES", "").strip()
                
                # Extract and generate charts
                updates["charts"] = self._extract_charts(content, state_dict["data"])
                logger.info(f"Generated {len(updates['charts'])} charts")
            
            return updates
        
        except Exception as e:
            logger.error(f"Error in analyst: {str(e)}")
            return {
                "needs_more_data": False,
                "analysis": f"Analysis based on available data: {list(state_dict['data'].keys())}",
                "charts": self._generate_default_charts(state_dict["data"])
            }
    
    def _extract_charts(self, content: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract chart configurations from analyst response"""
        charts = []
        
        if "CHARTS:" in content:
            try:
                charts_section = content.split("CHARTS:")[1].strip()
                # Try to parse JSON
                if "[" in charts_section:
                    # Extract JSON array
                    start_idx = charts_section.index("[")
                    bracket_count = 0
                    end_idx = start_idx
                    
                    for i, char in enumerate(charts_section[start_idx:], start_idx):
                        if char == "[":
                            bracket_count += 1
                        elif char == "]":
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_idx = i + 1
                                break
                    
                    charts_json = charts_section[start_idx:end_idx]
                    charts = json.loads(charts_json)
                    logger.info(f"Parsed {len(charts)} charts from analyst response")
                    return charts
            except Exception as e:
                logger.warning(f"Failed to parse charts from response: {str(e)}")
        
        # Fallback: Generate charts based on available data
        logger.info("Using default chart generation")
        return self._generate_default_charts(data)
    
    def _generate_default_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default chart configurations based on available data"""
        charts = []
        
        # Line chart for sales trend
        if "sales_trend" in data and data["sales_trend"].get("sales_trend"):
            charts.append({
                "type": "line",
                "title": "Sales Trend Over Time",
                "data_key": "sales_trend",
                "x_field": "date",
                "y_fields": ["revenue"],
                "description": "Daily revenue trend"
            })
            logger.info("Added sales trend line chart")
        
        # Bar chart for top products
        if "top_products" in data and data["top_products"].get("top_products"):
            charts.append({
                "type": "horizontal_bar",
                "title": "Top Products by Revenue",
                "data_key": "top_products",
                "x_field": "product_name",
                "y_fields": ["total_revenue"],
                "description": "Product performance comparison"
            })
            logger.info("Added top products bar chart")
        
        # Pie chart for revenue by category
        if "revenue_by_category" in data and data["revenue_by_category"].get("revenue_by_category"):
            charts.append({
                "type": "pie",
                "title": "Revenue Distribution by Category",
                "data_key": "revenue_by_category",
                "name_field": "category",
                "value_field": "revenue",
                "description": "Category revenue breakdown"
            })
            logger.info("Added revenue by category pie chart")
        
        # Bar chart for monthly comparison
        if "monthly_comparison" in data and data["monthly_comparison"].get("monthly_comparison"):
            charts.append({
                "type": "bar",
                "title": "Monthly Revenue Comparison",
                "data_key": "monthly_comparison",
                "x_field": "month",
                "y_fields": ["revenue"],
                "description": "Month-over-month revenue performance"
            })
            logger.info("Added monthly comparison bar chart")
        
        # Horizontal bar for customer segments
        if "customer_segments" in data and data["customer_segments"].get("customer_segments"):
            charts.append({
                "type": "horizontal_bar",
                "title": "Customer Segments Distribution",
                "data_key": "customer_segments",
                "x_field": "segment",
                "y_fields": ["customer_count"],
                "description": "Customer distribution across segments"
            })
            logger.info("Added customer segments horizontal bar chart")
        
        print("=" * 50)
        print("CHARTS BEING RETURNED:")
        for chart in charts:
            print(json.dumps(chart, indent=2))
        print("=" * 50)
        return charts
    
    def consultant(self, state: AnalysisState) -> Dict[str, Any]:
        """Generate actionable recommendations"""
        print("\n[CONSULTANT AGENT]")
        
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.dict()
        
        prompt = f"""
        Original Query: {state_dict["query"]}
        
        Analysis:
        {state_dict["analysis"]}
        
        Based on this analysis, provide 3-5 actionable business recommendations.
        
        Format your response as:
        1. [Recommendation]: [Specific action with expected impact]
        2. [Recommendation]: [Specific action with expected impact]
        3. [Recommendation]: [Specific action with expected impact]
        
        Focus on:
        - Practical, implementable actions
        - Expected business impact
        - Specific metrics to improve
        """
        
        try:
            response = self.llm.invoke(prompt)
            logger.info("Consultant provided recommendations")
            return {"recommendations": response.content}
        except Exception as e:
            logger.error(f"Error in consultant: {str(e)}")
            return {"recommendations": "Unable to generate recommendations. Please review the analysis."}
    
    def should_continue(self, state: AnalysisState) -> str:
        """Decide whether to fetch more data or proceed to consultant"""
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.dict()
        
        if state_dict.get("iteration_count", 0) > 3:
            logger.warning("Max iterations reached, proceeding to consultant")
            return "consultant"
        
        if state_dict.get("needs_more_data") and len(state_dict.get("data_requests", [])) > 0:
            logger.info("Analyst requested more data, returning to extractor")
            return "data_extractor"
        
        logger.info("Proceeding to consultant for recommendations")
        return "consultant"
    
    def _build_graph(self):
        """Build the workflow graph"""
        workflow = StateGraph(AnalysisState)
        
        workflow.add_node("data_extractor", self.data_extractor)
        workflow.add_node("analyst", self.analyst)
        workflow.add_node("consultant", self.consultant)
        
        workflow.set_entry_point("data_extractor")
        workflow.add_edge("data_extractor", "analyst")
        
        workflow.add_conditional_edges(
            "analyst",
            self.should_continue,
            {
                "data_extractor": "data_extractor",
                "consultant": "consultant"
            }
        )
        
        workflow.add_edge("consultant", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def analyze(self, query: str, thread_id: str = "default") -> Dict[str, Any]:
        """Main entry point for analysis"""
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = AnalysisState(
            query=query,
            data={},
            analysis="",
            recommendations="",
            charts=[],
            needs_more_data=False,
            data_requests=[],
            iteration_count=0
        )
        
        logger.info(f"Starting analysis for query: {query}")
        
        result = self.graph.invoke(initial_state, config=config)
        
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
        
        logger.info(f"Analysis complete. Iterations: {result_dict.get('iteration_count', 0)}, Charts: {len(result_dict.get('charts', []))}")
        
        return {
            "query": result_dict["query"],
            "data": result_dict["data"],
            "analysis": result_dict["analysis"],
            "recommendations": result_dict["recommendations"],
            "charts": result_dict.get("charts", [])
        }