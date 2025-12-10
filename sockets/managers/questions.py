"""
Question handling for Live Quiz Socket.IO Server

Handles:
- Loading questions from database
- Question delivery to students
- Answer validation
"""

from typing import Any, Optional
from datetime import datetime

from asgiref.sync import sync_to_async

from .sessions import active_sessions, SessionData
from ..utils.time import TimeUtils


class QuestionManager:
    """Manager class for question-related operations."""

    # Points awarded for correct answer
    POINTS_CORRECT = 20

    @staticmethod
    @sync_to_async(thread_sensitive=False)
    def load_topic_data(topic_id: int) -> Optional[dict[str, Any]]:
        """
        Load topic data from database.

        Args:
            topic_id: ID of the topic

        Returns:
            Dictionary with topic data or None if not found
        """
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

    @staticmethod
    @sync_to_async(thread_sensitive=False)
    def load_question_ids(topic_id: int) -> list[int]:
        """
        Load all question IDs for a topic.

        Args:
            topic_id: ID of the topic

        Returns:
            List of question IDs
        """
        from quizzes.models import Question

        return list(
            Question.objects.filter(topic_id=topic_id)
            .order_by("order_index")
            .values_list("id", flat=True)
        )

    @staticmethod
    @sync_to_async(thread_sensitive=False)
    def load_question(question_id: int) -> Optional[dict[str, Any]]:
        """
        Load a question with its options from database.

        Args:
            question_id: ID of the question

        Returns:
            Dictionary with question data or None if not found
        """
        from quizzes.models import Question

        try:
            question = Question.objects.prefetch_related("options").get(id=question_id)
            options = [
                {
                    "id": opt.id,
                    "text": opt.text,
                }
                for opt in question.options.all()
            ]
            return {
                "id": question.id,
                "text": question.text,
                "options": options,
            }
        except Question.DoesNotExist:
            return None

    @staticmethod
    @sync_to_async(thread_sensitive=False)
    def get_correct_option_id(question_id: int) -> Optional[int]:
        """
        Get the correct option ID for a question.

        Args:
            question_id: ID of the question

        Returns:
            ID of the correct option or None if not found
        """
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
            # If multiple correct answers, return the first one
            correct_option = AnswerOption.objects.filter(
                question_id=question_id,
                is_correct=True
            ).first()
            return correct_option.id if correct_option else None

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
