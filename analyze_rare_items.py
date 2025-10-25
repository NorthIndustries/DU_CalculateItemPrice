#!/usr/bin/env python3
"""
Analyze rare item distribution across planets
"""

import csv
import os
import re

def analyze_rare_items():
    """Analyze the distribution of rare items across planets"""
    
    market_orders_dir = "market_orders_generated"
    
    if not os.path.exists(market_orders_dir):
        print(f"Directory {market_orders_dir} not found.")
        return
    
    # Collect data
    plasma_items = {}
    warp_items = {}
    core_items = {}
    rare_items = {}
    
    planet_files = []
    for filename in os.listdir(market_orders_dir):
        if filename.endswith('.csv'):
            planet_id = os.path.splitext(filename)[0]
            planet_file = os.path.join(market_orders_dir, filename)
            planet_files.append((planet_id, planet_file))
    
    print(f"Analyzing rare items across {len(planet_files)} planets...")
    
    for planet_id, planet_file in planet_files:
        with open(planet_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 5:
                    item, sell_orders, sell_price, buy_orders, buy_price = row
                    
                    try:
                        sell_orders = int(sell_orders) if sell_orders else 0
                        buy_orders = int(buy_orders) if buy_orders else 0
                        
                        # Check for plasma items
                        if 'plasma' in item.lower():
                            if item not in plasma_items:
                                plasma_items[item] = []
                            plasma_items[item].append(planet_id)
                        
                        # Check for warp items
                        elif 'warp' in item.lower():
                            if item not in warp_items:
                                warp_items[item] = []
                            warp_items[item].append(planet_id)
                        
                        # Check for core items
                        elif 'core' in item.lower():
                            if item not in core_items:
                                core_items[item] = []
                            core_items[item].append(planet_id)
                        
                        # Check for other rare items (high price or special names)
                        elif any(indicator in item for indicator in ['Beacon', 'Drive', 'Cell', 'Engine', 'Thruster']):
                            if item not in rare_items:
                                rare_items[item] = []
                            rare_items[item].append(planet_id)
                    
                    except (ValueError, IndexError):
                        continue
    
    # Generate report
    report_lines = []
    report_lines.append("# Rare Items Distribution Report")
    report_lines.append("")
    
    # Plasma distribution
    report_lines.append("## Plasma Items (Ultra Rare - 1-2 planets each)")
    report_lines.append("")
    if plasma_items:
        for item, planets in plasma_items.items():
            report_lines.append(f"### {item}")
            report_lines.append(f"- **Available on**: {', '.join(planets)} ({len(planets)} planets)")
            report_lines.append("")
    else:
        report_lines.append("No plasma items found.")
        report_lines.append("")
    
    # Warp items distribution
    report_lines.append("## Warp Items (Ultra Rare - 2-4 planets each)")
    report_lines.append("")
    if warp_items:
        for item, planets in warp_items.items():
            report_lines.append(f"### {item}")
            report_lines.append(f"- **Available on**: {', '.join(planets)} ({len(planets)} planets)")
            report_lines.append("")
    else:
        report_lines.append("No warp items found.")
        report_lines.append("")
    
    # Core items distribution
    report_lines.append("## Core Items (Ultra Rare - 2-4 planets each)")
    report_lines.append("")
    if core_items:
        for item, planets in core_items.items():
            report_lines.append(f"### {item}")
            report_lines.append(f"- **Available on**: {', '.join(planets)} ({len(planets)} planets)")
            report_lines.append("")
    else:
        report_lines.append("No core items found.")
        report_lines.append("")
    
    # Other rare items
    report_lines.append("## Other Rare Items (Limited Distribution)")
    report_lines.append("")
    if rare_items:
        for item, planets in rare_items.items():
            report_lines.append(f"### {item}")
            report_lines.append(f"- **Available on**: {', '.join(planets)} ({len(planets)} planets)")
            report_lines.append("")
    else:
        report_lines.append("No other rare items found.")
        report_lines.append("")
    
    # Summary
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **Plasma Types**: {len(plasma_items)}")
    report_lines.append(f"- **Warp Items**: {len(warp_items)}")
    report_lines.append(f"- **Core Items**: {len(core_items)}")
    report_lines.append(f"- **Other Rare Items**: {len(rare_items)}")
    report_lines.append(f"- **Total Planets**: {len(planet_files)}")
    report_lines.append("")
    
    # Save report
    report_content = "\n".join(report_lines)
    
    with open("rare_items_report.md", "w") as f:
        f.write(report_content)
    
    print(f"Rare items report saved to: rare_items_report.md")
    print(f"Plasma items: {len(plasma_items)}")
    print(f"Warp items: {len(warp_items)}")
    print(f"Core items: {len(core_items)}")
    print(f"Other rare items: {len(rare_items)}")
    
    # Show some examples
    if plasma_items:
        print(f"\nPlasma Examples:")
        for item, planets in list(plasma_items.items())[:3]:
            print(f"   {item}: {', '.join(planets)}")
    
    if warp_items:
        print(f"\nWarp Examples:")
        for item, planets in list(warp_items.items())[:3]:
            print(f"   {item}: {', '.join(planets)}")

if __name__ == "__main__":
    analyze_rare_items()

