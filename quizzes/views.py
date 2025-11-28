from django.shortcuts import render

from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

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

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"message": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response({"message": "Quiz deleted"}, status=status.HTTP_200_OK)


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

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response({"message": "Question deleted"}, status=status.HTTP_200_OK)


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

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"message": "Choice not found"}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response({"message": "Choice deleted"}, status=status.HTTP_200_OK)

