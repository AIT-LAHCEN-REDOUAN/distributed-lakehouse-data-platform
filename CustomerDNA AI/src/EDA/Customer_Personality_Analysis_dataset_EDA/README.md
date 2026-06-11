# Simple Customer Personality Analysis EDA

A clean, minimal EDA solution for Customer Personality Analysis dataset.

## Quick Start

1. **Run the analysis**:
   ```bash
   cd scripts
   run_simple_eda.bat
   ```

2. **Or run directly**:
   ```bash
   python simple_customer_eda.py
   ```

## Folder Structure

```
Customer_Personality_Analysis_dataset_EDA/
├── config/           # Configuration files
├── output/           # Analysis results and visualizations
├── logs/             # Log files
└── scripts/          # Main EDA script and batch file
```

## Files

- `scripts/simple_customer_eda.py` - Main EDA analysis script
- `scripts/run_simple_eda.bat` - Windows batch file for easy execution
- `config/simple_config.json` - Configuration settings

## Output

The analysis generates:
- Cleaned dataset (`marketing_campaign_clean.csv`)
- Visualizations (PNG files)
- Text reports with key findings
- Summary report with recommendations

## Requirements

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn