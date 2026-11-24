"""Gestion de la session utilisateur dans Streamlit."""

import streamlit as st

KEY_TOKEN = "token"
KEY_EMAIL = "email"
KEY_ROLE = "role"
KEY_MESSAGES = "messages"
KEY_DOCUMENTS = "documents"
KEY_PENDING = "pending"

ROLE_ADMIN = "admin"
ROLE_STUDENT = "student"

ROLE_LABELS = {
    ROLE_ADMIN: "Administrateur",
    ROLE_STUDENT: "Étudiant",
}

_SESSION_KEYS = (
    KEY_TOKEN,
    KEY_EMAIL,
    KEY_ROLE,
    KEY_MESSAGES,
    KEY_DOCUMENTS,
    KEY_PENDING,
)


def is_authenticated() -> bool:
    """Indique si un utilisateur est connecté."""
    return KEY_TOKEN in st.session_state


def is_admin() -> bool:
    """Indique si l'utilisateur connecté a le rôle administrateur."""
    return st.session_state.get(KEY_ROLE) == ROLE_ADMIN


def start_session(token: str, email: str, role: str) -> None:
    """Enregistre les informations de l'utilisateur connecté."""
    st.session_state[KEY_TOKEN] = token
    st.session_state[KEY_EMAIL] = email
    st.session_state[KEY_ROLE] = role


def clear_session() -> None:
    """Supprime toutes les données de session de l'utilisateur."""
    for key in _SESSION_KEYS:
        st.session_state.pop(key, None)
