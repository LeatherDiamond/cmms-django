import json
from unittest.mock import call, patch

from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import reverse
from django.utils.timezone import now, timedelta

from freezegun import freeze_time

from proj.settings import DEFAULT_FROM_EMAIL

import pytest

from tasks.models import Task, TaskComment
from tasks.views import (
    TaskCreateView,
    TaskDeleteView,
    TaskEmployeeStatusUpdateView,
    TaskLeaveComment,
    TaskListView,
    TaskManagerStatusUpdateView,
    TaskUpdateView,
)

from users.models import AuditEntry


@pytest.mark.django_db
def test_task_list_view_authenticated_with_permission(
    rf, user_factory, view_task_permission_factory
):
    user = user_factory()
    permission = view_task_permission_factory()
    user.user_permissions.add(permission)
    request = rf.get(reverse("task_list"))
    request.user = user
    response = TaskListView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_task_list_view_authenticated_without_permission(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("task_list"))
    request.user = user
    with pytest.raises(PermissionDenied):
        TaskListView.as_view()(request)


@pytest.mark.django_db
def test_task_list_view_unauthenticated(rf, anonymous_user):
    request = rf.get(reverse("task_list"))
    user = anonymous_user()
    request.user = user
    response = TaskListView.as_view()(request)
    assert response.status_code == 302


@pytest.mark.django_db
def test_task_list_view_pagination_first_page(
    rf, user_factory, view_task_permission_factory, task_factory
):
    user = user_factory()
    permission = view_task_permission_factory()
    user.user_permissions.add(permission)

    for _ in range(15):
        task_factory(user=user)

    request = rf.get(reverse("task_list"))
    request.user = user

    response = TaskListView.as_view()(request)

    page_obj = response.context_data["page_obj"]
    assert page_obj.number == 1
    assert len(page_obj.object_list) == 10
    assert page_obj.has_next() is True


@pytest.mark.django_db
def test_task_list_view_pagination_second_page(
    rf, user_factory, view_task_permission_factory, task_factory
):
    user = user_factory()
    permission = view_task_permission_factory()
    user.user_permissions.add(permission)

    for _ in range(15):
        task_factory(user=user)

    request = rf.get(reverse("task_list") + "?page=2")
    request.user = user

    response = TaskListView.as_view()(request)

    page_obj = response.context_data["page_obj"]
    assert page_obj.number == 2
    assert len(page_obj.object_list) == 5
    assert page_obj.has_previous() is True
    assert page_obj.has_next() is False


@pytest.mark.django_db
def test_task_list_view_query_params_excludes_page(
    rf, user_factory, view_task_permission_factory, task_factory
):
    user = user_factory()
    permission = view_task_permission_factory()
    user.user_permissions.add(permission)

    for _ in range(15):
        task_factory(user=user, status_field="accepted")

    url = (
        reverse("task_list")
        + f"?assigned_person={user.pk}&status_field=accepted&page=2"
    )
    request = rf.get(url)
    request.user = user

    response = TaskListView.as_view()(request)
    query_params = response.context_data.get("query_params", "")

    assert "page=" not in query_params
    assert f"assigned_person={user.pk}" in query_params
    assert "status_field=accepted" in query_params


@pytest.mark.django_db
def test_task_create_view_authenticated_with_permissions(
    rf, user_factory, create_task_permission_factory
):
    user = user_factory()
    permission = create_task_permission_factory()
    user.user_permissions.add(permission)
    request = rf.get(reverse("task_create"))
    request.user = user
    response = TaskCreateView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_task_create_view_authenticated_without_permissions(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("task_create"))
    request.user = user
    with pytest.raises(PermissionDenied):
        TaskCreateView.as_view()(request)


@pytest.mark.django_db
def test_task_create_view_unauthenticated(rf, anonymous_user):
    request = rf.get(reverse("task_create"))
    user = anonymous_user()
    request.user = user
    response = TaskCreateView.as_view()(request)
    assert response.status_code == 302


