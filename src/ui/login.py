import streamlit as st


def dev_login(email: str, role: str):
    st.session_state["token"] = "dev-token"
    st.session_state["email"] = email
    st.session_state["role"] = role
    st.rerun()


st.title("Assistant intelligent EMSI")
st.write("Connecte-toi avec ton compte académique.")

st.link_button(
    "Se connecter avec Microsoft",
    "https://login.microsoftonline.com",
    disabled=True,
)
st.caption("La connexion Microsoft sera activée quand le backend sera prêt.")

st.divider()
st.subheader("Mode développement")
col1, col2 = st.columns(2)
if col1.button("Entrer comme étudiant"):
    dev_login("etudiant@emsi-edu.ma", "student")
if col2.button("Entrer comme admin"):
    dev_login("admin@emsi-edu.ma", "admin")