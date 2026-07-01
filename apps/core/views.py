from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "core/home.html")


def htmx_ping(request: HttpRequest) -> HttpResponse:
    if request.htmx:
        return render(request, "core/_pong.html")
    return HttpResponse("HTMX request expected", status=400)
