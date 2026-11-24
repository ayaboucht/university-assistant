import streamlit as st

st.set_page_config(page_title="Assistant EMSI", layout="wide")


def logout():
    for key in ("token", "role", "email", "messages", "documents"):
        st.session_state.pop(key, None)
    st.rerun()


login_page = st.Page("src/ui/login.py", title="Connexion", icon=":material/login:")
chat_page = st.Page("src/ui/chat.py", title="Assistant", icon=":material/chat:")
admin_page = st.Page(
    "src/ui/admin_docs.py", title="Documents", icon=":material/folder:"
)

if "token" not in st.session_state:
    pages = [login_page]
else:
    pages = [chat_page]
    if st.session_state["role"] == "admin":
        pages.append(admin_page)
    with st.sidebar:
        st.text(st.session_state["email"])
        st.caption(f"Rôle : {st.session_state['role']}")
        if st.button("Se déconnecter"):
            logout()

st.navigation(pages).run()