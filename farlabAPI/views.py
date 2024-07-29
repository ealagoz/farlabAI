# farlabAPI/views.py
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from .models import Document, EmbeddingManager
from farlabRAG.forms import DocumentForm
from farlabRAG.views import generate_llm_response
from langchain_community.embeddings import OllamaEmbeddings
import logging
import json
import os

# Initialize your Ollama Embeddings
embedding_model = OllamaEmbeddings(model='nomic-embed-text')  # avr/sfr-embedding-mistral

# Logging for debugging
logger = logging.getLogger('api')


def api_get_token_view(request):
    return render(request, 'rag/get_token.html')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('files')  # Get the list of files
        # print("Files:", files)  # Debug statement to check files
        if form.is_valid():
            for file in files:
                if isinstance(file, InMemoryUploadedFile):
                    file_data = file.read().decode('utf-8')
                    document = Document.objects.create(
                        file_name=file.name,
                        file_data=file_data
                    )
                    document.save()
            return redirect(reverse('farlabAPI:api_document_list'))
        else:
            print("Form is not valid:", form.errors)
    else:
        form = DocumentForm()
    return render(request, 'rag/upload.html', {'form': form})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_document_list(request):
    documents = Document.objects.all()
    return render(request, 'rag/document_list.html', {'documents': documents})


@api_view(['GET'])
def api_download_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    response = HttpResponse(document.file_data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
    return response


def parse_file_content(text):
    paragraphs = []
    buffer = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            buffer.append(line)
        elif len(buffer):
            paragraphs.append(" ".join(buffer))
            buffer = []
    if len(buffer):
        paragraphs.append(" ".join(buffer))
    return paragraphs


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def api_generate_embeddings(request):
    documents = Document.objects.all()
    for document in documents:
        try:
            text = document.file_data
            # print("Text: ", text)
            chunks = parse_file_content(text)
            # print("Chunks: ", chunks[:10])
            embeddings = embedding_model.embed_documents(chunks)
            embedding_manager = EmbeddingManager(document)
            # embedding_manager.save_embeddings(embeddings)
            embedding_manager.save_embeddings(embeddings, chunks)
            logger.debug("Embeddings generated successfully.")
        except Exception as e:
            logger.error(f"Error processing document {document.file_name}: {e}")
            continue
    return redirect(reverse('farlabAPI:api_document_list'))


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_document(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
        document.delete()
        return redirect(reverse('farlabAPI:api_document_list'))
        # return Response({"message": "Document deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    except Document.DoesNotExist:
        return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_all_documents(request):
    Document.objects.all().delete()
    return redirect(reverse('farlabAPI:api_document_list'))
    # return Response({"message": "All documents deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_list_embeddings(request):
    documents = Document.objects.all()  # Fetch all documents
    embeddings = []

    for document in documents:
        embedding_manager = EmbeddingManager(document)
        stored_data = embedding_manager.load_embeddings()

        if stored_data:
            embeddings.append({
                'document_id': document.id,
                'document_name': document.file_name,
                'embedding_data': stored_data["embeddings"][:10]  # Show only first 10 elements (optional)
            })
            logger.debug(f"Embeddings file id: {document.id}")

    context = {'embeddings': embeddings}
    return render(request, 'rag/list_embeddings.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_generate_response(request):
    prompt = request.data.get('prompt', '')
    document_id = request.data.get('document_id', '')

    if not prompt:
        return JsonResponse({'error': 'No prompt provided'}, status=400)
    if not document_id:
        return JsonResponse({'error': 'No document ID provided'}, status=400)

    try:
        document = Document.objects.get(id=document_id)
        embeddings_filename = document.get_embedding_filename()
        embeddings_filepath = os.path.join(settings.EMBEDDINGS_DIR, embeddings_filename)
        with open(embeddings_filepath, 'r') as f:
            stored_data = json.load(f)
        response = generate_llm_response(prompt, stored_data)
        return JsonResponse({'response': response})
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
