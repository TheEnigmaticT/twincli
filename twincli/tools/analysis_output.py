# twincli/tools/analysis_output.py
"""
Analysis output tool for saving reports and deliverables.

Category: documentation
Created: 2025-06-02
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def save_analysis_report(title: str, content: str, source_directory: Optional[str] = None, format: str = "markdown") -> str:
   """
   Save an analysis report to a file, optionally in the same directory as source data.
   
   Args:
       title: Title for the report file
       content: The analysis content
       source_directory: Directory where source files are located (optional)
       format: Output format ("markdown", "txt")
       
   Returns:
       String confirmation with file path and status
   """
   try:
       # Sanitize title for filename
       safe_title = re.sub(r'[^a-zA-Z0-9_\-\s]', '', title)
       safe_title = safe_title.replace(' ', '_')
       safe_title = safe_title.strip('_')  # Remove leading/trailing underscores
       
       if not safe_title:
           safe_title = "analysis_report"
       
       # Determine file extension
       ext = ".md" if format == "markdown" else ".txt"
       
       # Create filename with timestamp
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       filename = f"{safe_title}_{timestamp}{ext}"
       
       # Determine save location
       if source_directory and os.path.exists(source_directory):
           output_path = os.path.join(source_directory, filename)
           location_description = "Same directory as source data"
       else:
           # Fallback to current directory
           output_path = filename
           location_description = "Current directory"
       
       # Create the report content
       report_content = ""
       
       if format == "markdown":
           report_content += f"# {title}\n\n"
           report_content += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
           report_content += "---\n\n"
       else:
           report_content += f"{title}\n"
           report_content += f"{'=' * len(title)}\n\n"
           report_content += f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
           report_content += "-" * 50 + "\n\n"
       
       report_content += content
       
       # Write the file
       with open(output_path, 'w', encoding='utf-8') as f:
           f.write(report_content)
       
       # Get absolute path for display
       abs_path = os.path.abspath(output_path)
       
       return f"""📄 **Analysis Report Saved Successfully**

**File:** {filename}
**Full Path:** {abs_path}
**Format:** {format.title()}
**Location:** {location_description}
**Size:** {len(report_content)} characters

✅ Report is now available for review and sharing.
📂 You can find it alongside your source data for easy reference."""
       
   except PermissionError as e:
       return f"❌ Permission denied - cannot write to the specified location: {e}"
   except FileNotFoundError as e:
       return f"❌ Directory not found: {e}"
   except Exception as e:
       return f"❌ Failed to save analysis report: {e}"


def save_data_summary(data_description: str, key_metrics: dict, insights: list, source_files: list, output_directory: Optional[str] = None) -> str:
   """
   Save a structured data analysis summary with metrics and insights.
   
   Args:
       data_description: Description of the analyzed data
       key_metrics: Dictionary of key metrics (name: value)
       insights: List of key insights discovered
       source_files: List of source file names/paths
       output_directory: Directory to save the summary (optional)
       
   Returns:
       String confirmation with file path
   """
   try:
       # Create structured content
       timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       
       content = f"""# Data Analysis Summary

**Analysis Date:** {timestamp}
**Data Source:** {data_description}

## Source Files
"""
       
       for i, file in enumerate(source_files, 1):
           content += f"{i}. `{file}`\n"
       
       content += "\n## Key Metrics\n\n"
       
       for metric_name, metric_value in key_metrics.items():
           content += f"- **{metric_name}:** {metric_value}\n"
       
       content += "\n## Key Insights\n\n"
       
       for i, insight in enumerate(insights, 1):
           content += f"{i}. {insight}\n"
       
       content += f"\n---\n*Report generated automatically on {timestamp}*"
       
       # Use save_analysis_report to handle the file creation
       title = f"Data_Summary_{data_description.replace(' ', '_')}"
       return save_analysis_report(title, content, output_directory, "markdown")
       
   except Exception as e:
       return f"❌ Failed to save data summary: {e}"


# Tool registration for TwinCLI
save_analysis_report_metadata = {
   "function": save_analysis_report,
   "name": "save_analysis_report",
   "description": "Save analysis reports and deliverables to files, optionally in the same directory as source data",
   "category": "documentation",
   "parameters": {
       "type": "object",
       "properties": {
           "title": {
               "type": "string",
               "description": "Title for the report file"
           },
           "content": {
               "type": "string",
               "description": "The analysis content to save"
           },
           "source_directory": {
               "type": "string",
               "description": "Directory where source files are located (optional)"
           },
           "format": {
               "type": "string",
               "description": "Output format: 'markdown' or 'txt' (default: markdown)"
           }
       },
       "required": ["title", "content"]
   }
}

save_data_summary_metadata = {
   "function": save_data_summary,
   "name": "save_data_summary", 
   "description": "Save a structured data analysis summary with metrics and insights",
   "category": "documentation",
   "parameters": {
       "type": "object",
       "properties": {
           "data_description": {
               "type": "string",
               "description": "Description of the analyzed data"
           },
           "key_metrics": {
               "type": "object",
               "description": "Dictionary of key metrics (name: value pairs)"
           },
           "insights": {
               "type": "array",
               "items": {"type": "string"},
               "description": "List of key insights discovered"
           },
           "source_files": {
               "type": "array", 
               "items": {"type": "string"},
               "description": "List of source file names/paths"
           },
           "output_directory": {
               "type": "string",
               "description": "Directory to save the summary (optional)"
           }
       },
       "required": ["data_description", "key_metrics", "insights", "source_files"]
   }
}