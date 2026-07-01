from django.utils import translation


class UserLanguageMiddleware:
    """Override the active language to the authenticated user's preference.

    Runs after LocaleMiddleware so we can override the language Django
    already chose from session/Accept-Language. Only fires when the user
    is logged in and has a `language` field on their profile.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        lang = getattr(user, "language", None) if user and user.is_authenticated else None
        if lang:
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        try:
            return self.get_response(request)
        finally:
            if lang:
                translation.deactivate()
