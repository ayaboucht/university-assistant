"""Point d'entrée de l'application Streamlit."""

from pathlib import Path

import streamlit as st

from src.ui.components import render_user_card
from src.ui.session import (
    KEY_EMAIL,
    KEY_ROLE,
    ROLE_LABELS,
    clear_session,
    is_admin,
    is_authenticated,
)

ASSETS_DIR = Path("assets")
STYLE_FILE = ASSETS_DIR / "style.css"
LOGO_FILE = ASSETS_DIR / "emsi_logo.png"
SIDEBAR_USER_KEY = "sidebar_user"


def apply_branding() -> None:
    """Applique la feuille de style et le logo EMSI s'ils existent."""
    if STYLE_FILE.exists():
        css = STYLE_FILE.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    if LOGO_FILE.exists():
        st.logo(str(LOGO_FILE), size="large")


def build_pages() -> list[st.Page]:
    """Retourne les pages autorisées selon la connexion et le rôle."""
    if not is_authenticated():
        return [
            st.Page(
                "src/ui/login.py",
                title="Connexion",
                icon=":material/login:",
            )
        ]

    pages = [
        st.Page(
            "src/ui/chat.py",
            title="Assistant",
            icon=":material/chat:",
        )
    ]
    if is_admin():
        pages.append(
            st.Page(
                "src/ui/admin_docs.py",
                title="Documents",
                icon=":material/folder:",
            )
        )
    return pages


def render_sidebar() -> None:
    """Affiche la carte utilisateur et la déconnexion en bas de la sidebar."""
    role = st.session_state[KEY_ROLE]
    with st.sidebar.container(key=SIDEBAR_USER_KEY):
        render_user_card(st.session_state[KEY_EMAIL], ROLE_LABELS.get(role, role))
        if st.button(
            "Se déconnecter",
            key="logout",
            icon=":material/logout:",
            width="stretch",
        ):
            clear_session()
            st.rerun()


def main() -> None:
    """Configure la page puis lance la navigation."""
    st.set_page_config(
        page_title="Assistant EMSI",
        page_icon=":material/school:",
        layout="wide",
    )
    apply_branding()
    pages = build_pages()
    if is_authenticated():
        render_sidebar()
    st.navigation(pages).run()


main()
