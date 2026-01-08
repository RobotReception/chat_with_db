"""
Statistical Analysis Service - Converts data into actionable insights
Code-based analysis (no LLM) for production-ready statistical insights
"""
from typing import Dict, List, Optional, Tuple, Any
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Visualization mapping based on intent type
VISUALIZATION_MAP = {
    "correlation": "scatter",
    "comparison": "bar",
    "trend": "line",
    "aggregate": "bar",
    "list": "table",
    "unknown": "table"
}


class StatisticalAnalysisService:
    """Performs statistical analysis on query results"""
    
    def analyze(
        self, 
        data: List[Dict], 
        intent: Dict[str, Any],
        question: str
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis based on intent
        
        Returns:
            {
                "has_analysis": bool,
                "analysis_type": str,
                "statistical_result": dict,
                "interpretation": str,
                "visualization_type": str
            }
        """
        if not data or not isinstance(data, list) or len(data) == 0:
            return {
                "has_analysis": False,
                "analysis_type": None,
                "statistical_result": {},
                "interpretation": None,
                "visualization_type": "none"
            }
        
        intent_type = intent.get('type', 'unknown')
        
        # Convert to DataFrame for analysis
        try:
            df = pd.DataFrame(data)
        except Exception as e:
            logger.warning(f"Failed to convert data to DataFrame: {e}")
            return {
                "has_analysis": False,
                "analysis_type": None,
                "statistical_result": {},
                "interpretation": None,
                "visualization_type": "none"
            }
        
        # Route to appropriate analysis
        if intent_type == "correlation":
            return self._analyze_correlation(df, intent, question)
        elif intent_type == "comparison":
            return self._analyze_comparison(df, intent, question)
        elif intent_type == "trend":
            return self._analyze_trend(df, intent, question)
        elif intent_type == "aggregate":
            return self._analyze_aggregate(df, intent, question)
        else:
            return {
                "has_analysis": False,
                "analysis_type": None,
                "statistical_result": {},
                "interpretation": None,
                "visualization_type": self._suggest_visualization(intent_type, df)
            }
    
    def _analyze_correlation(
        self, 
        df: pd.DataFrame, 
        intent: Dict, 
        question: str
    ) -> Dict[str, Any]:
        """Analyze correlation between variables"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {
                "has_analysis": False,
                "analysis_type": "correlation",
                "statistical_result": {},
                "interpretation": "لا توجد أعمدة رقمية كافية لتحليل الارتباط",
                "visualization_type": "scatter"
            }
        
        # Try to find relevant columns based on intent metrics
        metrics = intent.get('metrics', [])
        x_col, y_col = self._identify_correlation_columns(df, numeric_cols, metrics)
        
        if not x_col or not y_col:
            # Use first two numeric columns
            x_col, y_col = numeric_cols[0], numeric_cols[1]
        
        try:
            # Calculate Pearson correlation
            correlation = df[x_col].corr(df[y_col])
            
            # Remove NaN values for calculation
            clean_df = df[[x_col, y_col]].dropna()
            if len(clean_df) < 3:
                return {
                    "has_analysis": False,
                    "analysis_type": "correlation",
                    "statistical_result": {},
                    "interpretation": "لا توجد بيانات كافية لتحليل الارتباط",
                    "visualization_type": "scatter"
                }
            
            correlation = clean_df[x_col].corr(clean_df[y_col])
            
            if pd.isna(correlation):
                correlation = 0.0
            
            # Interpret correlation
            strength, direction = self._interpret_correlation(correlation)
            
            # Generate interpretation text
            interpretation = self._generate_correlation_interpretation(
                correlation, strength, direction, x_col, y_col
            )
            
            return {
                "has_analysis": True,
                "analysis_type": "correlation",
                "statistical_result": {
                    "correlation_coefficient": round(correlation, 3),
                    "strength": strength,
                    "direction": direction,
                    "x_variable": x_col,
                    "y_variable": y_col,
                    "sample_size": len(clean_df)
                },
                "interpretation": interpretation,
                "visualization_type": "scatter"
            }
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}", exc_info=True)
            return {
                "has_analysis": False,
                "analysis_type": "correlation",
                "statistical_result": {},
                "interpretation": f"فشل تحليل الارتباط: {str(e)}",
                "visualization_type": "scatter"
            }
    
    def _analyze_comparison(
        self, 
        df: pd.DataFrame, 
        intent: Dict, 
        question: str
    ) -> Dict[str, Any]:
        """Analyze comparison between groups"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if len(numeric_cols) == 0:
            return {
                "has_analysis": False,
                "analysis_type": "comparison",
                "statistical_result": {},
                "interpretation": "لا توجد أعمدة رقمية للمقارنة",
                "visualization_type": "bar"
            }
        
        # Find the metric column and group column
        metric_col = numeric_cols[0] if numeric_cols else None
        group_col = text_cols[0] if text_cols else None
        
        if not metric_col:
            return {
                "has_analysis": False,
                "analysis_type": "comparison",
                "statistical_result": {},
                "interpretation": "لا توجد بيانات رقمية للمقارنة",
                "visualization_type": "bar"
            }
        
        try:
            if group_col:
                # Group comparison
                grouped = df.groupby(group_col)[metric_col].agg(['mean', 'sum', 'count'])
                max_group = grouped['mean'].idxmax() if len(grouped) > 0 else None
                min_group = grouped['mean'].idxmin() if len(grouped) > 0 else None
                
                interpretation = self._generate_comparison_interpretation(
                    grouped, max_group, min_group, metric_col, group_col
                )
                
                return {
                    "has_analysis": True,
                    "analysis_type": "comparison",
                    "statistical_result": {
                        "groups": grouped.to_dict(),
                        "highest": max_group,
                        "lowest": min_group,
                        "metric": metric_col,
                        "group_by": group_col
                    },
                    "interpretation": interpretation,
                    "visualization_type": "bar"
                }
            else:
                # Simple comparison (min/max/avg)
                avg_val = df[metric_col].mean()
                max_val = df[metric_col].max()
                min_val = df[metric_col].min()
                
                interpretation = f"متوسط {metric_col}: {avg_val:.2f}, الحد الأقصى: {max_val:.2f}, الحد الأدنى: {min_val:.2f}"
                
                return {
                    "has_analysis": True,
                    "analysis_type": "comparison",
                    "statistical_result": {
                        "average": round(avg_val, 2),
                        "maximum": round(max_val, 2),
                        "minimum": round(min_val, 2),
                        "metric": metric_col
                    },
                    "interpretation": interpretation,
                    "visualization_type": "bar"
                }
        except Exception as e:
            logger.error(f"Comparison analysis failed: {e}", exc_info=True)
            return {
                "has_analysis": False,
                "analysis_type": "comparison",
                "statistical_result": {},
                "interpretation": f"فشل تحليل المقارنة: {str(e)}",
                "visualization_type": "bar"
            }
    
    def _analyze_trend(
        self, 
        df: pd.DataFrame, 
        intent: Dict, 
        question: str
    ) -> Dict[str, Any]:
        """Analyze trends over time or sequence"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        if len(numeric_cols) == 0:
            return {
                "has_analysis": False,
                "analysis_type": "trend",
                "statistical_result": {},
                "interpretation": "لا توجد بيانات رقمية لتحليل الاتجاه",
                "visualization_type": "line"
            }
        
        try:
            metric_col = numeric_cols[0]
            
            # Simple trend: check if values are increasing/decreasing
            values = df[metric_col].dropna().tolist()
            if len(values) < 2:
                return {
                    "has_analysis": False,
                    "analysis_type": "trend",
                    "statistical_result": {},
                    "interpretation": "لا توجد بيانات كافية لتحليل الاتجاه",
                    "visualization_type": "line"
                }
            
            # Calculate trend direction
            first_half = np.mean(values[:len(values)//2])
            second_half = np.mean(values[len(values)//2:])
            
            trend_direction = "increasing" if second_half > first_half else "decreasing"
            trend_strength = abs(second_half - first_half) / first_half if first_half != 0 else 0
            
            interpretation = self._generate_trend_interpretation(
                trend_direction, trend_strength, metric_col
            )
            
            return {
                "has_analysis": True,
                "analysis_type": "trend",
                "statistical_result": {
                    "direction": trend_direction,
                    "strength": round(trend_strength, 3),
                    "metric": metric_col,
                    "first_half_avg": round(first_half, 2),
                    "second_half_avg": round(second_half, 2)
                },
                "interpretation": interpretation,
                "visualization_type": "line"
            }
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}", exc_info=True)
            return {
                "has_analysis": False,
                "analysis_type": "trend",
                "statistical_result": {},
                "interpretation": f"فشل تحليل الاتجاه: {str(e)}",
                "visualization_type": "line"
            }
    
    def _analyze_aggregate(
        self, 
        df: pd.DataFrame, 
        intent: Dict, 
        question: str
    ) -> Dict[str, Any]:
        """Analyze aggregate statistics"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) == 0:
            return {
                "has_analysis": False,
                "analysis_type": "aggregate",
                "statistical_result": {},
                "interpretation": "لا توجد بيانات رقمية للإحصائيات",
                "visualization_type": "table"
            }
        
        try:
            metric_col = numeric_cols[0]
            stats = df[metric_col].describe()
            
            def _safe_num(v: Any) -> Optional[float]:
                try:
                    fv = float(v)
                    if not np.isfinite(fv):
                        return None
                    return fv
                except Exception:
                    return None

            mean_v = _safe_num(stats.get("mean"))
            median_v = _safe_num(stats.get("50%"))
            std_v = _safe_num(stats.get("std"))
            min_v = _safe_num(stats.get("min"))
            max_v = _safe_num(stats.get("max"))
            count_v = stats.get("count")

            interpretation = (
                f"إحصائيات {metric_col}: "
                f"المتوسط {mean_v:.2f}، الوسيط {median_v:.2f}، الانحراف المعياري {(std_v if std_v is not None else 0.0):.2f}"
            )
            
            return {
                "has_analysis": True,
                "analysis_type": "aggregate",
                "statistical_result": {
                    "mean": round(mean_v, 2) if mean_v is not None else None,
                    "median": round(median_v, 2) if median_v is not None else None,
                    "std": round(std_v, 2) if std_v is not None else None,
                    "min": round(min_v, 2) if min_v is not None else None,
                    "max": round(max_v, 2) if max_v is not None else None,
                    "count": int(count_v) if count_v is not None else 0,
                    "metric": metric_col
                },
                "interpretation": interpretation,
                "visualization_type": "bar"
            }
        except Exception as e:
            logger.error(f"Aggregate analysis failed: {e}", exc_info=True)
            return {
                "has_analysis": False,
                "analysis_type": "aggregate",
                "statistical_result": {},
                "interpretation": f"فشل التحليل الإحصائي: {str(e)}",
                "visualization_type": "table"
            }
    
    def _identify_correlation_columns(
        self, 
        df: pd.DataFrame, 
        numeric_cols: List[str], 
        metrics: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Identify which columns to use for correlation"""
        if len(numeric_cols) < 2:
            return None, None
        
        # Try to match metrics to column names
        x_col, y_col = None, None
        
        for metric in metrics:
            for col in numeric_cols:
                if metric.lower() in col.lower() or col.lower() in metric.lower():
                    if not x_col:
                        x_col = col
                    elif not y_col:
                        y_col = col
                        break
        
        # If not found, use first two columns
        if not x_col or not y_col:
            x_col, y_col = numeric_cols[0], numeric_cols[1]
        
        return x_col, y_col
    
    def _interpret_correlation(self, value: float) -> Tuple[str, str]:
        """Interpret correlation coefficient"""
        abs_value = abs(value)
        
        if abs_value < 0.2:
            strength = "very_weak"
        elif abs_value < 0.4:
            strength = "weak"
        elif abs_value < 0.6:
            strength = "moderate"
        elif abs_value < 0.8:
            strength = "strong"
        else:
            strength = "very_strong"
        
        direction = "positive" if value >= 0 else "negative"
        
        return strength, direction
    
    def _generate_correlation_interpretation(
        self, 
        correlation: float, 
        strength: str, 
        direction: str,
        x_col: str,
        y_col: str
    ) -> str:
        """Generate human-readable interpretation"""
        strength_ar = {
            "very_weak": "ضعيفة جداً",
            "weak": "ضعيفة",
            "moderate": "متوسطة",
            "strong": "قوية",
            "very_strong": "قوية جداً"
        }
        
        direction_ar = {
            "positive": "موجبة",
            "negative": "سالبة"
        }
        
        strength_text = strength_ar.get(strength, strength)
        direction_text = direction_ar.get(direction, direction)
        
        interpretation = (
            f"📊 التحليل الإحصائي يظهر أن معامل الارتباط بين {x_col} و {y_col} هو **{correlation:.3f}**.\n\n"
            f"🔍 هذا يشير إلى **علاقة {strength_text}** ({direction_text})، "
        )
        
        if abs(correlation) < 0.3:
            interpretation += f"مما يعني أن {x_col} **ليس عاملًا مؤثرًا بشكل واضح** على {y_col}."
        elif abs(correlation) < 0.6:
            interpretation += f"مما يعني أن {x_col} له **تأثير متوسط** على {y_col}."
        else:
            interpretation += f"مما يعني أن {x_col} له **تأثير قوي** على {y_col}."
        
        return interpretation
    
    def _generate_comparison_interpretation(
        self,
        grouped: pd.DataFrame,
        max_group: Optional[str],
        min_group: Optional[str],
        metric_col: str,
        group_col: str
    ) -> str:
        """Generate comparison interpretation"""
        if max_group is None or min_group is None:
            return f"تم تحليل المقارنة بين المجموعات المختلفة لـ {metric_col}."
        
        max_val = grouped.loc[max_group, 'mean']
        min_val = grouped.loc[min_group, 'mean']
        
        interpretation = (
            f"📊 التحليل المقارن يظهر أن:\n\n"
            f"• **{max_group}** لديه أعلى قيمة في {metric_col} بمتوسط **{max_val:.2f}**\n"
            f"• **{min_group}** لديه أقل قيمة في {metric_col} بمتوسط **{min_val:.2f}**\n\n"
        )
        
        if max_val > 0:
            ratio = (max_val - min_val) / max_val * 100
            interpretation += f"🔍 الفرق بين الأعلى والأقل هو **{ratio:.1f}%**."
        
        return interpretation
    
    def _generate_trend_interpretation(
        self,
        direction: str,
        strength: float,
        metric_col: str
    ) -> str:
        """Generate trend interpretation"""
        direction_ar = {
            "increasing": "تصاعدي",
            "decreasing": "تنازلي"
        }
        
        direction_text = direction_ar.get(direction, direction)
        strength_pct = strength * 100
        
        interpretation = (
            f"📈 التحليل يظهر **اتجاه {direction_text}** في {metric_col}.\n\n"
            f"🔍 قوة الاتجاه: **{strength_pct:.1f}%** "
        )
        
        if strength < 0.1:
            interpretation += "(اتجاه ضعيف)"
        elif strength < 0.3:
            interpretation += "(اتجاه متوسط)"
        else:
            interpretation += "(اتجاه قوي)"
        
        return interpretation
    
    def _suggest_visualization(self, intent_type: str, df: pd.DataFrame) -> str:
        """Suggest visualization type based on intent and data"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if intent_type == "correlation" and len(numeric_cols) >= 2:
            return "scatter"
        elif intent_type == "comparison":
            if text_cols and numeric_cols:
                return "bar"
            elif numeric_cols:
                return "bar"
            else:
                return "table"
        elif intent_type == "trend":
            return "line"
        elif intent_type == "aggregate":
            return "bar" if numeric_cols else "table"
        else:
            return "table"


# Global instance
statistical_analysis_service = StatisticalAnalysisService()
