"""Page d'administration des documents (réservée aux administrateurs)."""

from pathlib import Path

import streamlit as st

from src.ui.session import KEY_DOCUMENTS, is_admin

COL_NAME = "Nom"
COL_TYPE = "Type"
COL_STATUS = "Statut"
STATUS_PENDING = "En attente"

INITIAL_DOCUMENTS = (
    {COL_NAME: "reglement_interieur.pdf", COL_TYPE: "PDF", COL_STATUS: "Indexé"},
    {COL_NAME: "guide_pedagogique.pdf", COL_TYPE: "PDF", COL_STATUS: "En cours"},
)


def init_documents() -> None:
    """Initialise la liste fictive de documents."""
    if KEY_DOCUMENTS not in st.session_state:
        st.session_state[KEY_DOCUMENTS] = [dict(doc) for doc in INITIAL_DOCUMENTS]


def add_documents(uploaded_files) -> int:
    """Ajoute les fichiers inconnus à la liste et retourne leur nombre."""
    documents = st.session_state[KEY_DOCUMENTS]
    known_names = {doc[COL_NAME] for doc in documents}
    added = 0
    for file in uploaded_files:
        if file.name in known_names:
            continue
        documents.append(
            {
                COL_NAME: file.name,
                COL_TYPE: Path(file.name).suffix.lstrip(".").upper(),
                COL_STATUS: STATUS_PENDING,
            }
        )
        known_names.add(file.name)
        added += 1
    return added


def main() -> None:
    """Affiche la gestion des documents (simulation sans backend)."""
    st.title("Gestion des documents")

    if not is_admin():
        st.error("Accès réservé aux administrateurs.")
        st.stop()

    init_documents()

    uploaded_files = st.file_uploader(
        "Importer des documents (PDF ou TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )
    if uploaded_files and st.button("Envoyer"):
        added = add_documents(uploaded_files)
        st.success(
            f"{added} document(s) ajouté(s) (simulation, rien n'est envoyé au backend)."
        )

    st.subheader("Documents du corpus")
    st.dataframe(st.session_state[KEY_DOCUMENTS])


main()
