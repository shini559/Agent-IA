import streamlit as st
from agents.agent import create_agent_executor

# --- Page config ---
st.set_page_config(page_title="Chatbot", layout="wide")

# --- States init ---
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False
if "toggle_chat" in st.query_params:
    st.session_state.show_chat = not st.session_state.show_chat
    st.query_params.clear()

if "history" not in st.session_state:
    st.session_state.history = []  # list of tuples: ("user", msg) / ("P'tibou", response)
if "typing" not in st.session_state:
    st.session_state.typing = False
if "selected_history_index" not in st.session_state:
    st.session_state.selected_history_index = None
if "prefill_input" not in st.session_state:
    st.session_state.prefill_input = ""
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# --- Dark mode CSS ---
dark_mode = st.session_state.dark_mode
st.markdown(f"""
    <style>
    body {{
        background-color: {'#1e1e1e' if dark_mode else '#ffffff'};
        color: {'#ffffff' if dark_mode else '#000000'};
    }}
    .chat-box {{
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        background-color: {'#2c2c2c' if dark_mode else '#f9f9f9'};
        color: {'#ffffff' if dark_mode else '#000000'};
        border: 1px solid {'#444' if dark_mode else '#ddd'};
        border-radius: 8px;
        margin-bottom: 10px;
    }}
    .history-column {{
        max-height: 400px;
        overflow-y: auto;
        background-color: {'#2c2c2c' if dark_mode else '#ffffff'};
        color: {'#ffffff' if dark_mode else '#000000'};
    }}
    </style>
""", unsafe_allow_html=True)

# --- Bouton principal pour afficher/masquer le chat ---
if st.button("🤖 P'tibou 🤖", key="open_button"):
    st.session_state.show_chat = not st.session_state.show_chat

# --- Sidebar for history ---
if st.session_state.show_chat:
    with st.sidebar:
        st.markdown("### 📜 Historique")
        st.markdown('<div class="history-column">', unsafe_allow_html=True)

        history_pairs = []
        h = st.session_state.history
        i = 0
        while i < len(h):
            if i + 1 < len(h) and h[i][0] == "user" and h[i + 1][0] == "P'tibou":
                history_pairs.append((h[i][1], h[i + 1][1]))
                i += 2
            else:
                i += 1

        for idx, (user_msg, _) in enumerate(history_pairs):
            if st.button(f"{user_msg[:30]}...", key=f"hist_{idx}"):
                st.session_state.selected_history_index = idx
                st.session_state.prefill_input = user_msg

        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("❌ Fermer le chat", key="close_chat_sidebar"):
            st.session_state.show_chat = False

        if st.button("🗑️ Effacer l'historique"):
            st.session_state.history.clear()
            st.session_state.selected_history_index = None
            st.session_state.prefill_input = ""

# --- Chat Page ---
if st.session_state.show_chat:
    if not st.session_state.history:
        st.session_state.history.append(("P'tibou", "Bonjour ! Je suis votre assistant IA. Posez-moi une question quand vous êtes prêt. 🤖"))

    st.title("💬 P'tibou")

    # Mode sombre bouton toggle
    theme_text = "🌙 Mode sombre" if not dark_mode else "☀️ Mode clair"
    if st.button(theme_text):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    # Chat messages
    chat_html = '<div class="chat-box">'
    if st.session_state.selected_history_index is not None:
        u, b = history_pairs[st.session_state.selected_history_index]
        chat_html += f"<p><strong>Vous :</strong> {u}</p>"
        chat_html += f"<p><strong>P'tibou :</strong> {b}</p>"
    else:
        for sender, message in st.session_state.history:
            role = "Vous" if sender == "user" else "P'tibou"
            chat_html += f"<p><strong>{role} :</strong> {message}</p>"
        if st.session_state.typing:
            chat_html += "<p><strong>P'tibou :</strong> ⌛ En train de répondre...</p>"
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Entrez votre message ici…", value=st.session_state.prefill_input)
        submitted = st.form_submit_button("Envoyer")

        if submitted and user_input.strip():
            st.session_state.history.append(("user", user_input))
            st.session_state.typing = True
            st.session_state.selected_history_index = None
            st.session_state.prefill_input = ""
            st.rerun()

    # Get response
    if st.session_state.typing:
        with st.spinner("P'tibou réfléchit..."):
            last_user_msg = st.session_state.history[-1][1]
            agent_executor = create_agent_executor()
            response = agent_executor.invoke({"input": last_user_msg})
            st.session_state.history.append(("P'tibou", response["output"]))
            st.session_state.typing = False
            st.rerun()
