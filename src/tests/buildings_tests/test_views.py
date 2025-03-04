import json
from unittest.mock import patch

from buildings.models import Building
from buildings.views import (
    BuildingCreateView,
    BuildingDeleteView,
    BuildingListView,
    BuildingUpdateView,
)

from django.contrib.messages import constants as message_constants
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import reverse

import pytest

from users.models import AuditEntry


@pytest.mark.django_db
def test_building_list_view_authenticated_with_permission(
    rf, user_factory, view_building_permission_factory
):
    user = user_factory()
    permission = view_building_permission_factory()
    user.user_permissions.add(permission)
    request = rf.get(reverse("building_list"))
    request.user = user
    response = BuildingListView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_building_list_view_authenticated_without_permission(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("building_list"))
    request.user = user
    with pytest.raises(PermissionDenied):
        BuildingListView.as_view()(request)


@pytest.mark.django_db
def test_building_list_view_unauthenticated(rf, anonymous_user):
    request = rf.get(reverse("building_list"))
    user = anonymous_user()
    request.user = user
    response = BuildingListView.as_view()(request)
    assert response.status_code == 302


@pytest.mark.django_db
def test_building_list_view_pagination_first_page(
    rf, user_factory, view_building_permission_factory, building_factory
):
    user = user_factory()
    permission = view_building_permission_factory()
    user.user_permissions.add(permission)

    for i in range(15):
        building_factory(name=f"Building {i:02d}")

    url = reverse("building_list")
    request = rf.get(url)
    request.user = user

    response = BuildingListView.as_view()(request)
    page_obj = response.context_data.get("page_obj")

    assert page_obj.number == 1
    assert len(page_obj.object_list) == 10

    names = [building.name for building in page_obj.object_list]
    assert names == sorted(names)


@pytest.mark.django_db
def test_building_list_view_pagination_second_page(
    rf, user_factory, view_building_permission_factory, building_factory
):
    user = user_factory()
    permission = view_building_permission_factory()
    user.user_permissions.add(permission)

    for i in range(15):
        building_factory(name=f"Building {i:02d}")

    url = reverse("building_list") + "?page=2"
    request = rf.get(url)
    request.user = user

    response = BuildingListView.as_view()(request)
    page_obj = response.context_data.get("page_obj")

    assert page_obj.number == 2
    assert len(page_obj.object_list) == 5


@pytest.mark.django_db
def test_building_create_view_authenticated_with_permission(
    rf, user_factory, add_building_permission_factory
):
    user = user_factory()
    permission = add_building_permission_factory()
    user.user_permissions.add(permission)
    request = rf.get(reverse("building_create"))
    request.user = user
    response = BuildingCreateView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_building_create_view_authenticated_without_permission(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("building_create"))
    request.user = user
    with pytest.raises(PermissionDenied):
        BuildingCreateView.as_view()(request)


@pytest.mark.django_db
def test_building_create_view_unauthenticated(rf, anonymous_user):
    request = rf.get(reverse("building_create"))
    user = anonymous_user()
    request.user = user
    response = BuildingCreateView.as_view()(request)
    assert response.status_code == 302


@pytest.mark.django_db
def test_building_create_view_valid_form_submission(
    rf, user_factory, add_building_permission_factory, attach_messages_middleware
):
    user = user_factory()
    permission = add_building_permission_factory()
    user.user_permissions.add(permission)
    data = {"name": "Test Building", "address": "123 Test St"}
    request = rf.post(reverse("building_create"), data)
    request = attach_messages_middleware(request)
    request.user = user
    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingCreateView.as_view()(request)
        assert response.status_code == 302
        assert Building.objects.filter(name="Test Building").exists()
        building = Building.objects.get(name="Test Building")
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_CREATED,
            request,
            f"Budynek '{building.name}' został utworzony.",
        )

        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Budynek utworzony pomyślnie."
        assert msg_list[0].level == message_constants.SUCCESS


