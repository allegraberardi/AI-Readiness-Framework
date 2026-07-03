"""Centralized OpenRouter client/model configuration, editable by the user at runtime."""
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from i18n import t

load_dotenv()

DEFAULT_MODEL = "mistralai/mistral-large-2512"
CUSTOM_MODEL_OPTION = "__custom__"

# Curated shortlist — users can also type any OpenRouter model ID directly.
AVAILABLE_MODELS = [
    (DEFAULT_MODEL, "Mistral Large"),
    ("openai/gpt-4o", "GPT-4o"),
    ("openai/gpt-4o-mini", "GPT-4o mini"),
    ("anthropic/claude-3.7-sonnet", "Claude 3.7 Sonnet"),
    ("google/gemini-2.0-flash-001", "Gemini 2.0 Flash"),
    ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B"),
    ("deepseek/deepseek-chat", "DeepSeek Chat"),
]


def get_api_key():
    custom_key = st.session_state.get("openrouter_api_key", "").strip()
    return custom_key if custom_key else os.getenv("OPENROUTER_API_KEY")


def get_model():
    return st.session_state.get("llm_model", DEFAULT_MODEL) or DEFAULT_MODEL


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=get_api_key(),
    )


def llm_settings_sidebar():
    if "llm_model" not in st.session_state:
        st.session_state.llm_model = DEFAULT_MODEL
    if "openrouter_api_key" not in st.session_state:
        st.session_state.openrouter_api_key = ""

    with st.sidebar:
        st.subheader(t("llm_settings_title"))

        api_key = st.text_input(
            t("llm_api_key_label"),
            value=st.session_state.openrouter_api_key,
            type="password",
            placeholder=t("llm_api_key_placeholder"),
            help=t("llm_api_key_help"),
        )
        st.session_state.openrouter_api_key = api_key

        model_ids = [m[0] for m in AVAILABLE_MODELS] + [CUSTOM_MODEL_OPTION]
        model_labels = {m[0]: m[1] for m in AVAILABLE_MODELS}
        model_labels[CUSTOM_MODEL_OPTION] = t("llm_model_custom_option")

        current = st.session_state.llm_model
        current_select = current if current in model_labels else CUSTOM_MODEL_OPTION

        selected = st.selectbox(
            t("llm_model_label"),
            model_ids,
            index=model_ids.index(current_select),
            format_func=lambda m: model_labels[m],
        )

        if selected == CUSTOM_MODEL_OPTION:
            custom_model = st.text_input(
                t("llm_model_custom_label"),
                value=current if current_select == CUSTOM_MODEL_OPTION else "",
                placeholder="provider/model-name",
                help=t("llm_model_custom_help"),
            )
            st.session_state.llm_model = custom_model.strip() or DEFAULT_MODEL
        else:
            st.session_state.llm_model = selected

        st.caption(t("llm_settings_caption"))
