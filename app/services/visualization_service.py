"""
Visualization Service - Orchestrates chart generation
"""
from typing import Dict, List, Optional, Any
import logging
import pandas as pd

from app.visualization.pandasai_engine import PandasAIEngine
from app.visualization.prompts import build_visualization_prompt
from app.config import settings

logger = logging.getLogger(__name__)


class VisualizationService:
    """
    Visualization Service
    
    Orchestrates chart generation using PandasAI.
    
    IMPORTANT: This service does NOT make decisions about visualization.
    It only executes visualization based on decisions made by:
    - Statistical Analysis Service (visualization_type)
    - Intent Detection (intent type)
    """
    
    def __init__(self):
        """Initialize Visualization Service"""
        self.pandasai_engine = None
        
        # Initialize PandasAI if available
        if settings.GEMINI_API_KEY:
            try:
                self.pandasai_engine = PandasAIEngine(
                    gemini_api_key=settings.GEMINI_API_KEY
                )
                logger.info(f"PandasAI Engine created, available: {self.pandasai_engine.is_available()}")
            except Exception as e:
                logger.error(f"Failed to create PandasAI Engine: {e}", exc_info=True)
                self.pandasai_engine = None
        else:
            logger.warning("GEMINI_API_KEY not set, PandasAI visualization disabled")
        
        if not self.pandasai_engine or not self.pandasai_engine.is_available():
            logger.warning(
                "PandasAI visualization not available",
                extra={
                    "engine_exists": self.pandasai_engine is not None,
                    "engine_available": self.pandasai_engine.is_available() if self.pandasai_engine else False,
                    "gemini_key_set": bool(settings.GEMINI_API_KEY),
                    "gemini_key_length": len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0
                }
            )
            self._available = False
        else:
            self._available = True
            logger.info(
                "Visualization Service initialized successfully",
                extra={
                    "engine_available": self.pandasai_engine.is_available(),
                    "charts_dir": str(self.pandasai_engine.charts_dir) if self.pandasai_engine else None
                }
            )
    
    def is_available(self) -> bool:
        """Check if visualization is available"""
        return self._available
    
    def generate_chart(
        self,
        data: List[Dict],
        visualization_type: str,
        intent: Dict[str, Any],
        statistical_insights: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate chart based on visualization decision
        
        Args:
            data: Query results data
            visualization_type: Type of chart (scatter, bar, line, etc.)
            intent: Query intent
            statistical_insights: Statistical analysis results
        
        Returns:
            {
                "success": bool,
                "chart": {
                    "type": str,
                    "url": str,
                    "path": str
                },
                "error": Optional[str]
            }
        """
        if not self._available:
            logger.warning(
                "Chart generation attempted but service not available",
                extra={
                    "_available": self._available,
                    "engine_exists": self.pandasai_engine is not None,
                    "engine_available": self.pandasai_engine.is_available() if self.pandasai_engine else False,
                    "visualization_type": visualization_type
                }
            )
            return {
                "success": False,
                "chart": None,
                "error": "Visualization service not available"
            }
        
        if not data or len(data) == 0:
            return {
                "success": False,
                "chart": None,
                "error": "No data to visualize"
            }
        
        if visualization_type == "none" or visualization_type == "table":
            return {
                "success": False,
                "chart": None,
                "error": "No visualization needed for table display"
            }
        
        try:
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Build visualization prompt
            stats = statistical_insights or {}
            prompt = build_visualization_prompt(
                visualization_type=visualization_type,
                intent=intent,
                stats=stats
            )
            
            # Generate chart using PandasAI
            result = self.pandasai_engine.generate_chart(
                df=df,
                prompt=prompt,
                chart_type=visualization_type
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "chart": {
                        "type": visualization_type,
                        "url": result.get("chart_url"),
                        "path": result.get("chart_path")
                    },
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "chart": None,
                    "error": result.get("error", "Chart generation failed")
                }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Visualization service error: {error_msg}",
                extra={"visualization_type": visualization_type},
                exc_info=True
            )
            return {
                "success": False,
                "chart": None,
                "error": f"Visualization error: {error_msg}"
            }


# Global instance
visualization_service = VisualizationService()
