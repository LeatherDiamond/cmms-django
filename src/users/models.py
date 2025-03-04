import logging

from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.models import AbstractUser
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.dispatch import receiver
from django.template import loader
from django.utils import timezone

from ipware import get_client_ip

from proj.settings import (
    DEBUG_DEFAULT_PASSWORD,
    DEBUG_PASSWORDS,
    DEFAULT_FROM_EMAIL,
)

import psycopg2

from users.managers import CmmsUserManager


logger = logging.getLogger(__name__)


class CmmsUser(AbstractUser):
    """
    Custom user having an email as a primary field.
    """

    username = None
    email = models.EmailField(("email address"), unique=True)
    first_login = models.BooleanField(default=True)
    is_manager = models.BooleanField(default=False, verbose_name=("Jest menedżerem"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CmmsUserManager()

    @property
    def full_name(self):
        """
        Returns a string consisting of this user's first_name and last_name.
        """
        return f"{self.first_name.title()} {self.last_name.capitalize()}"

    def save(self, *args, **kwargs):
        """
        Saves user to the database.
        Sets a randomly generated password if the user is created automatically.
        Sets a default password specified in DEBUG_DEFAULT_PASSWORD in settings.py if in debug mode.
        If the user is newly created, then an email is sent to user's email address.
        """
        if self.is_superuser:
            self.first_login = False
            self.is_staff = True

        if self.first_login and not CmmsUser.objects.filter(email=self.email).exists():
            if self.password:
                user_password = self.password
            else:
                if not DEBUG_PASSWORDS:
                    user_password = CmmsUser.objects.make_random_password()
                else:
                    user_password = DEBUG_DEFAULT_PASSWORD
            self.set_password(user_password)

            # send an email with a generated password
            context = {
                "user_email": self.email,
                "user_first_name": self.first_name,
                "user_password": user_password,
            }
            try:
                subject = loader.render_to_string(
                    "registration/initial_password_subject.txt", context
                )
                subject = "".join(subject.splitlines())
                body = loader.render_to_string(
                    "registration/initial_password_email.html", context
                )

                email_message = EmailMultiAlternatives(
                    subject, body, DEFAULT_FROM_EMAIL, [self.email]
                )
                html_email = loader.render_to_string(
                    "registration/initial_password_email.html", context
                )
                email_message.attach_alternative(html_email, "text/html")
                email_message.send()

                AuditEntry.log_action(
                    AuditEntry.USER_ADDED, None, f"id={self.id}, {self.full_name}", None
                )
                AuditEntry.log_action(
                    AuditEntry.EMAIL_SENT,
                    None,
                    f"Welcome email -> {self.full_name}",
                    None,
                )
            except Exception as exc:
                AuditEntry.log_action(
                    AuditEntry.EMAIL_FAILED,
                    None,
                    f"Welcome email - > {self.full_name}",
                    None,
                )
                logger.error(exc)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class AuditEntry(models.Model):
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_CHANGE_REQUESTED = "password_change_requested"
    USER_FIRST_LOGIN = "user_first_login"
    USER_ADDED = "user_added"
    TASK_CREATED = "task_created"
    TASK_CREATION_FAILED = "task_creation_failed"
    TASK_UPDATED = "task_updated"
    TASK_UPDATE_FAILED = "task_update_failed"
    TASK_DELETED = "task_deleted"
    TASK_DELETE_FAILED = "task_delete_failed"
    BUILDING_CREATED = "building_created"
    BUILDING_CREATION_FAILED = "building_creation_failed"
    BUILDING_UPDATED = "building_updated"
    BUILDING_UPDATE_FAILED = "building_update_failed"
    BUILDING_DELETED = "building_deleted"
    BUILDING_DELETE_FAILED = "building_delete_failed"
    TASK_COMMENT_CREATED = "task_comment_created"
    EMAIL_SENT = "email_sent"
    EMAIL_FAILED = "email_failed"

    action = models.CharField(max_length=64)
    ip = models.GenericIPAddressField(default=None, null=True, blank=True)
    email = models.EmailField(default=None, null=True, blank=True)
    date = models.DateTimeField(default=None, null=True, blank=True)
    description = models.TextField(default=None, null=True, blank=True)

    class Meta:
        verbose_name = "audit entry"
        verbose_name_plural = "audit entries"

    @staticmethod
    def log_action(action=None, request=None, description=None, ip=None):
        """
        Adds a new log as an AuditEntry object.
        params:
            action: str - a string specifying the type of action that is being logged.
                Preferably should be picked from members of AuditEntry class, e.g. AuditEntry.USER_ADDED
            request - a request object. Can be used to retrieve email of the user committing an action.
            description: str - additional info about the event.
            ip: str - an ip address of the person committing an action.
        """
        if not ip:
            if request:
                ip = get_visitor_ip(request)

        try:
            email = request.user.email if request else None
        except AttributeError:
            email = None

        AuditEntry.objects.create(
            action=action,
            ip=ip,
            email=email,
            date=timezone.now(),
            description=description,
        )

    def __unicode__(self):
        return "{0} - {1} - {2}".format(self.action, self.email, self.ip)

    def __str__(self):
        return "{0} - {1} - {2}".format(self.action, self.email, self.ip)


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """
    A callback function called on user's login.
    Creates a new log containing info about event (ip address of the user, their email and current date).
    """
    ip = get_visitor_ip(request)
    date = timezone.now()
    try:
        AuditEntry.objects.create(
            action="user_logged_in", ip=ip, email=user.email, date=date
        )
    except psycopg2.errors.UndefinedTable as exc:
        logger.error(exc)


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """
    A callback function called on user's logout.
    Creates a new log containing info about event (ip address of the user, their email and current date).
    """
    ip = get_visitor_ip(request)
    date = timezone.now()
    try:

        user_email = user.email if user else ""
        AuditEntry.objects.create(
            action="user_logged_out", ip=ip, email=user_email, date=date
        )
    except psycopg2.errors.UndefinedTable as exc:
        logger.error(exc)


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, request, **kwargs):
    """
    A callback function called when user failed to login.
    Creates a new log containing info about event (ip address of the user, their email and current date).
    An email is retrieved from credentials passed in an argument.
    """
    ip = get_visitor_ip(request)
    date = timezone.now()
    try:
        AuditEntry.objects.create(
            action="user_login_failed",
            ip=ip,
            email=credentials.get("email", None),
            date=date,
        )
    except psycopg2.errors.UndefinedTable as exc:
        logger.error(exc)


def get_visitor_ip(request):
    """
    Returns an ip address of http requestor. Returns an empty string if an ip address could not be retrieved.
    """
    try:
        ip = request.headers["X-Real-Ip"]
    except KeyError:
        try:
            ip = get_client_ip(request)[0]
        except Exception:
            ip = ""

    return ip
