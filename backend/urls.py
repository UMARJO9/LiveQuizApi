"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework import permissions
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from users.views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from quizzes.views import (
    QuizListCreateView,
    QuizDetailView,
    QuestionCreateView,
    QuestionDeleteView,
    ChoiceCreateView,
    ChoiceDeleteView,
)
urlpatterns = [
    path('admin/', admin.site.urls),

    # Registration
    path('api/register/', RegisterView.as_view()),

    # Login JWT
    path('api/login/', TokenObtainPairView.as_view()),
    path('api/refresh/', TokenRefreshView.as_view()),

     path('api/quizzes/', QuizListCreateView.as_view()),
    path('api/quizzes/<int:pk>/', QuizDetailView.as_view()),

    # QUESTION CRUD
    path('api/quizzes/<int:quiz_id>/questions/', QuestionCreateView.as_view()),
    path('api/questions/<int:pk>/delete/', QuestionDeleteView.as_view()),

    # CHOICE CRUD
    path('api/questions/<int:question_id>/choices/', ChoiceCreateView.as_view()),
    path('api/choices/<int:pk>/delete/', ChoiceDeleteView.as_view()),
]

# OpenAPI schema (JSON) and Swagger UI
class SchemaAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    renderer_classes = [JSONOpenAPIRenderer]

    def get(self, request, *args, **kwargs):
        from rest_framework.schemas.openapi import SchemaGenerator
        generator = SchemaGenerator(
            title="LiveQuiz API",
            description="API documentation for LiveQuiz",
            version="1.0.0",
        )
        schema = generator.get_schema(request=request, public=True)
        return Response(schema)

urlpatterns += [
    path('api/schema/', SchemaAPIView.as_view(), name='openapi-schema'),
    path('openapi.json', SchemaAPIView.as_view(), name='openapi-json'),
    path(
        'api/docs/',
        TemplateView.as_view(
            template_name='swagger-ui.html',
            extra_context={'schema_url': 'openapi-schema'},
        ),
        name='swagger-ui',
    ),
]
