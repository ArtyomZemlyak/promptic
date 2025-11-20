# Validate Data Schema

Verify that data structure matches expected schema and constraints.

## Schema Validation

1. **Check required fields**: Ensure all mandatory columns exist
2. **Verify data types**: Confirm each column has expected type
3. **Validate constraints**: Check ranges, formats, and business rules
4. **Document deviations**: Note any schema mismatches

## Common Validations

- Numeric ranges (e.g., age 0-120, percentage 0-100)
- String formats (e.g., email, phone, date)
- Required vs optional fields
- Enum values (e.g., status codes)
- Referential integrity (if applicable)

## Handling Schema Issues

- Report all violations clearly
- Suggest schema fixes when possible
- Document acceptable deviations
- Create schema migration plan if needed
