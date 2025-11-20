# Transform Feature

Apply appropriate transformation to a single feature.

## Transformation Selection

Choose transformation based on:
- Feature distribution (normal, skewed, categorical)
- Analysis requirements (linearity, normality)
- Domain knowledge (log scales, thresholds)
- Model requirements (scaling, encoding)

## Transformation Process

1. **Analyze current state**: Distribution, range, missing values
2. **Select transformation**: Based on goals and constraints
3. **Apply transformation**: Implement chosen method
4. **Validate result**: Check distribution and range
5. **Document change**: Record transformation for reproducibility

## Common Transformations

- **Log**: For right-skewed positive values
- **Square root**: For count data
- **Box-Cox**: Power transformation for normality
- **Standardization**: (x - mean) / std
- **Normalization**: (x - min) / (max - min)
