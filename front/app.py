import streamlit as st

from front.api_client import ErreurApi, se_connecter

st.set_page_config(page_title="VéloVille", page_icon="🚲", layout="wide")
st.title("VéloVille — Plateforme de restitution")

if st.session_state.get("access_token"):
    st.success(
        f"Connecté en tant que {st.session_state.get('username')} "
        f"(rôle : {st.session_state.get('role')})."
    )
    st.write("Utilisez le menu latéral pour accéder aux écrans.")
    if st.button("Se déconnecter"):
        for cle in ("access_token", "role", "username"):
            st.session_state.pop(cle, None)
        st.rerun()
else:
    st.subheader("Connexion")
    with st.form("formulaire_connexion"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        soumettre = st.form_submit_button("Se connecter")
    if soumettre:
        try:
            reponse = se_connecter(username, password)
            st.session_state["access_token"] = reponse["access_token"]
            st.session_state["role"] = reponse["role"]
            st.session_state["username"] = username
            st.success(
                f"Connecté en tant que {username} (rôle : {reponse['role']})."
            )
            st.rerun()
        except ErreurApi as erreur:
            st.error(str(erreur))
