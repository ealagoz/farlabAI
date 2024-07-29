# farlabAPI/serializers.py
from rest_framework import serializers
from farlabRAG.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
