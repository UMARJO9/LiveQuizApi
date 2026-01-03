"""
Live Quiz Socket.IO Server

Main server module implementing all socket event handlers for the
real-time quiz system (Kahoot-like functionality).

Events:
    Teacher:
        - teacher:create_session
        - teacher:start_session
        - teacher:next_question
        - teacher:finish_session

    Student:
        - student:join
        - student:answer
        - student:leave

    Server broadcasts:
        - teacher:session_created
        - session:state
        - session:question
        - session:question_closed
        - answer_result
        - ranking
        - quiz_finished
"""

import asyncio
import socketio
from typing import Any, Optional

from .managers.sessions import SessionManager, active_sessions
from .managers.questions import QuestionManager
from .managers.ranking import RankingManager
from .managers.persistence import persist_session
from .utils.time import TimeUtils


# Storage for active question timers
question_timers: dict[str, asyncio.Task] = {}


# Create AsyncServer with CORS support
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)

# Create ASGI application
socket_app = socketio.ASGIApp(
    sio,
    socketio_path="socket.io",
)


# =============================================================================
#                           HELPER FUNCTIONS
# =============================================================================


async def question_timer_task(session_id: str, timeout: int) -> None:
    """
    Background task that auto-closes question after timeout.

    Args:
        session_id: The session ID
        timeout: Seconds to wait before closing
    """
    try:
        await asyncio.sleep(timeout)

        session = SessionManager.get_session(session_id)
        if not session:
            return

        # Only close if still running and question not already closed
        if session["stage"] == "running" and session["current_question"] is not None:
            print(f"[TIMER] Time expired for session {session_id}, closing question")

            # Notify everyone that time expired
            room = SessionManager.get_room_name(session_id)

            # Send to all students
            await sio.emit(
                "session:timer_expired",
                {
                    "question_id": session["current_question"],
                    "message": "Time is up!"
                },
                room=room
            )

            # Send to teacher
            await sio.emit(
                "session:timer_expired",
                {
                    "question_id": session["current_question"],
                    "message": "Time is up!"
                },
                to=session["teacher_sid"]
            )

            # Close question and send results (from_timer=True to avoid self-cancellation)
            await close_question(session_id, from_timer=True)

            # Remove timer from dict after completion
            if session_id in question_timers:
                del question_timers[session_id]

    except asyncio.CancelledError:
        print(f"[TIMER] Timer cancelled for session {session_id}")


def start_question_timer(session_id: str, timeout: int) -> None:
    """
    Start a timer that will auto-close the question.

    Args:
        session_id: The session ID
        timeout: Seconds until question closes
    """
    # Cancel existing timer if any
    cancel_question_timer(session_id)

    # Create new timer task
    task = asyncio.create_task(question_timer_task(session_id, timeout))
    question_timers[session_id] = task
    print(f"[TIMER] Started {timeout}s timer for session {session_id}")


def cancel_question_timer(session_id: str) -> None:
    """
    Cancel the question timer if running.

    Args:
        session_id: The session ID
    """
    if session_id in question_timers:
        question_timers[session_id].cancel()
        del question_timers[session_id]
        print(f"[TIMER] Cancelled timer for session {session_id}")


async def send_question(session_id: str, question_id: int) -> bool:
    """
    Send a question to all students in the session.

    Steps:
        1. Set session["current_question"] = question_id
        2. Set session["answers"] = {}
        3. Set session["question_started_at"] = now
        4. Set session["question_deadline"] = now + time_per_question
        5. Load question + options from Django ORM
        6. Emit to ALL students in room

    Args:
        session_id: The session ID
        question_id: ID of the question to send

    Returns:
        True if question was sent successfully
    """
    session = SessionManager.get_session(session_id)
    if not session:
        return False

    # Load question from database
    question_data = await QuestionManager.load_question(question_id)
    if not question_data:
        return False

    # Setup session state for the question
    QuestionManager.setup_question(session, question_id)

    # Cache correct option ID in session (so we don't need DB query on timer)
    session["current_correct_option"] = question_data.get("correct_option_id")
    print(f"[SEND_QUESTION] Cached correct_option_id: {session['current_correct_option']}")

    # Build and send question payload (without correct_option_id!)
    payload = QuestionManager.build_question_payload(
        question_data,
        session["time_per_question"]
    )

    room = SessionManager.get_room_name(session_id)
    await sio.emit("session:question", payload, room=room)

    # Start auto-close timer
    start_question_timer(session_id, session["time_per_question"])

    return True


