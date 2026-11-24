"""Composants d'interface réutilisables."""

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def render_hero(title: str, subtitle: str) -> None:
    """Affiche un bloc centré avec un titre et un sous-titre."""
    st.markdown(
        f'<div class="hero"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def render_user_card(email: str, role_label: str) -> None:
    """Affiche une carte avec l'avatar, le nom, l'e-mail et le rôle."""
    local_part = email.split("@", maxsplit=1)[0]
    name = local_part.replace(".", " ").replace("_", " ").title()
    initials = "".join(word[0] for word in name.split()[:2]).upper() or "?"
    st.markdown(
        '<div class="user-card">'
        f'<div class="user-avatar">{escape(initials)}</div>'
        '<div class="user-info">'
        f'<div class="user-name">{escape(name)}</div>'
        f'<div class="user-email">{escape(email)}</div>'
        f'<span class="user-role">{escape(role_label)}</span>'
        "</div></div>",
        unsafe_allow_html=True,
    )


@lru_cache(maxsize=4)
def _encode_image(path: Path) -> str:
    """Encode une image en base64 (mis en cache pour éviter de relire le fichier)."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def apply_background(image_path: Path, overlay_opacity: float = 0.78) -> None:
    """Affiche une photo en fond de page, sous un voile vert EMSI."""
    mime_type = MIME_TYPES.get(image_path.suffix.lower())
    if mime_type is None or not image_path.exists():
        return
    encoded = _encode_image(image_path)
    css = (
        '[data-testid="stApp"] {'
        "background: linear-gradient("
        f"rgba(11, 93, 59, {overlay_opacity:.2f}), "
        f"rgba(22, 138, 85, {overlay_opacity - 0.1:.2f})), "
        f"url(data:{mime_type};base64,{encoded}) "
        "center / cover no-repeat fixed;"
        "}"
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
