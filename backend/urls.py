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
from users.views import LoginAPIView
from quizzes.views import (
    TopicListCreateView,
    TopicDetailView,
    QuestionCreateAPIView,
    QuestionDeleteView,
    AnswerOptionDeleteView,
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),

    # Auth: Login only
    path('api/auth/login/', LoginAPIView.as_view()),

    path('api/quizzes/', TopicListCreateView.as_view()),
    path('api/quizzes', TopicListCreateView.as_view()),
    path('api/quizzes/<int:pk>/', TopicDetailView.as_view()),
    path('api/quizzes/<int:pk>', TopicDetailView.as_view()),

    # QUESTION CRUD
    path('api/topics/<int:topic_id>/questions/', QuestionCreateAPIView.as_view()),
    path('api/topics/<int:topic_id>/questions', QuestionCreateAPIView.as_view()),
    path('api/questions/<int:pk>/delete/', QuestionDeleteView.as_view()),
    path('api/questions/<int:pk>/delete', QuestionDeleteView.as_view()),

    # ANSWER OPTION CRUD
    path('api/options/<int:pk>/delete/', AnswerOptionDeleteView.as_view()),
    path('api/options/<int:pk>/delete', AnswerOptionDeleteView.as_view()),
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
            {"name": "Auth", "description": "Authentication"},
            {"name": "Topics", "description": "Topic CRUD endpoints"},
            {"name": "Questions", "description": "Question CRUD endpoints"},
            {"name": "Answer Options", "description": "Answer option endpoints"},
        ],
        "paths": {
            "/api/auth/login/": {
                "post": {
                    "summary": "Login and obtain access token",
                    "tags": ["Auth"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LoginResponse"}
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LoginErrorResponse"}
                                }
                            }
                        }
                    },
                }
            },
            "/api/quizzes/": {
                "get": {
                    "summary": "List topics",
                    "tags": ["Topics"],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TopicListResponse"}
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create topic",
                    "tags": ["Topics"],
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TopicCreateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TopicResponse"}
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
                    "summary": "Retrieve topic",
                    "tags": ["Topics"],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TopicResponse"}
                                }
                            }
                        }
                    }
                },
                "put": {
                    "summary": "Update topic",
                    "tags": ["Topics"],
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TopicCreateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TopicResponse"}
                                }
                            }
                        }
                    }
                },
                "patch": {
                    "summary": "Partial update topic",
                    "tags": ["Topics"],
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TopicCreateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TopicResponse"}
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "summary": "Delete topic",
                    "tags": ["Topics"],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Deleted",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EmptyResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Not Found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EmptyResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/topics/{topic_id}/questions/": {
                "post": {
                    "summary": "Create question with options",
                    "tags": ["Questions"],
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "topic_id", "in": "path", "required": True, "schema": {"type": "integer"}}
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
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/QuestionResponse"}
                                }
                            }
                        }
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
                    "responses": {
                        "200": {
                            "description": "Deleted",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EmptyResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Not Found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EmptyResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/options/{id}/delete/": {
                "delete": {
                    "summary": "Delete answer option",
                    "tags": ["Answer Options"],
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Deleted",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EmptyResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Not Found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EmptyResponse"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
            "schemas": {
                "StandardResponseBase": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "code": {"type": "integer"},
                        "message": {"type": "string"}
                    },
                    "required": ["success", "code", "message"]
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["password"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "username": {"type": "string"},
                        "password": {"type": "string"}
                    }
                },
                "LoginSuccess": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "token": {"type": "string"},
                        "user": {"$ref": "#/components/schemas/UserFull"}
                    }
                },
                "LoginErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"}
                    }
                },
                "LoginResponse": {"$ref": "#/components/schemas/LoginSuccess"},
                "UserInfo": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "specialty": {"type": "string"}
                    }
                },
                "UserFull": {
                    "allOf": [
                        {"type": "object", "properties": {"id": {"type": "integer"}}},
                        {"$ref": "#/components/schemas/UserInfo"}
                    ]
                },
                "AnswerOption": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "text": {"type": "string"},
                        "is_correct": {"type": "boolean"}
                    }
                },
                "AnswerOptionCreate": {
                    "type": "object",
                    "required": ["text", "is_correct"],
                    "properties": {
                        "text": {"type": "string"},
                        "is_correct": {"type": "boolean"}
                    }
                },
                "Question": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "text": {"type": "string"},
                        "topic_id": {"type": "integer"},
                        "options": {"type": "array", "items": {"$ref": "#/components/schemas/AnswerOption"}}
                    }
                },
                "Topic": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string", "nullable": True},
                        "question_timer": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                        "questions": {"type": "array", "items": {"$ref": "#/components/schemas/Question"}}
                    }
                },
                "TopicCreateRequest": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "question_timer": {"type": "integer"}
                    }
                },
                "QuestionCreateRequest": {
                    "type": "object",
                    "required": ["text", "options"],
                    "properties": {
                        "text": {"type": "string"},
                        "options": {"type": "array", "items": {"$ref": "#/components/schemas/AnswerOptionCreate"}}
                    }
                },
                "TopicListResponse": {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponseBase"},
                        {
                            "type": "object",
                            "properties": {
                                "result": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Topic"}
                                }
                            }
                        }
                    ]
                },
                "TopicResponse": {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponseBase"},
                        {
                            "type": "object",
                            "properties": {"result": {"$ref": "#/components/schemas/Topic"}}
                        }
                    ]
                },
                "QuestionResponse": {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponseBase"},
                        {
                            "type": "object",
                            "properties": {"result": {"$ref": "#/components/schemas/Question"}}
                        }
                    ]
                },
                "EmptyResponse": {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponseBase"},
                        {
                            "type": "object",
                            "properties": {"result": {"nullable": True}}
                        }
                    ]
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
