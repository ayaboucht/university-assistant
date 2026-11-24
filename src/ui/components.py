"""Composants d'interface réutilisables."""

from html import escape

import streamlit as st


def render_hero(title: str, subtitle: str) -> None:
    """Affiche un bloc centré avec un titre et un sous-titre."""
    st.markdown(
        f'<div class="hero"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )
