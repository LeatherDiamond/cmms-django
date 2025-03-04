from django.utils import timezone
from django.utils.datastructures import MultiValueDict

import pytest

from tasks.forms import TaskCommentForm, TaskFilterForm, TaskForm


@pytest.mark.django_db
def test_task_form_valid_data(user_factory, building_factory):
    user = user_factory()
    building = building_factory()
    form = TaskForm(
        data={
            "title": "Task 1",
            "assigned_person": [user.id],
            "deadline": timezone.now() + timezone.timedelta(days=1),
            "category": "planned",
            "priority": "high",
            "description": "Description of task",
            "building": [building.id],
        }
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_task_form_empty_data():
    form = TaskForm(data={})
    assert not form.is_valid()
    assert "title" in form.errors
    assert "assigned_person" in form.errors
    assert "deadline" in form.errors


@pytest.mark.django_db
def test_task_form_with_attachments(test_files, multiple_users, multiple_buildings):
    buildings = multiple_buildings()
    users = multiple_users()

    form = TaskForm(
        data={
            "title": "Task 1",
            "assigned_person": [user.id for user in users],
            "deadline": timezone.now() + timezone.timedelta(days=1),
            "category": "planned",
            "priority": "high",
            "description": "Description of task",
            "building": [building.id for building in buildings],
        },
        files=MultiValueDict({"attachments": test_files}),
    )
    assert form.is_valid()
    assert form.cleaned_data["attachments"] == test_files


@pytest.mark.django_db
def test_task_filter_form_valid_data(multiple_users):
    users = multiple_users()
    form_data = {
        "assigned_person": users[0].id,
        "status_field": "accepted",
        "category": "planned",
        "priority": "high",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "closed_start": "2024-01-02",
        "closed_end": "2024-01-11",
        "deadline_start": "2024-01-05",
        "deadline_end": "2024-01-15",
    }
    form = TaskFilterForm(data=form_data)
    assert form.is_valid()


@pytest.mark.django_db
def test_task_filter_form_invalid_data():
    form_data = {"start_date": "invalid-date"}
    form = TaskFilterForm(data=form_data)
    assert not form.is_valid()
    assert "start_date" in form.errors


@pytest.mark.django_db
def test_task_comment_form_valid():
    form_data = {"comment_text": "This is a valid comment."}
    form = TaskCommentForm(data=form_data)
    assert form.is_valid()


@pytest.mark.django_db
def test_task_comment_form_invalid():
    form_data = {"comment_text": ""}
    form = TaskCommentForm(data=form_data)
    assert not form.is_valid()
    assert "comment_text" in form.errors
