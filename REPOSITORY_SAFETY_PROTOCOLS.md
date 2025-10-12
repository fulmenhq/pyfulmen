# PyFulmen – Repository Safety Protocols

This document outlines the safety protocols for PyFulmen repository operations, adapted from Crucible standards for library-specific needs.

## 🔑 Quick Reference

- **Human Oversight Required**: All architectural changes, major features, and releases need @3leapsdave approval
- **AI Agent Coordination**: All AI agents must use assigned identities from `MAINTAINERS.md`
- **Use Make Targets**: Prefer `make` commands for consistency
- **Plan Changes**: Document work in `.plans/` before implementation
- **Quality Gates**: No merges without passing all tests and quality checks

## 🚨 High-Risk Operations

### Operations Requiring Additional Oversight

| Operation | Risk Level | Required Approvals | Safety Checks |
|------------|--------------|-------------------|---------------|
| **Architecture Changes** | 🔴 High | @3leapsdave + maintainer consensus | Design review, impact analysis |
| **Breaking API Changes** | 🔴 High | @3leapsdave approval | Migration guide, deprecation timeline |
| **Release Management** | 🟡 Medium | @3leapsdave final approval | Version validation, changelog |
| **Schema Updates** | 🟡 Medium | Maintainer review | Schema validation, compatibility |
| **Standards Changes** | 🟡 Medium | Ecosystem coordination | Cross-language impact analysis |
| **Dependency Updates** | 🟡 Medium | Security review | License compatibility, vulnerability scan |

### Safety Protocols for High-Risk Operations

1. **Pre-Implementation Review**
   - Create design document in `.plans/`
   - Discuss in `#pyfulmen-development` (Mattermost)
   - Get approval from @3leapsdave
   - Document impact and migration strategy

2. **Implementation Phase**
   - Use feature branches for all changes
   - Comprehensive testing before merge
   - Code review from at least one maintainer
   - Update documentation and examples

3. **Release Phase**
   - Version bump following semantic versioning
   - Complete changelog with breaking changes noted
   - Test installation and basic usage
   - Coordinate with other *fulmen libraries if needed

## 🔧 Standard Operations

### Development Workflow
```bash
# Standard development cycle
make sync-crucible    # Sync latest standards
make test            # Run comprehensive test suite
make lint            # Check code quality
make fmt             # Format code consistently
make build           # Build distribution packages
```

### Release Workflow
```bash
# Release preparation
make release-check   # Verify all requirements met
make release-prepare # Sync assets and update docs
make release-build   # Build distribution packages
```

### AI Agent Operations
- **Identity Verification**: Check `MAINTAINERS.md` before taking action
- **Safety Protocol Review**: Consult this document before operations
- **Human Oversight**: Tag @3leapsdave for architectural decisions
- **Documentation**: Update relevant docs for all changes

## 🚨 Incident Response

### Critical Incident Process
1. **Immediate Assessment**: Evaluate impact on users and ecosystem
2. **Communication**: Notify in `#fulmen-incidents` with severity level
3. **Resolution**: Fix and deploy with appropriate urgency
4. **Post-Mortem**: Document root cause and prevention measures

### Security Issues
1. **Private Reporting**: Email maintainers@3leaps.net
2. **Immediate Response**: Acknowledge within 24 hours
3. **Coordination**: Work with FulmenHQ security team if needed
4. **Disclosure**: Follow responsible disclosure practices

## 📋 Planning Requirements

### Work Planning
- **Use `.plans/` Directory**: All significant work must be planned here
- **Include Timeline**: Start date, duration, and milestones
- **Risk Assessment**: Identify potential blockers and mitigation strategies
- **Success Criteria**: Define measurable outcomes and acceptance criteria

### Architecture Decisions
- **Document Rationale**: Record decision context and alternatives considered
- **Cross-Language Impact**: Consider effects on gofulmen and tsfulmen
- **Ecosystem Alignment**: Ensure consistency with FulmenHQ standards
- **Future Planning**: Consider extensibility and maintenance requirements

## 🔍 Quality Assurance

### Pre-Merge Checklist
- [ ] All tests passing (`make test`)
- [ ] Code quality checks passing (`make lint`)
- [ ] Documentation updated (`make docs`)
- [ ] Schema validation passing
- [ ] Security scan clean
- [ ] Performance benchmarks acceptable
- [ ] Breaking changes documented with migration guide

### Release Checklist
- [ ] Version number updated appropriately
- [ ] CHANGELOG.md updated with all changes
- [ ] README.md updated with new features
- [ ] Examples tested and updated
- [ ] API documentation current
- [ ] Distribution packages built successfully

## 📞 Communication Protocols

### Mattermost Channels
- **Development**: `#pyfulmen-development` (day-to-day development)
- **Architecture**: `#fulmen-architecture` (cross-language coordination)
- **Incidents**: `#fulmen-incidents` (critical issues)
- **Releases**: `#fulmen-releases` (version announcements)

### GitHub Workflow
- **Issues**: Use templates with appropriate labels
- **Pull Requests**: Require review and approval
- **Discussions**: Use for architecture proposals and questions
- **Releases**: Create GitHub releases with comprehensive notes

### External Communication
- **Community**: Respond to issues and discussions promptly
- **Ecosystem**: Coordinate with other *fulmen maintainers
- **Users**: Provide clear migration guides and support

---

## References

- [Crucible Repository Safety Protocols](../crucible/REPOSITORY_SAFETY_PROTOCOLS.md)
- [FulmenHQ Architecture Standards](docs/crucible-py/architecture/fulmen-helper-library-standard.md)
- [Maintainers](MAINTAINERS.md)
- [AI Agents](AGENTS.md)
- [Development Planning](.plans/)

---

*Repository follows FulmenHQ safety protocols with human oversight and AI agent coordination.*