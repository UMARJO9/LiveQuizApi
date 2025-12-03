from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.responses import StandardResponseMixin
from .models import AnswerOption, Question, Topic
from .serializers import (
    AnswerOptionSerializer,
    QuestionCreateSerializer,
    QuestionSerializer,
    TopicSerializer,
)


# ----- TOPIC CRUD -----

class TopicListCreateView(StandardResponseMixin, generics.ListCreateAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Topic.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class TopicDetailView(StandardResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"message": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response({"message": "Topic deleted"}, status=status.HTTP_200_OK)


# ----- QUESTION CRUD -----

class QuestionCreateAPIView(StandardResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic = get_object_or_404(Topic, pk=topic_id)
        if topic.teacher != request.user:
            return Response(
                {"message": "You do not have permission to add questions to this topic."},
                status=status.HTTP_403_FORBIDDEN,
            )

        question = serializer.save(topic=topic)
        response_data = QuestionCreateSerializer(question).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class QuestionDeleteView(StandardResponseMixin, generics.DestroyAPIView):
    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response({"message": "Question deleted"}, status=status.HTTP_200_OK)


# ----- ANSWER OPTION CRUD -----

class AnswerOptionDeleteView(StandardResponseMixin, generics.DestroyAPIView):
    queryset = AnswerOption.objects.all()
    serializer_class = AnswerOptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"message": "Answer option not found"}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response({"message": "Option deleted"}, status=status.HTTP_200_OK)

