"""
Data Saver - Saves scraped data and LLM responses for analysis
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import pandas as pd
from ..utils.logger import get_logger

class DataSaver:
    """Saves all scraped data and LLM analysis for review"""
    
    def __init__(self, base_dir: str = "pump_data"):
        self.logger = get_logger("DataSaver")
        self.base_dir = Path(base_dir)
        
        # Create directory structure
        self.scraped_dir = self.base_dir / "scraped"
        self.llm_dir = self.base_dir / "llm_responses"
        self.reports_dir = self.base_dir / "reports"
        
        for dir_path in [self.scraped_dir, self.llm_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def save_scraped_data(self, ticker: str, source: str, data: Any) -> str:
        """Save raw scraped data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{source}_{timestamp}.json"
        filepath = self.scraped_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'ticker': ticker,
                    'source': source,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2, ensure_ascii=False, default=str)
                
            self.logger.info(f"Saved scraped data to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving scraped data: {e}")
            return ""
            
    def save_llm_analysis(self, ticker: str, analysis: Dict[str, Any], 
                         model: str = "claude-opus-4") -> str:
        """Save LLM analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_analysis_{timestamp}.json"
        filepath = self.llm_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'ticker': ticker,
                    'model': model,
                    'timestamp': datetime.now().isoformat(),
                    'analysis': analysis
                }, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved LLM analysis to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving LLM analysis: {e}")
            return ""
            
    def save_pump_report(self, results: Dict[str, Any]) -> str:
        """Save comprehensive pump detection report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pump_report_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        try:
            # Save full JSON report
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                
            # Also save summary CSV for easy viewing
            if 'analyzed_candidates' in results:
                csv_filename = f"pump_summary_{timestamp}.csv"
                csv_filepath = self.reports_dir / csv_filename
                
                # Extract key fields for CSV
                summary_data = []
                for candidate in results['analyzed_candidates']:
                    summary_data.append({
                        'ticker': candidate.get('ticker'),
                        'pump_probability': candidate.get('pump_probability'),
                        'risk_level': candidate.get('risk_level'),
                        'confidence': candidate.get('confidence'),
                        'social_mentions': candidate.get('raw_metrics', {}).get('social_mentions', 0),
                        'key_findings': '; '.join(candidate.get('key_findings', [])[:3])
                    })
                    
                df = pd.DataFrame(summary_data)
                df.to_csv(csv_filepath, index=False)
                self.logger.info(f"Saved summary CSV to {csv_filepath}")
                
            self.logger.info(f"Saved pump report to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving pump report: {e}")
            return ""
            
    def save_social_media_batch(self, platform: str, posts: List[Dict[str, Any]]) -> str:
        """Save batch of social media posts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_batch_{timestamp}.json"
        filepath = self.scraped_dir / platform / filename
        
        # Create platform subdirectory
        filepath.parent.mkdir(exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'platform': platform,
                    'timestamp': datetime.now().isoformat(),
                    'post_count': len(posts),
                    'posts': posts
                }, f, indent=2, ensure_ascii=False, default=str)
                
            self.logger.info(f"Saved {len(posts)} {platform} posts to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving social media batch: {e}")
            return ""
            
    def get_saved_data_summary(self) -> Dict[str, Any]:
        """Get summary of all saved data"""
        summary = {
            'scraped_files': 0,
            'llm_analyses': 0,
            'reports': 0,
            'total_size_mb': 0,
            'latest_files': []
        }
        
        try:
            # Count files
            scraped_files = list(self.scraped_dir.rglob("*.json"))
            llm_files = list(self.llm_dir.glob("*.json"))
            report_files = list(self.reports_dir.glob("*"))
            
            summary['scraped_files'] = len(scraped_files)
            summary['llm_analyses'] = len(llm_files)
            summary['reports'] = len(report_files)
            
            # Calculate total size
            total_size = 0
            all_files = scraped_files + llm_files + report_files
            for file in all_files:
                total_size += file.stat().st_size
                
            summary['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Get latest files
            all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            summary['latest_files'] = [str(f) for f in all_files[:10]]
            
        except Exception as e:
            self.logger.error(f"Error getting data summary: {e}")
            
        return summary
        
    def cleanup_old_data(self, days: int = 7):
        """Clean up data older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days * 86400)
        deleted_count = 0
        
        try:
            for dir_path in [self.scraped_dir, self.llm_dir]:
                for file in dir_path.rglob("*.json"):
                    if file.stat().st_mtime < cutoff_time:
                        file.unlink()
                        deleted_count += 1
                        
            self.logger.info(f"Deleted {deleted_count} old files")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")