"""
Momentum Pattern Analyst - Analyzes pump patterns without ticker focus
"""

import json
import requests
from typing import Dict, List, Any
from datetime import datetime
import os

from ..utils.logger import get_logger

class MomentumAnalyst:
    """Analyzes momentum patterns and pump indicators"""
    
    def __init__(self):
        self.logger = get_logger("MomentumAnalyst")
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model = "anthropic/claude-3.5-sonnet"
        
    def analyze_momentum_cluster(self, cluster_data: Dict) -> Dict[str, Any]:
        """Analyze a momentum cluster for pump patterns"""
        
        prompt = f"""You are an expert at detecting cryptocurrency and stock pump & dump schemes.
Analyze this momentum cluster for pump indicators WITHOUT mentioning specific tickers.

MOMENTUM CLUSTER DATA:
- Theme: {cluster_data.get('theme', 'Unknown')}
- Total Events: {len(cluster_data.get('events', []))}
- Platforms Involved: {cluster_data.get('platform_diversity', 0)}
- Total Momentum Score: {cluster_data.get('total_momentum', 0)}

Sample Events (first 5 for better asset detection):
"""
        
        # Add sample events with content preview
        for i, event in enumerate(cluster_data.get('events', [])[:5]):
            content = event.get('content', {})
            
            # Extract text preview based on event type
            text_preview = ""
            if event.get('type') == 'reddit_surge':
                title = content.get('title', '')[:100]
                text_preview = f"Title: {title}"
            elif event.get('type') == 'stocktwits_burst':
                if isinstance(content, list) and content:
                    text_preview = f"Sample message: {content[0].get('body', '')[:100]}"
            
            prompt += f"""
Event {i+1}:
- Platform: {event.get('platform')}
- Momentum Score: {event.get('momentum_score', 0):.1f}
- Type: {event.get('type')}
- Preview: {text_preview}
"""
            
        prompt += """

IMPORTANT: Extract ALL company names, cryptocurrency names, or asset names mentioned in the content.
Look for:
- Company names (e.g., "GameStop", "AMC Entertainment", "Tesla")
- Cryptocurrency names (e.g., "Bitcoin", "Ethereum", "Dogecoin")
- Any other tradeable assets mentioned
- Both formal names and common abbreviations (but NOT ticker symbols)

ANALYZE FOR:
1. Asset Identification
   - What specific companies/cryptos/assets are being discussed?
   - How many times is each asset mentioned?
   - Are they using code names or euphemisms?

2. Coordination Patterns
   - Is there evidence of coordinated posting across platforms?
   - Are the events clustered in time?
   - Do they share similar language/talking points?

3. Content Patterns
   - What specific pump language is being used?
   - Are there urgency indicators ("NOW", "MOON", "DON'T MISS")?
   - Promises of unrealistic returns?

4. Account Patterns
   - New account activity indicators?
   - Bot-like behavior patterns?
   - Copy-paste content?

5. Risk Assessment
   - Pump probability (0-100%)
   - Primary red flags
   - Type of pump (penny stock, crypto, squeeze play, etc.)
   - Which specific assets are being pumped?

Provide response in JSON format:
{
    "pump_probability": <0-100>,
    "pump_type": "crypto_pump|penny_stock|squeeze_play|earnings_pump|other",
    "coordination_score": <0-10>,
    "urgency_indicators": ["list", "of", "indicators"],
    "red_flags": ["specific", "concerning", "patterns"],
    "time_sensitivity": "immediate|hours|days",
    "recommended_action": "high_alert|monitor|normal",
    "detected_assets": ["company/crypto/stock names mentioned - NOT ticker symbols, actual names"],
    "asset_mentions": {
        "asset_name": "number of mentions",
        "another_asset": "number of mentions"
    },
    "analysis_summary": "Brief explanation of findings including which specific assets are being pumped"
}
"""

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                try:
                    if '```json' in content:
                        json_str = content.split('```json')[1].split('```')[0].strip()
                    else:
                        json_str = content
                    
                    return json.loads(json_str)
                except:
                    self.logger.error(f"Failed to parse JSON from response")
                    return {
                        "pump_probability": 0,
                        "error": "Failed to parse analysis"
                    }
            else:
                self.logger.error(f"API error: {response.status_code}")
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            return {"error": str(e)}
            
    def analyze_platform_patterns(self, platform_data: Dict[str, float]) -> Dict[str, Any]:
        """Analyze cross-platform momentum patterns"""
        
        prompt = f"""Analyze these platform activity patterns for pump & dump indicators:

PLATFORM MOMENTUM DATA:
"""
        for platform, momentum in platform_data.items():
            prompt += f"- {platform}: {momentum:.1f} momentum score\n"
            
        prompt += """

ANALYZE:
1. Platform Coordination
   - Which platforms show simultaneous activity?
   - Is there a clear origination point?
   - Pattern of spread across platforms?

2. Activity Type
   - Organic discussion vs coordinated campaign
   - Natural momentum vs artificial pump
   - Community-driven vs manipulated

3. Risk Indicators
   - Cross-platform coordination level (0-10)
   - Artificial inflation indicators
   - Bot activity probability

Respond in JSON:
{
    "coordination_level": <0-10>,
    "origination_platform": "platform_name",
    "spread_pattern": "organic|coordinated|bot_driven",
    "artificial_indicators": ["list", "of", "indicators"],
    "risk_assessment": "low|medium|high|extreme",
    "confidence": <0-100>
}
"""

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    if '```json' in content:
                        json_str = content.split('```json')[1].split('```')[0].strip()
                    else:
                        json_str = content
                    
                    return json.loads(json_str)
                except:
                    return {"error": "Failed to parse platform analysis"}
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Platform analysis error: {e}")
            return {"error": str(e)}
            
    def generate_detailed_report(self, full_analysis: Dict) -> str:
        """Generate a detailed momentum report without ticker references"""
        
        prompt = f"""Generate a detailed pump & dump risk report based on this momentum analysis.
DO NOT mention any specific ticker symbols.

ANALYSIS DATA:
- Total momentum events: {full_analysis.get('momentum_events', 0)}
- Theme clusters: {full_analysis.get('clusters_found', 0)}
- Top theme: {full_analysis.get('top_theme', 'Unknown')}
- High risk patterns: {full_analysis.get('high_risk_patterns', 0)}

Theme Breakdown:
"""
        
        for theme, data in full_analysis.get('theme_breakdown', {}).items():
            prompt += f"- {theme}: {data['count']} events, {data['total_momentum']:.1f} momentum\n"
            
        prompt += f"""

Platform Activity:
"""
        for platform, momentum in full_analysis.get('platform_momentum', {}).items():
            prompt += f"- {platform}: {momentum:.1f} momentum score\n"
            
        prompt += """

Generate a report with:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FINDINGS (3-5 bullet points)
3. RISK ASSESSMENT
   - Overall risk level
   - Primary concerns
   - Suspicious patterns
4. RECOMMENDED ACTIONS
   - For traders
   - For monitoring
5. DETAILED OBSERVATIONS
   - Theme analysis
   - Platform patterns
   - Timing analysis

Keep it professional but accessible. Focus on patterns and behaviors, not specific assets.
"""

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error generating report: {response.status_code}"
                
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            return f"Error generating report: {str(e)}"