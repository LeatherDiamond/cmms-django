from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailFirstAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()

        if "@" not in username:
            username, domain = username, "dacpol.eu"
        else:
            username, domain = username.split("@")

        if "." not in username:
            username = username[0] + "." + username[1:]

        try:
            user = User.objects.get(email__iexact=username + "@" + domain)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None
