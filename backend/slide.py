




state = {"query": "Top products?", "data": {}, "analysis": "", "recommendations": "", 
         "charts": [], "needs_more_data": False, "iteration_count": 0}

from pydantic import BaseModel, Field
from typing import Dict, Any, List

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
