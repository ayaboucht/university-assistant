"""Page de chat de l'assistant."""

import streamlit as st

from src.ui.components import render_hero
from src.ui.session import KEY_MESSAGES, KEY_PENDING

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
MOCK_ANSWER = "Réponse fictive : le moteur RAG n'est pas encore connecté."
SUGGESTIONS = (
    "Quelles sont les règles concernant les absences ?",
    "Comment demander une attestation de scolarité ?",
    "Comment fonctionne la validation d'un module ?",
)


def add_message(role: str, content: str) -> None:
    """Ajoute un message à la conversation et l'affiche."""
    st.session_state[KEY_MESSAGES].append({"role": role, "content": content})
    with st.chat_message(role):
        st.write(content)


def render_history() -> None:
    """Affiche les messages déjà échangés."""
    for message in st.session_state[KEY_MESSAGES]:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def render_welcome() -> None:
    """Affiche l'écran d'accueil avec les questions suggérées."""
    render_hero(
        "Bonjour, comment puis-je t'aider ?",
        "Pose une question ou choisis une suggestion.",
    )
    for index, question in enumerate(SUGGESTIONS):
        if st.button(question, key=f"suggestion_{index}", width="stretch"):
            st.session_state[KEY_PENDING] = question
            st.rerun()


def main() -> None:
    """Affiche le chat (réponses fictives en attendant le backend)."""
    st.session_state.setdefault(KEY_MESSAGES, [])

    typed = st.chat_input("Pose ta question sur la vie universitaire")
    prompt = typed or st.session_state.pop(KEY_PENDING, None)

    if not st.session_state[KEY_MESSAGES] and not prompt:
        render_welcome()
        return

    render_history()
    if prompt:
        add_message(ROLE_USER, prompt)
        add_message(ROLE_ASSISTANT, MOCK_ANSWER)


main()
