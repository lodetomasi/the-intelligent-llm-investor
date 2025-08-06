#!/usr/bin/env python3
"""
Momentum-Based Pump & Dump Finder

Finds pumps by detecting momentum/hype FIRST, then extracting tickers
No ticker input required - pure momentum detection!
"""

import argparse
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scanners.momentum_pump_scanner import MomentumPumpScanner
from src.utils.logger import get_logger

logger = get_logger("MomentumFinder")

def print_banner():
    """Print startup banner"""
    print("="*80)
    print("     🌊 MOMENTUM-BASED PUMP DETECTOR")
    print("     Finds pumps from momentum patterns, not ticker searches!")
    print("="*80)
    print()

def print_momentum_results(results: dict):
    """Print momentum detection results"""
    
    print(f"\n✅ Scan completed in {results['scan_time']:.1f} seconds!")
    
    print(f"\n📊 MOMENTUM ANALYSIS:")
    print(f"   High-momentum events detected: {results['momentum_events']}")
    print(f"   Theme clusters identified: {results['clusters_found']}")
    
    # Show themes and patterns, NOT tickers
    if 'theme_breakdown' in results:
        print(f"\n🌊 MOMENTUM THEMES DETECTED:")
        print("-"*60)
        for theme, data in results['theme_breakdown'].items():
            if data['count'] > 0:
                momentum_bar = "█" * min(30, int(data['total_momentum'] / 10))
                print(f"   {theme:20s} Events: {data['count']:3d} | Momentum: {momentum_bar}")
    
    # Show platform activity
    if 'platform_momentum' in results:
        print(f"\n📱 PLATFORM ACTIVITY:")
        print("-"*60)
        for platform, momentum in results['platform_momentum'].items():
            activity_bar = "▓" * min(30, int(momentum / 20))
            print(f"   {platform:15s} {activity_bar}")
    
    # Show risk indicators WITHOUT tickers
    if results.get('high_risk_patterns', 0) > 0:
        print(f"\n⚠️  HIGH RISK PATTERNS DETECTED:")
        print(f"   Coordinated activity across {results.get('coordinated_platforms', 0)} platforms")
        print(f"   Unusual volume spikes: {results.get('volume_spikes', 0)}")
        print(f"   New account activity: {results.get('new_account_ratio', 0):.1%}")
        
    print(f"\n💡 INSIGHTS:")
    print(f"   • {results.get('momentum_events', 0)} high-momentum events found")
    print(f"   • Strongest activity in: {results.get('top_theme', 'N/A')} themes")
    print(f"   • Peak momentum time: {results.get('peak_time', 'N/A')}")
    
    if results.get('recommendation'):
        print(f"\n🎯 RECOMMENDATION: {results['recommendation']}")
        
    # Show AI analysis if available
    if 'ai_analysis' in results and results['ai_analysis']:
        print(f"\n🤖 AI ANALYSIS:")
        print("="*60)
        
        # Cluster analyses
        if 'cluster_analyses' in results['ai_analysis']:
            for cluster_analysis in results['ai_analysis']['cluster_analyses']:
                theme = cluster_analysis['theme']
                analysis = cluster_analysis['analysis']
                
                if 'error' not in analysis:
                    print(f"\n📊 {theme.replace('_', ' ').upper()}:")
                    print(f"   Pump Probability: {analysis.get('pump_probability', 0)}%")
                    print(f"   Type: {analysis.get('pump_type', 'Unknown')}")
                    print(f"   Coordination: {analysis.get('coordination_score', 0)}/10")
                    print(f"   Action: {analysis.get('recommended_action', 'monitor')}")
                    
                    # Show detected assets
                    if analysis.get('detected_assets'):
                        print(f"   🎯 Assets Detected: {', '.join(analysis['detected_assets'][:5])}")
                    
                    # Show asset mention counts
                    if analysis.get('asset_mentions'):
                        sorted_assets = sorted(analysis['asset_mentions'].items(), 
                                             key=lambda x: int(x[1]), reverse=True)[:3]
                        if sorted_assets:
                            print(f"   📈 Top Mentions:")
                            for asset, count in sorted_assets:
                                print(f"      • {asset}: {count} mentions")
                    
                    if analysis.get('red_flags'):
                        print(f"   ⚠️ Red Flags: {', '.join(analysis['red_flags'][:3])}")
                        
        # Platform analysis
        if 'platform_analysis' in results['ai_analysis']:
            pa = results['ai_analysis']['platform_analysis']
            if 'error' not in pa:
                print(f"\n🌐 CROSS-PLATFORM ANALYSIS:")
                print(f"   Coordination Level: {pa.get('coordination_level', 0)}/10")
                print(f"   Pattern: {pa.get('spread_pattern', 'Unknown')}")
                print(f"   Risk: {pa.get('risk_assessment', 'Unknown')}")
                
        # Overall assessment
        if 'overall_assessment' in results['ai_analysis']:
            oa = results['ai_analysis']['overall_assessment']
            print(f"\n⚡ OVERALL RISK: {oa.get('risk_level', 'Unknown')}")
            print(f"   Highest Pump Probability: {oa.get('highest_pump_probability', 0)}%")

def main():
    parser = argparse.ArgumentParser(
        description='Find pump & dumps using momentum detection'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=2.0,
        help='Minimum momentum threshold (default: 2.0 = 2x normal)'
    )
    
    parser.add_argument(
        '--hours',
        type=int,
        default=6,
        help='Time window to analyze in hours (default: 6)'
    )
    
    parser.add_argument(
        '--analyze',
        type=int,
        default=5,
        help='Number of top momentum events to analyze (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set!")
        print("\n❌ Please set your OpenRouter API key:")
        print("   export OPENROUTER_API_KEY='your-key-here'")
        return 1
        
    # Show search parameters
    print(f"🔍 Scanning for momentum surges...")
    print(f"├─ Momentum threshold: {args.threshold}x")
    print(f"├─ Time window: {args.hours} hours")
    print(f"└─ Will analyze: top {args.analyze} events")
    print()
    
    print("Scanning platforms:")
    print("  • Reddit (hot & rising posts)")
    print("  • StockTwits (activity bursts)")  
    print("  • 4chan /biz/ (high-reply threads)")
    print()
    
    try:
        # Create scanner
        scanner = MomentumPumpScanner()
        
        # Run momentum detection
        results = scanner.find_momentum_pumps(
            momentum_threshold=args.threshold,
            time_window_hours=args.hours,
            analyze_top=args.analyze
        )
        
        # Display results
        print_momentum_results(results)
        
        print("\n✅ Done!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())