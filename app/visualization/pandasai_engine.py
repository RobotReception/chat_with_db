"""
PandasAI Engine - Chart generation engine
NOTE: This is a RENDERER only, not an analyzer
"""
from typing import Optional, Dict, Any
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

# Configure matplotlib for server-side rendering
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Try to import Seaborn for professional styling
SEABORN_AVAILABLE = False
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Try to import PandasAI (optional dependency)
PANDASAI_AVAILABLE = False
ChatGoogleGenerativeAI = None

try:
    from pandasai import SmartDataframe
    from pandasai.llm import LangchainLLM
    # Try different import paths for Gemini
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info("Successfully imported ChatGoogleGenerativeAI for PandasAI")
    except ImportError as e:
        logger.debug(f"Failed to import ChatGoogleGenerativeAI: {e}")
        try:
            from langchain_google_vertexai import ChatVertexAI
            ChatGoogleGenerativeAI = ChatVertexAI  # Fallback
            logger.info("Using ChatVertexAI as fallback for PandasAI")
        except ImportError as e2:
            logger.debug(f"Failed to import ChatVertexAI: {e2}")
            ChatGoogleGenerativeAI = None
    
    # Check if both are available
    if ChatGoogleGenerativeAI is not None:
        PANDASAI_AVAILABLE = True
        logger.info("PandasAI and ChatGoogleGenerativeAI are available. Chart generation enabled.")
    else:
        logger.warning("PandasAI imported but ChatGoogleGenerativeAI not available. Chart generation disabled.")
except ImportError as e:
    PANDASAI_AVAILABLE = False
    ChatGoogleGenerativeAI = None
    logger.warning(f"PandasAI not installed: {e}. Chart generation will be disabled.")


class PandasAIEngine:
    """
    PandasAI Chart Generation Engine
    
    IMPORTANT: This is a RENDERER only.
    - Does NOT perform statistical analysis
    - Does NOT interpret results
    - Only generates visualizations based on provided instructions
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize PandasAI Engine
        
        Args:
            gemini_api_key: Gemini API key for PandasAI (uses same as main Gemini)
        """
        self._available = PANDASAI_AVAILABLE and gemini_api_key is not None
        self.gemini_api_key = gemini_api_key
        
        if not self._available:
            if not PANDASAI_AVAILABLE:
                logger.warning("PandasAI library not installed or ChatGoogleGenerativeAI not available")
            elif not gemini_api_key:
                logger.warning("Gemini API key not provided for PandasAI")
            else:
                logger.warning(f"PandasAI Engine not available: PANDASAI_AVAILABLE={PANDASAI_AVAILABLE}, gemini_api_key={bool(gemini_api_key)}")
            return
        
        # Create charts directory
        self.charts_dir = Path("charts/generated")
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure professional chart styling
        self._configure_chart_styling()
        
        logger.info("PandasAI Engine initialized")
    
    def _configure_chart_styling(self):
        """Configure professional chart styling with Seaborn if available"""
        if SEABORN_AVAILABLE:
            # Set Seaborn style for professional look
            sns.set_style("whitegrid")
            sns.set_palette("husl")
            logger.info("Seaborn professional styling enabled")
        
        # Configure matplotlib for better quality
        plt.rcParams['figure.figsize'] = (12, 7)  # Larger size
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 100
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titleweight'] = 'bold'
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['legend.framealpha'] = 0.8
        plt.rcParams['legend.fancybox'] = True
        
        logger.info(
            "Chart styling configured",
            extra={
                "seaborn_available": SEABORN_AVAILABLE,
                "figure_size": plt.rcParams['figure.figsize'],
                "dpi": plt.rcParams['figure.dpi']
            }
        )
    
    def is_available(self) -> bool:
        """Check if PandasAI is available"""
        return self._available
    
    def generate_chart(
        self,
        df: pd.DataFrame,
        prompt: str,
        chart_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate chart using PandasAI
        
        IMPORTANT: Prompt should ONLY request visualization, NOT analysis
        
        Args:
            df: DataFrame with data
            prompt: Visualization prompt (chart generation only)
            chart_type: Type of chart (scatter, bar, line, etc.)
        
        Returns:
            {
                "success": bool,
                "chart_path": str,
                "chart_url": str,
                "error": Optional[str]
            }
        """
        if not self._available:
            return {
                "success": False,
                "chart_path": None,
                "chart_url": None,
                "error": "PandasAI not available"
            }
        
        if df.empty or len(df) == 0:
            return {
                "success": False,
                "chart_path": None,
                "chart_url": None,
                "error": "Empty dataframe"
            }
        
        try:
            # Initialize PandasAI with Gemini via LangChain
            # PandasAI 2.0.0 uses LangchainLLM wrapper
            if ChatGoogleGenerativeAI is None:
                return {
                    "success": False,
                    "chart_path": None,
                    "chart_url": None,
                    "error": "ChatGoogleGenerativeAI not available"
                }
            
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.gemini_api_key
            )
            llm = LangchainLLM(langchain_llm=gemini_llm)
            
            # Create SmartDataframe
            sdf = SmartDataframe(
                df,
                config={
                    "llm": llm,
                    "save_charts": True,
                    "save_charts_path": str(self.charts_dir),
                    "verbose": False
                }
            )
            
            # Generate chart (PandasAI will save it automatically)
            response = sdf.chat(prompt)
            
            # Find the latest generated chart
            chart_path = self._find_latest_chart()
            
            if chart_path and chart_path.exists():
                chart_url = f"/charts/generated/{chart_path.name}"
                
                logger.info(
                    f"Chart generated successfully",
                    extra={
                        "chart_type": chart_type,
                        "chart_path": str(chart_path),
                        "rows": len(df)
                    }
                )
                
                return {
                    "success": True,
                    "chart_path": str(chart_path),
                    "chart_url": chart_url,
                    "chart_type": chart_type,
                    "error": None
                }
            else:
                logger.warning("Chart generated but file not found")
                return {
                    "success": False,
                    "chart_path": None,
                    "chart_url": None,
                    "error": "Chart file not found after generation"
                }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Chart generation failed: {error_msg}",
                extra={"chart_type": chart_type},
                exc_info=True
            )
            return {
                "success": False,
                "chart_path": None,
                "chart_url": None,
                "error": f"Chart generation failed: {error_msg}"
            }
    
    def _find_latest_chart(self) -> Optional[Path]:
        """Find the most recently created chart file"""
        if not self.charts_dir.exists():
            return None
        
        # Get all image files
        chart_files = list(self.charts_dir.glob("*.png")) + \
                     list(self.charts_dir.glob("*.jpg")) + \
                     list(self.charts_dir.glob("*.jpeg"))
        
        if not chart_files:
            return None
        
        # Return the most recently modified
        return max(chart_files, key=lambda p: p.stat().st_mtime)


# Global instance (will be initialized in visualization_service)
pandasai_engine = None
