#!/usr/bin/env python3
"""
Update market prices in CSV file based on calculated prices from calculate_prices.py
"""

import csv
import yaml
import json
from calculate_prices import *

def load_calculated_prices():
    """Load calculated prices from the output file"""
    prices = {}
    
    # Try to load from cache first (faster)
    try:
        with open('item_cache.yaml', 'r') as f:
            cache = yaml.safe_load(f) or {}
            # Filter out None values and base materials
            for item, price_data in cache.items():
                # Handle both old format (number) and new format (dict with price)
                if isinstance(price_data, dict):
                    price = price_data.get('price')
                else:
                    price = price_data
                
                if price is not None and price > 0:
                    prices[item] = price
        print(f"Loaded {len(prices)} prices from cache")
        return prices
    except FileNotFoundError:
        pass
    
    # Fallback: parse from output file
    try:
        with open('output_new.txt', 'r') as f:
            in_prices_section = False
            for line in f:
                line = line.strip()
                if line == "=== Calculated Prices ===":
                    in_prices_section = True
                    continue
                elif line.startswith("⚠️ Failed") or line.startswith("📝"):
                    break
                elif in_prices_section and line:
                    parts = line.split()
                    if len(parts) >= 2:
                        item = parts[0]
                        try:
                            price = float(parts[1])
                            prices[item] = price
                        except ValueError:
                            continue
        print(f"📁 Loaded {len(prices)} prices from output file")
        return prices
    except FileNotFoundError:
        print("❌ No price data found. Run calculate_prices.py first.")
        return {}

def calculate_order_counts(item, calculated_price, recipe_time=0, recipe_complexity=1):
    """Calculate realistic order counts based on item characteristics"""
    
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
    
    # Special cases for high-end items
    if 'WarpBeacon' in item:
        # WarpBeacon should be very rare
        sell_orders = max(1, int(base_sell_orders * 0.01 * price_tier))
        buy_orders = max(10, int(base_buy_orders * 0.1 * price_tier))
    elif 'WarpDrive' in item or 'WarpCell' in item:
        # Other warp items should be rare but not as rare as beacon
        sell_orders = max(5, int(base_sell_orders * 0.05 * price_tier))
        buy_orders = max(50, int(base_buy_orders * 0.3 * price_tier))
    elif 'CoreUnit' in item:
        # Core units should be moderately rare
        sell_orders = max(10, int(base_sell_orders * 0.1 * price_tier))
        buy_orders = max(100, int(base_buy_orders * 0.5 * price_tier))
    else:
        # Regular items
        sell_orders = max(10, int(base_sell_orders * price_tier * time_factor * complexity_factor))
        buy_orders = max(100, int(base_buy_orders * price_tier * time_factor * complexity_factor))
    
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
                # Calculate complexity based on number of inputs
                complexity = len(r.get('in', []))
                return time_val, complexity
    return 0, 1

def update_market_prices(input_csv, output_csv, calculated_prices):
    """Update market prices in CSV file"""
    
    # Load recipes for complexity analysis
    recipes = load_yaml_file('recipes.yaml')
    
    updated_count = 0
    not_found_count = 0
    
    with open(input_csv, 'r') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        for row in reader:
            if len(row) < 5:
                writer.writerow(row)
                continue
                
            item, sell_orders, sell_price, buy_orders, buy_price = row
            
            if item in calculated_prices:
                calculated_price = calculated_prices[item]
                
                # Get recipe info for order count calculation
                recipe_time, complexity = get_recipe_info(item, recipes)
                
                # Calculate new order counts
                new_sell_orders, new_buy_orders = calculate_order_counts(
                    item, calculated_price, recipe_time, complexity
                )
                
                # Set prices with some market spread
                # Sell price should be higher than calculated (seller profit)
                # Buy price should be lower than calculated (buyer savings)
                sell_price = calculated_price * 1.1  # 10% markup
                buy_price = calculated_price * 0.9   # 10% discount
                
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

def main():
    print("🔄 Updating market prices...")
    
    # Load calculated prices
    calculated_prices = load_calculated_prices()
    if not calculated_prices:
        print("❌ No calculated prices found. Run calculate_prices.py first.")
        return
    
    # Update the CSV file
    updated_count, not_found_count = update_market_prices(
        '77.csv', 
        '77_updated.csv', 
        calculated_prices
    )
    
    print(f"Updated {updated_count} items")
    print(f"⚠️  {not_found_count} items not found in calculations (kept original)")
    print(f"Output saved to: 77_updated.csv")
    
    # Show some examples
    print("\nSample updated prices:")
    sample_items = ['WarpDriveSmall', 'WarpBeacon', 'AluminiumPure', 'IronPure']
    with open('77_updated.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 5 and row[0] in sample_items:
                item, sell_orders, sell_price, buy_orders, buy_price = row
                print(f"  {item:20} Sell: {sell_orders:>8} @ {sell_price:>8} | Buy: {buy_orders:>8} @ {buy_price:>8}")

if __name__ == "__main__":
    main()
