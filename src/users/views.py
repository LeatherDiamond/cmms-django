from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from users.forms import FirstLoginPasswordChangeForm
from users.models import AuditEntry


class LoginView(LoginView):

    def form_valid(self, form):
        form.cleaned_data["username"] = form.cleaned_data["username"].split("@")[0]
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.user.first_login:
            AuditEntry.log_action(AuditEntry.USER_FIRST_LOGIN, self.request)
            return reverse("first_login_password_change")
        else:
            return super(LoginView, self).get_success_url()

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("index"))
        else:
            return super(LoginView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request.session.set_expiry(3600 * 8)
        return super().post(request, args, kwargs)


class LogoutView(LogoutView):
    next_page = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        """
        Delete 'user' cookie used in communication with declarations app.
        """
        response = super().dispatch(request, *args, **kwargs)
        response.delete_cookie("user")

        return response


class CmmstPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("password_change_done")

    def post(self, request, *args, **kwargs):
        request.user.first_login = False
        request.user.save(update_fields=["first_login"])
        return super().post(request, args, kwargs)


class CmmstPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"

    def post(self, request, *args, **kwargs):
        AuditEntry.log_action(AuditEntry.PASSWORD_CHANGE_REQUESTED, request)
        return super().post(request, *args, **kwargs)


class FirstLoginPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/first_login_password_change.html"
    form_class = FirstLoginPasswordChangeForm
    success_url = reverse_lazy("password_change_done")

    def get(self, request):
        user = request.user
        user.first_login = False
        user.save()
        return super(FirstLoginPasswordChangeView, self).get(request)


class PasswordResetView(PasswordResetView):
    html_email_template_name = "registration/password_reset_email.html"

    def post(self, request):
        AuditEntry.log_action(
            AuditEntry.PASSWORD_RESET_REQUESTED,
            request,
            f'for: {request.POST.get("email")}',
        )
        return super().post(request)
