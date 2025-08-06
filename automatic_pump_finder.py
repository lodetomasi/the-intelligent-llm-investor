#!/usr/bin/env python3
"""
Automatic Pump Finder - Main entry point
Finds pump & dump schemes automatically without ticker input
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scanners.social_pump_scanner import SocialPumpScanner
from src.utils.logger import get_logger

logger = get_logger("AutomaticPumpFinder")

def main():
    """Main entry point for automatic pump finder"""
    
    parser = argparse.ArgumentParser(
        description='Automatic Pump & Dump Finder - No ticker input required!'
    )
    
    parser.add_argument(
        '--min-mentions',
        type=int,
        default=10,
        help='Minimum social mentions to consider (default: 10)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top candidates to find (default: 10)'
    )
    
    parser.add_argument(
        '--analyze',
        type=int,
        default=5,
        help='Number to analyze with AI (default: 5)'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Run in continuous monitoring mode'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Check interval in minutes for monitoring (default: 15)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("     🚀 AUTOMATIC PUMP & DUMP FINDER")
    print("     No ticker input required - finds pumps automatically!")
    print("="*80 + "\n")
    
    scanner = SocialPumpScanner()
    
    if args.monitor:
        # Continuous monitoring mode
        print("🔴 Starting continuous pump monitoring...")
        print(f"├─ Check interval: {args.interval} minutes")
        print(f"├─ Min mentions: {args.min_mentions}")
        print(f"└─ Analyzing top {args.analyze} candidates\n")
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            scanner.monitor_live_pumps(check_interval_minutes=args.interval)
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
            
    else:
        # Single scan mode
        print("🔍 Scanning social media for pump & dump activity...")
        print(f"├─ Minimum mentions: {args.min_mentions}")
        print(f"├─ Finding top: {args.top} candidates")
        print(f"└─ AI analysis for: top {args.analyze}\n")
        
        print("Scanning platforms:")
        print("  • Reddit (wallstreetbets, pennystocks, etc.)")
        print("  • 4chan /biz/")
        print("  • InvestorsHub")
        print("  • StockTwits")
        print("  • BitcoinTalk (for crypto)\n")
        
        try:
            results = scanner.find_pump_candidates(
                min_mentions=args.min_mentions,
                top_n=args.top,
                analyze_top=args.analyze
            )
            
            # Display results
            print(f"\n✅ Scan completed in {results['scan_duration_seconds']:.1f} seconds!")
            print(f"\n📊 FOUND {results['total_tickers_found']} TOTAL TICKERS")
            print(f"   Active (>{args.min_mentions} mentions): {results['active_tickers']}")
            
            # Show top tickers
            print(f"\n🏆 TOP {len(results['ticker_rankings'])} TRENDING TICKERS:")
            print("-" * 60)
            for ranking in results['ticker_rankings']:
                print(f"  #{ranking['rank']:2} ${ranking['ticker']:6s} - {int(ranking['total_mentions']):3} mentions")
                
            # High risk alerts
            if results['high_risk_alerts']:
                print(f"\n\n🚨 ⚠️  HIGH RISK PUMP ALERTS ⚠️  🚨")
                print("="*60)
                
                for alert in results['high_risk_alerts']:
                    print(f"\n${alert['ticker']} - {alert['risk_level']} RISK")
                    print(f"├─ Pump Probability: {alert['pump_probability']}%")
                    print(f"├─ Confidence: {alert['confidence']}%")
                    
                    if alert.get('key_findings'):
                        print("├─ Key Findings:")
                        for finding in alert['key_findings'][:3]:
                            print(f"│  • {finding}")
                            
                    if alert.get('recommendations'):
                        print("└─ Recommendation: {alert['recommendations'][0]}")
                        
            # All analyzed results
            print(f"\n\n📊 AI ANALYSIS RESULTS (Top {len(results['top_pump_candidates'])}):")
            print("="*60)
            
            for i, candidate in enumerate(results['top_pump_candidates'], 1):
                risk_emoji = "🔴" if candidate['risk_level'] in ['HIGH', 'EXTREME'] else "🟡" if candidate['risk_level'] == 'MEDIUM' else "🟢"
                
                print(f"\n{risk_emoji} #{i} ${candidate['ticker']}")
                print(f"   Pump Probability: {candidate['pump_probability']}%")
                print(f"   Risk Level: {candidate['risk_level']}")
                print(f"   Confidence: {candidate['confidence']}%")
                print(f"   Mentions: {candidate['mention_count']} across {len(candidate['data_sources'])} platforms")
                
                # Timeline info
                if 'timeline_analysis' in candidate:
                    timeline = candidate['timeline_analysis']
                    if timeline.get('current_phase'):
                        print(f"   Phase: {timeline['current_phase']}")
                        
            # Data saved info
            print(f"\n\n💾 ALL DATA SAVED TO:")
            print(f"   • Scraped data: pump_data/scraped/")
            print(f"   • AI analyses: pump_data/llm_responses/")
            print(f"   • Full report: pump_data/reports/")
            
            # Final summary
            high_risk_count = len(results['high_risk_alerts'])
            if high_risk_count > 0:
                print(f"\n\n⚠️  SUMMARY: {high_risk_count} HIGH RISK PUMPS DETECTED!")
                print("   Exercise extreme caution with these tickers.")
            else:
                print(f"\n\n✅ SUMMARY: No high-risk pumps detected in current scan.")
                
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            print(f"\n❌ Error: {e}")
            return 1
            
    print("\n✅ Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())