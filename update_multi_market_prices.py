#!/usr/bin/env python3
"""
Update market prices for multiple planets with regional price variations
Creates realistic interplanetary trade opportunities
"""

import csv
import yaml
import os
import random
import math
from calculate_prices import *

# Regional price variation settings
REGIONAL_VARIATION = {
    'min_variation': 0.85,  # 15% below base price
    'max_variation': 1.25,  # 25% above base price
    'trade_profit_range': (0.05, 0.15)  # 5-15% profit potential between planets
}

def load_calculated_prices():
    """Load calculated prices from cache"""
    prices = {}
    
    try:
        with open('item_cache.yaml', 'r') as f:
            cache = yaml.safe_load(f) or {}
            for item, price in cache.items():
                if price is not None and price > 0:
                    prices[item] = price
        print(f"📁 Loaded {len(prices)} prices from cache")
        return prices
    except FileNotFoundError:
        print("❌ No price data found. Run calculate_prices.py first.")
        return {}

def calculate_regional_variation(base_price, planet_id, item_name):
    """Calculate regional price variation for a specific planet and item"""
    
    # Create a deterministic but varied seed based on planet and item
    seed = hash(f"{planet_id}_{item_name}") % 10000
    random.seed(seed)
    
    # Base variation
    variation = random.uniform(REGIONAL_VARIATION['min_variation'], REGIONAL_VARIATION['max_variation'])
    
    # Adjust for item type (some items are more/less affected by regional differences)
    if any(ore in item_name.lower() for ore in ['ore', 'pure']):
        # Raw materials have less variation
        variation = 1.0 + (variation - 1.0) * 0.5
    elif any(high_end in item_name for high_end in ['Warp', 'CoreUnit', 'Antimatter']):
        # High-end items have more variation
        variation = 1.0 + (variation - 1.0) * 1.5
    
    # Ensure variation stays within reasonable bounds
    variation = max(0.7, min(1.5, variation))
    
    return base_price * variation

def calculate_order_counts(item, calculated_price, recipe_time=0, recipe_complexity=1, planet_id=None):
    """Calculate realistic order counts with regional adjustments"""
    
    # Base factors
    base_sell_orders = 1000
    base_buy_orders = 10000
    
    # Adjust based on price tier
    if calculated_price < 100:
        price_tier = 1.0
    elif calculated_price < 1000:
        price_tier = 0.8
    elif calculated_price < 10000:
        price_tier = 0.6
    elif calculated_price < 100000:
        price_tier = 0.4
    else:
        price_tier = 0.2
    
    # Adjust based on production time (longer = rarer)
    time_factor = max(0.1, 1.0 / (1.0 + recipe_time / 1000))
    
    # Adjust based on complexity (more complex = rarer)
    complexity_factor = max(0.1, 1.0 / recipe_complexity)
    
    # Regional adjustments based on planet
    if planet_id:
        # Create deterministic but varied regional factors
        seed = hash(str(planet_id)) % 1000
        random.seed(seed)
        regional_factor = random.uniform(0.5, 1.5)
    else:
        regional_factor = 1.0
    
    # Special cases for high-end items
    if 'WarpBeacon' in item:
        sell_orders = max(1, int(base_sell_orders * 0.01 * price_tier * regional_factor))
        buy_orders = max(10, int(base_buy_orders * 0.1 * price_tier * regional_factor))
    elif 'WarpDrive' in item or 'WarpCell' in item:
        sell_orders = max(5, int(base_sell_orders * 0.05 * price_tier * regional_factor))
        buy_orders = max(50, int(base_buy_orders * 0.3 * price_tier * regional_factor))
    elif 'CoreUnit' in item:
        sell_orders = max(10, int(base_sell_orders * 0.1 * price_tier * regional_factor))
        buy_orders = max(100, int(base_buy_orders * 0.5 * price_tier * regional_factor))
    else:
        sell_orders = max(10, int(base_sell_orders * price_tier * time_factor * complexity_factor * regional_factor))
        buy_orders = max(100, int(base_buy_orders * price_tier * time_factor * complexity_factor * regional_factor))
    
    # Cap at maximum
    sell_orders = min(sell_orders, 200000000)
    buy_orders = min(buy_orders, 200000000)
    
    return sell_orders, buy_orders

def get_recipe_info(item, recipes):
    """Get recipe information for an item"""
    for r in recipes:
        for out in r.get('out', []):
            if item in out:
                time_val = r.get('time', 0)
                complexity = len(r.get('in', []))
                return time_val, complexity
    return 0, 1