@pytest.mark.django_db
def test_building_create_view_invalid_form_submission(
    rf, user_factory, add_building_permission_factory
):
    user = user_factory()
    permission = add_building_permission_factory()
    user.user_permissions.add(permission)
    data = {"name": "", "address": "123 Test St"}
    request = rf.post(reverse("building_create"), data)
    request.user = user
    response = BuildingCreateView.as_view()(request)
    assert response.status_code == 200
    assert not Building.objects.filter(address="123 Test St").exists()


@pytest.mark.django_db
def test_building_update_view_authenticated_with_permission(
    rf,
    user_factory,
    change_building_permission_factory,
    building_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = change_building_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    data = {"name": "New Name", "address": "123 Test St"}
    request = rf.post(reverse("building_update", args=[building.id]), data)
    request = attach_messages_middleware(request)
    request.user = user

    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingUpdateView.as_view()(request, pk=building.id)
        assert response.status_code == 302
        building.refresh_from_db()
        assert building.name == "New Name"
        building = Building.objects.get(name="New Name")
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_UPDATED,
            request,
            f"Budynek '{building.name}' został zaktualizowany.",
        )

        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Budynek zaktualizowany pomyślnie."
        assert msg_list[0].level == message_constants.SUCCESS


@pytest.mark.django_db
def test_building_update_view_authenticated_without_permission(
    rf, user_factory, building_factory
):
    user = user_factory()
    building = building_factory()
    data = {"name": "New Name", "address": "123 Test St"}
    request = rf.post(reverse("building_update", args=[building.id]), data)
    request.user = user
    with pytest.raises(PermissionDenied):
        BuildingUpdateView.as_view()(request, pk=building.id)


@pytest.mark.django_db
def test_building_update_view_unauthenticated(rf, building_factory, anonymous_user):
    building = building_factory()
    data = {"name": "New Name", "address": "123 Test St"}
    request = rf.post(reverse("building_update", args=[building.id]), data)
    user = anonymous_user()
    request.user = user
    response = BuildingUpdateView.as_view()(request, pk=building.id)
    assert response.status_code == 302


@pytest.mark.django_db
def test_building_update_view_invalid_form_submission(
    rf, user_factory, change_building_permission_factory, building_factory
):
    user = user_factory()
    permission = change_building_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    data = {"name": "", "address": "123 Test St"}
    request = rf.post(reverse("building_update", args=[building.id]), data)
    request.user = user
    response = BuildingUpdateView.as_view()(request, pk=building.id)
    assert response.status_code == 200
    building.refresh_from_db()
    assert building.name == "Building 1"


@pytest.mark.django_db
def test_building_delete_view_authenticated_with_permission(
    rf,
    user_factory,
    delete_building_permission_factory,
    building_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = delete_building_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    request = rf.post(reverse("building_delete", args=[building.id]))
    request = attach_messages_middleware(request)
    request.user = user

    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingDeleteView.as_view()(request, pk=building.id)
        assert response.status_code == 302
        assert not Building.objects.filter(id=building.id).exists()
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_DELETED,
            request,
            f"Budynek '{building.name}' został usunięty.",
        )

        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Budynek usunięty pomyślnie."
        assert msg_list[0].level == message_constants.SUCCESS


@pytest.mark.django_db
def test_building_delete_view_authenticated_without_permission(
    rf, user_factory, building_factory
):
    user = user_factory()
    building = building_factory()
    request = rf.post(reverse("building_delete", args=[building.id]))
    request.user = user
    with pytest.raises(PermissionDenied):
        BuildingDeleteView.as_view()(request, pk=building.id)


@pytest.mark.django_db
def test_building_delete_view_unauthenticated(rf, building_factory, anonymous_user):
    building = building_factory()
    request = rf.post(reverse("building_delete", args=[building.id]))
    user = anonymous_user()
    request.user = user
    response = BuildingDeleteView.as_view()(request, pk=building.id)
    assert response.status_code == 302


