from ipaddress import ip_address
from unittest.mock import Mock

from django.db.utils import IntegrityError
from django.utils.timezone import now

import pytest

from users.models import AuditEntry
from users.models import get_visitor_ip


@pytest.mark.django_db
def test_create_user(user_factory):
    user = user_factory()
    assert user.email == "t.test@dacpol.eu"
    assert user.first_name == "John"
    assert user.last_name == "Doe"


@pytest.mark.django_db
def test_create_superuser(superuser_factory):
    user = superuser_factory()
    assert user.is_superuser
    assert user.is_staff


@pytest.mark.django_db
def test_audit_entry_logging(db):
    entry = AuditEntry.objects.create(
        action=AuditEntry.USER_ADDED, description="Test Log"
    )
    assert AuditEntry.objects.count() == 1
    assert entry.action == AuditEntry.USER_ADDED


@pytest.mark.django_db
def test_audit_entry_fields(db):
    entry = AuditEntry.objects.create(
        action=AuditEntry.USER_ADDED, description="Test Log"
    )
    assert entry.description == "Test Log"


@pytest.mark.django_db
def test_user_unique_email(user_factory):
    user_factory(email="unique@dacpol.eu")
    with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
        user_factory(email="unique@dacpol.eu")


@pytest.mark.django_db
def test_user_change_password(user_factory):
    user = user_factory(password="old_password")
    user.set_password("new_password")
    user.save()
    assert user.check_password("new_password")


@pytest.mark.django_db
def test_audit_entry_missing_description(db):
    entry = AuditEntry.objects.create(action=AuditEntry.USER_ADDED, description="")
    assert entry.description == ""


@pytest.mark.django_db
def test_audit_entry_with_ip(user_factory):
    user = user_factory()
    entry = AuditEntry.objects.create(
        action=AuditEntry.USER_ADDED,
        description="User created",
        email=user,
        ip="192.168.1.1",
    )
    assert AuditEntry.objects.count() == 1
    assert entry.ip == "192.168.1.1"
    assert ip_address(entry.ip)


@pytest.mark.django_db
def test_audit_entry_without_ip(user_factory):
    user = user_factory()
    entry = AuditEntry.objects.create(
        action="user_logged_in",
        description="Login without IP",
        email=user,
    )
    assert AuditEntry.objects.count() == 1
    assert entry.ip is None


@pytest.mark.django_db
def test_audit_entry_with_timestamp(user_factory):
    user = user_factory()
    timestamp = now()
    entry = AuditEntry.objects.create(
        action=AuditEntry.USER_ADDED,
        description="Profile updated",
        email=user,
        ip="10.0.0.1",
        date=timestamp,
    )
    assert entry.date == timestamp
    assert entry.date <= now()


@pytest.mark.django_db
def test_audit_entry_invalid_ip(user_factory):
    user = user_factory()
    entry = AuditEntry(
        action="user_logged_in",
        description="Invalid IP test",
        email=user,
        ip="999.999.999.999",
    )
    with pytest.raises(
        ValueError,
        match="'999\\.999\\.999\\.999' does not appear to be an IPv4 or IPv6 address",
    ):
        ip_address(entry.ip)


@pytest.mark.django_db
def test_user_logged_out_callback(user_factory):
    user = user_factory()
    entry = AuditEntry.objects.create(
        action="user_logged_out",
        description="User logged out",
        email=user,
        ip="192.168.0.201",
    )
    assert AuditEntry.objects.count() == 1
    assert entry.action == "user_logged_out"
    assert entry.description == "User logged out"
    assert entry.email == user
    assert entry.ip == "192.168.0.201"


@pytest.mark.django_db
def test_user_login_failed_callback(user_factory):
    user = user_factory()
    entry = AuditEntry.objects.create(
        action="user_login_failed",
        description="User loggin failed",
        email=user,
        ip="192.168.0.201",
    )
    assert AuditEntry.objects.count() == 1
    assert entry.action == "user_login_failed"
    assert entry.description == "User loggin failed"
    assert entry.email == user
    assert entry.ip == "192.168.0.201"


@pytest.mark.django_db
def test_get_visitor_ip_with_x_real_ip():
    request = Mock()
    request.headers = {"X-Real-Ip": "192.168.1.1"}
    ip = get_visitor_ip(request)
    assert ip == "192.168.1.1"


@pytest.mark.django_db
def test_get_visitor_ip_if_its_empty():
    request = Mock()
    request.headers = {"X-Real-Ip": ""}
    ip = get_visitor_ip(request)
    assert ip == ""
