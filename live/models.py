from django.db import models
from django.utils import timezone

from users.models import User
from quizzes.models import Topic, Question, AnswerOption


class Session(models.Model):
    """
    Persisted quiz session.
    Created when teacher finishes a live session.
    """
    class Status(models.TextChoices):
        FINISHED = 'finished', 'Finished'
        CANCELLED = 'cancelled', 'Cancelled'

    code = models.CharField(max_length=10, db_index=True)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.FINISHED
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(default=timezone.now)
    time_per_question = models.IntegerField()
    total_questions = models.IntegerField()

    class Meta:
        db_table = 'live_session'
        ordering = ['-finished_at']
        indexes = [
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['finished_at']),
        ]

    def __str__(self):
        return f"{self.code} - {self.topic.title}"


class SessionQuestion(models.Model):
    """
    Question as it appeared in a session (with order).
    Needed because questions are shuffled per session.
    """
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='session_questions'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='session_appearances'
    )
    order = models.PositiveIntegerField()

    class Meta:
        db_table = 'live_session_question'
        ordering = ['order']
        unique_together = [['session', 'question']]

    def __str__(self):
        return f"Q{self.order}: {self.question.text[:30]}"


class SessionParticipant(models.Model):
    """
    Student who participated in a session.
    Students are anonymous (no User FK) — matches Socket.IO behavior.
    """
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    student_name = models.CharField(max_length=100)
    socket_id = models.CharField(max_length=100)
    joined_at = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)

    class Meta:
        db_table = 'live_session_participant'
        ordering = ['-score']

    def __str__(self):
        return f"{self.student_name} ({self.score} pts)"


class SessionAnswer(models.Model):
    """
    Individual answer record.
    Source of truth for what each student answered.
    """
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    participant = models.ForeignKey(
        SessionParticipant,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    session_question = models.ForeignKey(
        SessionQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    selected_option = models.ForeignKey(
        AnswerOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_answers'
    )
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'live_session_answer'
        unique_together = [['participant', 'session_question']]

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.participant.student_name} {status}"
