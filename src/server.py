"""MCP Memory Server - FastMCP server implementation.

This is the main entry point for the MCP Memory Server.
It exposes resources, tools, and prompts for LLM memory management.
"""

import argparse
import asyncio
from pathlib import Path
from typing import Any

from fastmcp import FastMCP, Context

from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
from src.middleware.auth import http_auth_middleware
from src.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from src.models import (
    ActiveContext,
    Decision,
    ProjectBrief,
    Task,
    TechStack,
)
from src.models.project import TechStackItem
from src.services.service_manager import ServiceManager
from src.utils.config import Settings, get_settings
from src.utils.logger import get_logger
from src.monitoring.collectors import system_metrics_collector

logger = get_logger(__name__)


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Server lifespan manager."""
    logger.info("Starting MCP Memory Server...")
    
    # Expose metrics endpoint
    # We use a separate port (8081) to avoid conflicts with FastMCP internal routing
    # and to ensure metrics are always accessible regardless of transport.
    try:
        from prometheus_client import start_http_server
        import threading
        
        # Start metrics server on 8081 in a daemon thread
        logger.info("Starting Prometheus metrics server on port 8081")
        start_http_server(8081)
        logger.info("Metrics exposed at http://localhost:8081")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        try:
            # Fallback: Start metrics server on side port
            from prometheus_client import start_http_server
            import threading
            
            # Start metrics server on 8081 in a daemon thread
            # Port 9090 is usually Prometheus itself
            logger.info("Starting Prometheus metrics server on port 8081")
            start_http_server(8081)
            metrics_mounted = True
        except Exception as e:
            logger.error(f"Failed to start fallback metrics server: {e}")

    # Initialize services
    await get_services()
    
    # Start background tasks
    await system_metrics_collector.start()
    
    yield
    
    # Shutdown logic
    logger.info("Stopping MCP Memory Server...")
    await system_metrics_collector.stop()

# Initialize FastMCP server
mcp = FastMCP(
    name="memory-server",
    version="1.0.0",
    lifespan=server_lifespan,
)

# Global service manager instance
_service_manager: ServiceManager | None = None


async def get_services():
    """Get initialized services."""
    global _service_manager
    if _service_manager is None:
        settings = get_settings()
        _service_manager = ServiceManager()
        await _service_manager.initialize(settings)
    return _service_manager.get_services()


# =============================================================================
# RESOURCES (Read-only access)
# =============================================================================


@mcp.resource("memory://project/brief")
async def get_project_brief() -> dict[str, Any]:
    """Get project overview information."""
    memory, _, _ = await get_services()
    brief = await memory.get_project_brief()
    if brief:
        return brief.model_dump(mode="json")
    return {"error": "No project brief found. Use set_project_brief tool to create one."}


@mcp.resource("memory://journal/today")
async def get_today_journal() -> dict[str, Any]:
    """Get today's work journal."""
    _, _, journal_service = await get_services()
    summary = await journal_service.generate_daily_summary()
    return summary


@mcp.resource("memory://project/tech-stack")
async def get_tech_stack() -> dict[str, Any]:
    """Get technology stack configuration."""
    memory, _, _ = await get_services()
    tech_stack = await memory.get_tech_stack()
    if tech_stack:
        return tech_stack.model_dump(mode="json")
    return {"error": "No tech stack found. Use set_tech_stack tool to create one."}


@mcp.resource("memory://context/active")
async def get_active_context() -> dict[str, Any]:
    """Get current working context."""
    memory, _, _ = await get_services()
    context = await memory.get_active_context()
    return context.model_dump(mode="json")


@mcp.resource("memory://decisions")
async def list_decisions() -> list[dict[str, Any]]:
    """List all architectural decisions."""
    memory, _, _ = await get_services()
    decisions = await memory.list_decisions()
    return [d.model_dump(mode="json") for d in decisions]


@mcp.resource("memory://decisions/{decision_id}")
async def get_decision(decision_id: str) -> dict[str, Any]:
    """Get a specific decision by ID."""
    memory, _, _ = await get_services()
    decision = await memory.get_decision(decision_id)
    if decision:
        return decision.model_dump(mode="json")
    return {"error": f"Decision '{decision_id}' not found"}


