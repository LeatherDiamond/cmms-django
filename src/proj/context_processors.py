from proj.settings import ADMINS, DEFAULT_DOMAIN


def admin_emails(request):
    return {"admin_emails": [admin[1] for admin in ADMINS]}


def default_domain(request):
    return {"default_domain": DEFAULT_DOMAIN}
