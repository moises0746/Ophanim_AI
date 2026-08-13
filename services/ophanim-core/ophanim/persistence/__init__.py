"""Persistence implementations for the workflow ports.

The in-memory store satisfies the current bounded slice (mirroring the
existing ``InMemoryTaskService`` pattern). PostgreSQL is the authoritative
future system of record (ADR-011) and will implement the same ports.
"""
