import streamlit as st

from front.api_client import ErreurApi, lire_stations
from front.ui import garder_session, montrer_lignes_vides


@st.cache_data(ttl=3600)
def charger_communes(jeton: str) -> list[str]:
    communes: set[str] = set()
    page = 1
    while True:
        resultat = lire_stations(jeton, page=page, taille_page=100)
        communes.update(ligne["commune"] for ligne in resultat["resultats"])
        if page * resultat["taille_page"] >= resultat["total"]:
            break
        page += 1
    return sorted(communes)


st.title("Stations")
if garder_session():
    jeton = st.session_state["access_token"]
    try:
        communes = ["Toutes", *charger_communes(jeton)]
        col_commune, col_taille, col_page = st.columns(3)
        commune = col_commune.selectbox("Commune", communes)
        taille_page = col_taille.selectbox("Taille de page", [10, 20, 50], index=1)
        page = col_page.number_input("Page", min_value=1, step=1, value=1)
        with st.spinner("Chargement..."):
            resultat = lire_stations(jeton, commune, int(page), taille_page)
        nombre_pages = max(1, (resultat["total"] + taille_page - 1) // taille_page)
        st.caption(f"{resultat['total']} stations au total — page {page} sur {nombre_pages}")
        if not montrer_lignes_vides(resultat["total"] if page == 1 else len(resultat["resultats"])):
            lignes = resultat["resultats"]
            if lignes:
                st.dataframe(
                    [
                        {
                            "Identifiant": ligne["station_id"],
                            "Nom": ligne["nom"],
                            "Commune": ligne["commune"],
                            "Capacité": ligne["capacite"],
                            "Mise en service": ligne["date_mise_en_service"],
                        }
                        for ligne in lignes
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Aucun résultat pour ces critères.")
    except ErreurApi as erreur:
        st.error(str(erreur))
