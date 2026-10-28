from django.urls import path

from . import views
from .views import (
    tutor_view, tutor_api
)

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/<int:pk>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:pk>/delete/', views.delete_subject, name='delete_subject'),
    path('notes/upload/', views.upload_notes, name='upload_notes'),
    path('notes/<int:pk>/delete/', views.delete_notes, name='delete_notes'),

    # AI Tutor chat endpoints
    path('chat/<int:note_id>/', views.ai_tutor_chat, name='ai_tutor_chat'),
    path('api/chat/<int:note_id>/', views.ai_tutor_api, name='ai_tutor_api'),
    path('tutor/<int:subject_id>/', tutor_view, name='tutor_view'),
    path('tutor/<int:subject_id>/api/', tutor_api, name='tutor_api'),
]
