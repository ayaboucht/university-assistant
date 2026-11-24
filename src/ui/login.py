"""Page de connexion."""

from pathlib import Path

import streamlit as st

from src.ui.components import apply_background, render_hero
from src.ui.session import ROLE_ADMIN, ROLE_STUDENT, start_session

BACKGROUND_FILE = Path("assets/login_bg.png")
LOGIN_CARD_KEY = "login_card"
DEV_TOKEN = "dev-token"
DEV_STUDENT_EMAIL = "etudiant@emsi-edu.ma"
DEV_ADMIN_EMAIL = "admin@emsi-edu.ma"


def dev_login(email: str, role: str) -> None:
    """Connexion de test sans backend (mode développement uniquement)."""
    start_session(DEV_TOKEN, email, role)
    st.rerun()


def main() -> None:
    """Affiche la carte de connexion sur la photo de l'école."""
    apply_background(BACKGROUND_FILE)
    _, center, _ = st.columns([1, 2, 1])
    with center, st.container(key=LOGIN_CARD_KEY):
        render_hero(
            "Assistant EMSI",
            "Ton assistant pour la vie universitaire : règlements, "
            "démarches et organisation.",
        )
        st.button(
            "Se connecter avec Microsoft",
            type="primary",
            width="stretch",
            disabled=True,
        )
        st.caption("Connexion Microsoft bientôt disponible.")
        with st.expander("Mode développement"):
            if st.button("Entrer comme étudiant", width="stretch"):
                dev_login(DEV_STUDENT_EMAIL, ROLE_STUDENT)
            if st.button("Entrer comme admin", width="stretch"):
                dev_login(DEV_ADMIN_EMAIL, ROLE_ADMIN)


main()