async def close_question(session_id: str, from_timer: bool = False) -> None:
    """
    Close the current question and process all answers.

    Event sequence:
        1. session:answer_count (final count) -> Teacher
        2. answer_result -> Each student
        3. session:question_closed -> Teacher + Students
        4. ranking + session:ranking -> Teacher

    Args:
        session_id: The session ID
        from_timer: If True, called from timer (don't cancel timer to avoid self-cancellation)
    """
    print(f"[CLOSE_QUESTION] Starting close_question for session {session_id}", flush=True)

    # Cancel timer if running (but not if we're called FROM the timer!)
    if not from_timer:
        cancel_question_timer(session_id)

    session = SessionManager.get_session(session_id)
    if not session:
        print(f"[CLOSE_QUESTION] ERROR: Session not found")
        return

    question_id = session["current_question"]
    if question_id is None:
        print(f"[CLOSE_QUESTION] ERROR: current_question is None")
        return

    # Get correct answer from cached session data (no DB query needed!)
    correct_option_id = session.get("current_correct_option")
    print(f"[CLOSE_QUESTION] Using cached correct_option_id: {correct_option_id}")

    if correct_option_id is None:
        print(f"[CLOSE_QUESTION] ERROR: correct_option_id is None for question {question_id}")
        return

    print(f"[CLOSE_QUESTION] Processing question {question_id}, correct_option: {correct_option_id}")

    room = SessionManager.get_room_name(session_id)
    teacher_sid = session["teacher_sid"]

    # 1. Send final answer count to teacher
    answer_count = len(session["answers"])
    student_count = len(session["students"])
    await sio.emit(
        "session:answer_count",
        {"answered": answer_count, "total": student_count},
        to=teacher_sid
    )
    print(f"[CLOSE_QUESTION] Sent answer_count: {answer_count}/{student_count}", flush=True)

    # Record this question for persistence
    SessionManager.record_answered_question(session_id, question_id, correct_option_id)

    # 2. Process each student's answer and send results
    print(f"[CLOSE_QUESTION] Processing {student_count} students...", flush=True)
    for sid, student_data in session["students"].items():
        print(f"[CLOSE_QUESTION] Processing student {sid}...", flush=True)
        student_answer = session["answers"].get(sid)
        correct = student_answer == correct_option_id

        # Record answer for persistence (even if None = no answer)
        if student_answer is not None:
            SessionManager.record_student_answer(
                session_id=session_id,
                sid=sid,
                question_id=question_id,
                option_id=student_answer,
                is_correct=correct,
            )

        # Award points
        score_delta = QuestionManager.POINTS_CORRECT if correct else 0
        if score_delta > 0:
            SessionManager.update_student_score(session_id, sid, score_delta)

        score_total = SessionManager.get_student_score(session_id, sid)

        # Build and send result to student
        result = QuestionManager.build_answer_result(
            correct=correct,
            correct_option_id=correct_option_id,
            student_answer=student_answer,
            score_delta=score_delta,
            score_total=score_total,
        )
        print(f"[CLOSE_QUESTION] Sending answer_result to {sid}...", flush=True)
        await sio.emit("answer_result", result, to=sid)
        print(f"[CLOSE_QUESTION] Sent answer_result to {sid}", flush=True)

    print(f"[CLOSE_QUESTION] Sent answer_result to all students", flush=True)

    # 3. Send question closed to everyone (students room + teacher)
    await sio.emit("session:question_closed", {"question_id": question_id}, room=room)
    await sio.emit("session:question_closed", {"question_id": question_id}, to=teacher_sid)
    print(f"[CLOSE_QUESTION] Sent session:question_closed")

    # 4. Build and send ranking to teacher (both event names for compatibility)
    ranking_payload = RankingManager.build_ranking_payload(session["students"])
    print(f"[CLOSE_QUESTION] Ranking payload: {ranking_payload}")

    await sio.emit("ranking", ranking_payload, to=teacher_sid)
    await sio.emit("session:ranking", ranking_payload, to=teacher_sid)

    print(f"[CLOSE_QUESTION] Sent ranking to teacher {teacher_sid}")

    # Clear answers and current question for next question
    SessionManager.clear_answers(session_id)
    session["current_question"] = None
    session["current_correct_option"] = None

    print(f"[CLOSE_QUESTION] Done!")


async def finish_session(session_id: str) -> None:
    """
    Finish the quiz session and send final results.

    Steps:
        1. Set session stage to finished
        2. Compute final ranking
        3. Determine all winners (max score)
        4. Emit quiz_finished to all participants
        5. Persist session to database

    Args:
        session_id: The session ID
    """
    # Cancel any running timer
    cancel_question_timer(session_id)

    session = SessionManager.get_session(session_id)
    if not session:
        return

    # Set stage to finished
    SessionManager.set_stage(session_id, SessionManager.STAGE_FINISHED)

    # Build final results payload
    payload = RankingManager.build_quiz_finished_payload(session["students"])

    # Send to all participants (room + teacher)
    room = SessionManager.get_room_name(session_id)
    await sio.emit("quiz_finished", payload, room=room)
    await sio.emit("quiz_finished", payload, to=session["teacher_sid"])

    # Persist session to database
    try:
        db_session_id = await persist_session(session)
        if db_session_id:
            print(f"[FINISH_SESSION] Session {session_id} persisted to DB with ID {db_session_id}")
        else:
            print(f"[FINISH_SESSION] Failed to persist session {session_id}")
    except Exception as e:
        print(f"[FINISH_SESSION] Error persisting session: {e}")


# =============================================================================
#                           CONNECTION EVENTS
# =============================================================================


@sio.event
async def connect(sid: str, environ: dict[str, Any], auth: dict[str, Any] | None = None) -> None:
    """
    Handle new socket connection.

    On connect we do NOT assign a role.
    We wait for teacher:create_session or student:join to identify the user.

    Args:
        sid: Socket ID of the connected client
        environ: WSGI environ dictionary
        auth: Authentication data sent by client (e.g., {"token": "..."})
    """
    print(f"[CONNECT] Client connected: {sid}")
    if auth:
        print(f"[CONNECT] Auth data received: {auth.get('token', 'N/A')[:20]}...")


@sio.event
async def disconnect(sid: str) -> None:
    """
    Handle socket disconnection.

    Clean up student from session if they disconnect.

    Args:
        sid: Socket ID of the disconnected client
    """
    print(f"[DISCONNECT] Client disconnected: {sid}")

    # Check if this was a student
    session = SessionManager.get_session_by_student(sid)
    if session:
        session_id = session["session_id"]
        SessionManager.remove_student(session_id, sid)

        # Notify teacher of updated student list
        student_list = SessionManager.get_student_list(session_id)
        await sio.emit(
            "session:state",
            {"students": student_list},
            to=session["teacher_sid"]
        )
        print(f"[DISCONNECT] Student removed from session {session_id}")

    # Check if this was a teacher
    session = SessionManager.get_session_by_teacher(sid)
    if session:
        session_id = session["session_id"]
        # Notify all students that session ended
        room = SessionManager.get_room_name(session_id)
        await sio.emit(
            "session:ended",
            {"reason": "Teacher disconnected"},
            room=room
        )
        # Clean up session
        SessionManager.delete_session(session_id)
        print(f"[DISCONNECT] Teacher disconnected, session {session_id} deleted")


# =============================================================================
#                           TEACHER EVENTS
# =============================================================================


@sio.on("teacher:create_session")
async def teacher_create_session(sid: str, data: dict[str, Any]) -> None:
    """
    Handle teacher creating a new quiz session.

    Event: teacher:create_session

    Steps:
        1. Extract topic_id
        2. Load Topic from Django ORM
        3. Load all questions for the topic
        4. Shuffle question list
        5. Load time_per_question
        6. Generate 4-character session_id
        7. Create session object
        8. Set teacher_sid
        9. Save into active_sessions
        10. Return session_id to teacher

    Args:
        sid: Teacher's socket ID
        data: {topic_id: int}
    """
    print(f"[TEACHER] Create session request from {sid}: {data}")

    topic_id = data.get("topic_id")
    if not topic_id:
        await sio.emit("error", {"message": "topic_id is required"}, to=sid)
        return

    # Load topic data
    topic_data = await QuestionManager.load_topic_data(topic_id)
    if not topic_data:
        await sio.emit("error", {"message": "Topic not found"}, to=sid)
        return

    # Load question IDs
    question_ids = await QuestionManager.load_question_ids(topic_id)
    if not question_ids:
        await sio.emit("error", {"message": "No questions found for topic"}, to=sid)
        return

    # Create session
    session = SessionManager.create_session(
        topic_id=topic_id,
        teacher_sid=sid,
        time_per_question=topic_data["time_per_question"],
        question_ids=question_ids,
    )

    # Add teacher to room
    room = SessionManager.get_room_name(session["session_id"])
    await sio.enter_room(sid, room)

    # Send session created event
    await sio.emit(
        "teacher:session_created",
        {
            "session_id": session["session_id"],
            "code": session["session_id"],  # 4-char code like "AB12"
            "topic": topic_data,
            "question_count": len(question_ids),
        },
        to=sid
    )

    print(f"[TEACHER] Session created: {session['session_id']}")


@sio.on("teacher:join_session")
async def teacher_join_session(sid: str, data: dict[str, Any]) -> None:
    """
    Handle teacher joining/reconnecting to an existing session.

    Event: teacher:join_session

    This is called when teacher navigates to session page after creating it.
    Updates teacher_sid and adds current socket to room.

    Args:
        sid: Teacher's socket ID
        data: {session_id: str}
    """
    try:
        print(f"[TEACHER] Join session request from {sid}: {data}", flush=True)

        session_id = data.get("session_id")
        if not session_id:
            await sio.emit("error", {"message": "session_id is required"}, to=sid)
            return

        session = SessionManager.get_session(session_id)
        if not session:
            await sio.emit("error", {"message": "Session not found"}, to=sid)
            return

        # Update teacher_sid to current socket
        old_sid = session["teacher_sid"]
        session["teacher_sid"] = sid
        print(f"[TEACHER] Updated teacher_sid: {old_sid} -> {sid}", flush=True)

        # Add current socket to room
        room = SessionManager.get_room_name(session_id)
        await sio.enter_room(sid, room)
        print(f"[TEACHER] Added {sid} to room {room}", flush=True)

        # Send current session state
        student_list = SessionManager.get_student_list(session_id)
        await sio.emit(
            "session:state",
            {
                "session_id": session_id,
                "stage": session["stage"],
                "students": student_list,
                "current_question": session["current_question"],
                "questions_remaining": len(session["question_queue"]),
            },
            to=sid
        )

        print(f"[TEACHER] Joined session {session_id}", flush=True)
    except Exception as e:
        print(f"[TEACHER] ERROR in join_session: {e}", flush=True)
        import traceback
        traceback.print_exc()


