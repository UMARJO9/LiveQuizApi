from rest_framework import serializers
from django.db.models import Avg

from .models import Session, SessionParticipant, SessionAnswer, SessionQuestion


class SessionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for session list.
    GET /api/sessions?status=finished
    """
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    participants_count = serializers.IntegerField(read_only=True)
    avg_score = serializers.FloatField(read_only=True)

    class Meta:
        model = Session
        fields = (
            'id',
            'code',
            'topic_title',
            'finished_at',
            'participants_count',
            'avg_score',
        )


class ParticipantSummarySerializer(serializers.ModelSerializer):
    """Participant info for session detail view."""
    class Meta:
        model = SessionParticipant
        fields = (
            'id',
            'student_name',
            'score',
            'correct_answers',
            'wrong_answers',
        )


class AnswerOptionBriefSerializer(serializers.Serializer):
    """Minimal option representation."""
    id = serializers.IntegerField()
    text = serializers.CharField()
    is_correct = serializers.BooleanField()


class QuestionStatsSerializer(serializers.Serializer):
    """Question with aggregated answer stats."""
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    text = serializers.CharField()
    options = AnswerOptionBriefSerializer(many=True)
    total_answers = serializers.IntegerField()
    correct_count = serializers.IntegerField()
    wrong_count = serializers.IntegerField()


class SessionDetailSerializer(serializers.ModelSerializer):
    """
    Full session detail.
    GET /api/sessions/{session_id}
    """
    topic_id = serializers.IntegerField(source='topic.id')
    topic_title = serializers.CharField(source='topic.title')
    teacher_email = serializers.CharField(source='teacher.email')
    participants = ParticipantSummarySerializer(many=True, read_only=True)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = (
            'id',
            'code',
            'topic_id',
            'topic_title',
            'teacher_email',
            'status',
            'started_at',
            'finished_at',
            'time_per_question',
            'total_questions',
            'participants',
            'questions',
        )

    def get_questions(self, obj):
        """Build question stats from prefetched data."""
        result = []
        for sq in obj.session_questions.all():
            answers = sq.answers.all()
            correct_count = sum(1 for a in answers if a.is_correct)
            total = len(answers)

            result.append({
                'id': sq.question.id,
                'order': sq.order,
                'text': sq.question.text,
                'options': [
                    {
                        'id': opt.id,
                        'text': opt.text,
                        'is_correct': opt.is_correct,
                    }
                    for opt in sq.question.options.all()
                ],
                'total_answers': total,
                'correct_count': correct_count,
                'wrong_count': total - correct_count,
            })
        return result


class StudentAnswerDetailSerializer(serializers.Serializer):
    """Single answer in student detail view."""
    question_id = serializers.IntegerField()
    question_order = serializers.IntegerField()
    question_text = serializers.CharField()
    selected_option_id = serializers.IntegerField(allow_null=True)
    selected_option_text = serializers.CharField(allow_null=True)
    correct_option_id = serializers.IntegerField()
    correct_option_text = serializers.CharField()
    is_correct = serializers.BooleanField()
    response_time_ms = serializers.IntegerField(allow_null=True)


class StudentSessionDetailSerializer(serializers.ModelSerializer):
    """
    Student detail within a session.
    GET /api/sessions/{session_id}/students/{student_id}
    """
    answers = serializers.SerializerMethodField()

    class Meta:
        model = SessionParticipant
        fields = (
            'id',
            'student_name',
            'score',
            'correct_answers',
            'wrong_answers',
            'joined_at',
            'answers',
        )

    def get_answers(self, obj):
        """Build answer list from prefetched data."""
        result = []
        for answer in obj.answers.all():
            sq = answer.session_question
            question = sq.question
            correct_option = next(
                (opt for opt in question.options.all() if opt.is_correct),
                None
            )

            result.append({
                'question_id': question.id,
                'question_order': sq.order,
                'question_text': question.text,
                'selected_option_id': answer.selected_option_id,
                'selected_option_text': answer.selected_option.text if answer.selected_option else None,
                'correct_option_id': correct_option.id if correct_option else None,
                'correct_option_text': correct_option.text if correct_option else None,
                'is_correct': answer.is_correct,
                'response_time_ms': answer.response_time_ms,
            })
        return result