@pytest.mark.django_db
def test_task_create_view_valid_form_submission(
    rf,
    user_factory,
    create_task_permission_factory,
    multiple_users,
    multiple_buildings,
    test_files,
    attach_messages_middleware,
):
    user = user_factory()
    permission = create_task_permission_factory()
    user.user_permissions.add(permission)

    buildings = multiple_buildings()
    users = multiple_users()

    data = {
        "title": "Test Task",
        "description": "Test Description",
        "deadline": "2022-01-01",
        "category": "planned",
        "priority": "medium",
        "building": [building.id for building in buildings],
        "assigned_person": [user.id for user in users],
    }

    request = rf.post(reverse("task_create"), data=data, format="multipart")
    request.FILES.setlist("attachments", test_files)
    request.user = user
    attach_messages_middleware(request)
    assert request.FILES.getlist("attachments") == test_files

    with patch("tasks.views.EmailMessage") as mock_email_class, patch(
        "users.models.AuditEntry.log_action"
    ) as mock_log_action:

        mock_email = mock_email_class.return_value

        response = TaskCreateView.as_view()(request)

        assert response.status_code == 302
        assert Task.objects.filter(title="Test Task").exists()

        task = Task.objects.get(title="Test Task")

        mock_email_class.assert_called_once_with(
            f"Nowe zadanie: {task.title}",
            f"Zostało ci przydzielone nowe zadanie:\n\n"
            f"Nazwa: {task.title}\n"
            f"Przypisana osoba: {', '.join(f'{user.first_name} {user.last_name}' for user in users)}\n"
            f"Termin: {task.deadline}\n"
            f"Kategoria: {task.get_category_display()}\n"
            f"Priorytet: {task.get_priority_display()}\n"
            f"Budynek: {', '.join(f'{building.name} ({building.address})' for building in buildings)}\n"
            f"Opis: {task.description}",
            DEFAULT_FROM_EMAIL,
            [user.email for user in users],
        )

        mock_email.send.assert_called_once()

        mock_log_action.assert_any_call(
            AuditEntry.TASK_CREATED, request, f"id={task.id}, {task.title}"
        )
        mock_log_action.assert_any_call(
            AuditEntry.EMAIL_SENT,
            request,
            f"Nowe zadanie: {task.title} -> ['user1@example.com', 'user2@example.com']",
        )

        assert task.attachments.count() == 2

        mock_email.attach.assert_any_call(
            task.attachments.get(file__icontains="test_file1").file.name,
            b"Test file content 1",
            "text/plain",
        )
        mock_email.attach.assert_any_call(
            task.attachments.get(file__icontains="test_file2").file.name,
            b"Test file content 2",
            "text/plain",
        )

        mock_email.send.assert_called_once()

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Zadanie utworzone pomyślnie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_create_view_invalid_form_submission(
    rf, user_factory, create_task_permission_factory
):
    user = user_factory()
    permission = create_task_permission_factory()
    user.user_permissions.add(permission)
    data = {
        "title": "Test Task",
        "description": "Test Description",
        "deadline": "2022-01-01",
    }
    request = rf.post(reverse("task_create"), data)
    request.user = user
    response = TaskCreateView.as_view()(request)
    assert response.status_code == 200
    assert not Task.objects.filter(title="Test Task").exists()


@pytest.mark.django_db
def test_task_update_view_authenticated_with_permission(
    rf,
    user_factory,
    update_task_permission_factory,
    task_factory,
    multiple_users,
    multiple_buildings,
    test_files,
    attach_messages_middleware,
):
    user = user_factory()
    permission = update_task_permission_factory()
    user.user_permissions.add(permission)
    old_task = task_factory(user=user)
    buildings = multiple_buildings()
    users = multiple_users()
    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "failure",
        "priority": "high",
        "building": [building.id for building in buildings],
        "assigned_person": [user.id for user in users],
    }
    request = rf.post(reverse("task_update", kwargs={"pk": old_task.id}), data)
    request.FILES.setlist("attachments", test_files)
    request.user = user
    attach_messages_middleware(request)
    assert request.FILES.getlist("attachments") == test_files

    with patch("tasks.views.EmailMessage") as mock_email_class, patch(
        "users.models.AuditEntry.log_action"
    ) as mock_log_action:

        mock_email = mock_email_class.return_value

        response = TaskUpdateView.as_view()(request, pk=old_task.id)
        assert response.status_code == 302
        old_task.refresh_from_db()
        assert old_task.title == "New Task"
        assert old_task.category == "failure"
        assert old_task.priority == "high"

        mock_email_class.assert_called_once_with(
            f"Zmiana zadania: {old_task.title}",
            f"Zostało zmienione zadanie:\n\n"
            f"Nazwa: {old_task.title}\n"
            f"Przypisana osoba: {', '.join(f'{user.first_name} {user.last_name}' for user in old_task.assigned_person.all())}\n"
            f"Status: -\n"
            f"Termin: {old_task.deadline}\n"
            f"Kategoria: {old_task.get_category_display()}\n"
            f"Priorytet: {old_task.get_priority_display()}\n"
            f"Budynek: {', '.join(f'{building.name} ({building.address})' for building in old_task.building.all())}\n"
            f"Opis: {old_task.description}\n"
            f"Komentarze: Brak",
            DEFAULT_FROM_EMAIL,
            [user.email for user in users],
        )

        mock_email.send.assert_called_once()

        mock_log_action.assert_any_call(
            AuditEntry.TASK_UPDATED, request, f"id={old_task.id}, {old_task.title}"
        )
        mock_log_action.assert_any_call(
            AuditEntry.EMAIL_SENT,
            request,
            f"Zmiana zadania: {old_task.title} -> ['user1@example.com', 'user2@example.com']",
        )

        assert old_task.attachments.count() == 2

        mock_email.attach.assert_any_call(
            old_task.attachments.get(file__icontains="test_file1").file.name,
            b"Test file content 1",
            "text/plain",
        )
        mock_email.attach.assert_any_call(
            old_task.attachments.get(file__icontains="test_file2").file.name,
            b"Test file content 2",
            "text/plain",
        )

        mock_email.send.assert_called_once()

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Zadanie zaktualizowane pomyślnie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_update_view_authenticated_without_permission(
    rf, user_factory, task_factory
):
    user = user_factory()
    old_task = task_factory(user=user)
    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "New Category",
        "priority": "New Priority",
        "building": [building.id for building in old_task.building.all()],
        "assigned_person": [
            assigned_person.id for assigned_person in old_task.assigned_person.all()
        ],
    }
    request = rf.post(reverse("task_update", kwargs={"pk": old_task.id}), data)
    request.user = user
    with pytest.raises(PermissionDenied):
        TaskUpdateView.as_view()(request, pk=old_task.id)


