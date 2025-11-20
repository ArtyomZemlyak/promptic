# Check Dependencies

Review how the changes interact with external dependencies and internal modules.

## Dependency Review

1. **New dependencies**: Are new packages necessary and justified?
2. **Version updates**: Do dependency updates introduce breaking changes?
3. **Internal dependencies**: Are module imports correct and necessary?
4. **Circular dependencies**: Are there any circular import issues?

## Checklist

- [ ] New dependencies are documented
- [ ] Version constraints are specified
- [ ] No unnecessary dependencies added
- [ ] Internal imports follow project structure
- [ ] No circular dependencies introduced

## Security Considerations

- Verify dependencies don't have known vulnerabilities
- Check license compatibility
- Ensure dependencies are actively maintained
