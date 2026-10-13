import streamlit as st


def garder_session() -> bool:
    jeton = st.session_state.get("access_token")
    if not jeton:
        st.info("Veuillez vous connecter.")
        st.page_link("app.py", label="Aller à la page de connexion")
        return False
    with st.sidebar:
        st.write(f"Connecté : {st.session_state.get('username', '')}")
        st.write(f"Rôle : {st.session_state.get('role', '')}")
        if st.button("Se déconnecter", key="deconnexion"):
            for cle in ("access_token", "role", "username"):
                st.session_state.pop(cle, None)
            st.switch_page("app.py")
    return True


def montrer_lignes_vides(total: int) -> bool:
    if total == 0:
        st.info("Aucun résultat pour ces critères.")
        return True
    return False
