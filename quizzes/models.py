from django.db import models
from users.models import User


class Topic(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    question_timer = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=500)
    order_index = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
