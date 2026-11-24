"""Page de chat de l'assistant."""

import time
from collections.abc import Iterator, Sequence

import streamlit as st

from src.ui.components import render_hero
from src.ui.session import KEY_MESSAGES, KEY_PENDING

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
AVATARS = {
    ROLE_USER: ":material/person:",
    ROLE_ASSISTANT: ":material/school:",
}

STREAM_DELAY_SECONDS = 0.03
THINKING_DELAY_SECONDS = 0.6

MOCK_ANSWER = (
    "Réponse fictive : le moteur RAG n'est pas encore connecté. "
    "Quand il le sera, la réponse s'appuiera sur les documents officiels "
    "et citera ses sources."
)
MOCK_SOURCES = (
    {
        "document": "reglement_interieur.pdf",
        "page": 12,
        "excerpt": "Extrait fictif du document utilisé pour répondre.",
    },
)
SUGGESTIONS = (
    (":material/event_busy:", "Quelles sont les règles concernant les absences ?"),
    (":material/description:", "Comment demander une attestation de scolarité ?"),
    (":material/school:", "Comment fonctionne la validation d'un module ?"),
)
DISCLAIMER = (
    "L'assistant peut se tromper. "
    "Vérifie les informations importantes dans les documents officiels."
)


def stream_text(text: str) -> Iterator[str]:
    """Simule une réponse qui s'écrit progressivement."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(STREAM_DELAY_SECONDS)


def render_sources(sources: Sequence[dict]) -> None:
    """Affiche les sources d'une réponse dans un bloc repliable."""
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})", icon=":material/description:"):
        for source in sources:
            st.markdown(f"**{source['document']}**, page {source['page']}")
            st.caption(source["excerpt"])


def render_message(role: str, content: str, sources: Sequence[dict] = ()) -> None:
    """Affiche un message avec son avatar et ses sources éventuelles."""
    with st.chat_message(role, avatar=AVATARS[role]):
        st.write(content)
        render_sources(sources)


def render_history() -> None:
    """Affiche les messages déjà échangés."""
    for message in st.session_state[KEY_MESSAGES]:
        render_message(
            message["role"],
            message["content"],
            message.get("sources", ()),
        )


def add_user_message(content: str) -> None:
    """Enregistre et affiche la question de l'utilisateur."""
    st.session_state[KEY_MESSAGES].append({"role": ROLE_USER, "content": content})
    render_message(ROLE_USER, content)


def answer_question() -> None:
    """Affiche une réponse fictive avec ses sources (en attendant le backend)."""
    with st.chat_message(ROLE_ASSISTANT, avatar=AVATARS[ROLE_ASSISTANT]):
        with st.spinner("Recherche dans les documents..."):
            time.sleep(THINKING_DELAY_SECONDS)
        content = st.write_stream(stream_text(MOCK_ANSWER))
        render_sources(MOCK_SOURCES)
    st.session_state[KEY_MESSAGES].append(
        {
            "role": ROLE_ASSISTANT,
            "content": content,
            "sources": list(MOCK_SOURCES),
        }
    )


def render_welcome() -> None:
    """Affiche l'écran d'accueil avec les questions suggérées."""
    render_hero(
        "Bonjour, comment puis-je t'aider ?",
        "Pose une question ou choisis une suggestion.",
    )
    for index, (icon, question) in enumerate(SUGGESTIONS):
        if st.button(question, key=f"suggestion_{index}", icon=icon, width="stretch"):
            st.session_state[KEY_PENDING] = question
            st.rerun()


def main() -> None:
    """Affiche le chat (réponses fictives en attendant le backend)."""
    st.session_state.setdefault(KEY_MESSAGES, [])

    typed = st.chat_input("Pose ta question sur la vie universitaire")
    prompt = typed or st.session_state.pop(KEY_PENDING, None)

    if not st.session_state[KEY_MESSAGES] and not prompt:
        render_welcome()
    else:
        render_history()
        if prompt:
            add_user_message(prompt)
            answer_question()
    st.caption(DISCLAIMER)


main()
