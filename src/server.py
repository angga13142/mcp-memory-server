"""MCP Memory Server - FastMCP server implementation.

This is the main entry point for the MCP Memory Server.
It exposes resources, tools, and prompts for LLM memory management.
"""

import argparse
import asyncio
from pathlib import Path
from typing import Any

from fastmcp import FastMCP, Context

from src.models import (
    ActiveContext,
    Decision,
    ProjectBrief,
    Task,
    TechStack,
)
from src.models.project import TechStackItem
from src.services.memory_service import MemoryService
from src.services.search_service import SearchService
from src.storage.database import Database, close_database
from src.storage.vector_store import VectorMemoryStore, close_vector_store
from src.utils.config import Settings, get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="memory-server",
    version="1.0.0",
)

# Global service instances (initialized on startup)
_memory_service: MemoryService | None = None
_search_service: SearchService | None = None


async def get_services() -> tuple[MemoryService, SearchService]:
    """Get initialized services."""
    global _memory_service, _search_service
    if _memory_service is None or _search_service is None:
        settings = get_settings()
        database = Database(settings)
        await database.init()
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        _memory_service = MemoryService(database, vector_store)
        _search_service = SearchService(vector_store)
    return _memory_service, _search_service


# =============================================================================
# RESOURCES (Read-only access)
# =============================================================================


@mcp.resource("memory://project/brief")
async def get_project_brief() -> dict[str, Any]:
    """Get project overview information."""
    memory, _ = await get_services()
    brief = await memory.get_project_brief()
    if brief:
        return brief.model_dump(mode="json")
    return {"error": "No project brief found. Use set_project_brief tool to create one."}


@mcp.resource("memory://project/tech-stack")
async def get_tech_stack() -> dict[str, Any]:
    """Get technology stack configuration."""
    memory, _ = await get_services()
    tech_stack = await memory.get_tech_stack()
    if tech_stack:
        return tech_stack.model_dump(mode="json")
    return {"error": "No tech stack found. Use set_tech_stack tool to create one."}


@mcp.resource("memory://context/active")
async def get_active_context() -> dict[str, Any]:
    """Get current working context."""
    memory, _ = await get_services()
    context = await memory.get_active_context()
    return context.model_dump(mode="json")


@mcp.resource("memory://decisions")
async def list_decisions() -> list[dict[str, Any]]:
    """List all architectural decisions."""
    memory, _ = await get_services()
    decisions = await memory.list_decisions()
    return [d.model_dump(mode="json") for d in decisions]


@mcp.resource("memory://decisions/{decision_id}")
async def get_decision(decision_id: str) -> dict[str, Any]:
    """Get a specific decision by ID."""
    memory, _ = await get_services()
    decision = await memory.get_decision(decision_id)
    if decision:
        return decision.model_dump(mode="json")
    return {"error": f"Decision '{decision_id}' not found"}


@mcp.resource("memory://progress")
async def get_progress() -> dict[str, Any]:
    """Get tasks grouped by status."""
    memory, _ = await get_services()
    grouped = await memory.get_tasks_grouped()
    return {
        status: [t.model_dump(mode="json") for t in tasks]
        for status, tasks in grouped.items()
    }


@mcp.resource("memory://tasks")
async def list_tasks() -> list[dict[str, Any]]:
    """List all tasks."""
    memory, _ = await get_services()
    tasks = await memory.list_tasks()
    return [t.model_dump(mode="json") for t in tasks]


@mcp.resource("memory://tasks/{task_id}")
async def get_task(task_id: str) -> dict[str, Any]:
    """Get a specific task by ID."""
    memory, _ = await get_services()
    task = await memory.get_task(task_id)
    if task:
        return task.model_dump(mode="json")
    return {"error": f"Task '{task_id}' not found"}


# =============================================================================
# TOOLS (Write operations)
# =============================================================================


