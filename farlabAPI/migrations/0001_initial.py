# Generated by Django 5.0.6 on 2024-07-20 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=255)),
                ('file_data', models.TextField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('embedding_file', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]
