import yaml
with open("ore_prices.yaml") as f:
    ore = yaml.safe_load(f)
print(ore)
