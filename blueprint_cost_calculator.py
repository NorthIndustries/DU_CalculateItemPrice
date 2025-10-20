#!/usr/bin/env python3
"""
Complete Blueprint Cost Calculator
Calculates costs for both elements and voxel materials in one script
"""

import json
import yaml
import os
import base64
import struct
from collections import defaultdict

def convert_voxel_quantity(raw_quantity):
    """Convert voxel quantity from raw format to actual quantity"""
    return raw_quantity / 256

def is_material_id(value):
    """Check if value could be a material ID"""
    return (1000000 <= value <= 5000000000)

def is_quantity(value):
    """Check if value could be a quantity (32-bit)"""
    return (1 <= value <= 1000000)

def decode_voxel_binary(binary_data):
    """Decode voxel binary data to extract material information"""
    
    materials = {}
    offset = 0
    
    while offset < len(binary_data) - 8:
        try:
            # Read 32-bit values
            val1 = struct.unpack('<I', binary_data[offset:offset+4])[0]
            val2 = struct.unpack('<I', binary_data[offset+4:offset+8])[0]
            
            # Check if this could be a material ID and quantity
            if (is_material_id(val1) and is_quantity(val2)):
                # Convert quantity from 2^24 format
                actual_quantity = convert_voxel_quantity(val2)
                if actual_quantity > 0:
                    materials[val1] = actual_quantity
                offset += 8
                continue
            
            # Strategy 2: Look for quantity followed by material ID
            if (is_quantity(val1) and is_material_id(val2)):
                # Convert quantity from 2^24 format
                actual_quantity = convert_voxel_quantity(val1)
                if actual_quantity > 0:
                    materials[val2] = actual_quantity
                offset += 8
                continue
            
            offset += 1
            
        except:
            offset += 1
    
    return materials

def extract_voxel_materials(blueprint_file):
    """Extract all voxel materials from a blueprint"""
    
    with open(blueprint_file, 'r') as f:
        data = json.load(f)
    
    voxel_data = data.get('VoxelData', [])
    all_materials = defaultdict(int)
    
    for voxel in voxel_data:
        if 'records' in voxel and 'meta' in voxel['records']:
            meta = voxel['records']['meta']
            
            if 'data' in meta and '$binary' in meta['data']:
                binary_str = meta['data']['$binary']
                binary_data = base64.b64decode(binary_str)
                
                materials = decode_voxel_binary(binary_data)
                
                for material_id, quantity in materials.items():
                    all_materials[material_id] += quantity
    
    return dict(all_materials)

def calculate_blueprint_cost(blueprint_file, item_cache):
    """Calculate complete blueprint cost including elements and voxel materials"""
    
    print(f"\nAnalyzing: {os.path.basename(blueprint_file)}")
    
    with open(blueprint_file, 'r') as f:
        data = json.load(f)
    
    # Extract blueprint details
    blueprint_name = data.get('Model', {}).get('Name', 'Unknown')
    blueprint_size = data.get('Model', {}).get('Size', 'Unknown')
    
    # Calculate element costs
    element_cost = 0
    element_breakdown = []
    element_counts = defaultdict(int)
    
    for element in data.get('Elements', []):
        element_type = element.get('elementType')
        element_counts[element_type] += 1
    
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
            element_cost += item_total
            
            element_breakdown.append({
                'item': found_item,
                'quantity': count,
                'unit_price': item_price,
                'total_price': item_total,
                'type': 'element'
            })
    
    # Calculate voxel material costs
    voxel_materials = extract_voxel_materials(blueprint_file)
    voxel_cost = 0
    voxel_breakdown = []
    
    for material_id, quantity in voxel_materials.items():
        # Find matching item in cache
        found_item = None
        for item_name, item_data in item_cache.items():
            if isinstance(item_data, dict) and 'id' in item_data:
                if item_data['id'] == material_id:
                    found_item = item_name
                    break
        
        if found_item and found_item in item_cache:
            item_data = item_cache[found_item]
            if isinstance(item_data, dict):
                item_price = item_data['price']
            else:
                item_price = item_data
            
            item_total = item_price * quantity
            voxel_cost += item_total
            
            voxel_breakdown.append({
                'item': found_item,
                'quantity': quantity,
                'unit_price': item_price,
                'total_price': item_total,
                'type': 'voxel_material'
            })
    
    # Combine results
    total_cost = element_cost + voxel_cost
    all_breakdown = element_breakdown + voxel_breakdown
    
    # Create summary
    summary = {
        'blueprint_name': os.path.basename(blueprint_file).replace('.json', ''),
        'blueprint_display_name': blueprint_name,
        'blueprint_size': blueprint_size,
        'total_cost': total_cost,
        'element_cost': element_cost,
        'voxel_cost': voxel_cost,
        'element_count': len(element_breakdown),
        'voxel_material_count': len(voxel_breakdown),
        'breakdown': all_breakdown
    }
    
    return summary

def save_blueprint_summary(summary, output_dir):
    """Save blueprint summary to a file"""
    
    blueprint_name = summary['blueprint_name']
    output_file = os.path.join(output_dir, f"{blueprint_name}_cost_summary.txt")
    
    with open(output_file, 'w') as f:
        f.write(f"BLUEPRINT COST SUMMARY: {summary['blueprint_display_name']}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Blueprint: {summary['blueprint_display_name']}\n")
        f.write(f"Size: {summary['blueprint_size']}\n")
        f.write(f"File: {blueprint_name}\n\n")
        
        f.write(f"TOTAL COST: {summary['total_cost']:,.2f}\n")
        f.write(f"Element Cost: {summary['element_cost']:,.2f}\n")
        f.write(f"Voxel Material Cost: {summary['voxel_cost']:,.2f}\n\n")
        
        f.write(f"Elements: {summary['element_count']}\n")
        f.write(f"Voxel Materials: {summary['voxel_material_count']}\n\n")
        
        f.write("DETAILED BREAKDOWN:\n")
        f.write("-" * 60 + "\n")
        
        # Sort by total price (descending)
        sorted_breakdown = sorted(summary['breakdown'], key=lambda x: x['total_price'], reverse=True)
        
        for item in sorted_breakdown:
            f.write(f"{item['item']:30} x{item['quantity']:8.3f} @ {item['unit_price']:8.2f} = {item['total_price']:10.2f} ({item['type']})\n")
    
    print(f"Saved summary to: {output_file}")

def main():
    """Main function"""
    
    print("Complete Blueprint Cost Calculator")
    print("=" * 40)
    
    # Load item cache
    try:
        with open('item_cache.yaml', 'r') as f:
            item_cache = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: item_cache.yaml not found. Run add_item_ids.py first.")
        return
    
    print(f"Loaded {len(item_cache)} items with IDs")
    
    # Create output directory
    output_dir = "blueprint_summaries"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
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
                summary = calculate_blueprint_cost(blueprint_file, item_cache)
                total_costs[blueprint_name] = summary['total_cost']
                
                # Save individual summary
                save_blueprint_summary(summary, output_dir)
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Overall summary
    print(f"\n{'='*60}")
    print("OVERALL BLUEPRINT COST SUMMARY")
    print(f"{'='*60}")
    
    for blueprint_name, cost in total_costs.items():
        print(f"{blueprint_name:30} {cost:15,.2f}")
    
    print(f"\nIndividual summaries saved in: {output_dir}/")

if __name__ == "__main__":
    main()
