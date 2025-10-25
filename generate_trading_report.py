#!/usr/bin/env python3
"""
Generate a comprehensive trading report for all market opportunities
"""

import csv
import yaml
import os
import random
import math
from calculate_prices import *

def load_calculated_prices():
    """Load calculated prices from cache and ore prices"""
    prices = {}
    
    # Load main item cache
    try:
        with open('item_cache.yaml', 'r') as f:
            cache = yaml.safe_load(f) or {}
            for item, price_data in cache.items():
                if isinstance(price_data, dict):
                    price = price_data.get('price')
                else:
                    price = price_data
                
                if price is not None and price > 0:
                    prices[item] = price
    except FileNotFoundError:
        pass
    
    # Load ore prices
    try:
        with open('ore_prices.yaml', 'r') as f:
            ore_prices = yaml.safe_load(f) or {}
            for item, price in ore_prices.items():
                if price > 0:
                    prices[item] = price
                    prices[item.lower()] = price
    except FileNotFoundError:
        pass
    
    return prices

def calculate_regional_variation(base_price, planet_id, item_name):
    """Calculate regional price variation for a specific planet and item"""
    seed = hash(f"{planet_id}_{item_name}") % 10000
    random.seed(seed)
    
    variation = random.uniform(0.85, 1.25)
    
    if any(ore in item_name.lower() for ore in ['ore', 'pure']):
        variation = 1.0 + (variation - 1.0) * 0.5
    elif any(high_end in item_name for high_end in ['Warp', 'CoreUnit', 'Antimatter']):
        variation = 1.0 + (variation - 1.0) * 1.5
    
    variation = max(0.7, min(1.5, variation))
    return base_price * variation

def is_ore_item(item_name):
    """Check if an item is an ore"""
    ore_indicators = ['ore', 'pure']
    return any(ore in item_name.lower() for ore in ore_indicators)

