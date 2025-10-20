# Blueprint Price Calculator

This extension adds blueprint price calculation functionality to the Dual Universe item price calculator. It analyzes blueprint files and calculates the total cost of all items used in the blueprint.

## Features

- **Blueprint Analysis**: Parses Dual Universe blueprint JSON files
- **Element Type Mapping**: Maps blueprint element types to actual item names
- **Cost Calculation**: Calculates total cost using cached item prices
- **Detailed Breakdown**: Shows cost per item with quantities
- **Multiple Blueprint Support**: Processes multiple blueprints at once
- **Report Generation**: Creates detailed YAML reports

## Files

### Core Scripts

- `blueprint_price_calculator.py` - Main blueprint price calculator
- `analyze_blueprint.py` - Blueprint structure analyzer
- `create_element_mapping.py` - Creates element type mappings
- `improve_element_mapping.py` - Improves mappings using price cache
- `examine_binary.py` - Examines binary data in blueprints

### Generated Files

- `element_type_mapping.yaml` - Basic element type mappings
- `element_type_mapping_improved.yaml` - Improved mappings with actual item names
- `blueprint_cost_report.yaml` - Detailed cost report for all blueprints

## Usage

### Basic Usage

```bash
# Calculate prices for all blueprints in the blueprints/ directory
python3 blueprint_price_calculator.py
```

### Prerequisites

1. **Run the main price calculator first**:

   ```bash
   python3 calculate_prices.py
   ```

   This creates the `item_cache.yaml` file with calculated prices.

2. **Place blueprint files** in the `blueprints/` directory:
   ```
   blueprints/
   ├── NQ - Novark Racer Mk 3.json
   ├── Captains Customs - Nautilus.json
   └── NQ - Outpost Dojo.json
   ```

### Output

The calculator provides:

1. **Console Output**: Real-time cost breakdown for each blueprint
2. **Summary**: Total costs for all blueprints
3. **Report File**: Detailed YAML report (`blueprint_cost_report.yaml`)

#### Example Output

```
Dual Universe Blueprint Price Calculator
==================================================
Loaded prices for 3346 items
Loaded mapping for 115 element types

Cost breakdown for NQ - Novark Racer Mk 3.json:
--------------------------------------------------
PVPSeat              x  1 @  4398.94 =    4398.94
WingSmall2           x  4 @   886.88 =    3547.50
SpaceEngineLarge     x  1 @ 18849.00 =   18849.00
RetroEngine          x  3 @   774.88 =    2324.62
hcSteelMatte         x 13 @  1080.12 =   14041.62
...
--------------------------------------------------
TOTAL COST                             89027.31
```

## Blueprint Format

Dual Universe blueprints are JSON files containing:

- **Elements**: List of all items in the blueprint
- **VoxelData**: Compressed binary data (not currently used)
- **Links**: Connections between elements
- **Model**: 3D model information

### Element Structure

Each element contains:

- `elementType`: Numeric ID identifying the item type
- `elementId`: Unique identifier
- `position`: 3D coordinates
- `properties`: Item-specific properties

## Element Type Mapping

The system maps blueprint element types to actual item names:

### Automatic Mapping

- Analyzes all blueprints to identify element types
- Creates initial mapping based on common patterns
- Improves mapping by matching with price cache items

### Manual Mapping

You can manually edit the mapping files:

- `element_type_mapping.yaml` - Basic mappings
- `element_type_mapping_improved.yaml` - Improved mappings

### Example Mapping

```yaml
183890713: "CoreUnitSpace32" # Core Unit
65048663: "WingSmall2" # Wing
177821174: "Headlight" # Light
710193240: "RetroEngine" # Engine
```

## Cost Calculation

The calculator:

1. **Loads Prices**: Reads calculated prices from `item_cache.yaml`
2. **Maps Elements**: Converts element types to item names
3. **Calculates Costs**: Multiplies item prices by quantities
4. **Handles Unknowns**: Reports items without price data

### Price Sources

- **Calculated Items**: Uses prices from the main calculator
- **Unknown Items**: Items without price data are marked as "Unknown"
- **Missing Mappings**: Element types without mappings are reported

## Advanced Usage

### Custom Element Mapping

Create custom mappings for specific element types:

```python
# In improve_element_mapping.py
mapping_rules = {
    123456789: ['CustomItem', 'SpecialPart'],
    # Add your custom mappings
}
```

### Binary Data Analysis

The system includes tools to analyze compressed binary data:

```bash
# Analyze binary data structure
python3 examine_binary.py blueprints/your_blueprint.json

# Analyze all blueprints
python3 analyze_blueprint.py
```

## Troubleshooting

### Common Issues

1. **"No prices found"**: Run `calculate_prices.py` first
2. **"Unknown items"**: Many element types may not have mappings
3. **"No blueprints found"**: Ensure blueprints are in `blueprints/` directory

### Improving Mappings

1. **Run the analyzer**:

   ```bash
   python3 create_element_mapping.py
   ```

2. **Improve mappings**:

   ```bash
   python3 improve_element_mapping.py
   ```

3. **Manual editing**: Edit the mapping files directly

### Binary Data Investigation

The binary data in blueprints appears to use a custom compression format. Current analysis shows:

- **Format**: Base64 encoded binary data
- **Compression**: Not standard zlib/gzip
- **Content**: Likely contains detailed item information
- **Status**: Under investigation for complete item extraction

## File Structure

```
du-maket-calc/
├── blueprints/                          # Blueprint files
│   ├── NQ - Novark Racer Mk 3.json
│   ├── Captains Customs - Nautilus.json
│   └── NQ - Outpost Dojo.json
├── blueprint_price_calculator.py        # Main calculator
├── analyze_blueprint.py                 # Structure analyzer
├── create_element_mapping.py           # Mapping creator
├── improve_element_mapping.py          # Mapping improver
├── examine_binary.py                    # Binary data examiner
├── element_type_mapping.yaml           # Basic mappings
├── element_type_mapping_improved.yaml  # Improved mappings
└── blueprint_cost_report.yaml          # Cost report
```

## Future Enhancements

- **Complete Binary Decoding**: Decode compressed binary data for complete item extraction
- **Visual Blueprint Viewer**: Create visual representation of blueprints
- **Cost Optimization**: Suggest cheaper alternatives for items
- **Batch Processing**: Process multiple blueprint directories
- **Export Formats**: Support CSV, JSON, and other export formats

## Contributing

To improve the blueprint price calculator:

1. **Add Element Mappings**: Identify unknown element types
2. **Improve Binary Decoding**: Help decode the binary data format
3. **Add Features**: Suggest new functionality
4. **Report Issues**: File bug reports for problems

## Related Tools

- `calculate_prices.py` - Main item price calculator
- `update_market_prices.py` - Market price updater
- `update_multi_market_prices.py` - Multi-planet market updater
