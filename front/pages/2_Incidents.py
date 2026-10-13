import streamlit as st

from front.api_client import ErreurApi, changer_statut, lire_incidents
from front.ui import garder_session

st.title("Incidents")
if garder_session():
    jeton = st.session_state["access_token"]
    role = st.session_state["role"]
    col_statut, col_taille, col_page = st.columns(3)
    statut = col_statut.selectbox("Statut", ["Tous", "ouvert", "en_cours", "resolu"])
    taille_page = col_taille.selectbox("Taille de page", [10, 20, 50], index=1)
    page = col_page.number_input("Page", min_value=1, step=1, value=1)
    try:
        with st.spinner("Chargement..."):
            resultat = lire_incidents(jeton, statut, int(page), taille_page)
        st.caption(f"{resultat['total']} incidents au total")
        lignes = resultat["resultats"]
        if not lignes:
            st.info("Aucun résultat pour ces critères.")
        else:
            st.dataframe(
                [
                    {
                        "Identifiant": ligne["incident_id"],
                        "Signalé le": ligne["date_signalement"],
                        "Cible": ligne["cible"],
                        "Vélo": ligne["velo_id"],
                        "Station": ligne["station_id"],
                        "Type": ligne["type_incident"],
                        "Statut": ligne["statut"],
                        "Résolu le": ligne["date_resolution"],
                        "Technicien": ligne["technicien"],
                    }
                    for ligne in lignes
                ],
                use_container_width=True,
                hide_index=True,
            )
        if role == "exploitant":
            st.subheader("Changer le statut d'un incident")
            if lignes:
                with st.form("formulaire_statut"):
                    incidents = {
                        f"{ligne['incident_id']} — {ligne['statut']}": ligne["incident_id"]
                        for ligne in lignes
                    }
                    choix = st.selectbox("Incident", list(incidents))
                    nouveau_statut = st.selectbox(
                        "Nouveau statut", ["en_cours", "resolu"]
                    )
                    appliquer = st.form_submit_button("Appliquer")
                if appliquer:
                    try:
                        mise_a_jour = changer_statut(
                            jeton, incidents[choix], nouveau_statut
                        )
                        st.success(
                            f"Statut de l'incident {mise_a_jour['incident_id']} "
                            f"mis à jour : {mise_a_jour['statut']}."
                        )
                        st.rerun()
                    except ErreurApi as erreur:
                        st.error(str(erreur))
        else:
            st.info("La modification des incidents est réservée aux exploitants.")
    except ErreurApi as erreur:
        st.error(str(erreur))
