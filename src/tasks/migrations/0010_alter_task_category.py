# Generated by Django 5.1.4 on 2025-02-17 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0009_task_created_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="category",
            field=models.CharField(
                choices=[("planned", "Zadanie planowe"), ("failure", "Awarie")],
                max_length=50,
                verbose_name="Category",
            ),
        ),
    ]
