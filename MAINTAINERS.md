# PyFulmen - Maintainers

**Project**: pyfulmen
**Purpose**: Enterprise-grade Python helper library for FulmenHQ ecosystem
**Governance Model**: 3leaps Initiative

---

## Human Maintainers

### @3leapsdave (Dave Thompson) - Project Lead

- **Role**: Project Lead & Primary Maintainer
- **Responsibilities**:
  - Architecture oversight and design decisions
  - Release management and version strategy
  - Cross-language coordination (gofulmen, tsfulmen, rsfulmen)
  - Ecosystem standards compliance
  - Community engagement and contributor guidance
- **Contact**: dave.thompson@3leaps.net | GitHub [@3leapsdave](https://github.com/3leapsdave) | X [@3leapsdave](https://x.com/3leapsdave)
- **Timezone**: America/New_York
- **Availability**: Core hours (9AM-5PM ET)
- **Expertise**: Python architecture, enterprise logging, API design, cross-language standards

---

## AI Agent Operations

PyFulmen uses Crucible v0.3.2 role-based agentic operations. AI agents operate in **supervised mode** with human review before commits.

### Available Roles

| Role       | Purpose                                      | Escalates To                    |
| ---------- | -------------------------------------------- | ------------------------------- |
| `devlead`  | Implementation, features, bug fixes          | @3leapsdave for releases        |
| `devrev`   | Code review, four-eyes audit                 | @3leapsdave for disputes        |
| `infoarch` | Documentation, schemas, standards            | @3leapsdave for standards       |
| `secrev`   | Security review, vulnerability analysis      | @3leapsdave immediately         |
| `entarch`  | Cross-repo coordination, ecosystem alignment | @3leapsdave for decisions       |

See [Role Catalog](config/crucible-py/agentic/roles/README.md) for full role definitions.

### Operating Model

- **Mode**: Supervised (human reviews all commits)
- **Role Selection**: Agents declare role via `Role:` commit trailer
- **Attribution**: Follow [Agentic Attribution Standard](docs/crucible-py/standards/agentic-attribution.md)
- **Quality Gates**: `make check-all` must pass before commits

---

## Contribution Guidelines

### For Human Contributors

1. **Architecture Changes**: Discuss with @3leapsdave before implementation
2. **Standards Compliance**: Ensure changes align with FulmenHQ ecosystem standards
3. **Documentation**: Update relevant docs and examples
4. **Testing**: Maintain comprehensive test coverage with proper isolation
5. **Code Quality**: Follow Python best practices and pass all quality gates
6. **Performance**: Measure and document overhead for performance-sensitive changes

### For AI Agents

1. **Role Declaration**: Use appropriate role from the [Role Catalog](config/crucible-py/agentic/roles/README.md)
2. **Human Oversight**: Tag @3leapsdave for significant architectural decisions
3. **Safety Protocols**: Follow `REPOSITORY_SAFETY_PROTOCOLS.md` for all operations
4. **Quality Focus**: Prioritize correctness over speed in all implementations
5. **Ecosystem Thinking**: Consider impact on other *fulmen libraries
6. **Test Accountability**:
   - Never dismiss test failures without proper investigation
   - Always perform root cause analysis for failing tests
   - Ensure all mocks properly reflect actual imports and dependencies
7. **Quality Gate Compliance**:
   - Run `make check-all` before all commits
   - All issues must be fixed before proceeding
   - No exceptions without explicit maintainer approval

---

## Communication Channels

### Primary Channels

- **Development**: `#pyfulmen-development` (Mattermost)
- **Architecture**: `#fulmen-architecture` (cross-language coordination)
- **Releases**: `#fulmen-releases` (announcements)
- **Incidents**: `#fulmen-incidents` (critical issues)

### Issue Management

- **Bug Reports**: Use GitHub Issues with appropriate labels
- **Feature Requests**: Discuss in `#pyfulmen-development` before creating issues
- **Security Issues**: Report privately to maintainers@3leaps.net

### Review Process

1. **All PRs**: Require review from at least one maintainer
2. **Architecture Changes**: Must have approval from @3leapsdave
3. **Standards Changes**: Require ecosystem coordination
4. **Release Management**: Version bump and changelog updates

---

## Release Process

### Version Strategy

- **Development**: Semantic versioning for API compatibility
- **Documentation**: Always updated with release notes
- **Quality Gates**:
  - All tests must pass (100% pass rate required)
  - Linting and type checking must be clean
  - Code coverage must be maintained or improved
  - `make check-all` must pass before any commit
- **Release Coordination**: Align with other *fulmen libraries when possible

### Release Authority

- **Final Approval**: @3leapsdave has final release authority
- **Emergency Releases**: Can be executed by any maintainer with proper justification
- **Post-Release**: Monitor for issues and provide rapid response

---

## Decision Making

### Consensus Model

- **Technical Decisions**: @3leapsdave makes final call with maintainer input
- **Architecture Changes**: Require ecosystem-wide coordination
- **Standards Changes**: Must align with FulmenHQ guidelines
- **Process**: Document rationale in issues and commit messages

### Escalation

- **Technical Disputes**: @3leapsdave mediates with technical input
- **Process Issues**: Escalate to maintainers for resolution
- **Security Issues**: Immediate response from all maintainers

---

_Repository follows 3leaps governance model with human oversight and role-based AI agent collaboration._
