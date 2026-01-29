# Contributing to Vibeguard

Thanks for your interest in contributing to Vibeguard!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/vibeguard.io.git`
3. Install dependencies: `pnpm install`
4. Create a branch: `git checkout -b feature/your-feature`

## Development

```bash
# Install dependencies
pnpm install

# Build all packages
pnpm build

# Run in development mode
pnpm dev

# Run tests
pnpm test
```

## Project Structure

```
vibeguard/
├── packages/
│   ├── core/        # Core logging engine
│   ├── sdk/         # Agent integration SDK
│   └── dashboard/   # Web UI (coming soon)
├── examples/        # Example integrations
└── docs/            # Documentation
```

## Commit Messages

Keep commits focused and messages clear:

```
feat: add undo support for file operations
fix: handle null risk level in classifier
docs: update README with new examples
```

## Pull Requests

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Keep PRs focused on a single change

## Code Style

- TypeScript for all packages
- Use Prettier for formatting
- Follow existing patterns in the codebase

## Questions?

Open an issue or start a discussion. We're happy to help!
