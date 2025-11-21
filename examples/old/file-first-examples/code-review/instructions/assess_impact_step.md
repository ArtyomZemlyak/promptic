# Assess Impact and Risk

Evaluate how changes affect the broader system and identify potential risks.

## Impact Assessment

1. **Scope of changes**: How many components are affected?
2. **Breaking changes**: Will this require updates elsewhere?
3. **User impact**: How will end users be affected?
4. **Migration needs**: Are data migrations or config changes required?

## Risk Evaluation

- **High risk**: Changes to core functionality, security-sensitive code, or critical paths
- **Medium risk**: Changes to non-critical features or well-tested areas
- **Low risk**: Minor bug fixes, documentation updates, or isolated improvements

## Mitigation Strategies

- Suggest additional testing for high-risk changes
- Recommend feature flags for gradual rollout
- Propose monitoring and alerting for production changes
