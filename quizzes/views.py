from django.shortcuts import render

from rest_framework import generics, permissions
from .models import Quiz, Question, Choice
from .serializers import QuizSerializer, QuestionSerializer, ChoiceSerializer


# ----- QUIZ CRUD -----

class QuizListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]


# ----- QUESTION CRUD -----

class QuestionCreateView(generics.CreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        quiz_id = self.kwargs["quiz_id"]
        serializer.save(quiz_id=quiz_id)


class QuestionDeleteView(generics.DestroyAPIView):
    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated]


# ----- CHOICE CRUD -----

class ChoiceCreateView(generics.CreateAPIView):
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        question_id = self.kwargs["question_id"]
        serializer.save(question_id=question_id)


class ChoiceDeleteView(generics.DestroyAPIView):
    queryset = Choice.objects.all()
    permission_classes = [permissions.IsAuthenticated]