@mcp.resource("memory://progress")
async def get_progress() -> dict[str, Any]:
    """Get tasks grouped by status."""
    memory, _, _ = await get_services()
    grouped = await memory.get_tasks_grouped()
    return {
        status: [t.model_dump(mode="json") for t in tasks]
        for status, tasks in grouped.items()
    }


@mcp.resource("memory://tasks")
async def list_tasks() -> list[dict[str, Any]]:
    """List all tasks."""
    memory, _, _ = await get_services()
    tasks = await memory.list_tasks()
    return [t.model_dump(mode="json") for t in tasks]


@mcp.resource("memory://tasks/{task_id}")
async def get_task(task_id: str) -> dict[str, Any]:
    """Get a specific task by ID."""
    memory, _, _ = await get_services()
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
) -> dict[str, Any]:
    """Set or update the project brief.

    Args:
        name: Project name
        description: Project description
        goals: List of project goals
        version: Project version

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        brief = ProjectBrief(
            name=name,
            description=description,
            goals=goals or [],
            version=version,
        )
        await memory.save_project_brief(brief)
        return {"success": True, "data": f"Project brief set: {name}", "error": None}
    except Exception as e:
        logger.exception(f"Error in set_project_brief: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def set_tech_stack(
    languages: list[str] | None = None,
    frameworks: list[dict[str, str]] | None = None,
    tools: list[str] | None = None,
) -> dict[str, Any]:
    """Set or update the technology stack.

    Args:
        languages: Programming languages used
        frameworks: Frameworks with versions (list of {name, version})
        tools: Development tools

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()

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
        return {"success": True, "data": "Tech stack updated", "error": None}
    except Exception as e:
        logger.exception(f"Error in set_tech_stack: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def update_active_context(
    current_task: str | None = None,
    related_files: list[str] | None = None,
    notes: str | None = None,
    working_branch: str | None = None,
) -> dict[str, Any]:
    """Update the current working context.

    Args:
        current_task: Current task being worked on
        related_files: Files relevant to current work
        notes: Free-form notes about current context
        working_branch: Git branch being worked on

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        await memory.update_active_context(
            current_task=current_task,
            related_files=related_files,
            notes=notes,
            working_branch=working_branch,
        )
        return {"success": True, "data": f"Context updated: {current_task or 'cleared'}", "error": None}
    except Exception as e:
        logger.exception(f"Error in update_active_context: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def clear_active_context() -> dict[str, Any]:
    """Clear the current working context.

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        context = ActiveContext()
        await memory.update_active_context(
            current_task="",
            related_files=[],
            relevant_decisions=[],
            notes="",
            working_branch="",
        )
        return {"success": True, "data": "Context cleared", "error": None}
    except Exception as e:
        logger.exception(f"Error in clear_active_context: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def log_decision(
    title: str,
    decision: str,
    rationale: str,
    alternatives_considered: list[str] | None = None,
    consequences: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Log an architectural decision.

    Args:
        title: Decision title/summary
        decision: The decision that was made
        rationale: Why this decision was made
        alternatives_considered: Other options that were considered
        consequences: Expected consequences of this decision
        tags: Categorization tags

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        result = await memory.log_decision(
            title=title,
            decision=decision,
            rationale=rationale,
            alternatives_considered=alternatives_considered,
            consequences=consequences,
            tags=tags,
        )
        return {"success": True, "data": f"Decision logged: {result.id} - {title}", "error": None}
    except Exception as e:
        logger.exception(f"Error in log_decision: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new task.

    Args:
        title: Task title
        description: Task description
        priority: Task priority (high, medium, low)
        tags: Categorization tags

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        result = await memory.create_task(
            title=title,
            description=description,
            priority=priority,
            tags=tags,
        )
        return {"success": True, "data": f"Task created: {result.id} - {title}", "error": None}
    except Exception as e:
        logger.exception(f"Error in create_task: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def update_task_status(
    task_id: str,
    status: str,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    """Update a task's status.

    Args:
        task_id: Task ID
        status: New status (done, doing, next, blocked)
        blocked_reason: Reason if blocked

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        result = await memory.update_task_status(
            task_id=task_id,
            status=status,
            blocked_reason=blocked_reason,
        )
        if result:
            return {"success": True, "data": f"Task {task_id} status updated to: {status}", "error": None}
        return {"success": False, "data": None, "error": f"Task {task_id} not found"}
    except Exception as e:
        logger.exception(f"Error in update_task_status: {e}")
        return {"success": False, "data": None, "error": str(e)}


@mcp.tool
async def search_memory(
    query: str,
    limit: int = 5,
    content_types: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Semantic search across all memory.

    Args:
        query: Search query text
        limit: Maximum number of results
        content_types: Filter by content types (decision, task, note, etc.)
        tags: Filter by tags

    Returns:
        Response with success status and search results or error message
    """
    try:
        _, search, _ = await get_services()
        results = await search.search(
            query=query,
            limit=limit,
            content_types=content_types,
            tags=tags,
        )
        return {"success": True, "data": results, "error": None}
    except Exception as e:
        logger.exception(f"Error in search_memory: {e}")
        return {"success": False, "data": [], "error": str(e)}


@mcp.tool
async def add_memory_note(
    content: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Add a free-form memory note.

    Args:
        content: Note content
        tags: Categorization tags

    Returns:
        Response with success status and data or error message
    """
    try:
        memory, _, _ = await get_services()
        result = await memory.add_memory(
            content=content,
            content_type="note",
            tags=tags,
        )
        return {"success": True, "data": f"Note added: {result.id}", "error": None}
    except Exception as e:
        logger.exception(f"Error in add_memory_note: {e}")
        return {"success": False, "data": None, "error": str(e)}


# =============================================================================
# JOURNAL TOOLS (Daily Work Tracking)
# =============================================================================

@mcp.tool
async def start_working_on(
    task: str
) -> dict[str, Any]:
    """Start a work session on a specific task. 
    
    This automatically tracks your work time, updates active context,
    and will generate AI reflections when you finish the session.
    
    Perfect for: 
    - Beginning a coding session
    - Starting a design task
    - Kicking off a research session
    - Any focused work block
    
    Args:
        task: Brief description of what you're working on (e.g., "Implementing user authentication")
    
    Returns:
        Response with session info
    """
    try:
        # Validate input
        if not task or len(task.strip()) == 0:
            return {
                "success": False,
                "error": "Task description is required",
                "tip": "Provide a brief description of what you're working on"
            }
        
        if len(task) > 500:
            return {
                "success": False,
                "error": "Task description too long (max 500 characters)",
                "tip": "Keep it concise - just the main focus"
            }
        
        # Get services
        memory, search, journal = await get_services()
        
        # Start session
        result = await journal.start_work_session(task.strip())
        
        # Also update active context for consistency
        if result.get("success"):
            await memory.update_active_context(
                current_task=task.strip(),
                notes=f"Started at {result['started_at']}"
            )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in start_working_on: {e}")
        return {
            "success": False,
            "error": f"Invalid input: {str(e)}"
        }
    except Exception as e:
        logger.exception("Unexpected error in start_working_on")
        return {
            "success": False,
            "error": "Failed to start work session. Please try again."
        }


@mcp.tool
async def end_work_session(
    what_i_learned: list[str] | None = None,
    challenges_faced: list[str] | None = None,
    quick_note: str = ""
) -> dict[str, Any]:
    """End current work session and get AI-powered reflection.
    
    Completes your active work session, automatically calculates duration,
    generates insights about your work, and connects it to related past work.
    
    Args: 
        what_i_learned: List of key learnings or insights (optional)
        challenges_faced: List of blockers or difficulties (optional)
        quick_note: Any additional context or notes (optional)
    
    Returns:
        Response with reflection
    """
    try:
        # Validate inputs
        if what_i_learned and len(what_i_learned) > 10:
            return {
                "success": False,
                "error": "Too many learnings (max 10)",
                "tip": "Focus on the most important insights"
            }
        
        if challenges_faced and len(challenges_faced) > 10:
            return {
                "success": False,
                "error": "Too many challenges (max 10)",
                "tip": "List the main blockers only"
            }
        
        if quick_note and len(quick_note) > 2000:
            return {
                "success": False,
                "error": "Note too long (max 2000 characters)",
                "tip": "Keep notes concise"
            }
        
        # Get services
        memory, _, journal = await get_services()
        
        # End session with reflection
        result = await journal.end_work_session(
            learnings=what_i_learned,
            challenges=challenges_faced,
            quick_note=quick_note.strip() if quick_note else ""
        )
        
        # Clear active context if session ended successfully
        if result.get("success"):
            await memory.update_active_context(
                current_task="",
                notes="Session completed"
            )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in end_work_session: {e}")
        return {
            "success": False,
            "error": f"Invalid input: {str(e)}"
        }
    except Exception as e:
        logger.exception("Unexpected error in end_work_session")
        return {
            "success": False,
            "error": "Failed to end work session. Please try again."
        }


@mcp.tool
async def how_was_my_day(
    date: str | None = None
) -> dict[str, Any]:
    """Get AI-generated summary of your workday.
    
    Args:
        date: Optional date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Daily summary and stats
    """
    try:
        # Parse date if provided
        target_date = None
        if date:
            try:
                from datetime import datetime
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid date format. Use YYYY-MM-DD (e.g., 2025-01-08)"
                }
        
        # Get services
        _, _, journal = await get_services()
        
        # Generate daily summary
        result = await journal.generate_daily_summary(target_date)
        
        return result
        
    except Exception as e:
        logger.exception("Unexpected error in how_was_my_day")
        return {
            "success": False,
            "error": "Failed to generate daily summary. Please try again."
        }


@mcp.tool
async def set_morning_intention(
    intention: str
) -> dict[str, Any]: 
    """Set your intention or goal for the day.
    
    Start your day by declaring what you want to focus on or accomplish.
    This intention will be included in your daily summary and help you
    stay aligned with your goals. 
    
    Args:
        intention: What you plan to focus on or accomplish today
    
    Returns: 
        Response with success status
    """
    try:
        # Validate
        if not intention or len(intention.strip()) == 0:
            return {
                "success": False,
                "error": "Intention is required",
                "tip": "What do you want to focus on today?"
            }
        
        if len(intention) > 1000:
            return {
                "success": False,
                "error": "Intention too long (max 1000 characters)",
                "tip": "Keep it focused and actionable"
            }
        
        # Get services
        _, _, journal = await get_services()
        
        # Get or create today's journal
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            daily_journal = await repo.get_or_create_today()
            daily_journal.morning_intention = intention.strip()
            await repo.save(daily_journal)
        
        logger.info(f"Set morning intention: {intention[:50]}...")
        
        return {
            "success": True,
            "message": "Morning intention set! 🌅",
            "intention": intention.strip(),
            "tip": "Use start_working_on when you begin your first task"
        }
        
    except Exception as e:
        logger.exception("Unexpected error in set_morning_intention")
        return {
            "success": False,
            "error": "Failed to set morning intention. Please try again."
        }


@mcp.tool
async def capture_win(
    win: str
) -> dict[str, Any]:
    """Capture a win or achievement for today.
    
    Celebrate your progress! Record wins, achievements, or breakthroughs
    as they happen. These will be included in your daily summary.
    
    Args:
        win: Description of the win or achievement
    
    Returns:
        Response with success status
    """
    try:
        # Validate
        if not win or len(win.strip()) == 0:
            return {
                "success": False,
                "error": "Win description is required",
                "tip": "What did you accomplish?"
            }
        
        if len(win) > 500:
            return {
                "success": False,
                "error": "Win description too long (max 500 characters)",
                "tip": "Keep it concise"
            }
        
        # Get services
        _, _, journal = await get_services()
        
        # Get or create today's journal
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            daily_journal = await repo.get_or_create_today()
            
            # Add win
            if not daily_journal.wins:
                daily_journal.wins = []
            daily_journal.wins.append(win.strip())
            
            await repo.save(daily_journal)
        
        logger.info(f"Captured win: {win[:50]}...")
        
        return {
            "success": True,
            "message": "Win captured! 🎉",
            "win": win.strip(),
            "total_wins_today": len(daily_journal.wins),
            "tip": "Keep celebrating your progress!"
        }
        
    except Exception as e:
        logger.exception("Unexpected error in capture_win")
        return {
            "success": False,
            "error": "Failed to capture win. Please try again."
        }


# =============================================================================
# JOURNAL RESOURCES (Read-only access)
# =============================================================================

@mcp.resource("memory://journal/today")
async def get_today_journal() -> dict[str, Any]:
    """Get today's complete journal with all sessions."""
    try:
        _, _, journal = await get_services()
        
        # Get today's journal
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            daily_journal = await repo.get_or_create_today()
        
        return daily_journal.model_dump(mode="json")
        
    except Exception as e:
        logger.exception("Failed to get today's journal")
        return {"error": f"Failed to retrieve journal: {str(e)}"}


@mcp.resource("memory://journal/{date}")
async def get_journal_by_date(date: str) -> dict[str, Any]:
    """Get journal for a specific date (YYYY-MM-DD format)."""
    try:
        from datetime import datetime
        
        # Parse date
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        _, _, journal = await get_services()
        
        # Get journal
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            daily_journal = await repo.get_by_date(target_date)
        
        if not daily_journal:
            return {"error": f"No journal found for {date}"}
        
        return daily_journal.model_dump(mode="json")
        
    except Exception as e:
        logger.exception(f"Failed to get journal for {date}")
        return {"error": f"Failed to retrieve journal: {str(e)}"}


@mcp.resource("memory://journal/recent")
async def get_recent_journals() -> list[dict[str, Any]]:
    """Get journals for the past 7 days."""
    try:
        _, _, journal = await get_services()
        
        # Get recent journals
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            journals = await repo.get_recent_journals(days=7)
        
        return [j.model_dump(mode="json") for j in journals]
        
    except Exception as e: 
        logger.exception("Failed to get recent journals")
        return [{"error": f"Failed to retrieve journals: {str(e)}"}]


@mcp.resource("memory://journal/stats/weekly")
async def get_weekly_stats() -> dict[str, Any]:
    """Get work statistics for the past week."""
    try:
        _, _, journal = await get_services()
        
        # Get last 7 days of journals
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            journals = await repo.get_recent_journals(days=7)
        
        # Calculate stats
        total_minutes = sum(j.total_work_minutes for j in journals)
        total_sessions = sum(len(j.work_sessions) for j in journals)
        total_tasks = sum(j.tasks_worked_on for j in journals)
        days_worked = len([j for j in journals if j.work_sessions])
        total_wins = sum(len(j.wins) for j in journals)
        
        # Calculate averages
        avg_hours_per_day = (total_minutes / 60 / days_worked) if days_worked > 0 else 0
        avg_sessions_per_day = (total_sessions / days_worked) if days_worked > 0 else 0
        
        return {
            "period": "Last 7 days",
            "total_hours": round(total_minutes / 60, 1),
            "days_worked": days_worked,
            "total_sessions": total_sessions,
            "total_tasks": total_tasks,
            "total_wins": total_wins,
            "averages": {
                "hours_per_day": round(avg_hours_per_day, 1),
                "sessions_per_day": round(avg_sessions_per_day, 1)
            }
        }
        
    except Exception as e:
        logger.exception("Failed to get weekly stats")
        return {"error": f"Failed to retrieve stats: {str(e)}"}


# =============================================================================
# PROMPTS (Context injection)
# =============================================================================


@mcp.prompt
async def context_prompt() -> str:
    """Inject active context into prompt."""
    memory, _, _ = await get_services()
    context = await memory.get_active_context()
    return context.to_prompt()


@mcp.prompt
async def recent_decisions_prompt(limit: int = 3) -> str:
    """Inject recent decisions into prompt."""
    memory, _, _ = await get_services()
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
    memory, _, _ = await get_services()
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
    memory, _, _ = await get_services()

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


@mcp.prompt
async def morning_briefing_prompt() -> str:
    """Generate morning briefing with yesterday's summary and today's focus.
    
    Perfect for starting your workday with context about: 
    - Yesterday's accomplishments
    - Pending tasks
    - Recent decisions to keep in mind
    - Suggested focus areas
    
    Use this prompt at the start of your day to get oriented.
    """
    try:
        memory, search, journal = await get_services()
        
        # Get morning briefing
        briefing = await journal.get_morning_briefing()
        
        # Enhance with pending tasks
        tasks = await memory.list_tasks()
        incomplete = [t for t in tasks if t.status in ("doing", "next")]
        
        # Add recent decisions
        decisions = await memory.recent_decisions(limit=2)
        
        # Build comprehensive briefing
        if incomplete:
            briefing += "\n## Today's Focus Areas\n\n**Pending Tasks:**\n"
            for task in incomplete[:5]: 
                # Ensure task.status is string
                status = str(task.status).upper() if task.status else "UNKNOWN"
                briefing += f"- [{status}] {task.title}\n"
        
        if decisions:
            briefing += "\n**Recent Decisions to Remember:**\n"
            for dec in decisions: 
                briefing += f"- {dec.title}\n"
        
        briefing += "\n---\n\n*What's your intention for today? Use `set_morning_intention` to declare it.*"
        
        return briefing
        
    except Exception as e:
        logger.exception("Failed to generate morning briefing")
        return f"# Morning Briefing\n\nFailed to generate briefing: {str(e)}"


@mcp.prompt
async def active_session_prompt() -> str:
    """Get status of your current work session.
    
    Shows:
    - What you're currently working on
    - How long you've been working
    - Related context
    
    Use this to quickly check your current focus.
    """
    try:
        _, _, journal = await get_services()
        
        # Get today's journal
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            daily_journal = await repo.get_or_create_today()
        
        # Check for active session
        active_session = daily_journal.get_active_session()
        
        if not active_session:
            return "# No Active Session\n\nYou're not currently tracking a work session.\n\nUse `start_working_on(\"task description\")` to begin."
        
        # Build session status
        duration = active_session.duration_minutes
        hours = duration // 60
        minutes = duration % 60
        
        status = f"""# Active Work Session

**Task:** {active_session.task}

**Duration:** {f"{hours}h " if hours > 0 else ""}{minutes}m

**Started:** {active_session.start_time.strftime('%I:%M %p')}

---

*Keep up the focus! Use `end_work_session()` when you're ready to wrap up.*
"""
        
        return status
        
    except Exception as e: 
        logger.exception("Failed to generate active session prompt")
        return f"# Active Session\n\nFailed to check session: {str(e)}"


@mcp.prompt  
async def daily_progress_prompt() -> str:
    """Get snapshot of today's progress.
    
    Shows:
    - Work sessions completed
    - Total time worked
    - Wins captured
    - Current momentum
    
    Use this throughout the day to track your progress. 
    """
    try:
        _, _, journal = await get_services()
        
        # Get today's journal
        from src.storage.repositories import JournalRepository
        async with journal.database.session() as session:
            repo = JournalRepository(session)
            daily_journal = await repo.get_or_create_today()
        
        # Calculate stats
        completed_sessions = [s for s in daily_journal.work_sessions if s.end_time is not None]
        active_session = daily_journal.get_active_session()
        total_minutes = daily_journal.total_work_minutes
        
        # Build progress report
        progress = f"""# Today's Progress - {daily_journal.date.strftime('%A, %B %d')}

## Work Sessions
- **Completed:** {len(completed_sessions)} sessions
- **Total Time:** {total_minutes // 60}h {total_minutes % 60}m
- **Tasks:** {daily_journal.tasks_worked_on}
"""
        
        if active_session:
            progress += f"\n**Currently Working:** {active_session.task} ({active_session.duration_minutes}m)\n"
        
        if daily_journal.wins:
            progress += f"\n## Wins Today 🎉\n"
            for win in daily_journal.wins:
                progress += f"- {win}\n"
        
        # Add motivation
        if total_minutes >= 240:  # 4+ hours
            progress += "\n---\n\n✨ **Great focus today!** You're in the zone."
        elif total_minutes >= 120:  # 2+ hours
            progress += "\n---\n\n💪 **Good progress!** Keep the momentum going."
        else:
            progress += "\n---\n\n🌱 **Getting started!** Every session counts."
        
        return progress
        
    except Exception as e: 
        logger.exception("Failed to generate daily progress prompt")
        return f"# Daily Progress\n\nFailed to generate progress: {str(e)}"


# =============================================================================
# Server Entry Point
# =============================================================================


async def cleanup() -> None:
    """Cleanup resources on shutdown."""
    global _service_manager
    if _service_manager:
        await _service_manager.cleanup()
        _service_manager = None
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
            # Apply authentication middleware for HTTP transport
            from fastapi import FastAPI
            from slowapi.errors import RateLimitExceeded
            
            # Get the underlying FastAPI app if available
            if hasattr(mcp, 'app') and isinstance(mcp.app, FastAPI):
                # Add rate limiting
                mcp.app.state.limiter = limiter
                mcp.app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
                
                # Add authentication middleware
                mcp.app.middleware("http")(http_auth_middleware)
                logger.info("HTTP authentication and rate limiting enabled")
            
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        else:
            # STDIO transport - no authentication needed (local use)
            mcp.run()
    finally:
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
