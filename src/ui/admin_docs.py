import streamlit as st

st.title("Gestion des documents")

if st.session_state.get("role") != "admin":
    st.error("Accès réservé aux administrateurs.")
    st.stop()

if "documents" not in st.session_state:
    st.session_state["documents"] = [
        {"Nom": "reglement_interieur.pdf", "Type": "PDF", "Statut": "Indexé"},
        {"Nom": "guide_pedagogique.pdf", "Type": "PDF", "Statut": "En cours"},
    ]

uploaded_files = st.file_uploader(
    "Importer des documents (PDF ou TXT)",
    type=["pdf", "txt"],
    accept_multiple_files=True,
)

if uploaded_files and st.button("Envoyer"):
    known_names = {doc["Nom"] for doc in st.session_state["documents"]}
    added = 0
    for file in uploaded_files:
        if file.name not in known_names:
            st.session_state["documents"].append(
                {
                    "Nom": file.name,
                    "Type": file.name.split(".")[-1].upper(),
                    "Statut": "En attente",
                }
            )
            added += 1
    st.success(f"{added} document(s) ajouté(s) (simulation, rien n'est envoyé au backend).")

st.subheader("Documents du corpus")
st.dataframe(st.session_state["documents"])