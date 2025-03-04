# Generated by Django 5.1.4 on 2025-01-23 09:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0005_remove_attachment_task"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="attachments",
        ),
        migrations.AddField(
            model_name="attachment",
            name="task",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attachments",
                to="tasks.task",
            ),
        ),
    ]