@pytest.mark.django_db
def test_building_list_view_ajax_authenticated_without_permission(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("building_list"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    request.user = user
    with pytest.raises(PermissionDenied):
        BuildingListView.as_view()(request)


@pytest.mark.django_db
def test_building_create_view_ajax_authenticated_with_permission(
    rf, user_factory, add_building_permission_factory, attach_messages_middleware
):
    user = user_factory()
    permission = add_building_permission_factory()
    user.user_permissions.add(permission)
    data = {"name": "Test Building", "address": "123 Test St"}
    request = rf.post(
        reverse("building_create"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    request = attach_messages_middleware(request)
    request.user = user

    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingCreateView.as_view()(request)
        assert response.status_code == 200
        assert isinstance(response, JsonResponse)
        assert Building.objects.filter(name="Test Building").exists()
        building = Building.objects.get(name="Test Building")
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_CREATED,
            request,
            f"Budynek '{building.name}' został utworzony.",
        )
        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Budynek utworzony pomyślnie."
        assert msg_list[0].level == message_constants.SUCCESS


@pytest.mark.django_db
def test_building_update_view_ajax_authenticated_with_permission(
    rf,
    user_factory,
    change_building_permission_factory,
    building_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = change_building_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    data = {"name": "New Name", "address": "123 Test St"}
    request = rf.post(
        reverse("building_update", args=[building.id]),
        data,
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request = attach_messages_middleware(request)
    request.user = user
    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingUpdateView.as_view()(request, pk=building.id)
        assert response.status_code == 200
        assert isinstance(response, JsonResponse)
        building.refresh_from_db()
        assert building.name == "New Name"
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_UPDATED,
            request,
            f"Budynek '{building.name}' został zaktualizowany.",
        )
        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Budynek zaktualizowany pomyślnie."
        assert msg_list[0].level == message_constants.SUCCESS


@pytest.mark.django_db
def test_building_delete_view_ajax_authenticated_with_permission(
    rf,
    user_factory,
    delete_building_permission_factory,
    building_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = delete_building_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    request = rf.post(
        reverse("building_delete", args=[building.id]),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request = attach_messages_middleware(request)
    request.user = user

    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingDeleteView.as_view()(request, pk=building.id)
        assert response.status_code == 200
        assert isinstance(response, JsonResponse)
        assert not Building.objects.filter(id=building.id).exists()
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_DELETED,
            request,
            f"Budynek '{building.name}' został usunięty.",
        )
        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Budynek usunięty pomyślnie."
        assert msg_list[0].level == message_constants.SUCCESS


@pytest.mark.django_db
def test_building_delete_view_ajax_failed_deletion(
    rf,
    user_factory,
    mocker,
    delete_building_permission_factory,
    building_factory,
    attach_messages_middleware,
):
    user = user_factory()
    permission = delete_building_permission_factory()
    user.user_permissions.add(permission)
    building = building_factory()
    mocker.patch.object(Building, "delete", side_effect=Exception("Bląd"))
    request = rf.post(
        reverse("building_delete", args=[building.id]),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request = attach_messages_middleware(request)
    request.user = user
    with patch("users.models.AuditEntry.log_action") as mock_log_action:
        response = BuildingDeleteView.as_view()(request, pk=building.id)
        assert response.status_code == 400
        assert isinstance(response, JsonResponse)
        assert Building.objects.filter(id=building.id).exists()
        assert json.loads(response.content)["message"] == "Bląd: Bląd"
        mock_log_action.assert_any_call(
            AuditEntry.BUILDING_DELETE_FAILED,
            request,
            "Bląd podczas usuwania budynku: Bląd",
        )
        msg_list = list(request._messages)
        assert len(msg_list) == 1
        assert msg_list[0].message == "Wystąpił błąd. Spróbuj ponownie."
        assert msg_list[0].level == message_constants.ERROR
