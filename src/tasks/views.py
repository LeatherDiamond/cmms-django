import datetime
import mimetypes
import os
import textwrap

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from proj.settings import DEFAULT_FROM_EMAIL

from tasks.forms import TaskCommentForm, TaskFilterForm, TaskForm
from tasks.models import Attachment, Task, TaskComment

from users.models import AuditEntry


class TaskListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Task
    permission_required = "tasks.view_task"
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()

        if not user.is_manager:
            queryset = queryset.filter(assigned_person=user)

        assigned_person = self.request.GET.get("assigned_person")
        status_field = self.request.GET.get("status_field")
        category = self.request.GET.get("category")
        priority = self.request.GET.get("priority")

        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        closed_start = self.request.GET.get("closed_start")
        closed_end = self.request.GET.get("closed_end")
        deadline_start = self.request.GET.get("deadline_start")
        deadline_end = self.request.GET.get("deadline_end")

        if start_date:
            start_date = parse_date(start_date)
        if end_date:
            end_date = parse_date(end_date)
        if closed_start:
            closed_start = parse_date(closed_start)
        if closed_end:
            closed_end = parse_date(closed_end)
        if deadline_start:
            deadline_start = parse_date(deadline_start)
        if deadline_end:
            deadline_end = parse_date(deadline_end)

        if assigned_person:
            queryset = queryset.filter(assigned_person=assigned_person)

        if status_field:
            queryset = queryset.filter(status_field=status_field)

        if category:
            queryset = queryset.filter(category=category)

        if priority:
            queryset = queryset.filter(priority=priority)

        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        if closed_start:
            queryset = queryset.filter(closed_at__date__gte=closed_start)
        if closed_end:
            queryset = queryset.filter(closed_at__date__lte=closed_end)

        if deadline_start:
            queryset = queryset.filter(deadline__date__gte=deadline_start)
        if deadline_end:
            queryset = queryset.filter(deadline__date__lte=deadline_end)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = TaskCommentForm()
        context["filter_form"] = TaskFilterForm(self.request.GET)
        query_params = self.request.GET.copy()
        if "page" in query_params:
            del query_params["page"]
        context["query_params"] = query_params.urlencode()
        return context


class TaskCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Task
    permission_required = "tasks.add_task"
    template_name = "tasks/task_create.html"
    form_class = TaskForm
    success_url = reverse_lazy("task_list")

    def form_valid(self, form):
        try:
            task = form.save()

            task.assigned_person.set(form.cleaned_data["assigned_person"])
            task.building.set(form.cleaned_data["building"])
            task.created_by = self.request.user
            task.save()

            attachments = self.request.FILES.getlist("attachments")
            self.save_attachments(task, attachments)

            AuditEntry.log_action(
                AuditEntry.TASK_CREATED, self.request, f"id={task.id}, {task.title}"
            )

            self.notify_users(task)
            messages.success(self.request, "Zadanie utworzone pomyślnie.")

            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Zadanie utworzone pomyślnie."}
                )
            return super().form_valid(form)

        except Exception as e:
            AuditEntry.log_action(
                AuditEntry.TASK_CREATION_FAILED,
                self.request,
                f"{task.title if 'task' in locals() else 'Unknown task'}",
            )
            messages.error(self.request, "Wystąpił błąd. Spróbuj ponownie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": f"Błąd: {str(e)}"})
            raise

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Błąd: Niepoprawne dane.",
                    "errors": form.errors,
                }
            )
        return super().form_invalid(form)

    def save_attachments(self, task, attachments):
        for file in attachments:
            Attachment.objects.create(file=file, task=task)

    def notify_users(self, task):
        assigned_persons = ", ".join(
            [user.full_name for user in task.assigned_person.all()]
        )
        buildings = ", ".join(
            [
                f"{building.name} ({building.address})"
                for building in task.building.all()
            ]
        )
        subject = f"Nowe zadanie: {task.title}"
        message = textwrap.dedent(
            f"""
            Zostało ci przydzielone nowe zadanie:
                                       
            Nazwa: {task.title}
            Przypisana osoba: {assigned_persons}
            Termin: {task.deadline}
            Kategoria: {task.get_category_display()}
            Priorytet: {task.get_priority_display()}
            Budynek: {buildings}
            Opis: {task.description}
        """
        ).strip()

        emails = list(task.assigned_person.values_list("email", flat=True))
        if emails:
            email = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, emails)
            for attachment in task.attachments.all():
                file_path = attachment.file.path
                mime_type, _ = mimetypes.guess_type(file_path)
                with open(file_path, "rb") as file_content:
                    email.attach(
                        attachment.file.name,
                        file_content.read(),
                        mime_type or "application/octet-stream",
                    )
            email.send()
            AuditEntry.log_action(
                AuditEntry.EMAIL_SENT, self.request, f"{subject} -> {emails}"
            )


class TaskUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Task
    permission_required = "tasks.change_task"
    template_name = "tasks/task_update.html"
    form_class = TaskForm
    success_url = reverse_lazy("task_list")

    def get_form_kwargs(self):
        """Transfer instance to the form"""
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_initial(self):
        """Transfer ManyToMany fileds to the form"""
        initial = super().get_initial()
        task = self.get_object()
        initial["assigned_person"] = task.assigned_person.all()
        initial["building"] = task.building.all()
        return initial

    def get_context_data(self, **kwargs):
        """Transfer existing attachments to the form"""
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        context["attachments"] = Attachment.objects.filter(task=task)
        return context

    def form_valid(self, form):
        try:
            task = form.save()

            task.assigned_person.set(form.cleaned_data["assigned_person"])
            task.building.set(form.cleaned_data["building"])

            files_to_delete = self.request.POST.get("delete_attachments", "")
            files_to_delete = [
                int(file_id)
                for file_id in files_to_delete.split(",")
                if file_id.isdigit()
            ]
            if files_to_delete:
                Attachment.objects.filter(id__in=files_to_delete).delete()

            task.save()

            attachments = self.request.FILES.getlist("attachments")
            self.save_attachments(task, attachments)

            AuditEntry.log_action(
                AuditEntry.TASK_UPDATED, self.request, f"id={task.id}, {task.title}"
            )

            self.notify_users(task)
            messages.success(self.request, "Zadanie zaktualizowane pomyślnie.")

            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Zadanie zaktualizowane pomyślnie."}
                )
            return super().form_valid(form)

        except Exception as e:
            AuditEntry.log_action(
                AuditEntry.TASK_UPDATE_FAILED,
                self.request,
                f"{task.title if 'task' in locals() else 'Unknown task'}",
            )
            messages.error(self.request, "Wystąpił błąd. Spróbuj ponownie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": f"Błąd: {str(e)}"})
            raise

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Błąd: Niepoprawne dane.",
                    "errors": form.errors,
                }
            )
        return super().form_invalid(form)

    def save_attachments(self, task, attachments):
        for file in attachments:
            Attachment.objects.create(file=file, task=task)

    def notify_users(self, task):
        assigned_persons = ", ".join(
            [user.full_name for user in task.assigned_person.all()]
        )
        buildings = ", ".join(
            [
                f"{building.name} ({building.address})"
                for building in task.building.all()
            ]
        )

        comments = task.taskcomment_set.all().order_by("-creation_date")
        if comments.exists():
            comments_text = "\n".join(
                [
                    f"- {comment.user.full_name}: {comment.comment_text}"
                    for comment in comments
                ]
            )
        else:
            comments_text = "Brak"

        subject = f"Zmiana zadania: {task.title}"

        message = textwrap.dedent(
            f"""
            Zostało zmienione zadanie:
            
            Nazwa: {task.title}
            Przypisana osoba: {assigned_persons}
            Status: {task.get_status_field_display() if task.status_field else '-'}
            Termin: {task.deadline}
            Kategoria: {task.get_category_display()}
            Priorytet: {task.get_priority_display()}
            Budynek: {buildings}
            Opis: {task.description}
            Komentarze: {comments_text}
        """
        ).strip()

        emails = list(task.assigned_person.values_list("email", flat=True))
        if emails:
            email = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, emails)
            for attachment in task.attachments.all():
                file_path = attachment.file.path
                mime_type, _ = mimetypes.guess_type(file_path)
                with open(file_path, "rb") as file_content:
                    email.attach(
                        attachment.file.name,
                        file_content.read(),
                        mime_type or "application/octet-stream",
                    )
            email.send()
            AuditEntry.log_action(
                AuditEntry.EMAIL_SENT, self.request, f"{subject} -> {emails}"
            )


class TaskEmployeeStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "tasks.employee_task_status_update"

    def get(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs["pk"])
        status = self.kwargs.get("status")

        if status == "none":
            status = None
            Task.objects.filter(pk=task.pk).update(status_field=status)
            task.refresh_from_db()

            AuditEntry.log_action(
                AuditEntry.TASK_UPDATED,
                request,
                f"id={task.id}, {task.title} -> Wykonanie zadania cofnięte.",
            )

            self.notify_manager(task)

            if status is None:
                messages.warning(request, f'Wykonanie "{task.title}" zadania cofnięte.')

        if status is not None:
            task.status_field = status
            task.save()

            AuditEntry.log_action(
                AuditEntry.TASK_UPDATED,
                request,
                f"id={task.id}, {task.title} -> {task.status_field}",
            )

            self.notify_manager(task)

            if status == "confirmed":
                messages.success(
                    request, f'Zadanie "{task.title}" jest oznczone jako wykonane.'
                )

        return HttpResponseRedirect(reverse_lazy("task_list"))

    def notify_manager(self, task):
        manager = task.created_by
        assigned_users = task.assigned_person.all().exclude(id=self.request.user.id)

        emails = [manager.email] if manager and manager.email else []
        emails += [user.email for user in assigned_users if user.email]

        if not emails:
            return
        subject = f"Aktualizacja statusu: {task.title}"

        status_text = (
            "Osoba odpowiedzialna za zadanie oznaczyła je jako wykonano:"
            if task.status_field
            else "Osoba odpowiedzialna za zadanie cofnęła wykonanie zadania!"
        )

        message = textwrap.dedent(
            f"""
            {status_text}
            
            Nazwa: {task.title}
            Przypisana osoba: {", ".join(user.full_name for user in task.assigned_person.all())}
            Status: {task.get_status_field_display() if task.status_field else '-'}
            Termin: {task.deadline}
            Kategoria: {task.get_category_display()}
            Priorytet: {task.get_priority_display()}
            Budynek: {", ".join(f"{b.name} ({b.address})" for b in task.building.all())}
            Opis: {task.description}
            """
        ).strip()

        email_message = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, emails)
        for attachment in task.attachments.all():
            file_path = attachment.file.path
            mime_type, _ = mimetypes.guess_type(file_path)
            with open(file_path, "rb") as file_content:
                email_message.attach(
                    attachment.file.name,
                    file_content.read(),
                    mime_type or "application/octet-stream",
                )
        email_message.send()

        AuditEntry.log_action(
            AuditEntry.EMAIL_SENT, self.request, f"{subject} -> {emails}"
        )


class TaskManagerStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "tasks.change_task"

    def get(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs["pk"])
        status = self.kwargs.get("status")

        if status:
            task.status_field = status
            task.closed_at = datetime.datetime.now()
            task.save()

            AuditEntry.log_action(
                AuditEntry.TASK_UPDATED,
                request,
                f"id={task.id}, {task.title} -> {task.status_field}",
            )
            self.notify_users(task)

            if status == "accepted":
                messages.success(
                    request, f'Wykonanie zadania "{task.title}" potwierdzone.'
                )

        return HttpResponseRedirect(reverse_lazy("task_list"))

    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs["pk"])
        task.status_field = "declined"
        task.save()
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment_text = form.cleaned_data["comment_text"]
            TaskComment.objects.create(
                task=task,
                user=request.user,
                comment_text=comment_text,
            )
            messages.warning(
                request, f'Wykonanie zadania "{task.title}" nie potwierdzone.'
            )
        else:
            messages.error(
                request, "Wystąpił błąd. Proszę wypełnić poprawnie formularz."
            )

        AuditEntry.log_action(
            AuditEntry.TASK_UPDATED,
            request,
            f"id={task.id}, {task.title} -> {task.status_field}",
        )

        self.notify_users(task)

        return HttpResponseRedirect(reverse_lazy("task_list"))

    def notify_users(self, task):
        assigned_persons = ", ".join(
            [user.full_name for user in task.assigned_person.all()]
        )
        buildings = ", ".join(
            [
                f"{building.name} ({building.address})"
                for building in task.building.all()
            ]
        )

        comments = task.taskcomment_set.all().order_by("-creation_date")
        if comments.exists():
            comments_text = "\n".join(
                [
                    f"- {comment.user.full_name}: {comment.comment_text}"
                    for comment in comments
                ]
            )
        else:
            comments_text = "Brak"

        subject = f"Aktualizacja statusu: {task.title}"

        if task.status_field == "accepted":
            status_text = "Wykonanie zadania potwierdzone."
        else:
            status_text = "Wykonanie zadania nie potwierdzone."

        message = textwrap.dedent(
            f"""
            {status_text}
            
            Nazwa: {task.title}
            Przypisana osoba: {assigned_persons}
            Status: {task.get_status_field_display() if task.status_field else '-'}
            Termin: {task.deadline}
            Kategoria: {task.get_category_display()}
            Priorytet: {task.get_priority_display()}
            Budynek: {buildings}
            Opis: {task.description}
            Komentarze: {comments_text}
        """
        ).strip()

        emails = list(task.assigned_person.values_list("email", flat=True))
        if emails:
            email = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, emails)
            for attachment in task.attachments.all():
                file_path = attachment.file.path
                mime_type, _ = mimetypes.guess_type(file_path)
                with open(file_path, "rb") as file_content:
                    email.attach(
                        attachment.file.name,
                        file_content.read(),
                        mime_type or "application/octet-stream",
                    )
            email.send()
            AuditEntry.log_action(
                AuditEntry.EMAIL_SENT, self.request, f"{subject} -> {emails}"
            )


class TaskDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "tasks.delete_task"

    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs.get("pk"))
        task_id = task.id
        task_title = task.title
        assigned_emails = list(task.assigned_person.values_list("email", flat=True))

        try:
            task.delete()
            AuditEntry.log_action(
                AuditEntry.TASK_DELETED, self.request, f"id={task_id}, {task_title}"
            )
            self.notify_users(task_title, assigned_emails)
            messages.success(request, "Zadanie usunięte pomyślnie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Zadanie usunięte pomyślnie."},
                    status=200,
                )
            return redirect("task_list")

        except Exception as e:
            AuditEntry.log_action(
                AuditEntry.TASK_DELETE_FAILED, self.request, f"{task_title}"
            )
            messages.error(request, "Wystąpił błąd. Spróbuj ponownie.")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": f"Błąd: {str(e)}"}, status=400
                )
            return redirect("task_list")

    def notify_users(self, task_title, assigned_emails):
        subject = f"Usunięcie zadania: {task_title}"
        message = textwrap.dedent(
            f"""
            Zadanie {task_title} zostało usunięte.
        """
        ).strip()

        if assigned_emails:
            email = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, assigned_emails)
            email.send()
            AuditEntry.log_action(
                AuditEntry.EMAIL_SENT, self.request, f"{subject} -> {assigned_emails}"
            )


class TaskLeaveComment(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "tasks.leave_comment"

    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs["pk"])
        form = TaskCommentForm(request.POST)

        if form.is_valid():
            comment = TaskComment.objects.create(
                task=task,
                user=request.user,
                comment_text=form.cleaned_data["comment_text"],
            )
            AuditEntry.log_action(
                AuditEntry.TASK_COMMENT_CREATED,
                request,
                f"id={task.id}, {task.title} -> {comment.comment_text}",
            )

            self.notify_users(task)

            return JsonResponse(
                {
                    "success": True,
                    "message": "Komentarz został pomyślnie utworzony.",
                    "comment": {
                        "user": request.user.full_name,
                        "text": comment.comment_text,
                        "date": comment.creation_date.strftime("%Y-%m-%d %H:%M"),
                    },
                }
            )

        return JsonResponse({"success": False, "errors": form.errors})

    def notify_users(self, task):
        assigned_persons = set(task.assigned_person.all())
        created_by = task.created_by
        comment_author = self.request.user

        recipients = set()
        if created_by and created_by.email:
            recipients.add(created_by)
        recipients.update(assigned_persons)

        recipients.discard(comment_author)

        emails = [user.email for user in recipients if user.email]

        if not emails:
            return

        assigned_persons_str = ", ".join(user.full_name for user in assigned_persons)
        buildings = ", ".join(f"{b.name} ({b.address})" for b in task.building.all())

        comments = task.taskcomment_set.all().order_by("-creation_date")
        if comments.exists():
            comments_text = "\n".join(
                f"- {c.user.full_name}: {c.comment_text}" for c in comments
            )
        else:
            comments_text = "Brak"

        subject = f"Dodanie komentarza do zadania: {task.title}"
        message = textwrap.dedent(
            f"""
            Użytkownik {comment_author.full_name} dodał komentarz do zadania:
            
            Nazwa: {task.title}
            Przypisane osoby: {assigned_persons_str}
            Status: {task.get_status_field_display() if task.status_field else '-'}
            Termin: {task.deadline}
            Kategoria: {task.get_category_display()}
            Priorytet: {task.get_priority_display()}
            Budynek: {buildings}
            Opis: {task.description}
            Komentarze: {comments_text}
        """.strip()
        )

        email = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, emails)

        for attachment in task.attachments.all():
            file_path = attachment.file.path
            mime_type, _ = mimetypes.guess_type(file_path)
            with open(file_path, "rb") as file_content:
                email.attach(
                    attachment.file.name,
                    file_content.read(),
                    mime_type or "application/octet-stream",
                )
        email.send()

        AuditEntry.log_action(
            AuditEntry.EMAIL_SENT, self.request, f"{subject} -> {emails}"
        )


def serve_attachment(request, file_path):
    """
    Allows to attach files from media folder in templates.
    """
    file_full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    if not os.path.exists(file_full_path):
        raise Http404("File not found")

    try:
        file = open(file_full_path, "rb")
        return FileResponse(file, as_attachment=False)
    except IOError:
        raise Http404("Error opening file")
