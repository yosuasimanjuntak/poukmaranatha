from django.test import Client
from django.urls import reverse


def test_home_returns_200(db, client: Client) -> None:
    response = client.get(reverse("core:home"))
    assert response.status_code == 200


def test_htmx_ping_requires_htmx_header(client: Client) -> None:
    response = client.get(reverse("core:htmx_ping"))
    assert response.status_code == 400


def test_htmx_ping_renders_partial_with_htmx_header(client: Client) -> None:
    response = client.get(reverse("core:htmx_ping"), headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert b"pong" in response.content