@sio.on("teacher:start_session")
async def teacher_start_session(sid: str, data: dict[str, Any]) -> None:
    """
    Handle teacher starting the quiz session.

    Event: teacher:start_session

    Steps:
        1. Verify sid == teacher_sid
        2. Set session stage to running
        3. Pop first question from queue
        4. Call send_question()

    Args:
        sid: Teacher's socket ID
        data: {session_id: str}
    """
    print(f"[TEACHER] Start session request from {sid}: {data}")

    session_id = data.get("session_id")
    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    # Verify teacher
    if session["teacher_sid"] != sid:
        await sio.emit("error", {"message": "Not authorized"}, to=sid)
        return

    # Check stage
    if session["stage"] != SessionManager.STAGE_WAITING:
        await sio.emit("error", {"message": "Session already started"}, to=sid)
        return

    # Check if there are students
    if not session["students"]:
        await sio.emit("error", {"message": "No students in session"}, to=sid)
        return

    # Set stage to running and mark start time
    SessionManager.set_stage(session_id, SessionManager.STAGE_RUNNING)
    SessionManager.mark_session_started(session_id)

    # Pop and send first question
    question_id = SessionManager.pop_next_question(session_id)
    if question_id:
        await send_question(session_id, question_id)
        await sio.emit(
            "session:started",
            {"session_id": session_id},
            to=sid
        )
        print(f"[TEACHER] Session {session_id} started")
    else:
        await sio.emit("error", {"message": "No questions available"}, to=sid)


@sio.on("teacher:next_question")
async def teacher_next_question(sid: str, data: dict[str, Any]) -> None:
    """
    Handle teacher requesting next question.

    Event: teacher:next_question

    Steps:
        1. If queue empty -> finish_session()
        2. Else pop next question and call send_question()

    Args:
        sid: Teacher's socket ID
        data: {session_id: str}
    """
    print(f"[TEACHER] Next question request from {sid}: {data}")

    session_id = data.get("session_id")
    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    # Verify teacher
    if session["teacher_sid"] != sid:
        await sio.emit("error", {"message": "Not authorized"}, to=sid)
        return

    # Check stage
    if session["stage"] != SessionManager.STAGE_RUNNING:
        await sio.emit("error", {"message": "Session not running"}, to=sid)
        return

    # Close current question first
    await close_question(session_id)

    # Check if there are more questions
    if SessionManager.has_questions_remaining(session_id):
        question_id = SessionManager.pop_next_question(session_id)
        if question_id:
            await send_question(session_id, question_id)
            print(f"[TEACHER] Next question sent for session {session_id}")
    else:
        await finish_session(session_id)
        print(f"[TEACHER] Session {session_id} finished - no more questions")


@sio.on("teacher:finish_session")
async def teacher_finish_session(sid: str, data: dict[str, Any]) -> None:
    """
    Handle teacher manually finishing the session.

    Event: teacher:finish_session

    Args:
        sid: Teacher's socket ID
        data: {session_id: str}
    """
    print(f"[TEACHER] Finish session request from {sid}: {data}")

    session_id = data.get("session_id")
    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    # Verify teacher
    if session["teacher_sid"] != sid:
        await sio.emit("error", {"message": "Not authorized"}, to=sid)
        return

    # Close current question if running
    if session["stage"] == SessionManager.STAGE_RUNNING:
        await close_question(session_id)

    # Finish session
    await finish_session(session_id)
    print(f"[TEACHER] Session {session_id} manually finished")


# =============================================================================
#                           STUDENT EVENTS
# =============================================================================


