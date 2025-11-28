from django.shortcuts import render

from rest_framework import generics, permissions

from backend.responses import StandardResponseMixin
from .models import Quiz, Question, Choice
from .serializers import QuizSerializer, QuestionSerializer, ChoiceSerializer


# ----- QUIZ CRUD -----

class QuizListCreateView(StandardResponseMixin, generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class QuizDetailView(StandardResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]


# ----- QUESTION CRUD -----

class QuestionCreateView(StandardResponseMixin, generics.CreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        quiz_id = self.kwargs["quiz_id"]
        serializer.save(quiz_id=quiz_id)


class QuestionDeleteView(StandardResponseMixin, generics.DestroyAPIView):
    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated]


# ----- CHOICE CRUD -----

class ChoiceCreateView(StandardResponseMixin, generics.CreateAPIView):
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        question_id = self.kwargs["question_id"]
        serializer.save(question_id=question_id)


class ChoiceDeleteView(StandardResponseMixin, generics.DestroyAPIView):
    queryset = Choice.objects.all()
    permission_classes = [permissions.IsAuthenticated]

