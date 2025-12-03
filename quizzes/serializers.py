from rest_framework import serializers

from .models import AnswerOption, Question, Topic


class AnswerOptionSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        # Drop any incoming id silently
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if k != "id"}
        return super().to_internal_value(data)

    class Meta:
        model = AnswerOption
        fields = ("id", "text", "is_correct")
        read_only_fields = ("id",)


class QuestionCreateSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True)
    topic_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "topic_id", "options")
        read_only_fields = ("id", "topic_id")

    def validate(self, attrs):
        options = attrs.get("options") or []
        if len(options) != 4:
            raise serializers.ValidationError("Exactly four options are required.")
        if not any(option.get("is_correct") for option in options):
            raise serializers.ValidationError("At least one option must be marked as correct.")
        return attrs

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        topic = validated_data.pop("topic", None)
        question = Question.objects.create(topic=topic, **validated_data)

        AnswerOption.objects.bulk_create(
            [AnswerOption(question=question, **option_data) for option_data in options_data]
        )
        return question


class QuestionSerializer(serializers.ModelSerializer):
    topic_id = serializers.IntegerField(read_only=True)
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "topic_id", "options")


class TopicSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = (
            "id",
            "title",
            "description",
            "question_timer",
            "questions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
