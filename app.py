"""Point d'entrée de l'application Streamlit."""

from pathlib import Path

import streamlit as st

from src.ui.session import (
    KEY_EMAIL,
    KEY_ROLE,
    clear_session,
    is_admin,
    is_authenticated,
)

ASSETS_DIR = Path("assets")
STYLE_FILE = ASSETS_DIR / "style.css"
LOGO_FILE = ASSETS_DIR / "emsi_logo.png"


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
    """Affiche l'utilisateur connecté et le bouton de déconnexion."""
    with st.sidebar:
        st.text(st.session_state[KEY_EMAIL])
        st.caption(f"Rôle : {st.session_state[KEY_ROLE]}")
        if st.button("Se déconnecter"):
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
