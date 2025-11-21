# Identify Outliers

Detect and analyze outliers that may affect analysis results.

## Outlier Detection Methods

1. **Statistical methods**:
   - Z-score (values >3 standard deviations)
   - IQR method (values outside Q1-1.5*IQR or Q3+1.5*IQR)
   - Modified Z-score (more robust)

2. **Domain-specific methods**:
   - Business rule violations
   - Known impossible values
   - Expert-defined thresholds

## Outlier Analysis

For each outlier:
- Identify variable and value
- Check if it's a data error
- Assess impact on analysis
- Decide on treatment (remove, transform, keep)

## Outlier Treatment Options

- **Remove**: If clearly erroneous
- **Transform**: Apply log or other transformations
- **Cap**: Replace with threshold values
- **Keep**: If legitimate extreme values

## Documentation

Record:
- Detection method used
- Number of outliers found
- Treatment decisions
- Impact on final results
