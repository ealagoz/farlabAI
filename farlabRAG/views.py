# farlabRAG/views.py
import json

from django.shortcuts import render, HttpResponse
from farlabAPI.models import Document, EmbeddingManager
from .prompts import prompts
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from django.conf import settings
import numpy as np
import ollama
import logging
import re


# Logging for debugging
logger = logging.getLogger('rag')

# Initialize your Ollama Embeddings
embedding_model = OllamaEmbeddings(model='nomic-embed-text')  # avr/sfr-embedding-mistral


# Create a function for Cosine similarity
# https://en.wikipedia.org/wiki/Cosine_similarity
# Function to find most similar chunks
def find_most_similar(prompt_embedding, stored_embeddings, top_k=5):
    similarities = []
    for idx, embedding in enumerate(stored_embeddings):
        prompt_embedding = np.array(prompt_embedding)
        embedding = np.array(embedding)
        similarity = (np.dot(prompt_embedding, embedding) /
                      (np.linalg.norm(prompt_embedding) * np.linalg.norm(embedding)))
        similarities.append((similarity, idx))
    similarities.sort(reverse=True, key=lambda x: x[0])
    return similarities[:top_k]


# @method_decorator(cache_page(60*1), name='dispatch')
@csrf_exempt
def generate_response(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '')
        document_id = settings.DEFAULT_DOCUMENT_ID  # request.POST.get('document_id', '')

        logger.debug(f"Received prompt: {prompt}")
        logger.debug(f"Received document_id: {document_id}")

        if not prompt:
            logger.error('No prompt provided')
            return JsonResponse({'error': 'No prompt provided'}, status=400)
        if not document_id:
            logger.error('No document ID provided')
            return JsonResponse({'error': 'No document ID provided'}, status=400)

        try:
            document = Document.objects.get(id=document_id)
            embedding_manager = EmbeddingManager(document)
            stored_data = embedding_manager.load_embeddings()

            if not stored_data:
                logger.error(f"No embeddings found for document ID {document_id}")
                return JsonResponse({'error': 'No embeddings found for this document'}, status=404)
            sanitized_prompt = sanitize_prompt(prompt)
            response = generate_llm_response(sanitized_prompt, stored_data)
            return JsonResponse({'response': response})
        except Document.DoesNotExist:
            logger.error(f"Document with ID {document_id} does not exist.")
            return JsonResponse({'error': 'Document not found'}, status=404)
        except Exception as e:
            log_suspicious_activity(f"Exception occurred: {e}")
            logger.error(f"An error occurred during processing: {e}")
            return JsonResponse({'error': 'An error occurred during processing.'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def generate_llm_response(prompt, stored_data):
    if not prompt:
        return "Please provide a prompt to generate a response."

    prompt_embedding = embedding_model.embed_documents([prompt])[0]
    most_similar_chunks = find_most_similar(prompt_embedding, stored_data["embeddings"], top_k=5)

    new_context = ""
    for similarity, idx in most_similar_chunks:
        chunk_text = stored_data["chunks"][idx]
        new_context += chunk_text + "\n"

    system_prompt = prompts()

    messages = [
        {
            "role": "system",
            "content": system_prompt + new_context
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        # Query the Ollama chatbot
        response = ollama.chat(
            model="llama3.1",
            messages=messages)

        # Extract the response content safely
        response_content = response['message']['content']
    except Exception as e:
        logger.error(f"An error occurred while querying Ollama: {str(e)}")
        response_content = "An error occurred while generating the response."
    return response_content


def chatbot(request):
    documents = Document.objects.all()  # Fetch all documents
    return render(request, 'rag/public_chatbot.html', {'documents': documents})


def sanitize_prompt(prompt):
    return re.sub(r'[^a-zA-Z0-9.,!?\'\"()\-\s]', '', prompt)


def log_suspicious_activity(activity):
    logger.warning(f"Suspicious activity detected: {activity}")
