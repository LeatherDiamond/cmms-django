from buildings.models import Building

from django.db import models

from users.models import CmmsUser


class Attachment(models.Model):
    file = models.FileField(upload_to="attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.file.name


class Task(models.Model):
    CATEGORY_CHOICES = [
        ("planned", "Zadanie planowe"),
        ("failure", "Awarie"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Niski"),
        ("medium", "Średni"),
        ("high", "Wysoki"),
    ]

    STATUS_CHOICES = [
        ("confirmed", "Wykonano"),
        ("declined", "Wykonanie nie potwierdzone"),
        ("accepted", "Wykonanie potwierdzone"),
    ]

    assigned_person = models.ManyToManyField(
        CmmsUser,
        related_name="assigned_person",
        verbose_name="assigned person",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    deadline = models.DateTimeField(
        verbose_name="Deadline",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Closed at",
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Category",
    )
    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_CHOICES,
        verbose_name="Priority",
    )
    description = models.TextField(
        max_length=2048,
        verbose_name="Description",
    )
    building = models.ManyToManyField(
        Building,
        related_name="building",
        verbose_name="Building",
    )
    status_field = models.CharField(
        max_length=30, choices=STATUS_CHOICES, blank=True, null=True
    )
    created_by = models.ForeignKey(
        CmmsUser,
        on_delete=models.CASCADE,
        related_name="manager",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        CmmsUser,
        on_delete=models.CASCADE,
    )

    comment_text = models.TextField(verbose_name=("Comment text"), blank=True)
    creation_date = models.DateTimeField(
        auto_now_add=True, verbose_name=("Creation date")
    )

    def __str__(self):
        return self.comment_text
