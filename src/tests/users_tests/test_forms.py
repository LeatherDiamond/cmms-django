import pytest

from users.forms import CmmsUserCreationForm


@pytest.mark.django_db
def test_user_creation_form_valid():
    form_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password1": "123123!!",
        "password2": "123123!!",
    }
    form = CmmsUserCreationForm(data=form_data)
    assert form.is_valid()
    user = form.save()
    assert user.email == "test@example.com"


@pytest.mark.django_db
def test_user_creation_form_invalid():
    form_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password1": "123123!!",
        "password2": "different_password",
    }
    form = CmmsUserCreationForm(data=form_data)
    assert not form.is_valid()


@pytest.mark.django_db
def test_user_creation_form_missing_fields():
    form_data = {
        "email": "test@example.com",
        "first_name": "",
        "last_name": "Doe",
        "password1": "123123!!",
        "password2": "123123!!",
    }
    form = CmmsUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "first_name" in form.errors


@pytest.mark.django_db
def test_user_creation_form_short_password():
    form_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password1": "short",
        "password2": "short",
    }
    form = CmmsUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "password2" in form.errors
