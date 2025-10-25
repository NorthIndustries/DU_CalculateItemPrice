#!/usr/bin/env python3
"""
Generate all market files from scratch using item cache
Creates realistic interplanetary trading opportunities while preventing arbitrage
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

# Basic ores that should only have buy orders (no sell orders)
BASIC_ORES = {
    'carbonore', 'siliconore', 'aluminiumore', 'ironore', 
    'sodiumore', 'calciumore', 'chromiumore', 'copperore'
}

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
        print(f"Loaded {len(prices)} prices from item cache")
    except FileNotFoundError:
        print("⚠️  No item cache found")
        return {}
    
    # Load ore prices
    try:
        with open('ore_prices.yaml', 'r') as f:
            ore_prices = yaml.safe_load(f) or {}
            for item, price in ore_prices.items():
                if price > 0:
                    # Map both original case and lowercase versions
                    prices[item] = price
                    prices[item.lower()] = price
        print(f"Loaded {len(ore_prices)} ore prices")
    except FileNotFoundError:
        print("⚠️  No ore prices found")
    
    print(f"Total loaded: {len(prices)} prices")
    return prices

def get_planet_ids():
    """Get all planet IDs from existing market files"""
    market_orders_dir = "market_orders"
    planet_ids = []
    
    if os.path.exists(market_orders_dir):
        for filename in os.listdir(market_orders_dir):
            if filename.endswith('.csv'):
                planet_id = os.path.splitext(filename)[0]
                planet_ids.append(planet_id)
    
    # Also check output directory for any additional planets
    output_dir = "market_orders_output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith('.csv'):
                planet_id = os.path.splitext(filename)[0]
                if planet_id not in planet_ids:
                    planet_ids.append(planet_id)
    
    return sorted(planet_ids)

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

def is_ore_item(item_name):
    """Check if an item is an ore"""
    ore_indicators = ['ore', 'pure']
    return any(ore in item_name.lower() for ore in ore_indicators)

def is_basic_ore(item_name):
    """Check if an item is a basic ore (buy orders only)"""
    return item_name.lower() in BASIC_ORES

def is_plasma_item(item_name):
    """Check if an item is plasma"""
    return 'plasma' in item_name.lower()

def is_ultra_rare_item(item_name, price):
    """Check if an item is ultra rare (high price, special items)"""
    # High-end items that should be very rare
    ultra_rare_indicators = [
        'WarpBeacon', 'WarpDrive', 'WarpCell', 'CoreUnit', 'Antimatter',
        'Warp', 'Beacon', 'Drive', 'Cell', 'Core'
    ]
    
    # Check for ultra rare indicators or very high price
    has_ultra_rare_indicator = any(indicator in item_name for indicator in ultra_rare_indicators)
    is_very_expensive = price > 50000  # Very high price threshold
    
    return has_ultra_rare_indicator or is_very_expensive

def is_rare_item(item_name, price):
    """Check if an item is rare (medium-high price, special items)"""
    # Medium-high end items that should be somewhat rare
    rare_indicators = [
        'Engine', 'Thruster', 'Shield', 'Weapon', 'Advanced',
        'Large', 'Medium', 'Small', 'XtraSmall'
    ]
    
    # Check for rare indicators or high price
    has_rare_indicator = any(indicator in item_name for indicator in rare_indicators)
    is_expensive = price > 10000  # High price threshold
    
    return has_rare_indicator or is_expensive

def create_global_trading_strategy(all_items, planet_ids, calculated_prices):
    """Create a global trading strategy for all items across all planets"""
    
    item_strategy = {}
    
    for item in all_items:
        if item not in calculated_prices:
            continue
        
        price = calculated_prices[item]
        
        # Plasma items: ULTRA RARE - only one type per planet
        if is_plasma_item(item):
            # Each plasma type appears on only 1-2 planets
            random.seed(hash(item) % 10000)
            available_planets = planet_ids.copy()
            random.shuffle(available_planets)
            
            # Only 1-2 planets have each plasma type
            num_planets = random.randint(1, 2)
            plasma_planets = available_planets[:num_planets]
            
            item_strategy[item] = {
                'type': 'ultra_rare_plasma',
                'planets': plasma_planets
            }
        
        # Ultra rare items: very limited distribution
        elif is_ultra_rare_item(item, price):
            # Ultra rare items appear on only 2-4 planets
            random.seed(hash(item) % 10000)
            available_planets = planet_ids.copy()
            random.shuffle(available_planets)
            
            num_planets = random.randint(2, 4)
            rare_planets = available_planets[:num_planets]
            
            # Split into buyers and sellers
            num_sellers = max(1, num_planets // 2)
            num_buyers = max(1, num_planets - num_sellers)
            
            seller_planets = rare_planets[:num_sellers]
            buyer_planets = rare_planets[num_sellers:num_sellers + num_buyers]
            
            item_strategy[item] = {
                'type': 'ultra_rare_trade',
                'seller_planets': seller_planets,
                'buyer_planets': buyer_planets
            }
        
        # Rare items: limited distribution
        elif is_rare_item(item, price):
            # Rare items appear on 30-50% of planets
            random.seed(hash(item) % 10000)
            available_planets = planet_ids.copy()
            random.shuffle(available_planets)
            
            num_planets = max(2, int(len(available_planets) * random.uniform(0.3, 0.5)))
            rare_planets = available_planets[:num_planets]
            
            # Split into buyers and sellers
            num_sellers = max(1, num_planets // 2)
            num_buyers = max(1, num_planets - num_sellers)
            
            seller_planets = rare_planets[:num_sellers]
            buyer_planets = rare_planets[num_sellers:num_sellers + num_buyers]
            
            item_strategy[item] = {
                'type': 'rare_trade',
                'seller_planets': seller_planets,
                'buyer_planets': buyer_planets
            }
        
        # Basic ores: only buy orders, distributed across planets
        elif is_basic_ore(item):
            # Distribute buy orders across planets (no sell orders)
            random.seed(hash(item) % 10000)
            available_planets = planet_ids.copy()
            random.shuffle(available_planets)
            
            # Each basic ore appears on 60-80% of planets as buy orders
            num_planets = max(1, int(len(available_planets) * random.uniform(0.6, 0.8)))
            buy_planets = available_planets[:num_planets]
            
            item_strategy[item] = {
                'type': 'basic_ore_buy_only',
                'buy_planets': buy_planets
            }
        
        # Other ore items (Pure, etc.): same price on each planet, but different between planets
        elif is_ore_item(item):
            item_strategy[item] = {
                'type': 'ore_interplanetary',
                'planets': planet_ids
            }
        
        # Common manufactured items: normal distribution
        else:
            # Create buy/sell distribution across planets
            random.seed(hash(item) % 10000)
            available_planets = planet_ids.copy()
            random.shuffle(available_planets)
            
            # Split into buyers and sellers
            num_planets = len(available_planets)
            num_sellers = max(1, num_planets // 2)
            num_buyers = max(1, num_planets - num_sellers)
            
            seller_planets = available_planets[:num_sellers]
            buyer_planets = available_planets[num_sellers:num_sellers + num_buyers]
            
            item_strategy[item] = {
                'type': 'multi_planet_trade',
                'seller_planets': seller_planets,
                'buyer_planets': buyer_planets
            }
    
    return item_strategy

def determine_market_role(planet_id, item_name, item_strategy):
    """Determine if this planet should have buy orders, sell orders, or both for this item"""
    
    if item_name not in item_strategy:
        return 'none'
    
    strategy = item_strategy[item_name]
    
    if strategy['type'] == 'ultra_rare_plasma':
        if planet_id in strategy['planets']:
            return 'both_same_price'  # Plasma: same price on each planet, but different between planets
        else:
            return 'none'
    
    elif strategy['type'] == 'ultra_rare_trade':
        if planet_id in strategy['seller_planets']:
            return 'sell_only'
        elif planet_id in strategy['buyer_planets']:
            return 'buy_only'
        else:
            return 'none'
    
    elif strategy['type'] == 'rare_trade':
        if planet_id in strategy['seller_planets']:
            return 'sell_only'
        elif planet_id in strategy['buyer_planets']:
            return 'buy_only'
        else:
            return 'none'
    
    elif strategy['type'] == 'basic_ore_buy_only':
        if planet_id in strategy['buy_planets']:
            return 'buy_only'
        else:
            return 'none'
    
    elif strategy['type'] == 'ore_interplanetary':
        return 'both_same_price'  # Ore items: same price on each planet, but different between planets
    
    elif strategy['type'] == 'multi_planet_trade':
        if planet_id in strategy['seller_planets']:
            return 'sell_only'
        elif planet_id in strategy['buyer_planets']:
            return 'buy_only'
        else:
            return 'none'
    
    return 'none'

def generate_planet_market(planet_id, calculated_prices, item_strategy, recipes):
    """Generate market data for a single planet"""
    
    market_data = []
    
    for item, base_price in calculated_prices.items():
        # Calculate regional variation
        regional_price = calculate_regional_variation(base_price, planet_id, item)
        
        # Get recipe info for order count calculation
        recipe_time, complexity = get_recipe_info(item, recipes)
        
        # Determine market role for this item on this planet
        market_role = determine_market_role(planet_id, item, item_strategy)
        
        if market_role == 'both_same_price':
            # Ore items: both buy and sell at EXACTLY the same price
            new_sell_orders, new_buy_orders = calculate_order_counts(
                item, regional_price, recipe_time, complexity, planet_id
            )
            
            # CRITICAL: Same price for both (no profit margin possible)
            same_price = regional_price
            
            market_data.append([
                item,
                int(new_sell_orders),
                f"{same_price:.2f}",
                int(new_buy_orders),
                f"{same_price:.2f}"
            ])
            
        elif market_role == 'sell_only':
            # This planet sells this item
            new_sell_orders, _ = calculate_order_counts(
                item, regional_price, recipe_time, complexity, planet_id
            )
            
            # Sell price with markup
            sell_price = regional_price * 1.1
            
            market_data.append([
                item,
                int(new_sell_orders),
                f"{sell_price:.2f}",
                0,  # No buy orders
                "0.00"
            ])
            
        elif market_role == 'buy_only':
            # This planet buys this item
            _, new_buy_orders = calculate_order_counts(
                item, regional_price, recipe_time, complexity, planet_id
            )
            
            # Buy price with discount
            buy_price = regional_price * 0.9
            
            market_data.append([
                item,
                0,  # No sell orders
                "0.00",
                int(new_buy_orders),
                f"{buy_price:.2f}"
            ])
        
        # Items with 'none' role are not included in the market
    
    return market_data

def main():
    print("Generating all market files from scratch...")
    
    # Load calculated prices
    calculated_prices = load_calculated_prices()
    if not calculated_prices:
        print("❌ No calculated prices found. Run calculate_prices.py first.")
        return
    
    # Get planet IDs
    planet_ids = get_planet_ids()
    if not planet_ids:
        print("❌ No planet IDs found. Check market_orders directory.")
        return
    
    print(f"Found {len(planet_ids)} planets: {', '.join(planet_ids[:10])}{'...' if len(planet_ids) > 10 else ''}")
    
    # Load recipes
    recipes = load_yaml_file('recipes.yaml')
    
    # Create global trading strategy
    print("Creating global trading strategy...")
    item_strategy = create_global_trading_strategy(calculated_prices.keys(), planet_ids, calculated_prices)
    
    # Create output directory
    output_dir = "market_orders_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate market files for each planet
    total_items = 0
    total_arbitrage_prevented = 0
    
    for planet_id in planet_ids:
        print(f"Generating market for planet {planet_id}...")
        
        # Generate market data
        market_data = generate_planet_market(planet_id, calculated_prices, item_strategy, recipes)
        
        # Write to file
        output_file = os.path.join(output_dir, f"{planet_id}.csv")
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in market_data:
                writer.writerow(row)
        
        # Count items and arbitrage prevention
        items_count = len(market_data)
        arbitrage_prevented = sum(1 for row in market_data if (row[1] == '0' and row[3] != '0') or (row[1] != '0' and row[3] == '0'))
        
        total_items += items_count
        total_arbitrage_prevented += arbitrage_prevented
        
        print(f"   Generated {items_count} items, {arbitrage_prevented} arbitrage prevented")
    
    print(f"\nSummary:")
    print(f"   Total items generated: {total_items}")
    print(f"   Arbitrage prevented: {total_arbitrage_prevented}")
    print(f"   Output saved to: {output_dir}/")
    print(f"   Planets: {len(planet_ids)}")
    
    # Save planet IDs for reference
    with open("planet_ids.txt", "w") as f:
        for planet_id in planet_ids:
            f.write(f"{planet_id}\n")
    
    print(f"   Planet IDs saved to: planet_ids.txt")
    
    print(f"\nReady to copy files from {output_dir}/ to your server!")
    print(f"Arbitrage protection: Basic ores buy-only, other items buy/sell distributed")
    print(f"Interplanetary trading: Players can profit by trading between planets")

if __name__ == "__main__":
    main()
