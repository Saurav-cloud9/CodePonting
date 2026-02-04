"""
ENGINE MODULE

Responsibility:
- Drive the event loop.
- Feed data events to strategy.
- Route signals to the broker adapter.
- Coordinate portfolio updates.

Rules:
- Environment-agnostic.
- No strategy-specific logic.
- No direct data source or broker calls.
- Uses adapters for all external interaction.

This is the system's core runtime.
"""
