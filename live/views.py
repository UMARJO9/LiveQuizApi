from django.db.models import Count, Avg, Prefetch
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.responses import StandardResponseMixin
from .models import Session, SessionParticipant, SessionAnswer, SessionQuestion
from .serializers import (
    SessionListSerializer,
    SessionDetailSerializer,
    StudentSessionDetailSerializer,
)


class SessionListView(StandardResponseMixin, generics.ListAPIView):
    """
    GET /api/sessions?status=finished

    Returns lightweight list of sessions for the authenticated teacher.
    Supports filtering by status query param.
    """
    serializer_class = SessionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Session.objects.filter(teacher=self.request.user)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.select_related('topic').annotate(
            participants_count=Count('participants'),
            avg_score=Avg('participants__score')
        )


class SessionDetailView(StandardResponseMixin, generics.RetrieveAPIView):
    """
    GET /api/sessions/{session_id}

    Returns full session details including participants and question stats.
    """
    serializer_class = SessionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Session.objects.filter(
            teacher=self.request.user
        ).select_related(
            'topic', 'teacher'
        ).prefetch_related(
            Prefetch(
                'participants',
                queryset=SessionParticipant.objects.order_by('-score')
            ),
            Prefetch(
                'session_questions',
                queryset=SessionQuestion.objects.select_related(
                    'question'
                ).prefetch_related(
                    'question__options',
                    'answers'
                ).order_by('order')
            ),
        )


class StudentDetailView(StandardResponseMixin, APIView):
    """
    GET /api/sessions/{session_id}/students/{student_id}

    Returns all answers for a specific student in a session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id, student_id):
        try:
            session = Session.objects.get(
                pk=session_id,
                teacher=request.user
            )
        except Session.DoesNotExist:
            return Response(
                {"message": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            participant = SessionParticipant.objects.prefetch_related(
                Prefetch(
                    'answers',
                    queryset=SessionAnswer.objects.select_related(
                        'session_question__question',
                        'selected_option'
                    ).prefetch_related(
                        'session_question__question__options'
                    ).order_by('session_question__order')
                )
            ).get(pk=student_id, session=session)
        except SessionParticipant.DoesNotExist:
            return Response(
                {"message": "Student not found in this session"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentSessionDetailSerializer(participant)
        return Response(serializer.data)
