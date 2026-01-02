"""
Session persistence manager.

Saves completed sessions to the database when they finish.
"""

import asyncio
from datetime import datetime
from typing import Any

from django.utils import timezone


async def persist_session(session_data: dict[str, Any]) -> int | None:
    """
    Persist a finished session to the database.

    Args:
        session_data: The in-memory session dict from SessionManager

    Returns:
        Session ID if saved successfully, None otherwise
    """
    from live.models import Session, SessionParticipant, SessionQuestion, SessionAnswer
    from quizzes.models import Topic, AnswerOption

    def _save():
        try:
            topic = Topic.objects.select_related('teacher').get(pk=session_data['topic_id'])
        except Topic.DoesNotExist:
            return None

        # Create Session
        session = Session.objects.create(
            code=session_data['session_id'],
            topic=topic,
            teacher=topic.teacher,
            status=Session.Status.FINISHED,
            started_at=session_data.get('started_at') or timezone.now(),
            finished_at=timezone.now(),
            time_per_question=session_data['time_per_question'],
            total_questions=len(session_data.get('answered_questions', [])),
        )

        # Create SessionQuestions
        sq_map = {}  # question_id -> SessionQuestion
        for order, q_data in enumerate(session_data.get('answered_questions', []), start=1):
            sq = SessionQuestion.objects.create(
                session=session,
                question_id=q_data['question_id'],
                order=order
            )
            sq_map[q_data['question_id']] = sq

        # Create SessionParticipants and their answers
        for sid, student_data in session_data.get('students', {}).items():
            # Calculate correct/wrong counts
            student_answers = session_data.get('student_answers', {}).get(sid, {})
            correct_count = 0
            wrong_count = 0

            for q_id, answer_data in student_answers.items():
                if answer_data.get('is_correct'):
                    correct_count += 1
                else:
                    wrong_count += 1

            participant = SessionParticipant.objects.create(
                session=session,
                student_name=student_data['name'],
                socket_id=sid,
                score=student_data.get('score', 0),
                correct_answers=correct_count,
                wrong_answers=wrong_count,
            )

            # Create SessionAnswers
            for q_id_str, answer_data in student_answers.items():
                q_id = int(q_id_str) if isinstance(q_id_str, str) else q_id_str
                sq = sq_map.get(q_id)
                if not sq:
                    continue

                SessionAnswer.objects.create(
                    session=session,
                    participant=participant,
                    session_question=sq,
                    selected_option_id=answer_data.get('option_id'),
                    is_correct=answer_data.get('is_correct', False),
                    answered_at=answer_data.get('answered_at'),
                    response_time_ms=answer_data.get('response_time_ms'),
                )

        return session.id

    return await asyncio.to_thread(_save)
