from django.utils import timezone

import pytest

from tasks.models import Attachment, Task, TaskComment


@pytest.mark.django_db
def test_create_task(task_factory):
    task = task_factory()

    assert task.title == "Test Task"
    assert task.category == "planned"
    assert task.priority == "medium"
    assert task.description == "This is a test task."
    assert task.assigned_person.count() == 1
    assert task.building.count() == 1
    assert task.assigned_person.first().first_name == "John"
    assert task.building.first().name == "Building 1"


@pytest.mark.django_db
def test_task_str(task_factory):
    task = task_factory()

    assert str(task) == "Test Task"


@pytest.mark.django_db
def test_task_with_attachments(task_factory, attachment_factory):
    task = task_factory()
    attachment = attachment_factory(task=task)

    assert task.attachments.count() == 1
    assert task.attachments.first() == attachment
    assert attachment.file == "Test_attachment.txt"


@pytest.mark.django_db
def test_task_with_comments(task_factory):
    task = task_factory(comments="This is a comment.")

    assert task.taskcomment_set.count() == 1
    assert task.taskcomment_set.first().comment_text == "This is a comment."


@pytest.mark.django_db
def test_delete_task(task_factory):
    task = task_factory()

    task_id = task.id
    task.delete()

    with pytest.raises(Task.DoesNotExist):
        Task.objects.get(id=task_id)


@pytest.mark.django_db
def test_attachment_creation(task_factory, attachment_factory):
    task = task_factory()
    attachment = attachment_factory(task=task)

    assert Attachment.objects.count() == 1
    assert attachment.file == "Test_attachment.txt"
    assert attachment.task == task


@pytest.mark.django_db
def test_attachment_str_representation(attachment_factory):
    attachment = attachment_factory()

    assert str(attachment) == "Test_attachment.txt"


@pytest.mark.django_db
def test_attachment_task_deletion(task_factory, attachment_factory):
    task = task_factory()
    attachment = attachment_factory(task=task)
    assert Attachment.objects.count() == 1
    task.delete()
    assert Attachment.objects.count() == 0


@pytest.mark.django_db
def test_attachment_without_task(attachment_factory):
    attachment = Attachment.objects.create(
        file="Test_attachment.txt",
        task=None,
    )

    assert Attachment.objects.count() == 1
    assert attachment.task is None
    assert attachment.file == "Test_attachment.txt"


@pytest.mark.django_db
def test_attachment_update(task_factory, attachment_factory):
    task = task_factory()
    attachment = attachment_factory(task=task)

    attachment.file = "Updated_file.txt"
    attachment.save()

    updated_attachment = Attachment.objects.get(id=attachment.id)
    assert updated_attachment.file == "Updated_file.txt"


@pytest.mark.django_db
def test_create_comment(task_factory):
    task = task_factory(comments="This is a test comment.")

    assert task.taskcomment_set.count() == 1
    comment = task.taskcomment_set.first()
    assert comment.comment_text == "This is a test comment."
    assert comment.creation_date is not None


@pytest.mark.django_db
def test_long_comment_text(task_factory):
    long_text = "A" * 2048
    task = task_factory(comments=long_text)

    assert task.taskcomment_set.first().comment_text == long_text


@pytest.mark.django_db
def test_comment_deletion_with_task(task_factory):
    task = task_factory(comments="Test Comment")

    task.delete()
    assert TaskComment.objects.count() == 0


@pytest.mark.django_db
def test_creation_date_auto(task_factory):
    task = task_factory(comments="Test Comment")
    comment = task.taskcomment_set.first()

    assert abs(timezone.now() - comment.creation_date).seconds < 5


@pytest.mark.django_db
def test_comment_str_representation(task_factory):
    task = task_factory(comments="Test Comment")
    comment = task.taskcomment_set.first()

    assert str(comment) == "Test Comment"


@pytest.mark.django_db
def test_filter_comments_by_user(task_factory, multiple_users):
    users = multiple_users()
    task = task_factory()
    TaskComment.objects.create(
        task=task, user=users[0], comment_text="Comment from user 1"
    )
    TaskComment.objects.create(
        task=task, user=users[1], comment_text="Comment from user 2"
    )

    assert TaskComment.objects.filter(user=users[0]).count() == 1
    assert TaskComment.objects.filter(user=users[1]).count() == 1
