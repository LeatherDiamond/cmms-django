from django.urls import reverse


def test_urls(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
