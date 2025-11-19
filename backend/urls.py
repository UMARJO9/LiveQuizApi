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
from django.views.generic.base import RedirectView
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import RegisterView
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
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),

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
def openapi_schema_view(request):
    schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "LiveQuiz API",
            "version": "1.0.0",
            "description": "API documentation for LiveQuiz",
        },
        "tags": [
            {"name": "Auth", "description": "Authentication and user registration"},
            {"name": "Quizzes", "description": "Quiz CRUD endpoints"},
            {"name": "Questions", "description": "Question CRUD endpoints"},
            {"name": "Choices", "description": "Choice CRUD endpoints"},
        ],
        "paths": {
            "/api/register/": {
                "post": {
                    "summary": "Register new user",
                    "tags": ["Auth"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RegisterRequest"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RegisterResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/login/": {
                "post": {
                    "summary": "Obtain JWT pair",
                    "tags": ["Auth"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TokenObtainRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TokenObtainResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/refresh/": {
                "post": {
                    "summary": "Refresh JWT access token",
                    "tags": ["Auth"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TokenRefreshRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TokenRefreshResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/quizzes/": {
                "get": {
                    "summary": "List quizzes",
                    "tags": ["Quizzes"],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Quiz"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create quiz",
                    "tags": ["Quizzes"],
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QuizCreateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Quiz"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/quizzes/{id}/": {
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "get": {
                    "summary": "Retrieve quiz",
                    "tags": ["Quizzes"],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Quiz"}
                                }
                            }
                        }
                    }
                },
                "put": {
                    "summary": "Update quiz",
                    "tags": ["Quizzes"],
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QuizCreateRequest"}
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}}
                },
                "patch": {
                    "summary": "Partial update quiz",
                    "tags": ["Quizzes"],
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QuizCreateRequest"}
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}}
                },
                "delete": {
                    "summary": "Delete quiz",
                    "tags": ["Quizzes"],
                    "security": [{"bearerAuth": []}],
                    "responses": {"204": {"description": "No Content"}}
                }
            },
            "/api/quizzes/{quiz_id}/questions/": {
                "post": {
                    "summary": "Create question",
                    "tags": ["Questions"],
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "quiz_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QuestionCreateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Created"}
                    }
                }
            },
            "/api/questions/{id}/delete/": {
                "delete": {
                    "summary": "Delete question",
                    "tags": ["Questions"],
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"204": {"description": "No Content"}}
                }
            },
            "/api/questions/{question_id}/choices/": {
                "post": {
                    "summary": "Create choice",
                    "tags": ["Choices"],
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "question_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChoiceCreateRequest"}
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            },
            "/api/choices/{id}/delete/": {
                "delete": {
                    "summary": "Delete choice",
                    "tags": ["Choices"],
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"204": {"description": "No Content"}}
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
            "schemas": {
                "RegisterRequest": {
                    "type": "object",
                    "required": ["email", "password", "password2"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string"},
                        "password2": {"type": "string"}
                    }
                },
                "RegisterResponse": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"}
                    }
                },
                "TokenObtainRequest": {
                    "type": "object",
                    "required": ["email", "password"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string"}
                    }
                },
                "TokenObtainResponse": {
                    "type": "object",
                    "properties": {
                        "access": {"type": "string"},
                        "refresh": {"type": "string"}
                    }
                },
                "TokenRefreshRequest": {
                    "type": "object",
                    "required": ["refresh"],
                    "properties": {"refresh": {"type": "string"}}
                },
                "TokenRefreshResponse": {
                    "type": "object",
                    "properties": {"access": {"type": "string"}}
                },
                "Choice": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "text": {"type": "string"},
                        "is_correct": {"type": "boolean"}
                    }
                },
                "Question": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "text": {"type": "string"},
                        "order_index": {"type": "integer"},
                        "choices": {"type": "array", "items": {"$ref": "#/components/schemas/Choice"}}
                    }
                },
                "Quiz": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                        "questions": {"type": "array", "items": {"$ref": "#/components/schemas/Question"}}
                    }
                },
                "QuizCreateRequest": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "QuestionCreateRequest": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"},
                        "order_index": {"type": "integer"},
                        "choices": {"type": "array", "items": {"$ref": "#/components/schemas/Choice"}}
                    }
                },
                "ChoiceCreateRequest": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"},
                        "is_correct": {"type": "boolean"}
                    }
                }
            }
        }
    }
    return JsonResponse(schema)

urlpatterns += [
    path('api/schema/', openapi_schema_view, name='openapi-schema'),
    path('openapi.json', openapi_schema_view, name='openapi-json'),
    path(
        'api/docs/',
        TemplateView.as_view(
            template_name='swagger-ui.html',
            extra_context={'schema_url': 'openapi-schema'},
        ),
        name='swagger-ui',
    ),
]
