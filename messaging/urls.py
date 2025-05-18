from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('send/<int:recipient_id>/', views.send_message, name='send_message'),
    path('view/<int:pk>/', views.view_message, name='view_message'),
    path('sent/', views.sent_messages, name='sent_messages'),
] 