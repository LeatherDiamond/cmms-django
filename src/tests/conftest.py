import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")
django.setup()
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth import get_user_model
from django.contrib.auth.models import ContentType, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.utils import timezone

import pytest

from buildings.models import Building

from tasks.models import Attachment, Task, TaskComment


@pytest.fixture
def user_factory(db):
    def create_user(**kwargs):
        defaults = {
            "email": "t.test@dacpol.eu",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe",
            "first_login": False,
        }
        defaults.update(kwargs)
        user = get_user_model().objects.create(
            email=defaults["email"],
            first_name=defaults["first_name"],
            last_name=defaults["last_name"],
            first_login=defaults["first_login"],
        )
        user.set_password(defaults["password"])
        user.save()
        return user

    return create_user


@pytest.fixture
def multiple_users(user_factory):
    def create_multiple(count=2):
        users = []
        for i in range(count):
            users.append(
                user_factory(
                    email=f"user{i+1}@example.com",
                    first_name=f"User{i+1}",
                    last_name="Test",
                )
            )
        return users

    return create_multiple


def generate_test_file(name, content, content_type):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type=content_type)


@pytest.fixture
def test_files():
    return [
        generate_test_file("test_file1.txt", "Test file content 1", "text/plain"),
        generate_test_file("test_file2.txt", "Test file content 2", "text/plain"),
    ]


@pytest.fixture
def superuser_factory(db):
    def create_superuser(**kwargs):
        defaults = {
            "email": "a.admin@dacpol.eu",
            "password": "password",
            "first_name": "Admin",
            "last_name": "User",
        }
        defaults.update(kwargs)
        return get_user_model().objects.create_superuser(**defaults)

    return create_superuser


@pytest.fixture
def building_factory(db):
    def create_building(**kwargs):
        defaults = {
            "name": "Building 1",
            "address": "123 Main St",
        }
        defaults.update(kwargs)
        return Building.objects.create(**defaults)

    return create_building


@pytest.fixture
def multiple_buildings(building_factory):
    def create_multiple(count=2):
        buildings = []
        for i in range(count):
            buildings.append(
                building_factory(name=f"Building {i+1}", address=f"Address {i+1}")
            )
        return buildings

    return create_multiple


@pytest.fixture
def task_factory(db, user_factory, building_factory):
    def create_task(user=None, comments=None, **kwargs):
        user = user or user_factory()
        building = building_factory()
        defaults = {
            "title": "Test Task",
            "deadline": timezone.now() + timezone.timedelta(days=1),
            "category": "planned",
            "priority": "medium",
            "description": "This is a test task.",
        }
        defaults.update(kwargs)
        task = Task.objects.create(**defaults)
        task.assigned_person.add(user)
        task.building.add(building)
        task.save()
        if comments:
            TaskComment.objects.create(task=task, user=user, comment_text=comments)

        return task

    return create_task


@pytest.fixture
def task_employee_status_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Task)
        defaults = {
            "name": "Can update task status as employee",
            "codename": "employee_task_status_update",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def attachment_factory(db, task_factory):
    def create_attachment(task=None, **kwargs):
        if task is None:
            task = task_factory()
        defaults = {
            "file": "Test_attachment.txt",
            "task": task,
        }
        defaults.update(kwargs)
        return Attachment.objects.create(**defaults)

    return create_attachment


@pytest.fixture
def view_building_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Building)
        defaults = {
            "name": "Can view building",
            "codename": "view_building",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def change_building_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Building)
        defaults = {
            "name": "Can change building",
            "codename": "change_building",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def add_building_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Building)
        defaults = {
            "name": "Can add building",
            "codename": "add_building",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def delete_building_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Building)
        defaults = {
            "name": "Can delete building",
            "codename": "delete_building",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def view_task_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Task)
        defaults = {
            "name": "Can view task",
            "codename": "view_task",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def create_task_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Task)
        defaults = {
            "name": "Can add task",
            "codename": "add_task",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def update_task_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Task)
        defaults = {
            "name": "Can change task",
            "codename": "change_task",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def delete_task_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Task)
        defaults = {
            "name": "Can delete task",
            "codename": "delete_task",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def task_leave_comment_permission_factory(db):
    def create_permission(**kwargs):
        content_type = ContentType.objects.get_for_model(Task)
        defaults = {
            "name": "Can leave task comment",
            "codename": "leave_comment",
            "content_type": content_type,
        }
        defaults.update(kwargs)
        permission, created = Permission.objects.get_or_create(
            codename=defaults["codename"],
            content_type=defaults["content_type"],
            defaults=defaults,
        )
        return permission

    return create_permission


@pytest.fixture
def anonymous_user():
    return lambda: type("AnonymousUser", (), {"is_authenticated": False})()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def attach_messages_middleware(rf):
    def _attach(request):
        middleware_session = SessionMiddleware(lambda req: None)
        middleware_session.process_request(request)

        middleware_messages = MessageMiddleware(lambda req: None)
        middleware_messages.process_request(request)

        request._messages = FallbackStorage(request)
        return request

    return _attach
