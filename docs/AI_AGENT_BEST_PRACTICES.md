# AI Agent Development Best Practices for Books Project

This document provides conventions for AI coding assistants (e.g., Cursor, Copilot) contributing to the Books Project. Follow these standards to keep code quality high and changes easy to review.

## General Workflow
- Keep changes small and focused; explain rationale in commit messages and PR descriptions.
- Prefer incremental improvements over sweeping refactors unless explicitly requested.
- Document assumptions and TODOs in code comments or docs when behavior is non-obvious.
- When touching data files, describe expected schema and transformations in commit messages and tests.

## Python Style and Quality
- Use clear, explicit names; avoid abbreviations that hide intent.
- Keep functions small and cohesive. Extract helpers rather than nesting complex logic.
- Type annotate functions and public variables. Prefer concrete types over `Any`.
- Avoid mutable default arguments. Use `Optional[...]` with `None` checks where needed.
- Handle errors narrowly; do not blanket `except Exception` unless you re-raise with context.
- Keep logging structured and actionable. Use `logger.warning`/`logger.error` with context values.
- Avoid side effects in module import time. Prefer functions or `if __name__ == "__main__":` guards.

## Testing
- Add or update tests when behavior changes. Place FastAPI route tests alongside other API tests.
- Use meaningful test names that describe behavior (`test_creates_book_when_payload_valid`).
- Arrange/Act/Assert: set up data, perform the action, then assert expected outputs or status codes.
- Prefer factory helpers/fixtures for test data to reduce duplication.

## FastAPI Guidelines
- Keep request/response models in Pydantic schemas; validate inputs at the boundary.
- Return explicit response models rather than raw dicts where practical.
- Use dependency injection for shared resources (DB sessions, config) instead of globals.
- Ensure routes provide proper status codes (201 for creation, 404 for missing resources, etc.).
- Add concise docstrings and `summary`/`description` metadata on routes for automatic docs.
- Validate query/path parameters with types, bounds, and enums when applicable.

## Data and I/O
- Avoid hard-coding file paths; make them configurable or derive from project settings.
- Document expected CSV/JSON columns when reading or writing data.
- Use context managers for file and network I/O to prevent leaks.

## Dependencies and Packaging
- Keep `requirements.txt` synchronized with imports; remove unused dependencies.
- Prefer standard library and existing project utilities before adding new packages.
- Pin versions only when necessary (compatibility, security).

## Performance and Security
- Prefer lazy loading or pagination for endpoints that may return large datasets.
- Validate and sanitize user inputs; never trust client-provided data.
- Avoid exposing internal exceptions directly; map to safe HTTP responses.
- Ensure secrets and tokens stay out of code, commits, and logs.

## Documentation and Comments
- Update `README` or route-specific docs when behavior changes in a user-visible way.
- Keep comments actionable and current; remove stale notes during refactors.
- Include examples in docstrings when they clarify usage or edge cases.

## Git Hygiene
- Format code before committing and run relevant tests locally.
- Write descriptive commit messages summarizing intent and scope.
- Keep PR descriptions clear: what changed, why, and how to verify.