@mcp.tool
async def set_project_brief(
    name: str,
    description: str,
    goals: list[str] | None = None,
    version: str = "1.0.0",
) -> str:
    """Set or update the project brief.

    Args:
        name: Project name
        description: Project description
        goals: List of project goals
        version: Project version
    """
    memory, _ = await get_services()
    brief = ProjectBrief(
        name=name,
        description=description,
        goals=goals or [],
        version=version,
    )
    await memory.save_project_brief(brief)
    return f"Project brief set: {name}"


@mcp.tool
async def set_tech_stack(
    languages: list[str] | None = None,
    frameworks: list[dict[str, str]] | None = None,
    tools: list[str] | None = None,
) -> str:
    """Set or update the technology stack.

    Args:
        languages: Programming languages used
        frameworks: Frameworks with versions (list of {name, version})
        tools: Development tools
    """
    memory, _ = await get_services()

    framework_items = []
    if frameworks:
        for f in frameworks:
            framework_items.append(TechStackItem(
                name=f.get("name", ""),
                version=f.get("version", ""),
            ))

    tech_stack = TechStack(
        languages=languages or [],
        frameworks=framework_items,
        tools=tools or [],
    )
    await memory.save_tech_stack(tech_stack)
    return "Tech stack updated"


@mcp.tool
async def update_active_context(
    current_task: str | None = None,
    related_files: list[str] | None = None,
    notes: str | None = None,
    working_branch: str | None = None,
) -> str:
    """Update the current working context.

    Args:
        current_task: Current task being worked on
        related_files: Files relevant to current work
        notes: Free-form notes about current context
        working_branch: Git branch being worked on
    """
    memory, _ = await get_services()
    await memory.update_active_context(
        current_task=current_task,
        related_files=related_files,
        notes=notes,
        working_branch=working_branch,
    )
    return f"Context updated: {current_task or 'cleared'}"


@mcp.tool
async def clear_active_context() -> str:
    """Clear the current working context."""
    memory, _ = await get_services()
    context = ActiveContext()
    await memory.update_active_context(
        current_task="",
        related_files=[],
        relevant_decisions=[],
        notes="",
        working_branch="",
    )
    return "Context cleared"


@mcp.tool
async def log_decision(
    title: str,
    decision: str,
    rationale: str,
    alternatives_considered: list[str] | None = None,
    consequences: list[str] | None = None,
    tags: list[str] | None = None,
) -> str:
    """Log an architectural decision.

    Args:
        title: Decision title/summary
        decision: The decision that was made
        rationale: Why this decision was made
        alternatives_considered: Other options that were considered
        consequences: Expected consequences of this decision
        tags: Categorization tags
    """
    memory, _ = await get_services()
    result = await memory.log_decision(
        title=title,
        decision=decision,
        rationale=rationale,
        alternatives_considered=alternatives_considered,
        consequences=consequences,
        tags=tags,
    )
    return f"Decision logged: {result.id} - {title}"


@mcp.tool
async def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    tags: list[str] | None = None,
) -> str:
    """Create a new task.

    Args:
        title: Task title
        description: Task description
        priority: Task priority (high, medium, low)
        tags: Categorization tags
    """
    memory, _ = await get_services()
    result = await memory.create_task(
        title=title,
        description=description,
        priority=priority,
        tags=tags,
    )
    return f"Task created: {result.id} - {title}"


@mcp.tool
async def update_task_status(
    task_id: str,
    status: str,
    blocked_reason: str | None = None,
) -> str:
    """Update a task's status.

    Args:
        task_id: Task ID
        status: New status (done, doing, next, blocked)
        blocked_reason: Reason if blocked
    """
    memory, _ = await get_services()
    result = await memory.update_task_status(
        task_id=task_id,
        status=status,
        blocked_reason=blocked_reason,
    )
    if result:
        return f"Task {task_id} status updated to: {status}"
    return f"Task {task_id} not found"


