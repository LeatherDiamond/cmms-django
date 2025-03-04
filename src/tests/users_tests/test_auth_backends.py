import pytest

from users.auth_backends import EmailFirstAuthBackend


@pytest.mark.django_db
def test_email_first_auth_backend_valid(rf, user_factory):
    backend = EmailFirstAuthBackend()
    user_factory(email="t.test@dacpol.eu", password="password")
    request = rf.post("/login/", {"username": "ttest", "password": "password"})
    authenticated_user = backend.authenticate(
        request=request, username="ttest", password="password"
    )
    assert authenticated_user is not None
    assert authenticated_user.email == "t.test@dacpol.eu"


@pytest.mark.django_db
def test_email_first_auth_backend_invalid():
    backend = EmailFirstAuthBackend()
    authenticated_user = backend.authenticate(
        None, username="invalid@example.com", password="password"
    )
    assert authenticated_user is None


@pytest.mark.django_db
def test_email_first_auth_backend_invalid_password(rf, user_factory):
    backend = EmailFirstAuthBackend()
    user_factory(email="t.test@dacpol.eu", password="password")
    request = rf.post("/login/", {"username": "ttest", "password": "wrong_password"})
    authenticated_user = backend.authenticate(
        request=request, username="ttest", password="wrong_password"
    )
    assert authenticated_user is None


@pytest.mark.django_db
def test_email_first_auth_backend_user_not_found(rf):
    backend = EmailFirstAuthBackend()
    request = rf.post("/login/", {"username": "hey", "password": "password"})
    authenticated_user = backend.authenticate(
        request=request, username="hey", password="password"
    )
    assert authenticated_user is None
