import pytest

from front import api_client


@pytest.mark.parametrize(
    ("status_code", "path", "detail", "expected"),
    [
        (404, "/stations/S999", "Station introuvable", "Station introuvable."),
        (404, "/incidents/I999", "Incident introuvable", "Incident introuvable."),
        (
            422,
            "/incidents/I001/statut",
            "Transition de statut non autorisee",
            "Cette transition de statut n'est pas autorisée.",
        ),
        (
            422,
            "/trajets",
            [{"loc": ["query", "page"], "msg": "Input should be greater than 0"}],
            "Les critères ou la transition demandés ne sont pas valides.",
        ),
    ],
)
def test_erreurs_404_422_sont_traduites_en_messages_utilisateur(
    monkeypatch, status_code, path, detail, expected
):
    class Reponse:
        ok = False

        def __init__(self):
            self.status_code = status_code

        def json(self):
            return {"detail": detail}

    monkeypatch.setattr(api_client.requests, "request", lambda *args, **kwargs: Reponse())

    with pytest.raises(api_client.ErreurApi) as erreur:
        api_client._requete("GET", path, "test-token")

    assert erreur.value.statut == status_code
    assert str(erreur.value) == expected