@sio.on("student:join")
async def student_join(sid: str, data: dict[str, Any]) -> None:
    """
    Handle student joining a quiz session.

    Event: student:join

    Steps:
        1. Extract session_id, name
        2. Check active_sessions
        3. Reject if session not found or stage != waiting
        4. Add student to session
        5. Add student to room
        6. Emit updated student list to teacher

    Args:
        sid: Student's socket ID
        data: {session_id: str, name: str}
    """
    print(f"[STUDENT] Join request from {sid}: {data}")

    session_id = data.get("session_id")
    name = data.get("name", "").strip()

    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    if not name:
        await sio.emit("error", {"message": "name is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    # Check stage
    if session["stage"] != SessionManager.STAGE_WAITING:
        await sio.emit(
            "error",
            {"message": "Cannot join - quiz already started"},
            to=sid
        )
        return

    # Add student
    if not SessionManager.add_student(session_id, sid, name):
        await sio.emit("error", {"message": "Could not join session"}, to=sid)
        return

    # Add to room
    room = SessionManager.get_room_name(session_id)
    await sio.enter_room(sid, room)

    # Confirm join to student
    await sio.emit(
        "student:joined",
        {
            "session_id": session_id,
            "name": name,
            "message": "Successfully joined the quiz"
        },
        to=sid
    )

    # Send updated student list to teacher
    student_list = SessionManager.get_student_list(session_id)
    await sio.emit(
        "session:state",
        {"students": student_list},
        to=session["teacher_sid"]
    )

    print(f"[STUDENT] {name} joined session {session_id}")


@sio.on("student:answer")
async def student_answer(sid: str, data: dict[str, Any]) -> None:
    """
    Handle student submitting an answer.

    Event: student:answer

    Rules:
        1. Session stage must be "running"
        2. Question deadline must NOT be expired
        3. Student must NOT have already answered this question
        4. Save answer
        5. If all students answered -> close_question()

    Args:
        sid: Student's socket ID
        data: {session_id: str, option_id: int}
    """
    print(f"[STUDENT] Answer from {sid}: {data}")

    session_id = data.get("session_id")
    option_id = data.get("option_id")

    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    if option_id is None:
        await sio.emit("error", {"message": "option_id is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    # Check if student is in this session
    if sid not in session["students"]:
        await sio.emit("error", {"message": "Not in this session"}, to=sid)
        return

    # Validate answering is allowed
    if not QuestionManager.is_answer_valid(session):
        await sio.emit(
            "error",
            {"message": "Cannot answer - time expired or quiz not running"},
            to=sid
        )
        return

    # Check if already answered
    if SessionManager.has_student_answered(session_id, sid):
        await sio.emit(
            "error",
            {"message": "Already answered this question"},
            to=sid
        )
        return

    # Record answer
    if not SessionManager.record_answer(session_id, sid, option_id):
        await sio.emit("error", {"message": "Could not record answer"}, to=sid)
        return

    # Confirm answer received
    await sio.emit(
        "student:answer_received",
        {"message": "Answer received"},
        to=sid
    )

    # Notify teacher of answer count
    answer_count = len(session["answers"])
    student_count = len(session["students"])
    await sio.emit(
        "session:answer_count",
        {
            "answered": answer_count,
            "total": student_count
        },
        to=session["teacher_sid"]
    )

    print(f"[STUDENT] Answer recorded: {answer_count}/{student_count}")

    # Check if all students answered
    if SessionManager.all_students_answered(session_id):
        print(f"[SESSION] All students answered, closing question")
        await close_question(session_id)


@sio.on("student:leave")
async def student_leave(sid: str, data: dict[str, Any]) -> None:
    """
    Handle student leaving a quiz session.

    Event: student:leave (optional)

    Args:
        sid: Student's socket ID
        data: {session_id: str}
    """
    print(f"[STUDENT] Leave request from {sid}: {data}")

    session_id = data.get("session_id")
    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        return

    # Remove student
    if SessionManager.remove_student(session_id, sid):
        # Leave room
        room = SessionManager.get_room_name(session_id)
        await sio.leave_room(sid, room)

        # Confirm leave
        await sio.emit("student:left", {"message": "Left the quiz"}, to=sid)

        # Notify teacher
        student_list = SessionManager.get_student_list(session_id)
        await sio.emit(
            "session:state",
            {"students": student_list},
            to=session["teacher_sid"]
        )

        print(f"[STUDENT] Left session {session_id}")


# =============================================================================
#                           UTILITY EVENTS
# =============================================================================


@sio.event
async def get_session_state(sid: str, data: dict[str, Any]) -> None:
    """
    Get current session state (for reconnection or debugging).

    Args:
        sid: Socket ID
        data: {session_id: str}
    """
    session_id = data.get("session_id")
    if not session_id:
        await sio.emit("error", {"message": "session_id is required"}, to=sid)
        return

    session = SessionManager.get_session(session_id)
    if not session:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    student_list = SessionManager.get_student_list(session_id)

    await sio.emit(
        "session:state",
        {
            "session_id": session_id,
            "stage": session["stage"],
            "students": student_list,
            "current_question": session["current_question"],
            "questions_remaining": len(session["question_queue"]),
        },
        to=sid
    )
