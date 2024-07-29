# farlabAPI/models.py
from django.db import models
from django.conf import settings
import os
import json


# Create your models here.
class Document(models.Model):
    file_name = models.CharField(max_length=255)
    file_data = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    embedding_file = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.file_name

    def get_embedding_filename(self):
        base_name = os.path.splitext(self.file_name)[0]
        return f"{base_name}.json"


class EmbeddingManager:
    def __init__(self, document):
        self.document = document
        self.embeddings_dir = settings.EMBEDDINGS_DIR

    def save_embeddings(self, embeddings, chunks):
        if not os.path.exists(self.embeddings_dir):
            os.makedirs(self.embeddings_dir)
        embedding_filename = self.document.get_embedding_filename()
        filepath = os.path.join(self.embeddings_dir, embedding_filename)
        data = {"embeddings": embeddings, "chunks": chunks}
        with open(filepath, "w") as f:
            json.dump(data, f)
        self.document.embedding_file = embedding_filename
        self.document.save()

    def load_embeddings(self):
        if not self.document:
            return None
        embedding_filename = self.document.get_embedding_filename()
        filepath = os.path.join(self.embeddings_dir, embedding_filename)
        # print(f"Loading embeddings from: {filepath}")
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return None
        with open(filepath, "r") as f:
            return json.load(f)
