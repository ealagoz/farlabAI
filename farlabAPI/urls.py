# farlabAPI/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

app_name = 'farlabAPI'

urlpatterns = [
    path('documents/', views.api_document_list, name='api_document_list'),
    path('upload/', views.api_upload_document, name='api_upload_document'),
    path('download_document/<int:document_id>/', views.api_download_document, name='api_download_document'),
    path('generate_embeddings/', views.api_generate_embeddings, name='api_generate_embeddings'),
    path('generate_response/', views.api_generate_response, name='api_generate_response'),
    path('list_embeddings/', views.api_list_embeddings, name='api_list_embeddings'),
    path('delete_document/<int:document_id>/', views.api_delete_document, name='api_delete_document'),
    path('delete_all_documents/', views.api_delete_all_documents, name='api_delete_all_documents'),
    path('get_token/', views.api_get_token_view, name='api_get_token_view'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
