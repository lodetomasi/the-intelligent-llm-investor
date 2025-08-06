"""
Alert Management System
"""

import time
import json
from typing import Dict, List, Optional
from pathlib import Path
from ..utils.logger import get_logger

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.logger = get_logger("AlertManager")
        self.alerts_dir = Path("data/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Alert history
        self.active_alerts = []
        
    def create_alert(self, ticker: str, alert_type: str, 
                    severity: str, data: Dict) -> Dict:
        """
        Create a new alert
        
        Args:
            ticker: Stock ticker
            alert_type: Type of alert
            severity: Alert severity
            data: Alert data
            
        Returns:
            Alert object
        """
        alert = {
            'id': f"{ticker}_{int(time.time())}",
            'ticker': ticker,
            'type': alert_type,
            'severity': severity,
            'timestamp': time.time(),
            'data': data,
            'status': 'ACTIVE'
        }
        
        # Save alert
        self._save_alert(alert)
        
        # Log alert
        self.logger.warning(
            f"ALERT: {severity} {alert_type} for ${ticker} - "
            f"Risk Score: {data.get('risk_score', 'N/A')}"
        )
        
        # Add to active alerts
        self.active_alerts.append(alert)
        
        return alert
        
    def _save_alert(self, alert: Dict):
        """Save alert to file"""
        filename = f"{alert['id']}.json"
        filepath = self.alerts_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(alert, f, indent=2, default=str)
            
    def get_active_alerts(self, ticker: Optional[str] = None) -> List[Dict]:
        """Get active alerts"""
        if ticker:
            return [a for a in self.active_alerts if a['ticker'] == ticker]
        return self.active_alerts