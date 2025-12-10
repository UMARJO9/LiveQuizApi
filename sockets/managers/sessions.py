"""
Session management for Live Quiz Socket.IO Server

Handles:
- Session creation and storage
- Session state management
- Student management within sessions
"""

import random
import string
from datetime import datetime
from typing import Any, Optional, TypedDict


class StudentData(TypedDict):
    """Type definition for student data."""
    name: str
    score: int


class SessionData(TypedDict):
    """Type definition for session data."""
    session_id: str
    topic_id: int
    teacher_sid: str
    time_per_question: int
    question_queue: list[int]
    current_question: Optional[int]
    current_correct_option: Optional[int]  # Cached correct option ID
    question_started_at: Optional[datetime]
    question_deadline: Optional[datetime]
    answers: dict[str, int]  # sid -> option_id
    students: dict[str, StudentData]  # sid -> StudentData
    stage: str  # waiting | running | finished


# Global storage for active sessions
active_sessions: dict[str, SessionData] = {}


class SessionManager:
    """Manager class for quiz session operations."""

    # Session stages
    STAGE_WAITING = "waiting"
    STAGE_RUNNING = "running"
    STAGE_FINISHED = "finished"

    @staticmethod
    def generate_session_id(length: int = 4) -> str:
        """
        Generate a unique 4-character session ID like 'AB12'.

        Args:
            length: Length of the session ID (default: 4)

        Returns:
            Unique session ID string
        """
        characters = string.ascii_uppercase + string.digits
        while True:
            session_id = ''.join(random.choices(characters, k=length))
            if session_id not in active_sessions:
                return session_id

    @staticmethod
    def create_session(
        topic_id: int,
        teacher_sid: str,
        time_per_question: int,
        question_ids: list[int]
    ) -> SessionData:
        """
        Create a new quiz session.

        Args:
            topic_id: ID of the topic/quiz
            teacher_sid: Socket ID of the teacher
            time_per_question: Time allowed per question in seconds
            question_ids: List of question IDs to include

        Returns:
            Created session data
        """
        # Shuffle question IDs
        shuffled_questions = question_ids.copy()
        random.shuffle(shuffled_questions)

        session_id = SessionManager.generate_session_id()

        session: SessionData = {
            "session_id": session_id,
            "topic_id": topic_id,
            "teacher_sid": teacher_sid,
            "time_per_question": time_per_question,
            "question_queue": shuffled_questions,
            "current_question": None,
            "current_correct_option": None,
            "question_started_at": None,
            "question_deadline": None,
            "answers": {},
            "students": {},
            "stage": SessionManager.STAGE_WAITING,
        }

        active_sessions[session_id] = session
        return session

    @staticmethod
    def get_session(session_id: str) -> Optional[SessionData]:
        """
        Get session by ID.

        Args:
            session_id: The session ID to look up

        Returns:
            Session data if found, None otherwise
        """
        return active_sessions.get(session_id)

    @staticmethod
    def get_session_by_teacher(teacher_sid: str) -> Optional[SessionData]:
        """
        Get session by teacher's socket ID.

        Args:
            teacher_sid: Teacher's socket ID

        Returns:
            Session data if found, None otherwise
        """
        for session in active_sessions.values():
            if session["teacher_sid"] == teacher_sid:
                return session
        return None

    @staticmethod
    def get_session_by_student(student_sid: str) -> Optional[SessionData]:
        """
        Get session by student's socket ID.

        Args:
            student_sid: Student's socket ID

        Returns:
            Session data if found, None otherwise
        """
        for session in active_sessions.values():
            if student_sid in session["students"]:
                return session
        return None

    @staticmethod
    def add_student(session_id: str, sid: str, name: str) -> bool:
        """
        Add a student to a session.

        Args:
            session_id: The session ID
            sid: Student's socket ID
            name: Student's display name

        Returns:
            True if student was added, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return False

        if session["stage"] != SessionManager.STAGE_WAITING:
            return False

        session["students"][sid] = {
            "name": name,
            "score": 0
        }
        return True

    @staticmethod
    def remove_student(session_id: str, sid: str) -> bool:
        """
        Remove a student from a session.

        Args:
            session_id: The session ID
            sid: Student's socket ID

        Returns:
            True if student was removed, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return False

        if sid in session["students"]:
            del session["students"][sid]
            return True
        return False

    @staticmethod
    def get_student_list(session_id: str) -> list[dict[str, Any]]:
        """
        Get list of students in a session.

        Args:
            session_id: The session ID

        Returns:
            List of student dictionaries with sid, name, and score
        """
        session = active_sessions.get(session_id)
        if not session:
            return []

        return [
            {
                "sid": sid,
                "name": data["name"],
                "score": data["score"]
            }
            for sid, data in session["students"].items()
        ]

    @staticmethod
    def set_stage(session_id: str, stage: str) -> bool:
        """
        Set session stage.

        Args:
            session_id: The session ID
            stage: New stage (waiting/running/finished)

        Returns:
            True if stage was set, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return False

        session["stage"] = stage
        return True

    @staticmethod
    def pop_next_question(session_id: str) -> Optional[int]:
        """
        Pop and return the next question ID from the queue.

        Args:
            session_id: The session ID

        Returns:
            Question ID if available, None if queue is empty
        """
        session = active_sessions.get(session_id)
        if not session or not session["question_queue"]:
            return None

        return session["question_queue"].pop(0)

    @staticmethod
    def has_questions_remaining(session_id: str) -> bool:
        """
        Check if there are questions remaining in the queue.

        Args:
            session_id: The session ID

        Returns:
            True if questions remain, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return False

        return len(session["question_queue"]) > 0

    @staticmethod
    def record_answer(session_id: str, sid: str, option_id: int) -> bool:
        """
        Record a student's answer.

        Args:
            session_id: The session ID
            sid: Student's socket ID
            option_id: Selected option ID

        Returns:
            True if answer was recorded, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return False

        if sid in session["answers"]:
            return False  # Already answered

        session["answers"][sid] = option_id
        return True

    @staticmethod
    def has_student_answered(session_id: str, sid: str) -> bool:
        """
        Check if a student has already answered the current question.

        Args:
            session_id: The session ID
            sid: Student's socket ID

        Returns:
            True if student has answered, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return True  # Treat as answered if session not found

        return sid in session["answers"]

    @staticmethod
    def all_students_answered(session_id: str) -> bool:
        """
        Check if all students have answered the current question.

        Args:
            session_id: The session ID

        Returns:
            True if all students answered, False otherwise
        """
        session = active_sessions.get(session_id)
        if not session:
            return False

        student_count = len(session["students"])
        answer_count = len(session["answers"])

        return student_count > 0 and answer_count >= student_count

    @staticmethod
    def clear_answers(session_id: str) -> None:
        """
        Clear all answers for the current question.

        Args:
            session_id: The session ID
        """
        session = active_sessions.get(session_id)
        if session:
            session["answers"] = {}

    @staticmethod
    def update_student_score(session_id: str, sid: str, points: int) -> int:
        """
        Add points to a student's score.

        Args:
            session_id: The session ID
            sid: Student's socket ID
            points: Points to add

        Returns:
            New total score
        """
        session = active_sessions.get(session_id)
        if not session or sid not in session["students"]:
            return 0

        session["students"][sid]["score"] += points
        return session["students"][sid]["score"]

    @staticmethod
    def get_student_score(session_id: str, sid: str) -> int:
        """
        Get a student's current score.

        Args:
            session_id: The session ID
            sid: Student's socket ID

        Returns:
            Current score
        """
        session = active_sessions.get(session_id)
        if not session or sid not in session["students"]:
            return 0

        return session["students"][sid]["score"]

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """
        Delete a session from active sessions.

        Args:
            session_id: The session ID

        Returns:
            True if deleted, False if not found
        """
        if session_id in active_sessions:
            del active_sessions[session_id]
            return True
        return False

    @staticmethod
    def get_room_name(session_id: str) -> str:
        """
        Get the room name for a session.

        Args:
            session_id: The session ID

        Returns:
            Room name string
        """
        return f"room_{session_id}"
