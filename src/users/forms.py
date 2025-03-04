from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

from users.models import CmmsUser


class CmmsUserCreationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        random_generated_password = CmmsUser.objects.make_random_password()
        self.fields["password1"].default = random_generated_password
        self.fields["password1"].required = False
        self.fields["password2"].default = random_generated_password
        self.fields["password2"].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = self.cleaned_data["password1"]
        if commit:
            user.save()
        return user

    class Meta:
        model = CmmsUser
        fields = ("email", "first_name", "last_name")


class CmmsUserChangeForm(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    class Meta:
        model = CmmsUser
        fields = ("email", "first_name", "last_name")


class FirstLoginPasswordChangeForm(PasswordChangeForm):
    old_password = None

    class Meta:
        fields = ["password1", "password2"]
