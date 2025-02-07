# Contributing to InfraOS AI

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Test with mock mode: `K8S_MOCK_MODE=true`
4. Run tests: `pytest`
5. Run linter: `ruff check . && ruff format .`
6. Open a Pull Request

## Adding New Integrations

- K8s integrations: add to `backend/k8s/`
- Cloud provider support: add to `backend/integrations/`
- New AI analyzers: add to `backend/ai/`

## Code Style

- Python: PEP 8, enforced via `ruff`
- TypeScript: strict mode
- Commit messages: Conventional Commits

## Testing

Always test both `K8S_MOCK_MODE=true` (CI) and with a real cluster when possible.
