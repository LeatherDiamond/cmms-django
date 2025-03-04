# Generated by Django 5.1.4 on 2025-01-22 13:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0003_attachment_remove_task_attachments_task_attachments"),
    ]

    operations = [
        migrations.AddField(
            model_name="attachment",
            name="task",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="task",
                to="tasks.task",
                verbose_name="task",
            ),
            preserve_default=False,
        ),
    ]
