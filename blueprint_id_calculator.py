#!/usr/bin/env python3
"""
Simple Blueprint Price Calculator using item IDs
"""

import json
import yaml
import os
from collections import defaultdict

def load_item_cache():
    """Load item cache with IDs"""
    with open('item_cache.yaml', 'r') as f:
        return yaml.safe_load(f)

def calculate_blueprint_cost(blueprint_file, item_cache):
    """Calculate cost of a blueprint using element IDs"""
    
    with open(blueprint_file, 'r') as f:
        data = json.load(f)
    
    blueprint_name = os.path.basename(blueprint_file).replace('.json', '')
    
    print(f"\\nAnalyzing: {blueprint_name}")
    print(f"Elements: {len(data.get('Elements', []))}")
    
    # Count element types
    element_counts = defaultdict(int)
    for element in data.get('Elements', []):
        element_type = element.get('elementType')
        element_counts[element_type] += 1
    
    total_cost = 0
    item_breakdown = []
    unknown_items = []
    
    print(f"\\nCost breakdown for {blueprint_name}:")
    print("-" * 50)
    
    for element_type, count in element_counts.items():
        # Look for this element type in our cache
        found_item = None
        for item_name, item_data in item_cache.items():
            if isinstance(item_data, dict) and 'id' in item_data:
                if item_data['id'] == element_type:
                    found_item = item_name
                    break
        
        if found_item and found_item in item_cache:
            item_data = item_cache[found_item]
            if isinstance(item_data, dict):
                item_price = item_data['price']
            else:
                item_price = item_data
            
            item_total = item_price * count
            total_cost += item_total
            
            item_breakdown.append({
                'item': found_item,
                'quantity': count,
                'unit_price': item_price,
                'total_price': item_total
            })
            
            print(f"{found_item:30} x{count:3} @ {item_price:8.2f} = {item_total:10.2f}")
        else:
            unknown_items.append((f"Element_{element_type}", count))
            print(f"Element_{element_type:25} x{count:3} @ {'N/A':>8} = {'Unknown':>10}")
    
    print("-" * 50)
    print(f"{'TOTAL COST':30} {'':>15} {total_cost:10.2f}")
    
    if unknown_items:
        print(f"\\nUnknown items ({len(unknown_items)}):")
        for item, count in unknown_items[:5]:  # Show first 5
            print(f"  {item} x{count}")
    
    return total_cost, item_breakdown, unknown_items

def main():
    """Main function"""
    
    print("Blueprint Price Calculator (ID-based)")
    print("=" * 40)
    
    # Load item cache with IDs
    item_cache = load_item_cache()
    print(f"Loaded {len(item_cache)} items with IDs")
    
    # Process blueprints
    blueprint_dir = "blueprints"
    if not os.path.exists(blueprint_dir):
        print(f"Error: {blueprint_dir} directory not found")
        return
    
    total_costs = {}
    
    for filename in os.listdir(blueprint_dir):
        if filename.endswith('.json'):
            blueprint_file = os.path.join(blueprint_dir, filename)
            blueprint_name = filename.replace('.json', '')
            
            try:
                cost, breakdown, unknown = calculate_blueprint_cost(
                    blueprint_file, item_cache
                )
                total_costs[blueprint_name] = {
                    'cost': cost,
                    'breakdown': breakdown,
                    'unknown_count': len(unknown)
                }
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Summary
    print(f"\\n{'='*60}")
    print("BLUEPRINT COST SUMMARY")
    print(f"{'='*60}")
    
    for blueprint_name, data in total_costs.items():
        print(f"{blueprint_name:30} {data['cost']:10.2f} (Unknown: {data['unknown_count']})")

if __name__ == "__main__":
    main()