@mcp.tool
async def search_memory(
    query: str,
    limit: int = 5,
    content_types: list[str] | None = None,
    tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Semantic search across all memory.

    Args:
        query: Search query text
        limit: Maximum number of results
        content_types: Filter by content types (decision, task, note, etc.)
        tags: Filter by tags

    Returns:
        List of search results with content, metadata, and relevance score
    """
    _, search = await get_services()
    results = await search.search(
        query=query,
        limit=limit,
        content_types=content_types,
        tags=tags,
    )
    return results


@mcp.tool
async def add_memory_note(
    content: str,
    tags: list[str] | None = None,
) -> str:
    """Add a free-form memory note.

    Args:
        content: Note content
        tags: Categorization tags
    """
    memory, _ = await get_services()
    result = await memory.add_memory(
        content=content,
        content_type="note",
        tags=tags,
    )
    return f"Note added: {result.id}"


# =============================================================================
# PROMPTS (Context injection)
# =============================================================================


@mcp.prompt
async def context_prompt() -> str:
    """Inject active context into prompt."""
    memory, _ = await get_services()
    context = await memory.get_active_context()
    return context.to_prompt()


@mcp.prompt
async def recent_decisions_prompt(limit: int = 3) -> str:
    """Inject recent decisions into prompt."""
    memory, _ = await get_services()
    decisions = await memory.recent_decisions(limit)

    if not decisions:
        return "No recent decisions logged."

    lines = ["Recent Decisions:"]
    for d in decisions:
        lines.append(f"\n## {d.title}")
        lines.append(f"Decision: {d.decision}")
        lines.append(f"Rationale: {d.rationale}")
        if d.tags:
            lines.append(f"Tags: {', '.join(d.tags)}")
    return "\n".join(lines)


@mcp.prompt
async def progress_summary_prompt() -> str:
    """Inject progress summary into prompt."""
    memory, _ = await get_services()
    grouped = await memory.get_tasks_grouped()

    lines = ["Progress Summary:"]

    if grouped["doing"]:
        lines.append(f"\n**In Progress ({len(grouped['doing'])}):**")
        for t in grouped["doing"][:5]:
            lines.append(f"- {t.title}")

    if grouped["blocked"]:
        lines.append(f"\n**Blocked ({len(grouped['blocked'])}):**")
        for t in grouped["blocked"][:3]:
            lines.append(f"- {t.title}: {t.blocked_reason or 'No reason'}")

    if grouped["next"]:
        lines.append(f"\n**Next Up ({len(grouped['next'])}):**")
        for t in grouped["next"][:5]:
            lines.append(f"- {t.title}")

    lines.append(f"\n**Completed:** {len(grouped['done'])} tasks")

    return "\n".join(lines)


@mcp.prompt
async def full_context_prompt() -> str:
    """Inject full context including active context, recent decisions, and progress."""
    memory, _ = await get_services()

    parts = []

    # Project brief
    brief = await memory.get_project_brief()
    if brief:
        parts.append(f"# Project: {brief.name}\n{brief.description}")

    # Active context
    context = await memory.get_active_context()
    if context.current_task:
        parts.append(f"\n## Current Context\n{context.to_prompt()}")

    # Recent decisions
    decisions = await memory.recent_decisions(2)
    if decisions:
        parts.append("\n## Recent Decisions")
        for d in decisions:
            parts.append(f"- **{d.title}**: {d.decision}")

    # Progress
    grouped = await memory.get_tasks_grouped()
    doing = grouped.get("doing", [])
    if doing:
        parts.append(f"\n## In Progress ({len(doing)})")
        for t in doing[:3]:
            parts.append(f"- {t.title}")

    return "\n".join(parts) if parts else "No context available."


# =============================================================================
# Server Entry Point
# =============================================================================


async def cleanup() -> None:
    """Cleanup resources on shutdown."""
    await close_database()
    await close_vector_store()
    logger.info("Server shutdown complete")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Memory Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port (default: 8080)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Configuration file path",
    )

    args = parser.parse_args()

    # Load configuration
    if Path(args.config).exists():
        settings = Settings.from_yaml(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    else:
        settings = get_settings()

    # Configure logging
    logger.info(f"Starting {settings.server.name} v{settings.server.version}")
    logger.info(f"Transport: {args.transport}")

    try:
        if args.transport == "http":
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        else:
            mcp.run()
    finally:
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
