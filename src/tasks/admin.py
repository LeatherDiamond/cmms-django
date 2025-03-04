from django.contrib import admin
from django.contrib.auth.models import Permission

from tasks.models import Attachment, Task, TaskComment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["file", "task", "uploaded_at"]
    list_filter = ["uploaded_at"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "created_at",
        "closed_at",
        "status_field",
        "dispay_building",
        "deadline",
        "category",
        "priority",
        "display_assigned_person",
        "attachments",
    ]
    list_filter = ["category", "priority", "created_at", "closed_at"]
    filter_horizontal = ["assigned_person", "building"]

    def display_assigned_person(self, obj):
        return ", ".join([user.full_name for user in obj.assigned_person.all()])

    def dispay_building(self, obj):
        return ", ".join([building.name for building in obj.building.all()])

    def attachments(self, obj):
        return ", ".join([attachment.file.name for attachment in obj.attachments.all()])


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "codename", "content_type")
    search_fields = ("name", "codename")
    list_filter = ("content_type",)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "user", "comment_text", "creation_date"]
    search_fields = ["task", "user"]
    list_filter = ["creation_date"]