def update_planet_market(input_file, output_file, calculated_prices, planet_id):
    """Update market prices for a single planet"""
    
    recipes = load_yaml_file('recipes.yaml')
    updated_count = 0
    not_found_count = 0
    
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        for row in reader:
            if len(row) < 5:
                writer.writerow(row)
                continue
                
            item, sell_orders, sell_price, buy_orders, buy_price = row
            
            if item in calculated_prices:
                base_price = calculated_prices[item]
                
                # Calculate regional variation
                regional_price = calculate_regional_variation(base_price, planet_id, item)
                
                # Get recipe info for order count calculation
                recipe_time, complexity = get_recipe_info(item, recipes)
                
                # Calculate new order counts with regional adjustments
                new_sell_orders, new_buy_orders = calculate_order_counts(
                    item, regional_price, recipe_time, complexity, planet_id
                )
                
                # Set prices with market spread and regional variation
                sell_price = regional_price * 1.1  # 10% markup
                buy_price = regional_price * 0.9   # 10% discount
                
                # Write updated row
                writer.writerow([
                    item,
                    int(new_sell_orders),
                    f"{sell_price:.2f}",
                    int(new_buy_orders),
                    f"{buy_price:.2f}"
                ])
                updated_count += 1
            else:
                # Keep original values for items not in our calculations
                writer.writerow(row)
                not_found_count += 1
    
    return updated_count, not_found_count

def analyze_trade_opportunities(calculated_prices, planet_files):
    """Analyze potential trade opportunities between planets"""
    
    trade_opportunities = []
    
    # Sample a few items to check for trade opportunities
    sample_items = ['AluminiumPure', 'IronPure', 'CarbonPure', 'SiliconPure', 'WarpDriveSmall']
    
    for item in sample_items:
        if item not in calculated_prices:
            continue
            
        base_price = calculated_prices[item]
        prices = []
        
        for planet_file in planet_files:
            planet_id = os.path.splitext(os.path.basename(planet_file))[0]
            regional_price = calculate_regional_variation(base_price, planet_id, item)
            prices.append((planet_id, regional_price))
        
        if prices:
            min_price = min(prices, key=lambda x: x[1])
            max_price = max(prices, key=lambda x: x[1])
            profit_potential = (max_price[1] - min_price[1]) / min_price[1]
            
            if profit_potential > 0.05:  # At least 5% profit potential
                trade_opportunities.append({
                    'item': item,
                    'buy_from': min_price[0],
                    'sell_to': max_price[0],
                    'buy_price': min_price[1] * 0.9,
                    'sell_price': max_price[1] * 1.1,
                    'profit_percent': profit_potential * 100
                })
    
    return trade_opportunities

def main():
    print("🌍 Updating multi-planet market prices...")
    
    # Load calculated prices
    calculated_prices = load_calculated_prices()
    if not calculated_prices:
        print("❌ No calculated prices found. Run calculate_prices.py first.")
        return
    
    # Create output directory
    output_dir = "market_orders_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all planet files
    market_orders_dir = "market_orders"
    planet_files = []
    
    if os.path.exists(market_orders_dir):
        for filename in os.listdir(market_orders_dir):
            if filename.endswith('.csv'):
                planet_files.append(os.path.join(market_orders_dir, filename))
    
    if not planet_files:
        print(f"❌ No CSV files found in {market_orders_dir}")
        return
    
    print(f"📁 Found {len(planet_files)} planet market files")
    
    # Process each planet
    total_updated = 0
    total_not_found = 0
    
    for planet_file in planet_files:
        planet_id = os.path.splitext(os.path.basename(planet_file))[0]
        output_file = os.path.join(output_dir, os.path.basename(planet_file))
        
        print(f"🔄 Processing planet {planet_id}...")
        
        updated_count, not_found_count = update_planet_market(
            planet_file, output_file, calculated_prices, planet_id
        )
        
        total_updated += updated_count
        total_not_found += not_found_count
        
        print(f"   ✅ Updated {updated_count} items, {not_found_count} not found")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Total updated: {total_updated} items")
    print(f"   ⚠️  Total not found: {total_not_found} items")
    print(f"   📁 Output saved to: {output_dir}/")
    
    # Analyze trade opportunities
    print(f"\n💰 Trade Opportunities:")
    opportunities = analyze_trade_opportunities(calculated_prices, planet_files)
    
    if opportunities:
        for opp in opportunities[:5]:  # Show top 5 opportunities
            print(f"   {opp['item']:15} Buy from {opp['buy_from']:>6} @ {opp['buy_price']:>8.2f} → Sell to {opp['sell_to']:>6} @ {opp['sell_price']:>8.2f} ({opp['profit_percent']:>5.1f}% profit)")
        
        if len(opportunities) > 5:
            print(f"   ... and {len(opportunities) - 5} more opportunities")
    else:
        print("   No significant trade opportunities found")
    
    print(f"\n🎯 Ready to copy files from {output_dir}/ to your server!")

if __name__ == "__main__":
    main()
