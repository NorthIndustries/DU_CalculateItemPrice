import yaml
from collections import defaultdict

# Configuration constants
TIME_COST_FACTOR = 2.0  # Cost per minute of production (adjust as needed)
DEBUG = True  # Enable debugging to see what's happening

# Catalysts are reusable - they don't add to cost
CATALYSTS = {
    'Catalyst1', 'Catalyst2', 'Catalyst3', 'Catalyst4', 'Catalyst5',
    'Catalyst6', 'Catalyst7', 'Catalyst8', 'Catalyst9', 'Catalyst10'
}

def load_yaml_file(filename):
    with open(filename, 'r') as f:
        data = list(yaml.safe_load_all(f))
    return data

def calculate_cost(item, ore_prices, recipes, cache, visited=None):
    # If already calculated
    if item in cache:
        return cache[item]
    
    # Initialize visited set for cycle detection
    if visited is None:
        visited = set()
    
    # Check for circular dependency
    if item in visited:
        if DEBUG:
            print(f"⚠️ Circular dependency detected for {item}")
        cache[item] = None
        return None
    
    # Add current item to visited set
    visited.add(item)
    
    # Catalysts are reusable - they have zero cost
    if item in CATALYSTS:
        cache[item] = 0
        visited.remove(item)  # Remove from visited before returning
        return 0
    
    # Base material (e.g. ore) - these are terminal nodes
    if item in ore_prices:
        cache[item] = ore_prices[item]
        visited.remove(item)  # Remove from visited before returning
        return ore_prices[item]
    
    # Find ALL recipes that output this item
    possible_recipes = []
    for r in recipes:
        for output in r.get('out', []):
            if item in output:
                possible_recipes.append(r)
                break
    
    if not possible_recipes:
        if DEBUG:
            print(f"⚠️ No recipe found for {item}")
        cache[item] = None
        visited.remove(item)  # Remove from visited before returning
        return None
    
    # Choose the recipe with the lowest cost per unit
    best_recipe = None
    best_cost = float('inf')
    
    for recipe in possible_recipes:
        # Calculate input costs for this recipe
        total_input_cost = 0
        missing_dependencies = []
        
        for input_item in recipe.get('in', []):
            for name, qty in input_item.items():
                # Skip catalysts - they are reusable and don't add to cost
                if name in CATALYSTS:
                    if DEBUG:
                        print(f"🔄 Skipping catalyst {name} (reusable)")
                    continue
                    
                sub_cost = calculate_cost(name, ore_prices, recipes, cache, visited.copy())
                if sub_cost is None:
                    missing_dependencies.append(name)
                    if DEBUG:
                        print(f"⚠️ Missing sub-cost for {name}")
                else:
                    total_input_cost += sub_cost * qty
        
        # If we have missing dependencies, skip this recipe
        if missing_dependencies:
            continue
        
        # Calculate cost per unit for this recipe
        # Use only the first output (main product), ignore byproducts
        first_output = recipe.get('out', [])[0]
        main_product_quantity = list(first_output.values())[0]
        cost_per_unit = total_input_cost / main_product_quantity
        
        # Add time-based cost
        time_cost = recipe.get('time', 0) * TIME_COST_FACTOR
        final_cost = cost_per_unit + time_cost
        
        if final_cost < best_cost:
            best_cost = final_cost
            best_recipe = recipe
    
    if not best_recipe:
        if DEBUG:
            print(f"⚠️ No valid recipe found for {item}")
        cache[item] = None
        visited.remove(item)  # Remove from visited before returning
        return None
    
    # Use the best cost we calculated
    final_cost = best_cost

    cache[item] = final_cost
    visited.remove(item)  # Remove from visited before returning
    return final_cost

def identify_problematic_recipes(recipes, ore_prices):
    """Identify recipes that produce base materials, which could cause circular dependencies"""
    problematic = []
    for r in recipes:
        for out in r.get('out', []):
            for item in out.keys():
                if item in ore_prices:
                    problematic.append((r.get('id', 'unknown'), item))
    return problematic

