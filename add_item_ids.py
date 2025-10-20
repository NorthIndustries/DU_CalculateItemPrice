#!/usr/bin/env python3
"""
Add item IDs from database to item_cache.yaml
"""

import subprocess
import yaml
import re

def run_database_query(query):
    """Run a SQL query against the Dual Universe database"""
    try:
        cmd = [
            'docker', 'exec', '-i', 'du-server2-postgres-1',
            'psql', '-U', 'dual', '-d', 'dual', '-t', '-c', query
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Database query failed: {e}")
        return None

def find_item_id_table():
    """Find the table that contains item IDs and names"""
    
    print("Looking for item ID table...")
    
    # Try different possible table names
    tables_to_try = [
        "item_definition",
        "item", 
        "items",
        "element_definition",
        "element"
    ]
    
    for table in tables_to_try:
        print(f"Trying table: {table}")
        query = f"SELECT id, name FROM {table} WHERE name IS NOT NULL LIMIT 5;"
        result = run_database_query(query)
        
        if result and not "ERROR" in result:
            print(f"Found data in {table}")
            return table
    
    return None

def extract_item_ids_and_names(table_name):
    """Extract all item IDs and names from the table"""
    
    print(f"Extracting item IDs from {table_name}...")
    
    query = f"SELECT id, name FROM {table_name} WHERE name IS NOT NULL ORDER BY name;"
    result = run_database_query(query)
    
    if not result:
        return None
    
    items = {}
    for line in result.split('\n'):
        if line.strip() and '|' in line:
            parts = line.split('|')
            if len(parts) >= 2:
                try:
                    item_id = int(parts[0].strip())
                    name = parts[1].strip()
                    items[name] = item_id
                except ValueError:
                    continue
    
    print(f"Extracted {len(items)} items with IDs")
    return items

def add_ids_to_cache():
    """Add item IDs to the existing item_cache.yaml"""
    
    print("Loading item cache...")
    
    # Load existing cache
    with open('item_cache.yaml', 'r') as f:
        cache = yaml.safe_load(f)
    
    print(f"Loaded {len(cache)} items from cache")
    
    # Find the item table
    table_name = find_item_id_table()
    if not table_name:
        print("Could not find item table in database")
        return
    
    # Extract item IDs
    db_items = extract_item_ids_and_names(table_name)
    if not db_items:
        print("Could not extract items from database")
        return
    
    # Match and add IDs
    matched = 0
    for item_name, price in cache.items():
        if item_name in db_items:
            # Add ID to the cache entry
            if isinstance(cache[item_name], dict):
                cache[item_name]['id'] = db_items[item_name]
            else:
                # Convert to dict format
                cache[item_name] = {
                    'price': price,
                    'id': db_items[item_name]
                }
            matched += 1
    
    print(f"Matched {matched} items with database IDs")
    
    # Save updated cache
    with open('item_cache.yaml', 'w') as f:
        yaml.dump(cache, f, default_flow_style=False)
    
    print("Updated item_cache.yaml with IDs")

def main():
    """Main function"""
    
    print("Adding Item IDs to Cache")
    print("=" * 30)
    
    add_ids_to_cache()
    
    print("Done!")

if __name__ == "__main__":
    main()
