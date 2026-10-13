def test_sante(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_connexion_reussie_et_refusee(client):
    valide = client.post(
        "/auth/login",
        json={"username": "exploitant01", "password": "Formation2026!"},
    )
    mdp_invalide = client.post(
        "/auth/login",
        json={"username": "exploitant01", "password": "mauvais"},
    )
    utilisateur_inconnu = client.post(
        "/auth/login", json={"username": "inconnu", "password": "Formation2026!"}
    )
    assert valide.status_code == 200
    assert valide.json()["role"] == "exploitant"
    assert valide.json()["token_type"] == "bearer"
    assert mdp_invalide.status_code == utilisateur_inconnu.status_code == 401
    assert mdp_invalide.json() == utilisateur_inconnu.json() == {
        "detail": "Identifiants invalides"
    }


def test_ressource_protegee_sans_jeton_refusee(client):
    assert client.get("/stations").status_code == 401


def test_jeton_modifie_est_refuse(client, jetons):
    jeton = jetons["direction01"]
    dernier = "a" if jeton[-1] != "a" else "b"
    entetes = {"Authorization": f"Bearer {jeton[:-1]}{dernier}"}
    assert client.get("/stations", headers=entetes).status_code == 401


def test_direction_ne_peut_pas_modifier_un_incident(client, jetons):
    reponse = client.put(
        "/incidents/I2026-0001/statut",
        headers={"Authorization": f"Bearer {jetons['direction01']}"},
        json={"statut": "en_cours"},
    )
    assert reponse.status_code == 403
    assert reponse.json() == {"detail": "Acces reserve au role exploitant"}


def test_exploitant_peut_modifier_et_transition_invalide_renvoie_422(client, jetons):
    entetes = {"Authorization": f"Bearer {jetons['exploitant01']}"}
    succes = client.put(
        "/incidents/I2026-0001/statut",
        headers=entetes,
        json={"statut": "en_cours"},
    )
    seconde_transition = client.put(
        "/incidents/I2026-0001/statut",
        headers=entetes,
        json={"statut": "en_cours"},
    )
    assert succes.status_code == 200
    assert succes.json()["statut"] == "en_cours"
    assert seconde_transition.status_code == 422
    assert seconde_transition.json() == {
        "detail": "Transition de statut non autorisee"
    }


def test_pagination_filtre_et_bornes(client, jetons):
    entetes = {"Authorization": f"Bearer {jetons['direction01']}"}
    resultat = client.get(
        "/stations?commune=Lille&page=1&taille_page=2", headers=entetes
    )
    hors_limite = client.get("/stations?page=0", headers=entetes)
    taille_invalide = client.get("/stations?taille_page=101", headers=entetes)
    assert resultat.status_code == 200
    assert resultat.json()["total"] == 3
    assert len(resultat.json()["resultats"]) == 2
    assert hors_limite.status_code == 422
    assert taille_invalide.status_code == 422


def test_station_introuvable(client, jetons):
    entetes = {"Authorization": f"Bearer {jetons['direction01']}"}
    reponse = client.get("/stations/S999", headers=entetes)
    assert reponse.status_code == 404
    assert reponse.json() == {"detail": "Station introuvable"}


def test_indicateur_activite_coherent_avec_liste(client, jetons):
    entetes = {"Authorization": f"Bearer {jetons['direction01']}"}
    activite = client.get(
        "/indicateurs/activite-par-jour?date_debut=2026-08-24&date_fin=2026-08-25",
        headers=entetes,
    ).json()["donnees"]
    trajets = client.get(
        "/trajets?date_debut=2026-08-24&date_fin=2026-08-25",
        headers=entetes,
    ).json()["total"]
    assert sum(ligne["nb_trajets"] for ligne in activite) == trajets == 3