def save_cache_to_file(cache, filename="item_cache.yaml"):
    """Save calculated prices to a cache file"""
    with open(filename, 'w') as f:
        yaml.dump(cache, f, default_flow_style=False, sort_keys=True)
    print(f"💾 Saved {len(cache)} items to {filename}")

def load_cache_from_file(filename="item_cache.yaml"):
    """Load previously calculated prices from cache file"""
    try:
        with open(filename, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def load_manual_prices(filename="independent_items.yaml"):
    """Load manually set prices for independent items"""
    try:
        with open(filename, 'r') as f:
            data = yaml.safe_load(f) or {}
            # Filter out None values (items without manual prices)
            return {k: v for k, v in data.items() if v is not None}
    except FileNotFoundError:
        return {}

def identify_independent_items(recipes, ore_prices):
    """Identify items that are used as inputs but have no recipes (independent items)"""
    all_inputs = set()
    all_outputs = set()
    
    for r in recipes:
        for out in r.get('out', []):
            all_outputs.update(out.keys())
        for inp in r.get('in', []):
            all_inputs.update(inp.keys())
    
    # Items that are inputs but not outputs (and not base materials)
    independent = all_inputs - all_outputs - set(ore_prices.keys())
    return independent

def main():
    # Load base ore prices
    with open("ore_prices.yaml", "r") as f:
        ore_prices = yaml.safe_load(f)

    # Load recipes
    recipes = load_yaml_file("recipes.yaml")
    
    # Load existing cache
    cache = load_cache_from_file()
    print(f"📁 Loaded {len(cache)} items from cache")
    
    # Load manual prices for independent items
    manual_prices = load_manual_prices()
    if manual_prices:
        print(f"💰 Loaded {len(manual_prices)} manual prices for independent items")
        # Add manual prices to cache
        cache.update(manual_prices)
    
    # Identify problematic recipes
    problematic = identify_problematic_recipes(recipes, ore_prices)
    if problematic:
        print("⚠️ Found recipes that produce base materials (these will be ignored):")
        for recipe_id, item in problematic:
            print(f"  Recipe {recipe_id} produces {item}")
        print()

    # Identify independent items (no recipes)
    independent_items = identify_independent_items(recipes, ore_prices)
    print(f"🔍 Found {len(independent_items)} independent items (no recipes):")
    for item in sorted(list(independent_items)[:10]):
        print(f"  {item}")
    if len(independent_items) > 10:
        print(f"  ... and {len(independent_items) - 10} more")
    print()

    # Collect all possible output items
    all_outputs = set()
    for r in recipes:
        for out in r.get('out', []):
            all_outputs.update(out.keys())

    # Calculate prices for all items
    calculated_prices = {}
    failed_items = []
    
    for item in all_outputs:
        # Skip base materials that are in ore_prices
        if item in ore_prices:
            continue
            
        cost = calculate_cost(item, ore_prices, recipes, cache)
        if cost:
            calculated_prices[item] = round(cost, 2)
        else:
            failed_items.append(item)

    # Save cache for future use
    save_cache_to_file(cache)

    # Sort and print
    print("\n=== Calculated Prices ===")
    for k, v in sorted(calculated_prices.items()):
        print(f"{k:30} {v:>8}")
    
    if failed_items:
        print(f"\n⚠️ Failed to calculate prices for {len(failed_items)} items:")
        for item in failed_items[:10]:  # Show first 10
            print(f"  {item}")
        if len(failed_items) > 10:
            print(f"  ... and {len(failed_items) - 10} more")
    
    # Save independent items to a separate file for manual pricing
    if independent_items:
        independent_data = {item: None for item in independent_items}
        with open("independent_items.yaml", 'w') as f:
            yaml.dump(independent_data, f, default_flow_style=False, sort_keys=True)
        print(f"\n📝 Saved {len(independent_items)} independent items to independent_items.yaml")
        print("   You can manually add prices for these items in that file")

if __name__ == "__main__":
    main()
