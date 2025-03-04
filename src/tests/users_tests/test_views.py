from django.urls import reverse

import pytest


@pytest.mark.django_db
def test_login_view_get(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_not_first_time(client, user_factory):
    user_factory()
    response = client.post(
        reverse("login"), {"username": "ttest", "password": "password"}
    )
    assert response.status_code == 302
    assert response.url == reverse("index")


@pytest.mark.django_db
def test_loginfirst_time(client, user_factory):
    user_factory(first_login=True)
    response = client.post(
        reverse("login"), {"username": "ttest", "password": "password"}
    )
    assert response.status_code == 302
    assert response.url == reverse("first_login_password_change")


@pytest.mark.django_db
def test_logout_view(client, user_factory):
    user = user_factory()
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_logout_view_unauthenticated(client):
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")


@pytest.mark.django_db
def test_logout_view_authenticated(client, user_factory):
    user = user_factory()
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")


@pytest.mark.django_db
def test_login_nonexistent_user(client):
    response = client.post(
        reverse("login"), {"username": "nonexistent", "password": "password"}
    )
    assert response.status_code == 200
    assert b"Please enter a correct email address and password." in response.content


@pytest.mark.django_db
def test_first_login_password_change_flow(client, user_factory):
    user = user_factory(
        first_login=True, email="t.test@dacpol.eu", password="old_password"
    )

    response = client.post(
        reverse("login"), {"username": "t.test@dacpol.eu", "password": "old_password"}
    )
    assert response.status_code == 302
    assert response.url == reverse("first_login_password_change")

    client.force_login(user)
    new_password = "new_secure_password123!!"
    response = client.post(
        reverse("first_login_password_change"),
        {
            "old_password": "old_password",
            "new_password1": new_password,
            "new_password2": new_password,
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("password_change_done")

    user.refresh_from_db()
    user.first_login = False
    user.save()

    client.logout()
    response = client.post(
        reverse("login"), {"username": "t.test@dacpol.eu", "password": new_password}
    )
    assert response.status_code == 302
    assert response.url == reverse("index")

    user.refresh_from_db()
    assert not user.first_login
