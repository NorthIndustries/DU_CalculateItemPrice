# DU Calculate Item Price

A Python tool for calculating realistic item prices in Dual Universe based on ore costs, production time, and recipe complexity.

## What It Does

This tool calculates the economic value of every craftable item in Dual Universe by:

- **Base Material Pricing**: Starting from ore prices and working up the production chain
- **Time Cost Calculation**: Adding production time costs to reflect opportunity cost
- **Recipe Optimization**: Automatically selecting the most efficient production method
- **Byproduct Handling**: Properly accounting for main products vs byproducts
- **Catalyst Support**: Treating reusable catalysts as zero-cost items
- **Market Generation**: Creating realistic buy/sell orders with appropriate scarcity

## Features

- **3,300+ Items Calculated**: Covers the vast majority of craftable items
- **Smart Recipe Selection**: Chooses the most cost-effective production method
- **Realistic Market Data**: Generates CSV files with buy/sell orders and prices
- **Cache System**: Fast subsequent runs with intelligent caching
- **Circular Dependency Detection**: Prevents infinite loops in complex recipes
- **Time-Based Pricing**: Accounts for production time in final costs

## Installation

### Prerequisites

- Python 3.7 or higher
- PyYAML library

### Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/NorthIndustries/DU_CalculateItemPrice.git
   cd DU_CalculateItemPrice
   ```

2. **Install dependencies**:

   ```bash
   pip install pyyaml
   ```

3. **Configure base prices**:
   Edit `ore_prices.yaml` to set your server's ore prices:

   ```yaml
   # T1 Ores
   IronOre: 25
   SiliconOre: 25
   CarbonOre: 25
   AluminiumOre: 25

   # T2 Ores
   CopperOre: 75
   SodiumOre: 75
   # ... etc
   ```

## Usage

### Basic Price Calculation

```bash
python calculate_prices.py
```

This will:

- Load ore prices from `ore_prices.yaml`
- Load recipes from `recipes.yaml`
- Calculate prices for all craftable items
- Save results to `output.txt` and cache to `item_cache.yaml`

### Market Data Generation

**Single Planet:**
```bash
python update_market_prices.py
```

**Multi-Planet Economy:**
```bash
python update_multi_market_prices.py
```

This will:

- Load calculated prices from cache
- Generate realistic market data for all planets
- Create regional price variations for interplanetary trade
- Output files to `market_orders_output/` directory

### Configuration

Edit `calculate_prices.py` to adjust:

```python
TIME_COST_FACTOR = 2.0  # Cost per minute of production
DEBUG = True            # Enable debug output
```

## File Structure

```
DU_CalculateItemPrice/
├── calculate_prices.py      # Main price calculation script
├── update_market_prices.py # Market data generation
├── ore_prices.yaml         # Base ore prices (configure this)
├── recipes.yaml           # Game recipes (provided)
├── README.md              # This file
├── .gitignore            # Git ignore rules
└── examples/
    ├── 77.csv            # Sample market data
    └── output.txt        # Sample calculation results
```

## How It Works

### 1. Base Material Loading

The tool starts with your configured ore prices and treats them as terminal costs.

### 2. Recipe Analysis

For each craftable item, it finds all possible recipes and selects the most cost-effective one.

### 3. Cost Calculation

```
Item Cost = (Input Material Costs + Time Cost) / Main Product Quantity
```

### 4. Market Generation

Creates realistic buy/sell orders based on:

- Item rarity and complexity
- Production time requirements
- Market spread (10% markup/discount)

## Example Output

```
=== Calculated Prices ===
AluminiumPure                      41.5
CarbonPure                         41.5
IronPure                           41.5
SiliconPure                        41.5
WarpDriveSmall                453354.09
WarpBeacon                  21957124.62
```

## Dual Universe Integration

### Server Economy Setup

1. **Configure Ore Prices**: Update `ore_prices.yaml` with your server's current ore prices
2. **Run Calculations**: Execute `python calculate_prices.py`
3. **Generate Market Data**: 
   - Single planet: `python update_market_prices.py`
   - Multi-planet: `python update_multi_market_prices.py`
4. **Import to Game**: Copy files from `market_orders_output/` to your server

### Multi-Planet Economy Features

- **Regional Price Variations**: Each planet has slightly different prices (15-25% variation)
- **Trade Opportunities**: Players can buy on one planet and sell on another for profit
- **Realistic Scarcity**: High-end items are rarer on certain planets
- **Balanced Profits**: Trade profits are limited to 5-15% to prevent exploitation

### Market Data Format

The generated CSV files contain:

- Item name
- Sell order count and price
- Buy order count and price

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source. Feel free to use and modify for your Dual Universe server.

## Support

If you encounter issues:

1. Check that your `ore_prices.yaml` is properly formatted
2. Ensure `recipes.yaml` is up to date with the latest game version
3. Clear the cache by deleting `item_cache.yaml` and running again

## Updates

This tool is designed to work with the latest Dual Universe recipes. When new items are added to the game, simply update your `recipes.yaml` file and recalculate prices.

---

**Made for the Dual Universe community by North Industries**