def analyze_planet_markets():
    """Analyze all planet markets and find trading opportunities"""
    
    calculated_prices = load_calculated_prices()
    market_orders_dir = "market_orders_output"
    
    if not os.path.exists(market_orders_dir):
        print(f"❌ Output directory {market_orders_dir} not found. Run the market update script first.")
        return
    
    # Collect all planet data
    planet_data = {}
    planet_files = []
    
    for filename in os.listdir(market_orders_dir):
        if filename.endswith('.csv'):
            planet_id = os.path.splitext(filename)[0]
            planet_file = os.path.join(market_orders_dir, filename)
            planet_files.append(planet_file)
            
            planet_data[planet_id] = {}
            
            with open(planet_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 5:
                        item, sell_orders, sell_price, buy_orders, buy_price = row
                        
                        # Parse prices and orders
                        try:
                            sell_orders = int(sell_orders) if sell_orders else 0
                            sell_price = float(sell_price) if sell_price else 0
                            buy_orders = int(buy_orders) if buy_orders else 0
                            buy_price = float(buy_price) if buy_price else 0
                            
                            planet_data[planet_id][item] = {
                                'sell_orders': sell_orders,
                                'sell_price': sell_price,
                                'buy_orders': buy_orders,
                                'buy_price': buy_price
                            }
                        except (ValueError, IndexError):
                            continue
    
    print(f"Analyzed {len(planet_data)} planets")
    
    # Find trading opportunities
    opportunities = []
    
    # Get all unique items
    all_items = set()
    for planet_items in planet_data.values():
        all_items.update(planet_items.keys())
    
    for item in all_items:
        if item not in calculated_prices:
            continue
            
        base_price = calculated_prices[item]
        
        # Collect price data for this item across all planets
        item_prices = []
        for planet_id, planet_items in planet_data.items():
            if item in planet_items:
                item_data = planet_items[item]
                
                # Check for sell opportunities (this planet sells)
                if item_data['sell_orders'] > 0 and item_data['sell_price'] > 0:
                    item_prices.append({
                        'planet': planet_id,
                        'type': 'sell',
                        'price': item_data['sell_price'],
                        'orders': item_data['sell_orders']
                    })
                
                # Check for buy opportunities (this planet buys)
                if item_data['buy_orders'] > 0 and item_data['buy_price'] > 0:
                    item_prices.append({
                        'planet': planet_id,
                        'type': 'buy',
                        'price': item_data['buy_price'],
                        'orders': item_data['buy_orders']
                    })
        
        # Find trading pairs
        sell_opportunities = [p for p in item_prices if p['type'] == 'sell']
        buy_opportunities = [p for p in item_prices if p['type'] == 'buy']
        
        # For ore items, look for price differences between planets
        if is_ore_item(item) and len(sell_opportunities) >= 2:
            # Find cheapest and most expensive planets
            cheapest = min(sell_opportunities, key=lambda x: x['price'])
            most_expensive = max(sell_opportunities, key=lambda x: x['price'])
            
            if cheapest['planet'] != most_expensive['planet']:
                profit = most_expensive['price'] - cheapest['price']
                profit_percent = (profit / cheapest['price']) * 100
                
                if profit_percent > 5:  # At least 5% profit
                    opportunities.append({
                        'item': item,
                        'type': 'ore_trading',
                        'buy_from': cheapest['planet'],
                        'sell_to': most_expensive['planet'],
                        'buy_price': cheapest['price'],
                        'sell_price': most_expensive['price'],
                        'profit': profit,
                        'profit_percent': profit_percent,
                        'buy_orders': cheapest['orders'],
                        'sell_orders': most_expensive['orders']
                    })
        
        # For other items, look for buy/sell pairs
        else:
            for sell_opp in sell_opportunities:
                for buy_opp in buy_opportunities:
                    if sell_opp['planet'] != buy_opp['planet']:
                        profit = buy_opp['price'] - sell_opp['price']
                        profit_percent = (profit / sell_opp['price']) * 100
                        
                        if profit_percent > 5:  # At least 5% profit
                            opportunities.append({
                                'item': item,
                                'type': 'buy_sell_trading',
                                'buy_from': sell_opp['planet'],
                                'sell_to': buy_opp['planet'],
                                'buy_price': sell_opp['price'],
                                'sell_price': buy_opp['price'],
                                'profit': profit,
                                'profit_percent': profit_percent,
                                'buy_orders': sell_opp['orders'],
                                'sell_orders': buy_opp['orders']
                            })
    
    return opportunities, planet_data, calculated_prices

def generate_detailed_report():
    """Generate a comprehensive trading report"""
    
    print("Generating comprehensive trading report...")
    
    opportunities, planet_data, calculated_prices = analyze_planet_markets()
    
    # Sort opportunities by profit percentage
    opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
    
    # Generate report
    report_lines = []
    report_lines.append("# Dual Universe Market Trading Report")
    report_lines.append(f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Summary
    report_lines.append("## Summary")
    report_lines.append(f"- **Total Planets Analyzed**: {len(planet_data)}")
    report_lines.append(f"- **Total Trading Opportunities**: {len(opportunities)}")
    report_lines.append(f"- **Items with Prices**: {len(calculated_prices)}")
    report_lines.append("")
    
    # Top opportunities
    report_lines.append("## Top Trading Opportunities")
    report_lines.append("")
    
    if opportunities:
        for i, opp in enumerate(opportunities[:20], 1):  # Top 20
            report_lines.append(f"### {i}. {opp['item']} ({opp['type'].replace('_', ' ').title()})")
            report_lines.append(f"- **Route**: {opp['buy_from']} → {opp['sell_to']}")
            report_lines.append(f"- **Buy Price**: {opp['buy_price']:.2f} (Orders: {opp['buy_orders']:,})")
            report_lines.append(f"- **Sell Price**: {opp['sell_price']:.2f} (Orders: {opp['sell_orders']:,})")
            report_lines.append(f"- **Profit**: {opp['profit']:.2f} ({opp['profit_percent']:.1f}%)")
            report_lines.append("")
    else:
        report_lines.append("No significant trading opportunities found.")
        report_lines.append("")
    
    # Planet analysis
    report_lines.append("## Planet Market Analysis")
    report_lines.append("")
    
    for planet_id, planet_items in planet_data.items():
        sell_items = [item for item, data in planet_items.items() if data['sell_orders'] > 0]
        buy_items = [item for item, data in planet_items.items() if data['buy_orders'] > 0]
        
        report_lines.append(f"### Planet {planet_id}")
        report_lines.append(f"- **Items for Sale**: {len(sell_items)}")
        report_lines.append(f"- **Items to Buy**: {len(buy_items)}")
        report_lines.append(f"- **Total Items**: {len(planet_items)}")
        
        # Show top items by price
        if sell_items:
            sell_prices = [(item, planet_items[item]['sell_price']) for item in sell_items if planet_items[item]['sell_price'] > 0]
            sell_prices.sort(key=lambda x: x[1], reverse=True)
            report_lines.append(f"- **Most Expensive Items**: {', '.join([f'{item} ({price:.0f})' for item, price in sell_prices[:3]])}")
        
        if buy_items:
            buy_prices = [(item, planet_items[item]['buy_price']) for item in buy_items if planet_items[item]['buy_price'] > 0]
            buy_prices.sort(key=lambda x: x[1], reverse=True)
            report_lines.append(f"- **Highest Buy Orders**: {', '.join([f'{item} ({price:.0f})' for item, price in buy_prices[:3]])}")
        
        report_lines.append("")
    
    # Item categories
    report_lines.append("## Item Categories")
    report_lines.append("")
    
    ore_opportunities = [opp for opp in opportunities if opp['type'] == 'ore_trading']
    other_opportunities = [opp for opp in opportunities if opp['type'] == 'buy_sell_trading']
    
    report_lines.append(f"### Ore Trading ({len(ore_opportunities)} opportunities)")
    if ore_opportunities:
        for opp in ore_opportunities[:10]:  # Top 10 ore opportunities
            report_lines.append(f"- **{opp['item']}**: {opp['buy_from']} → {opp['sell_to']} ({opp['profit_percent']:.1f}% profit)")
    else:
        report_lines.append("No ore trading opportunities found.")
    report_lines.append("")
    
    report_lines.append(f"### Manufactured Items ({len(other_opportunities)} opportunities)")
    if other_opportunities:
        for opp in other_opportunities[:10]:  # Top 10 other opportunities
            report_lines.append(f"- **{opp['item']}**: {opp['buy_from']} → {opp['sell_to']} ({opp['profit_percent']:.1f}% profit)")
    else:
        report_lines.append("No manufactured item trading opportunities found.")
    report_lines.append("")
    
    # Arbitrage prevention summary
    report_lines.append("## Arbitrage Prevention")
    report_lines.append("")
    report_lines.append("The market system prevents arbitrage by ensuring:")
    report_lines.append("- **Ore items**: Same buy/sell price on each planet (no same-planet arbitrage)")
    report_lines.append("- **Other items**: Either buy OR sell orders on each planet (no same-planet arbitrage)")
    report_lines.append("- **Interplanetary trading**: Price differences between planets create legitimate trading opportunities")
    report_lines.append("")
    
    # Save report
    report_content = "\n".join(report_lines)
    
    with open("trading_report.md", "w") as f:
        f.write(report_content)
    
    print(f"Report saved to: trading_report.md")
    print(f"Found {len(opportunities)} trading opportunities")
    print(f"Analyzed {len(planet_data)} planets")
    
    if opportunities:
        print(f"\nTop 5 Opportunities:")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"   {i}. {opp['item']:20} {opp['buy_from']} → {opp['sell_to']} ({opp['profit_percent']:>5.1f}% profit)")

if __name__ == "__main__":
    generate_detailed_report()

