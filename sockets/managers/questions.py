"""
Question handling for Live Quiz Socket.IO Server

Handles:
- Loading questions from database
- Question delivery to students
- Answer validation
"""

import asyncio
from typing import Any, Optional
from datetime import datetime

from .sessions import active_sessions, SessionData
from ..utils.time import TimeUtils


def _get_correct_option_id_sync(question_id: int) -> Optional[int]:
    """Synchronous function to get correct option from DB."""
    from quizzes.models import AnswerOption

    try:
        correct_option = AnswerOption.objects.get(
            question_id=question_id,
            is_correct=True
        )
        return correct_option.id
    except AnswerOption.DoesNotExist:
        return None
    except AnswerOption.MultipleObjectsReturned:
        correct_option = AnswerOption.objects.filter(
            question_id=question_id,
            is_correct=True
        ).first()
        return correct_option.id if correct_option else None


def _load_topic_data_sync(topic_id: int) -> Optional[dict[str, Any]]:
    """Synchronous function to load topic data."""
    from quizzes.models import Topic

    try:
        topic = Topic.objects.get(id=topic_id)
        return {
            "id": topic.id,
            "title": topic.title,
            "description": topic.description,
            "time_per_question": topic.question_timer,
        }
    except Topic.DoesNotExist:
        return None


def _load_question_ids_sync(topic_id: int) -> list[int]:
    """Synchronous function to load question IDs."""
    from quizzes.models import Question

    return list(
        Question.objects.filter(topic_id=topic_id)
        .order_by("order_index")
        .values_list("id", flat=True)
    )


def _load_question_sync(question_id: int) -> Optional[dict[str, Any]]:
    """Synchronous function to load question with options."""
    from quizzes.models import Question

    try:
        question = Question.objects.prefetch_related("options").get(id=question_id)
        correct_option_id = None
        options = []
        for opt in question.options.all():
            options.append({
                "id": opt.id,
                "text": opt.text,
            })
            if opt.is_correct:
                correct_option_id = opt.id

        return {
            "id": question.id,
            "text": question.text,
            "options": options,
            "correct_option_id": correct_option_id,
        }
    except Question.DoesNotExist:
        return None


class QuestionManager:
    """Manager class for question-related operations."""

    # Points awarded for correct answer
    POINTS_CORRECT = 20

    @staticmethod
    async def load_topic_data(topic_id: int) -> Optional[dict[str, Any]]:
        """Load topic data from database."""
        return await asyncio.to_thread(_load_topic_data_sync, topic_id)

    @staticmethod
    async def load_question_ids(topic_id: int) -> list[int]:
        """Load all question IDs for a topic."""
        return await asyncio.to_thread(_load_question_ids_sync, topic_id)

    @staticmethod
    async def load_question(question_id: int) -> Optional[dict[str, Any]]:
        """Load a question with its options from database."""
        return await asyncio.to_thread(_load_question_sync, question_id)

    @staticmethod
    async def get_correct_option_id(question_id: int) -> Optional[int]:
        """Get the correct option ID for a question."""
        return await asyncio.to_thread(_get_correct_option_id_sync, question_id)

    @staticmethod
    def setup_question(
        session: SessionData,
        question_id: int,
    ) -> None:
        """
        Setup session state for a new question.

        Args:
            session: Session data dictionary
            question_id: ID of the question to setup
        """
        now = TimeUtils.now()
        time_limit = session["time_per_question"]

        session["current_question"] = question_id
        session["answers"] = {}
        session["question_started_at"] = now
        session["question_deadline"] = TimeUtils.add_seconds(now, time_limit)

    @staticmethod
    def build_question_payload(
        question_data: dict[str, Any],
        time_per_question: int
    ) -> dict[str, Any]:
        """
        Build the question payload to send to students.

        Args:
            question_data: Question data from database
            time_per_question: Time allowed for the question

        Returns:
            Formatted question payload
        """
        return {
            "type": "question",
            "id": question_data["id"],
            "text": question_data["text"],
            "options": question_data["options"],
            "time": time_per_question,
        }

    @staticmethod
    def is_answer_valid(session: SessionData) -> bool:
        """
        Check if answering is currently valid for a session.

        Args:
            session: Session data dictionary

        Returns:
            True if answering is valid, False otherwise
        """
        # Check stage
        if session["stage"] != "running":
            return False

        # Check deadline
        if TimeUtils.is_expired(session["question_deadline"]):
            return False

        return True

    @staticmethod
    def build_answer_result(
        correct: bool,
        correct_option_id: int,
        student_answer: Optional[int],
        score_delta: int,
        score_total: int
    ) -> dict[str, Any]:
        """
        Build the answer result payload for a student.

        Args:
            correct: Whether the answer was correct
            correct_option_id: ID of the correct option
            student_answer: ID of the student's answer (or None)
            score_delta: Points gained this question
            score_total: Total score after this question

        Returns:
            Formatted answer result payload
        """
        return {
            "type": "answer_result",
            "correct": correct,
            "correct_option": correct_option_id,
            "your_answer": student_answer,
            "score_delta": score_delta,
            "score_total": score_total,
        }
