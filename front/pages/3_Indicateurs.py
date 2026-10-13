from datetime import date

import streamlit as st

from front.api_client import (
    ErreurApi,
    lire_activite,
    lire_incidents_par_statut,
    lire_stations_actives,
)
from front.ui import garder_session

st.title("Indicateurs")
if garder_session():
    col_debut, col_fin, col_limite = st.columns(3)
    date_debut = col_debut.date_input(
        "Date de début", value=date(2026, 8, 24), key="date_debut"
    )
    date_fin = col_fin.date_input(
        "Date de fin", value=date(2026, 8, 30), key="date_fin"
    )
    limite = col_limite.number_input(
        "Nombre de stations", min_value=1, max_value=50, value=10
    )
    if date_debut > date_fin:
        st.error("La date de début doit précéder la date de fin.")
    else:
        try:
            jeton = st.session_state["access_token"]
            debut, fin = date_debut.isoformat(), date_fin.isoformat()
            with st.spinner("Chargement..."):
                activite = lire_activite(jeton, debut, fin)["donnees"]
                stations = lire_stations_actives(jeton, int(limite))["donnees"]
                incidents = lire_incidents_par_statut(jeton)
            trajets = sum(ligne["nb_trajets"] for ligne in activite)
            col_trajets, col_stations, col_delai = st.columns(3)
            col_trajets.metric("Trajets sur la période", trajets)
            col_stations.metric("Stations actives", len(stations))
            delai = incidents["delai_moyen_resolution_heures"]
            col_delai.metric(
                "Délai moyen de résolution (h)",
                f"{delai:.1f}" if delai is not None else "n. d.",
            )
            st.subheader("Activité par jour")
            if activite:
                st.dataframe(
                    [
                        {"Jour": ligne["jour"], "Nombre de trajets": ligne["nb_trajets"]}
                        for ligne in activite
                    ],
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("Aucun résultat pour ces critères.")
            st.subheader("Stations les plus actives")
            st.dataframe(
                [
                    {
                        "Identifiant": ligne["station_id"],
                        "Nom": ligne["nom"],
                        "Départs": ligne["nb_departs"],
                        "Arrivées": ligne["nb_arrivees"],
                        "Total": ligne["nb_departs"] + ligne["nb_arrivees"],
                    }
                    for ligne in stations
                ],
                width="stretch",
                hide_index=True,
            )
            st.subheader("Incidents par statut")
            st.dataframe(
                [
                    {"Statut": ligne["statut"], "Nombre d'incidents": ligne["nb_incidents"]}
                    for ligne in incidents["donnees"]
                ],
                width="stretch",
                hide_index=True,
            )
        except ErreurApi as erreur:
            st.error(str(erreur))
