# CLAUDE.md

This file provides guidance for AI assistants (like Claude) working in this repository.

## Repository Overview

- **Repository**: toto5032/Claude
- **Status**: Newly initialized repository — project structure and tooling are not yet established.

## Getting Started

This repository does not yet have a defined tech stack, build system, or project structure. When adding initial project scaffolding, follow these principles:

- Choose a tech stack appropriate for the project's goals.
- Include a `README.md` describing the project purpose, setup instructions, and usage.
- Add a `.gitignore` suited to the chosen language/framework.
- Set up linting and formatting from the start.

## Development Workflow

### Branching

- Feature branches should follow the pattern: `claude/<description>-<id>`
- Develop on the designated feature branch, never push directly to `main`.

### Commits

- Write clear, descriptive commit messages.
- Keep commits focused — one logical change per commit.
- Do not commit secrets, credentials, or `.env` files.

### Code Quality

- Prefer simple, readable code over clever abstractions.
- Only add complexity when clearly justified by requirements.
- Write tests alongside new functionality.
- Validate at system boundaries (user input, external APIs); trust internal code.

## Project Structure

> **Note**: No project files exist yet. Update this section as the project takes shape.

```
Claude/
├── CLAUDE.md        # This file — AI assistant guidance
└── (awaiting initial project scaffolding)
```

## Conventions

- Follow the established style of existing code when making changes.
- Do not introduce new dependencies without justification.
- Keep PRs small and focused for easier review.

## Common Commands

> **Note**: Update this section once build tools and scripts are configured.

```bash
# (No commands configured yet)
```

## AI Assistant Guidelines

When working in this repository:

1. **Read before writing** — Understand existing code before making changes.
2. **Stay focused** — Only make changes that are directly requested or clearly necessary.
3. **Don't over-engineer** — Avoid adding features, abstractions, or error handling beyond what's needed.
4. **Be security-conscious** — Never commit secrets; avoid introducing OWASP top-10 vulnerabilities.
5. **Test your changes** — Run available tests and linters before committing.
6. **Update docs** — Keep this file and other documentation current as the project evolves.
