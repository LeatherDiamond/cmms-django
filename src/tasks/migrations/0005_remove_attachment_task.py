# Generated by Django 5.1.4 on 2025-01-22 13:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0004_attachment_task"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="attachment",
            name="task",
        ),
    ]
