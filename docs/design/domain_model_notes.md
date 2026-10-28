# Domain Model Design Decisions - Week 3

## Design Choices
1. **Separation of Concerns:** Models are built purely as Python standard dataclasses and enums. They contain zero database logic, ORM mapping (like SQLAlchemy Base), or web framework dependencies (like FastAPI/Pydantic validation models), keeping the domain completely agnostic.
2. **Encapsulated State Machine:** Valid status transitions are explicitly regulated inside a class method map (`ComplaintStatus.valid_transitions()`). The `transition_status` mutator method actively prevents illegal jumps (e.g., bypassing `UNDER_REVIEW`).
3. **Auditability:** Every successful transition appends a immutable-style `ComplaintStatusEvent` tracking record into a local list history, supporting traceability requirements.