from django.urls import reverse

from homepage.views import IndexView

import pytest


@pytest.mark.django_db
def test_index_view_authenticated(rf, user_factory):
    user = user_factory(first_name="John")
    request = rf.get(reverse("index"))
    request.user = user
    response = IndexView.as_view()(request)

    assert response.status_code == 200
    assert (
        b'Witaj w CMMS <b><i style="color: var(--cmms-red);">DACPOL</i></b>'
        in response.content
    )
    assert f", {user.first_name}!".encode() in response.content


@pytest.mark.django_db
def test_index_view_superuser(rf, superuser_factory):
    user = superuser_factory(first_name="Admin")
    request = rf.get(reverse("index"))
    request.user = user
    response = IndexView.as_view()(request)

    assert response.status_code == 200
    assert (
        b'Witaj w CMMS <b><i style="color: var(--cmms-red);">DACPOL</i></b>'
        in response.content
    )
    assert f", {user.first_name}!".encode() in response.content


@pytest.mark.django_db
def test_dashboard_stats_display(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("index"))
    request.user = user
    response = IndexView.as_view()(request)

    assert response.status_code == 200
    assert b"Ca\xc5\x82kowita liczba zada\xc5\x84" in response.content
    assert b"Zadania otwarte" in response.content
    assert b"Zadania zamkni\xc4\x99te" in response.content
    assert b"Zadania zaleg\xc5\x82e" in response.content


@pytest.mark.django_db
def test_recent_tasks_section(rf, user_factory):
    user = user_factory()
    request = rf.get(reverse("index"))
    request.user = user
    response = IndexView.as_view()(request)

    assert response.status_code == 200
    assert b"Najnowsze zadania" in response.content


@pytest.mark.django_db
def test_index_view_unauthenticated(rf, anonymous_user):
    request = rf.get(reverse("index"))
    user = anonymous_user()
    request.user = user
    response = IndexView.as_view()(request)
    assert response.status_code == 302
