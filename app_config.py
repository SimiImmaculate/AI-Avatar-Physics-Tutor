"""Shared configuration for local and hosted runs."""
import os


def get_sarvam_api_key():
    """Read the key from the environment first, then Streamlit secrets."""
    key = os.getenv("SARVAM_API_KEY")
    if key:
        return key

    try:
        import streamlit as st
        key = st.secrets.get("SARVAM_API_KEY")
        if key:
            return str(key)
    except Exception:
        # Streamlit secrets may not be configured during local/offline runs.
        pass

    return None


def use_session_storage():
    """Use isolated per-session progress only when explicitly configured."""
    mode = os.getenv("PROGRESS_MODE", "").strip().lower()
    if mode:
        return mode in {"session", "session_state", "temporary"}

    try:
        import streamlit as st
        mode = str(st.secrets.get("PROGRESS_MODE", "")).strip().lower()
        return mode in {"session", "session_state", "temporary"}
    except Exception:
        return False