@pytest.mark.django_db
def test_task_update_view_unathenticated(rf, task_factory, anonymous_user):
    old_task = task_factory()
    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "New Category",
        "priority": "New Priority",
        "building": [building.id for building in old_task.building.all()],
        "assigned_person": [
            assigned_person.id for assigned_person in old_task.assigned_person.all()
        ],
    }
    request = rf.post(reverse("task_update", kwargs={"pk": old_task.id}), data)
    user = anonymous_user()
    request.user = user
    response = TaskUpdateView.as_view()(request, pk=old_task.id)
    assert response.status_code == 302


@pytest.mark.django_db
def test_task_update_invalid_form_submission(
    rf, user_factory, update_task_permission_factory, task_factory
):
    user = user_factory()
    permission = update_task_permission_factory()
    user.user_permissions.add(permission)
    old_task = task_factory(user=user)
    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "",
    }
    requset = rf.post(reverse("task_update", kwargs={"pk": old_task.id}), data)
    requset.user = user
    response = TaskUpdateView.as_view()(requset, pk=old_task.id)
    assert response.status_code == 200
    old_task.refresh_from_db()
    assert old_task.title == "Test Task"


@pytest.mark.django_db
def test_task_delete_view_autheticated_with_permission(
    rf,
    user_factory,
    delete_task_permission_factory,
    task_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = delete_task_permission_factory()
    user.user_permissions.add(permission)
    task = task_factory(user=user)
    request = rf.post(reverse("task_delete", kwargs={"pk": task.id}))
    request.user = user
    attach_messages_middleware(request)

    with patch("tasks.views.EmailMessage") as mock_email_class, patch(
        "users.models.AuditEntry.log_action"
    ) as mock_log_action:
        mock_email = mock_email_class.return_value
        response = TaskDeleteView.as_view()(request, pk=task.id)
        assert response.status_code == 302
        assert not Task.objects.filter(title="Test Task").exists()
        mock_email_class.assert_called_once_with(
            f"Usunięcie zadania: {task.title}",
            f"Zadanie {task.title} zostało usunięte.",
            DEFAULT_FROM_EMAIL,
            [user.email],
        )
        mock_email.send.assert_called_once()
        mock_log_action.assert_any_call(
            AuditEntry.TASK_DELETED, request, f"id={task.id}, {task.title}"
        )
        mock_log_action.assert_any_call(
            AuditEntry.EMAIL_SENT,
            request,
            f"Usunięcie zadania: {task.title} -> ['t.test@dacpol.eu']",
        )
        assert task.attachments.count() == 0

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Zadanie usunięte pomyślnie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_delete_view_authenticated_without_permission(
    rf, user_factory, task_factory
):
    user = user_factory()
    task = task_factory(user=user)
    request = rf.post(reverse("task_delete", kwargs={"pk": task.id}))
    request.user = user
    with pytest.raises(PermissionDenied):
        TaskDeleteView.as_view()(request, pk=task.id)


@pytest.mark.django_db
def test_task_delete_view_unauthenticated(rf, task_factory, anonymous_user):
    task = task_factory()
    request = rf.post(reverse("task_delete", kwargs={"pk": task.id}))
    user = anonymous_user()
    request.user = user
    response = TaskDeleteView.as_view()(request, pk=task.id)
    assert response.status_code == 302


@pytest.mark.django_db
def test_task_list_view_ajax_authenticated_without_permission(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("task_list"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    request.user = user
    with pytest.raises(PermissionDenied):
        TaskListView.as_view()(request)


@pytest.mark.django_db
def test_task_create_view_ajax_authenticated_with_permission(
    rf,
    user_factory,
    create_task_permission_factory,
    building_factory,
    multiple_users,
    test_files,
    attach_messages_middleware,
):
    user = user_factory()
    permission = create_task_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    assigned_persons = multiple_users()
    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "failure",
        "priority": "medium",
        "building": [building.id],
        "assigned_person": [assigned_person.id for assigned_person in assigned_persons],
    }
    request = rf.post(
        reverse("task_create"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    request.FILES.setlist("attachments", test_files)
    request.user = user
    attach_messages_middleware(request)
    assert request.FILES.getlist("attachments") == test_files

    with patch("tasks.views.EmailMessage") as mock_email_class, patch(
        "users.models.AuditEntry.log_action"
    ) as mock_log_action:

        mock_email = mock_email_class.return_value
        response = TaskCreateView.as_view()(request)
        assert response.status_code == 200
        assert isinstance(response, JsonResponse)
        assert Task.objects.filter(title="New Task").exists()

        task = Task.objects.get(title="New Task")

        mock_email_class.assert_called_once_with(
            f"Nowe zadanie: {task.title}",
            f"Zostało ci przydzielone nowe zadanie:\n\n"
            f"Nazwa: {task.title}\n"
            f"Przypisana osoba: {', '.join(f'{assigned_person.first_name} {assigned_person.last_name}' for assigned_person in assigned_persons)}\n"
            f"Termin: {task.deadline}\n"
            f"Kategoria: {task.get_category_display()}\n"
            f"Priorytet: {task.get_priority_display()}\n"
            f"Budynek: {building.name} ({building.address})\n"
            f"Opis: {task.description}",
            DEFAULT_FROM_EMAIL,
            [assigned_person.email for assigned_person in assigned_persons],
        )

        mock_email.send.assert_called_once()
        mock_log_action.assert_any_call(
            AuditEntry.TASK_CREATED, request, f"id={task.id}, {task.title}"
        )
        mock_log_action.assert_any_call(
            AuditEntry.EMAIL_SENT,
            request,
            f"Nowe zadanie: {task.title} -> ['user1@example.com', 'user2@example.com']",
        )

        assert task.attachments.count() == 2

        mock_email.attach.assert_any_call(
            task.attachments.get(file__icontains="test_file1").file.name,
            b"Test file content 1",
            "text/plain",
        )
        mock_email.attach.assert_any_call(
            task.attachments.get(file__icontains="test_file2").file.name,
            b"Test file content 2",
            "text/plain",
        )
        mock_email.send.assert_called_once()

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Zadanie utworzone pomyślnie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_update_view_ajax_authenticated_with_permission(
    rf,
    user_factory,
    update_task_permission_factory,
    task_factory,
    multiple_users,
    multiple_buildings,
    test_files,
    attach_messages_middleware,
):
    user = user_factory()
    permission = update_task_permission_factory()
    user.user_permissions.add(permission)
    old_task = task_factory(user=user)
    buildings = multiple_buildings()
    users = multiple_users()
    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "planned",
        "priority": "low",
        "building": [building.id for building in buildings],
        "assigned_person": [users.id for users in users],
    }
    request = rf.post(
        reverse("task_update", kwargs={"pk": old_task.id}),
        data,
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.FILES.setlist("attachments", test_files)
    request.user = user
    attach_messages_middleware(request)
    assert request.FILES.getlist("attachments") == test_files

    with patch("tasks.views.EmailMessage") as mock_email_class, patch(
        "users.models.AuditEntry.log_action"
    ) as mock_log_action:
        mock_email = mock_email_class.return_value
        response = TaskUpdateView.as_view()(request, pk=old_task.id)
        assert response.status_code == 200
        assert isinstance(response, JsonResponse)
        old_task.refresh_from_db()
        assert old_task.title == "New Task"
        assert old_task.priority == "low"
        assert old_task.category == "planned"
        mock_email_class.assert_called_once_with(
            f"Zmiana zadania: {old_task.title}",
            f"Zostało zmienione zadanie:\n\n"
            f"Nazwa: {old_task.title}\n"
            f"Przypisana osoba: {', '.join(f'{user.first_name} {user.last_name}' for user in old_task.assigned_person.all())}\n"
            f"Status: -\n"
            f"Termin: {old_task.deadline}\n"
            f"Kategoria: {old_task.get_category_display()}\n"
            f"Priorytet: {old_task.get_priority_display()}\n"
            f"Budynek: {', '.join(f'{building.name} ({building.address})' for building in old_task.building.all())}\n"
            f"Opis: {old_task.description}\n"
            f"Komentarze: Brak",
            DEFAULT_FROM_EMAIL,
            [user.email for user in users],
        )
        mock_email.send.assert_called_once()
        mock_log_action.assert_any_call(
            AuditEntry.TASK_UPDATED, request, f"id={old_task.id}, {old_task.title}"
        )
        mock_log_action.assert_any_call(
            AuditEntry.EMAIL_SENT,
            request,
            f"Zmiana zadania: {old_task.title} -> ['user1@example.com', 'user2@example.com']",
        )
        assert old_task.attachments.count() == 2
        mock_email.attach.assert_any_call(
            old_task.attachments.get(file__icontains="test_file1").file.name,
            b"Test file content 1",
            "text/plain",
        )
        mock_email.attach.assert_any_call(
            old_task.attachments.get(file__icontains="test_file2").file.name,
            b"Test file content 2",
            "text/plain",
        )
        mock_email.send.assert_called_once()

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Zadanie zaktualizowane pomyślnie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_delete_view_ajax_authenticated_with_permission(
    rf,
    user_factory,
    delete_task_permission_factory,
    task_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = delete_task_permission_factory()
    user.user_permissions.add(permission)
    task = task_factory(user=user)
    request = rf.post(
        reverse("task_delete", kwargs={"pk": task.id}),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = user
    attach_messages_middleware(request)

    with patch("tasks.views.EmailMessage") as mock_email_class, patch(
        "users.models.AuditEntry.log_action"
    ) as mock_log_action:
        mock_email = mock_email_class.return_value
        response = TaskDeleteView.as_view()(request, pk=task.id)
        assert response.status_code == 200
        assert isinstance(response, JsonResponse)
        assert not Task.objects.filter(title="Test Task").exists()
        mock_email_class.assert_called_once_with(
            f"Usunięcie zadania: {task.title}",
            f"Zadanie {task.title} zostało usunięte.",
            DEFAULT_FROM_EMAIL,
            [user.email],
        )
        mock_email.send.assert_called_once()
        mock_log_action.assert_any_call(
            AuditEntry.TASK_DELETED, request, f"id={task.id}, {task.title}"
        )
        mock_log_action.assert_any_call(
            AuditEntry.EMAIL_SENT,
            request,
            f"Usunięcie zadania: {task.title} -> ['t.test@dacpol.eu']",
        )
        assert task.attachments.count() == 0

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Zadanie usunięte pomyślnie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_delete_view_ajax_failed_deletion(
    rf,
    user_factory,
    mocker,
    delete_task_permission_factory,
    task_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = delete_task_permission_factory()
    user.user_permissions.add(permission)
    task = task_factory(user=user)
    mocker.patch.object(Task, "delete", side_effect=Exception("Błąd"))
    request = rf.post(
        reverse("task_delete", kwargs={"pk": task.id}),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = user
    attach_messages_middleware(request)

    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = TaskDeleteView.as_view()(request, pk=task.id)
        assert response.status_code == 400
        assert isinstance(response, JsonResponse)
        assert Task.objects.filter(title="Test Task").exists()
        assert json.loads(response.content)["message"] == "Błąd: Błąd"
        mock_log_action.assert_any_call(
            AuditEntry.TASK_DELETE_FAILED, request, f"{task.title}"
        )

        messages_list = list(get_messages(request))
        assert any(
            msg.message == "Wystąpił błąd. Spróbuj ponownie." for msg in messages_list
        )


@pytest.mark.django_db
def test_task_employee_status_update_view(
    rf,
    user_factory,
    multiple_buildings,
    multiple_users,
    create_task_permission_factory,
    task_employee_status_permission_factory,
    attach_messages_middleware,
):
    manager = user_factory()
    manager.is_manager = True
    manager.save()

    assigned_persons = multiple_users()
    buildings = multiple_buildings()

    permission_create = create_task_permission_factory()
    permission_status = task_employee_status_permission_factory()

    assigned_persons[0].user_permissions.add(permission_status)
    manager.user_permissions.add(permission_create)

    data = {
        "title": "New Task",
        "description": "New Description",
        "deadline": "2022-01-01",
        "category": "failure",
        "priority": "medium",
        "building": [building.id for building in buildings],
        "assigned_person": [assigned_person.id for assigned_person in assigned_persons],
        "created_by": manager.id,
    }
    request_task_create = rf.post(reverse("task_create"), data=data, format="multipart")
    request_task_create.user = manager
    attach_messages_middleware(request_task_create)
    response = TaskCreateView.as_view()(request_task_create)

    task = Task.objects.get(title="New Task")
    request_task_status_update = rf.get(
        reverse(
            "task_employee_status_update", kwargs={"pk": task.pk, "status": "confirmed"}
        )
    )
    request_task_status_update.user = assigned_persons[0]
    attach_messages_middleware(request_task_status_update)

    with patch("tasks.views.AuditEntry.log_action") as mock_log_action, patch(
        "tasks.views.EmailMessage"
    ) as mock_email_class:

        mock_email = mock_email_class.return_value

        response = TaskEmployeeStatusUpdateView.as_view()(
            request_task_status_update, pk=task.pk, status="confirmed"
        )

        assert response.status_code == 302
        task.refresh_from_db()
        assert task.status_field == "confirmed"

        mock_email_class.assert_called_once_with(
            f"Aktualizacja statusu: {task.title}",
            f"Osoba odpowiedzialna za zadanie oznaczyła je jako wykonano:\n\n"
            f"Nazwa: {task.title}\n"
            f"Przypisana osoba: {', '.join(f'{user.first_name} {user.last_name}' for user in assigned_persons)}\n"
            f"Status: Wykonano\n"
            f"Termin: {task.deadline}\n"
            f"Kategoria: {task.get_category_display()}\n"
            f"Priorytet: {task.get_priority_display()}\n"
            f"Budynek: {', '.join(f'{building.name} ({building.address})' for building in buildings)}\n"
            f"Opis: {task.description}",
            DEFAULT_FROM_EMAIL,
            [manager.email, assigned_persons[1].email],
        )

        mock_email.send.assert_called_once()

        expected_calls = [
            call(
                AuditEntry.TASK_UPDATED,
                request_task_status_update,
                f"id={task.id}, {task.title} -> {task.status_field}",
            ),
            call(
                AuditEntry.EMAIL_SENT,
                request_task_status_update,
                f"Aktualizacja statusu: {task.title} -> ['{task.created_by.email}', '{assigned_persons[1].email}']",
            ),
        ]

        mock_log_action.assert_has_calls(expected_calls, any_order=True)

        messages_list = list(get_messages(request_task_status_update))
        assert any(
            msg.message == f'Zadanie "{task.title}" jest oznczone jako wykonane.'
            for msg in messages_list
        )


@pytest.mark.django_db
def test_task_employee_status_update_view_return_empty_status(
    rf,
    user_factory,
    task_factory,
    attach_messages_middleware,
    task_employee_status_permission_factory,
):
    user = user_factory()
    task = task_factory(user=user)
    task.created_by = user
    task.status_field = "accepted"
    task.save()

    permission = task_employee_status_permission_factory()
    user.user_permissions.add(permission)

    request = rf.get(
        reverse("task_employee_status_update", kwargs={"pk": task.pk, "status": "none"})
    )
    request.user = user
    attach_messages_middleware(request)

    with patch("tasks.views.AuditEntry.log_action") as mock_log_action, patch(
        "tasks.views.EmailMessage"
    ):
        response = TaskEmployeeStatusUpdateView.as_view()(
            request, pk=task.pk, status="none"
        )

        assert response.status_code == 302
        task.refresh_from_db()
        assert task.status_field is None

        expected_calls = [
            call(
                AuditEntry.TASK_UPDATED,
                request,
                f"id={task.id}, {task.title} -> Wykonanie zadania cofnięte.",
            ),
            call(
                AuditEntry.EMAIL_SENT,
                request,
                f"Aktualizacja statusu: {task.title} -> ['{task.created_by.email}']",
            ),
        ]

        mock_log_action.assert_has_calls(expected_calls, any_order=True)

        messages_list = list(get_messages(request))
        assert any(
            msg.message == f'Wykonanie "{task.title}" zadania cofnięte.'
            for msg in messages_list
        )


@pytest.mark.django_db
def test_task_manager_status_update_view_get(
    rf, superuser_factory, task_factory, attach_messages_middleware
):
    user = superuser_factory()
    task = task_factory(user=user)
    task.created_by = user
    task.save()

    request = rf.get(
        reverse(
            "task_manager_status_update", kwargs={"pk": task.pk, "status": "accepted"}
        )
    )
    request.user = user
    attach_messages_middleware(request)

    with patch("tasks.views.AuditEntry.log_action") as mock_log_action:
        response = TaskManagerStatusUpdateView.as_view()(
            request, pk=task.pk, status="accepted"
        )

        assert response.status_code == 302
        task.refresh_from_db()
        assert task.status_field == "accepted"
        assert task.closed_at is not None

        messages_list = list(get_messages(request))
        assert any(
            msg.message == f'Wykonanie zadania "{task.title}" potwierdzone.'
            for msg in messages_list
        )

        expected_calls = [
            call(
                AuditEntry.TASK_UPDATED,
                request,
                f"id={task.id}, {task.title} -> {task.status_field}",
            ),
            call(
                AuditEntry.EMAIL_SENT,
                request,
                f"Aktualizacja statusu: {task.title} -> ['{task.created_by.email}']",
            ),
        ]

        mock_log_action.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.django_db
def test_task_manager_status_update_view_post(
    rf, superuser_factory, task_factory, attach_messages_middleware
):
    user = superuser_factory()
    task = task_factory(user=user)
    task.created_by = user
    task.save()

    data = {"comment_text": "Zadanie nie zostało wykonane poprawnie."}
    request = rf.post(
        reverse(
            "task_manager_status_update", kwargs={"pk": task.pk, "status": "declined"}
        ),
        data,
    )
    request.user = user
    attach_messages_middleware(request)

    with patch("tasks.views.AuditEntry.log_action") as mock_log_action:
        response = TaskManagerStatusUpdateView.as_view()(request, pk=task.pk)

        assert response.status_code == 302
        task.refresh_from_db()
        assert task.status_field == "declined"

        assert TaskComment.objects.filter(
            task=task, user=user, comment_text="Zadanie nie zostało wykonane poprawnie."
        ).exists()

        messages_list = list(get_messages(request))
        assert any(
            msg.message == f'Wykonanie zadania "{task.title}" nie potwierdzone.'
            for msg in messages_list
        )

        expected_calls = [
            call(
                AuditEntry.TASK_UPDATED,
                request,
                f"id={task.id}, {task.title} -> {task.status_field}",
            ),
            call(
                AuditEntry.EMAIL_SENT,
                request,
                f"Aktualizacja statusu: {task.title} -> ['{task.created_by.email}']",
            ),
        ]

        mock_log_action.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.django_db
def test_task_list_view_filters(
    rf, user_factory, task_factory, view_task_permission_factory
):
    user = user_factory()
    task1 = task_factory(
        user=user, title="Planned Task", category="planned", priority="high"
    )
    task2 = task_factory(
        user=user, title="Failure Task", category="failure", priority="low"
    )
    permission = view_task_permission_factory()
    user.user_permissions.add(permission)

    request = rf.get(reverse("task_list"), {"category": "planned"})
    request.user = user
    response = TaskListView.as_view()(request)
    response.render()

    assert response.status_code == 200
    assert task1.title in response.content.decode()
    assert task2.title not in response.content.decode()


@pytest.mark.django_db
def test_task_list_view_date_filtering(
    rf, user_factory, task_factory, view_task_permission_factory
):
    user = user_factory()

    with freeze_time(now() - timedelta(days=2)):
        task1 = task_factory(user=user, title="Planned Task")

    with freeze_time(now() - timedelta(days=10)):
        task2 = task_factory(user=user, title="Failure Task")

    permission = view_task_permission_factory()
    user.user_permissions.add(permission)

    start_date_str = (now() - timedelta(days=5)).strftime("%Y-%m-%d")
    request = rf.get(reverse("task_list"), {"start_date": start_date_str})
    request.user = user
    response = TaskListView.as_view()(request)
    response.render()

    assert response.status_code == 200
    assert task1.title in response.content.decode()
    assert task2.title not in response.content.decode()


@pytest.mark.django_db
def test_task_list_view_manager_access(
    rf, user_factory, multiple_users, task_factory, view_task_permission_factory
):
    manager = user_factory()
    manager.is_manager = True
    manager.save()

    users = multiple_users()

    task1 = task_factory(user=users[0], title="Planned Task")
    task2 = task_factory(user=users[1], title="Failure Task")

    permission = view_task_permission_factory()
    manager.user_permissions.add(permission)

    request = rf.get(reverse("task_list"))
    request.user = manager
    response = TaskListView.as_view()(request)
    response.render()

    assert response.status_code == 200
    assert task1.title in str(response.content)
    assert task2.title in str(response.content)


@pytest.mark.django_db
def test_task_list_view_non_manager_access(
    rf, multiple_users, task_factory, view_task_permission_factory
):
    users = multiple_users()

    user = users[0]
    task1 = task_factory(user=user, title="Planned Task 1")
    task2 = task_factory(user=users[1], title="Planned Task2")

    permission = view_task_permission_factory()
    user.user_permissions.add(permission)

    request = rf.get(reverse("task_list"))
    request.user = user
    response = TaskListView.as_view()(request)
    response.render()

    assert response.status_code == 200
    assert task1.title in str(response.content)
    assert task2.title not in str(response.content)


@pytest.mark.django_db
def test_task_leave_comment_authenticated_with_permission(
    rf,
    user_factory,
    task_leave_comment_permission_factory,
    task_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = task_leave_comment_permission_factory()
    user.user_permissions.add(permission)
    task = task_factory(user=user)

    data = {"comment_text": "This is a test comment"}
    request = rf.post(reverse("task_leave_comment", kwargs={"pk": task.id}), data)
    request.user = user
    attach_messages_middleware(request)

    with patch.object(TaskLeaveComment, "notify_users") as mock_notify:
        response = TaskLeaveComment.as_view()(request, pk=task.id)

        assert response.status_code == 200
        json_response = json.loads(response.content.decode())
        assert json_response["success"] is True
        assert json_response["comment"]["text"] == data["comment_text"]

        comment = TaskComment.objects.get(task=task)
        assert comment.comment_text == data["comment_text"]
        assert comment.user == user

        mock_notify.assert_called_once_with(task)


@pytest.mark.django_db
def test_task_leave_comment_without_permission(
    rf, user_factory, task_factory, attach_messages_middleware
):
    user = user_factory()
    task = task_factory(user=user)

    data = {"comment_text": "Unauthorized comment"}
    request = rf.post(reverse("task_leave_comment", kwargs={"pk": task.id}), data)
    request.user = user
    attach_messages_middleware(request)

    with pytest.raises(PermissionDenied):
        TaskLeaveComment.as_view()(request, pk=task.id)


@pytest.mark.django_db
def test_task_leave_comment_invalid_data(
    rf, user_factory, task_leave_comment_permission_factory, task_factory
):
    user = user_factory()
    permission = task_leave_comment_permission_factory()
    user.user_permissions.add(permission)
    task = task_factory(user=user)

    request = rf.post(reverse("task_leave_comment", kwargs={"pk": task.id}), {})
    request.user = user

    response = TaskLeaveComment.as_view()(request, pk=task.id)

    assert response.status_code == 200
    json_response = json.loads(response.content.decode())
    assert json_response["success"] is False
    assert "comment_text" in json_response["errors"]
    assert TaskComment.objects.count() == 0


@pytest.mark.django_db
def test_task_leave_comment_email_recipients(
    rf,
    user_factory,
    task_leave_comment_permission_factory,
    task_factory,
    multiple_users,
):
    user = user_factory()
    permission = task_leave_comment_permission_factory()
    user.user_permissions.add(permission)
    users = multiple_users(count=3)
    task = task_factory(user=user)
    task.assigned_person.add(*users)

    request = rf.post(
        reverse("task_leave_comment", kwargs={"pk": task.id}),
        {"comment_text": "Test email"},
    )
    request.user = user

    with patch.object(TaskLeaveComment, "notify_users") as mock_notify:
        response = TaskLeaveComment.as_view()(request, pk=task.id)

        assert response.status_code == 200
        json_response = json.loads(response.content.decode())
        assert json_response["success"] is True

        mock_notify.assert_called_once_with(task)


@pytest.mark.django_db
def test_task_leave_comment_email_with_attachments(
    rf,
    user_factory,
    task_leave_comment_permission_factory,
    task_factory,
    attachment_factory,
    test_files,
):
    user = user_factory()
    permission = task_leave_comment_permission_factory()
    user.user_permissions.add(permission)
    task = task_factory(user=user)

    request = rf.post(
        reverse("task_leave_comment", kwargs={"pk": task.id}),
        {"comment_text": "Comment with attachments"},
    )
    request.user = user

    with patch.object(TaskLeaveComment, "notify_users") as mock_notify:
        response = TaskLeaveComment.as_view()(request, pk=task.id)

        assert response.status_code == 200
        json_response = json.loads(response.content.decode())
        assert json_response["success"] is True

        mock_notify.assert_called_once_with(task)
