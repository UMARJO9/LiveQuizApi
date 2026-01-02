from django.urls import path
from .views import SessionListView, SessionDetailView, StudentDetailView

urlpatterns = [
    path('', SessionListView.as_view(), name='session-list'),
    path('<int:pk>', SessionDetailView.as_view(), name='session-detail'),
    path('<int:pk>/', SessionDetailView.as_view(), name='session-detail-slash'),
    path(
        '<int:session_id>/students/<int:student_id>',
        StudentDetailView.as_view(),
        name='student-detail'
    ),
    path(
        '<int:session_id>/students/<int:student_id>/',
        StudentDetailView.as_view(),
        name='student-detail-slash'
    ),
]
