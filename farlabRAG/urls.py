from django.urls import path, re_path
from . import views

app_name = 'farlabRAG'

urlpatterns = [
    path('generate_response/', views.generate_response, name='generate_response'),
    path('', views.chatbot, name='chatbot'),  # Publicly accessible chatbot view
    # re_path(r'^chatbot(?:/(?P<document_id>\d+))?/$', views.chatbot, name='chatbot'),  # Optional document ID
]
