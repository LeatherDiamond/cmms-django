def admin_emails(settings):
    return {"admin_emails": [email for _, email in settings.ADMINS]}


def default_domain(settings):
    return {"default_domain": getattr(settings, "DEFAULT_DOMAIN", "")}
