"""
Excel Export Utility - Export query results to Excel files
"""
import os
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Handles Excel file exports"""
    
    def __init__(self, export_dir: str = "exports"):
        """
        Initialize Excel exporter
        
        Args:
            export_dir: Directory to save Excel files
        """
        self.export_dir = export_dir
        self._ensure_export_dir()
    
    def _ensure_export_dir(self):
        """Create export directory if it doesn't exist"""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            logger.info(f"Created export directory: {self.export_dir}")
    
    def export_to_excel(
        self, 
        data: List[Dict], 
        filename: Optional[str] = None,
        sheet_name: str = "Data"
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Export data to Excel file
        
        Args:
            data: List of dictionaries (query results)
            filename: Optional custom filename (without extension)
            sheet_name: Name of the Excel sheet
        
        Returns:
            (success, file_path, error_message)
        """
        if not data:
            return False, None, "No data to export"
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{timestamp}"
            
            # Ensure .xlsx extension
            if not filename.endswith('.xlsx'):
                filename = f"{filename}.xlsx"
            
            file_path = os.path.join(self.export_dir, filename)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Export to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
            
            logger.info(
                f"Data exported to Excel",
                extra={
                    "file_path": file_path,
                    "rows": len(data),
                    "columns": len(df.columns)
                }
            )
            
            return True, file_path, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Excel export failed: {error_msg}",
                exc_info=True
            )
            return False, None, error_msg
    
    def get_export_url(self, file_path: str) -> str:
        """
        Get URL/path for downloaded file
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            Relative URL path
        """
        # Return relative path from export directory
        if file_path.startswith(self.export_dir):
            return file_path.replace(self.export_dir, "").lstrip("/")
        return file_path


# Global exporter instance
excel_exporter = ExcelExporter()
