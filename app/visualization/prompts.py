"""
Visualization Prompts for PandasAI
IMPORTANT: These prompts ONLY request visualization, NOT analysis
"""
from typing import Dict, Any


def get_correlation_prompt(stats: Dict[str, Any]) -> str:
    """
    Generate prompt for correlation scatter plot
    
    Args:
        stats: Statistical analysis results with x_variable, y_variable
    """
    x_var = stats.get("x_variable", "x")
    y_var = stats.get("y_variable", "y")
    
    return f"""
Create a scatter plot showing the relationship between {x_var} and {y_var}.

Requirements:
- X-axis: {x_var}
- Y-axis: {y_var}
- Clear labels and title
- Professional styling
- Do NOT calculate statistics (already done)
- Just visualize the data points clearly
"""


def get_comparison_prompt(intent: Dict[str, Any], stats: Dict[str, Any]) -> str:
    """
    Generate prompt for comparison bar chart (e.g., top customers, top products)
    
    Args:
        intent: Query intent with entities and metrics
        stats: Statistical analysis results
    """
    group_by = stats.get("group_by", "category")
    metric = stats.get("metric", "value")
    
    return f"""
Create a professional bar chart comparing {metric} across different {group_by}.

Requirements:
- Bar chart with horizontal or vertical bars (choose best for data readability)
- X-axis: {group_by} (with clear labels)
- Y-axis: {metric} (with clear axis label)
- Sort bars in descending order (highest first)
- Bold, descriptive title
- Professional color scheme (use gradient or distinct colors)
- Include value labels on bars for clarity
- Clean grid lines
- Professional fonts (size 12+ for labels, 14+ for title)
- Chart size: 12x7 inches
- High quality output (100+ DPI)
- Do NOT calculate statistics (already done)
- Focus on clear, professional, publication-ready visualization
"""


def get_trend_prompt(intent: Dict[str, Any], stats: Dict[str, Any]) -> str:
    """
    Generate prompt for trend line chart
    
    Args:
        intent: Query intent
        stats: Statistical analysis results with metric
    """
    metric = stats.get("metric", "value")
    
    return f"""
Create a professional line chart showing {metric} over time or sequence.

CRITICAL REQUIREMENTS:
- X-axis: Time/Sequence (convert to datetime if needed, sort chronologically)
- Y-axis: {metric}
- Sort data by time/sequence BEFORE plotting
- Clear labels and title
- Professional styling
- Chart size: 12x7 inches
- High DPI: 100+ for crisp output
- Professional fonts (size 12+ for labels, 14+ for axis labels, 16+ for title)

IMPORTANT:
- Do NOT use idxmax() or idxmin() on datetime columns
- Use numeric indices or iloc for accessing rows by position
- If you need to annotate max/min values, use: df.loc[df['{metric}'].idxmax()] for the row, then access the datetime column
- Do NOT calculate statistics (already done)
- Just visualize the trend clearly
- Use markers on data points for clarity
- Include grid lines for readability
"""


def get_aggregate_prompt(stats: Dict[str, Any]) -> str:
    """
    Generate prompt for aggregate statistics chart (e.g., top N rankings)
    
    Args:
        stats: Statistical analysis results with metric
    """
    metric = stats.get("metric", "value")
    
    return f"""
Create a professional, publication-ready bar chart showing the data sorted by {metric} in descending order.

CRITICAL REQUIREMENTS:
- Bar chart format (horizontal if many categories, vertical if few)
- Sort by {metric} from highest to lowest (top values first)
- X-axis: Category/Name labels (rotate if needed for readability)
- Y-axis: {metric} values with clear axis label
- Bold, descriptive title (size 16+) that explains what the chart shows
- Professional color scheme (use gradient or distinct colors, avoid bright red/green together)
- Include value labels on top of each bar for exact numbers
- Clean, subtle grid lines (light gray, alpha=0.3)
- Professional fonts: Sans-serif, size 12+ for labels, 14+ for axis labels, 16+ for title
- Chart size: 12 inches width x 7 inches height
- High DPI: 100+ for crisp output
- Remove unnecessary borders and decorations
- Ensure all text is readable and not overlapping
- Add proper spacing between elements
- Use professional color palette (seaborn/matplotlib professional themes)

STYLING:
- Clean white background or light gray grid
- Professional color gradient or distinct palette
- Subtle shadows/effects if appropriate
- Clear separation between bars
- Professional legend if needed

Do NOT calculate statistics or add analysis text - only create the visualization.
Focus on clear, professional, publication-ready chart that looks like it came from a data analysis tool.
"""


def build_visualization_prompt(
    visualization_type: str,
    intent: Dict[str, Any],
    stats: Dict[str, Any]
) -> str:
    """
    Build appropriate visualization prompt based on type
    
    Args:
        visualization_type: Type of chart (scatter, bar, line, etc.)
        intent: Query intent
        stats: Statistical analysis results
    
    Returns:
        Prompt string for PandasAI
    """
    if visualization_type == "scatter":
        return get_correlation_prompt(stats)
    elif visualization_type == "bar":
        if intent.get("type") == "comparison":
            return get_comparison_prompt(intent, stats)
        else:
            return get_aggregate_prompt(stats)
    elif visualization_type == "line":
        return get_trend_prompt(intent, stats)
    else:
        # Default prompt
        return f"""
Create a clear, professional chart visualizing the data.
Use appropriate chart type for the data structure.
Include clear labels and title.
"""
