"""Journal service for daily work tracking."""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from src.models.journal import DailyJournal, SessionReflection, WorkSession
from src.services.search_service import SearchService
from src.storage.database import Database
from src.storage.repositories import JournalRepository
from src.storage.vector_store import VectorMemoryStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JournalService:
    """Daily work journal with AI-powered reflections."""

    def __init__(
        self,
        database: Database,
        vector_store: VectorMemoryStore,
        search_service: SearchService,
        sampling_service: Any = None,  # SamplingService when implemented
    ):
        self.database = database
        self.vector_store = vector_store
        self.search_service = search_service
        self.sampling_service = sampling_service
        self._lock = asyncio.Lock()

    async def start_work_session(self, task_description: str) -> dict[str, Any]:
        """Start tracking a work session.

        Args:
            task_description: What you're working on

        Returns:
            Dict with session info and tips
        """
        async with self._lock:
            try:
                # Get or create today's journal
                async with self.database.session() as session:
                    repo = JournalRepository(session)
                    journal = await repo.get_or_create_today()

                    # Check if there's already an active session
                    active_session = journal.get_active_session()
                    if active_session:
                        return {
                            "success": False,
                            "error": f"Session already active: {active_session.task}",
                            "tip": "Use end_work_session to complete current session first",
                        }

                    # Create new session
                    new_session = WorkSession(
                        task=task_description, start_time=datetime.now(timezone.utc)
                    )

                    # Save session
                    await repo.add_session(journal.id, new_session)

                logger.info(f"Started work session: {task_description}")

                return {
                    "success": True,
                    "session_id": new_session.id,
                    "task": task_description,
                    "started_at": new_session.start_time.isoformat(),
                    "message": f"Started working on: {task_description}",
                    "tip": "Use end_work_session when done to get AI reflection",
                }

            except Exception as e:
                logger.exception("Failed to start work session")
                return {"success": False, "error": f"Failed to start session: {str(e)}"}

    async def end_work_session(
        self,
        learnings: list[str] | None = None,
        challenges: list[str] | None = None,
        quick_note: str = "",
    ) -> dict[str, Any]:
        """End current work session and generate reflection.

        Args:
            learnings: Key learnings from this session
            challenges: Any blockers or difficulties
            quick_note: Additional notes

        Returns:
            Dict with session summary and reflection
        """
        async with self._lock:
            try:
                async with self.database.session() as session:
                    repo = JournalRepository(session)
                    journal = await repo.get_or_create_today()

                    # Get active session
                    active_session = journal.get_active_session()
                    if not active_session:
                        return {
                            "success": False,
                            "error": "No active work session found",
                            "tip": "Use start_working_on to begin a session",
                        }

                    # Update session details
                    active_session.end_time = datetime.now(timezone.utc)
                    active_session.learnings = learnings or []
                    active_session.challenges = challenges or []
                    active_session.notes = quick_note

                    # Save updated session
                    await repo.update_session(active_session)

                    # Generate reflection if significant session (>= 30 min)
                    reflection_text = ""
                    # For implementation, we keep 30m threshold as per spec
                    if active_session.duration_minutes >= 30:
                        reflection = await self._generate_session_reflection(
                            active_session
                        )

                        # Save reflection
                        await repo.save_reflection(reflection)

                        # Save to vector store for searchability
                        await self.vector_store.add_memory(
                            id=f"reflection_{reflection.session_id}",
                            content=reflection.reflection_text,
                            metadata={
                                "content_type": "session_reflection",
                                "date": journal.date.isoformat(),
                                "task": active_session.task,
                                "duration_minutes": active_session.duration_minutes,
                            },
                        )

                        reflection_text = reflection.reflection_text

                logger.info(
                    f"Ended work session: {active_session.task} ({active_session.duration_minutes}min)"
                )

                return {
                    "success": True,
                    "session_id": active_session.id,
                    "task": active_session.task,
                    "duration_minutes": active_session.duration_minutes,
                    "reflection": reflection_text,
                    "message": "Session ended. Reflection generated and saved."
                    if reflection_text
                    else "Session ended.",
                    "next": "Check recent reflections with: search_memory('reflection today')",
                }

            except Exception as e:
                logger.exception("Failed to end work session")
                return {"success": False, "error": f"Failed to end session: {str(e)}"}

    async def _generate_session_reflection(
        self, session: WorkSession
    ) -> SessionReflection:
        """Generate AI reflection for a work session.

        Args:
            session: The completed work session

        Returns:
            SessionReflection with AI-generated insights
        """
        # Search for related past work
        related_results = await self.search_service.search(query=session.task, limit=3)

        context_text = (
            "\n".join([f"- {r.content[:100]}..." for r in related_results])
            if related_results
            else "No related past work found."
        )

        # Build reflection prompt
        prompt = f"""Reflect on this work session: 

Task: {session.task}
Duration: {session.duration_minutes} minutes
Notes: {session.notes if session.notes else 'No notes'}
Files modified: {', '.join(session.files_touched[:5]) if session.files_touched else 'None'}
Learnings: {', '.join(session.learnings) if session.learnings else 'None'}
Challenges: {', '.join(session.challenges) if session.challenges else 'None'}

Related past work:
{context_text}

Generate a brief reflection (2-3 sentences) about:
1. What was accomplished
2. Key insights or patterns
3. How this builds upon past work

Be concise, insightful, and encouraging."""

        # Generate using sampling service if available
        if self.sampling_service:
            try:
                reflection_text = await self.sampling_service.request_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.7,
                )
            except Exception as e:
                logger.warning(f"Sampling service failed: {e}")
                reflection_text = f"Session completed on {session.task}."
        else:
            # Fallback: simple summary
            reflection_text = (
                f"Completed {session.duration_minutes}-minute session on {session.task}. "
                f"{'Learned: ' + ', '.join(session.learnings[:2]) + '. ' if session.learnings else ''}"
                f"{'Faced challenges with: ' + ', '.join(session.challenges[:2]) + '.' if session.challenges else ''}"
            )

        # Extract key insights (simplified for now)
        key_insights = session.learnings[:3] if session.learnings else []

        # Get related memory IDs
        related_memory_ids = [r.id for r in related_results[:3]]

        return SessionReflection(
            session_id=session.id,
            task=session.task,
            duration_minutes=session.duration_minutes,
            reflection_text=str(reflection_text).strip(),
            key_insights=key_insights,
            related_memories=related_memory_ids,
        )

    async def generate_daily_summary(
        self, target_date: date | None = None
    ) -> dict[str, Any]:
        """Generate end-of-day summary with AI insights.

        Args:
            target_date: Date to summarize (defaults to today)

        Returns:
            Dict with daily summary and statistics
        """
        try:
            if target_date is None:
                target_date = datetime.now(timezone.utc).date()

            async with self.database.session() as session:
                repo = JournalRepository(session)

                # Get journal for date
                journal = await repo.get_by_date(target_date)

                if not journal or not journal.work_sessions:
                    return {
                        "success": False,
                        "message": f"No work sessions recorded for {target_date}",
                        "date": target_date.isoformat(),
                    }

                # Calculate statistics
                total_minutes = journal.total_work_minutes
                tasks_count = journal.tasks_worked_on
                all_learnings = []
                all_challenges = []

                for sess in journal.work_sessions:
                    all_learnings.extend(sess.learnings)
                    all_challenges.extend(sess.challenges)

                # Generate AI summary
                summary_text = await self._generate_ai_summary(
                    journal, total_minutes, tasks_count, all_learnings, all_challenges
                )

                # Save summary to journal
                journal.end_of_day_reflection = summary_text
                await repo.save(journal)

                # Save summary as searchable memory
                await self.vector_store.add_memory(
                    id=f"daily_summary_{target_date.isoformat()}",
                    content=f"Daily Summary ({target_date})\n\n{summary_text}\n\nStats: {total_minutes/60:.1f}h, {tasks_count} tasks",
                    metadata={
                        "content_type": "daily_summary",
                        "date": target_date.isoformat(),
                        "work_minutes": total_minutes,
                        "tasks_count": tasks_count,
                    },
                )

            logger.info(f"Generated daily summary for {target_date}")

            return {
                "success": True,
                "date": target_date.isoformat(),
                "summary": summary_text,
                "stats": {
                    "total_hours": round(total_minutes / 60, 1),
                    "tasks_worked_on": tasks_count,
                    "sessions": len(journal.work_sessions),
                    "learnings_captured": len(all_learnings),
                    "challenges_noted": len(all_challenges),
                },
            }

        except Exception as e:
            logger.exception("Failed to generate daily summary")
            return {"success": False, "error": f"Failed to generate summary: {str(e)}"}

    async def _generate_ai_summary(
        self,
        journal: DailyJournal,
        total_minutes: int,
        tasks_count: int,
        learnings: list[str],
        challenges: list[str],
    ) -> str:
        """Generate AI-powered daily summary.

        Args:
            journal: The daily journal
            total_minutes: Total work time
            tasks_count: Number of tasks
            learnings: All learnings
            challenges: All challenges

        Returns:
            AI-generated summary text
        """
        # Build context
        sessions_summary = "\n".join(
            [f"- {s.task} ({s.duration_minutes}min)" for s in journal.work_sessions]
        )

        learnings_text = (
            "\n".join([f"- {l}" for l in learnings[:5]])
            if learnings
            else "None recorded"
        )
        challenges_text = (
            "\n".join([f"- {c}" for c in challenges[:5]])
            if challenges
            else "None recorded"
        )

        prompt = f"""Summarize this workday:

Date: {journal.date}
Total work time: {total_minutes} minutes ({total_minutes/60:.1f} hours)
Tasks: {tasks_count}

Work Sessions:
{sessions_summary}

Learnings: 
{learnings_text}

Challenges:
{challenges_text}

Generate a thoughtful daily summary that:
1. Highlights the main theme of the day
2. Notes key progress or insights
3. Suggests what to focus on tomorrow
4. Acknowledges challenges empathetically

Keep it personal and encouraging (3-4 sentences)."""

        # Generate using sampling service if available
        if self.sampling_service:
            try:
                summary = await self.sampling_service.request_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.8,
                )
            except Exception as e:
                logger.warning(f"Sampling service failed: {e}")
                summary = f"Workday complete. {total_minutes} minutes spent on {tasks_count} tasks."
        else:
            # Fallback: structured summary
            tasks_list = sorted(list(set(s.task for s in journal.work_sessions)))
            tasks_str = ", ".join(tasks_list[:3])
            if len(tasks_list) > 3:
                tasks_str += f" and {len(tasks_list) - 3} others"

            summary = (
                f"You worked for {total_minutes/60:.1f} hours on {tasks_str}. "
                f"{'Your key learnings: ' + ', '.join(learnings[:2]) + '. ' if learnings else ''}"
                f"{'Tomorrow, consider addressing: ' + ', '.join(challenges[:2]) + '.' if challenges else 'Keep up the momentum!'}"
            )

        return str(summary).strip()

    async def get_morning_briefing(self) -> str:
        """Generate morning briefing with yesterday's summary and today's focus.

        Returns:
            Formatted morning briefing text
        """
        try:
            # Get yesterday's journal
            yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

            async with self.database.session() as session:
                repo = JournalRepository(session)
                yesterday_journal = await repo.get_by_date(yesterday)

            # Build briefing
            briefing_parts = [
                f"# Morning Briefing - {datetime.now().strftime('%A, %B %d')}",
                "",
            ]

            # Yesterday's recap
            if yesterday_journal and yesterday_journal.end_of_day_reflection:
                briefing_parts.extend(
                    [
                        "## Yesterday's Recap",
                        yesterday_journal.end_of_day_reflection,
                        "",
                    ]
                )
            elif yesterday_journal:
                briefing_parts.extend(
                    [
                        "## Yesterday's Recap",
                        f"Worked on {len(yesterday_journal.work_sessions)} sessions.",
                        "",
                    ]
                )
            else:
                briefing_parts.extend(
                    [
                        "## Yesterday's Recap",
                        "No journal entry found for yesterday.",
                        "",
                    ]
                )

            # Today's focus placeholder
            briefing_parts.extend(
                ["## Today's Focus", "*What's your intention for today?*", ""]
            )

            return "\n".join(briefing_parts)

        except Exception as e:
            logger.exception("Failed to generate morning briefing")
            return f"# Morning Briefing\n\nFailed to generate briefing: {str(e)}"
