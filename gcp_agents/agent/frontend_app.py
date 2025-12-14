import streamlit as st
import requests
import json
import time

# --- Configuration ---
# Point this to your local Flask API server (must match the port in backend_api.py)
API_BASE_URL = "http://127.0.0.1:5000" 

# --- UI Setup ---
st.set_page_config(layout="wide", page_title="Vertex AI Agent Dashboard")
st.title("🤖 Vertex AI Agent Dashboard")

# Initialize session state for agents and chat
if 'agents' not in st.session_state:
    st.session_state.agents = []
if 'selected_agent_id' not in st.session_state:
    st.session_state.selected_agent_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- Functions ---

# Use st.cache_data to avoid re-fetching the agent list on every user interaction
@st.cache_data(ttl=3600)
def fetch_agents():
    """Fetches the list of available agents from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/agents")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        # This error is critical if the backend isn't running
        st.error(f"Cannot connect to backend API at {API_BASE_URL}. Ensure 'python backend_api.py' is running in a separate terminal.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching agents: {e}")
        return []

def select_agent_callback():
    """Handles agent selection from the dropdown."""
    st.session_state.selected_agent_id = st.session_state.agent_selector
    st.session_state.messages = [] # Clear chat history on new agent selection
    # Find the selected agent's name for the toast message
    selected_agent = next(a for a in st.session_state.agents if a['id'] == st.session_state.selected_agent_id)
    st.session_state.selected_agent_name = selected_agent['name']
    st.toast(f"Switched to agent: {st.session_state.selected_agent_name}")

@st.cache_data(ttl=3600)
def fetch_tools():
    """Fetches the list of available pre-built tools from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/tools")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # If the API is running, but the route fails, this handles the error.
        st.error(f"Error fetching pre-built tools: {e}")
        return []

def handle_user_input(prompt):
    """Sends the user's prompt and history to the backend API for processing."""
    
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Add a 'thinking' placeholder message
    st.session_state.messages.append({"role": "assistant", "content": "🤔 Thinking..."}) 
    
    # Rerun to display the user message and 'thinking' message immediately
    st.rerun() 

    # 3. Call the backend API
    try:
        # Prepare the history to send to the backend
        data = {
            "agentId": st.session_state.selected_agent_id,
            "prompt": prompt,
            "history": [
                {"role": m["role"], "text": m["content"]}
                for m in st.session_state.messages[:-1] # Exclude the 'thinking' message
            ]
        }
        
        # Make the API request to the running Flask backend
        response = requests.post(f"{API_BASE_URL}/api/v1/chat", json=data)
        response.raise_for_status()
        
        response_data = response.json()
        agent_response = response_data.get("response", "Could not get a valid response from the agent.")
        
        # 4. Update the 'thinking' placeholder with the real response
        st.session_state.messages[-1] = {"role": "assistant", "content": agent_response}
        
    except requests.exceptions.RequestException as e:
        # 4. Update the 'thinking' placeholder with the error
        error_message = f"Backend Request Error: {e}. Ensure the Flask API is running correctly."
        st.session_state.messages[-1] = {"role": "error", "content": error_message}
        st.error(error_message)
    
    # 5. Rerun to display the final response
    st.rerun()

# --- Main Layout ---

# Sidebar for Agent Selection
with st.sidebar:
    st.header("Select an Agent")
    
    # Fetch agents and prepare selection map
    agent_list = fetch_agents()
    if not agent_list:
        st.warning("Backend API not reachable. Please check Terminal 1 and ensure 'backend_api.py' is running.")
        st.stop() # Stop if the backend is not available

    st.session_state.agents = agent_list
    agent_options = {a['id']: f"[{a['type']}] {a['name']}" for a in agent_list}
    
    # Determine the default selection
    default_index = 0
    if st.session_state.selected_agent_id in agent_options:
        default_index = list(agent_options.keys()).index(st.session_state.selected_agent_id)
    
    # Agent Selector Dropdown
    selected_agent_option = st.selectbox(
        "Available Agents",
        options=list(agent_options.keys()),
        format_func=lambda x: agent_options[x],
        index=default_index,
        key="agent_selector",
        on_change=select_agent_callback
    )
    
    # Update the selected agent details in session state
    st.session_state.selected_agent_id = selected_agent_option
    selected_agent = next(a for a in agent_list if a['id'] == selected_agent_option)
    st.session_state.selected_agent_name = selected_agent['name']
    
    st.markdown("---")
    st.subheader("Agent Details")
    st.caption(f"**Name:** {selected_agent['name']}")
    st.caption(f"**Type:** `{selected_agent['type']}`")
    st.caption(f"**Description:** {selected_agent['description']}")
    st.caption(f"**Resource Name:** `{selected_agent['resource_name']}`")

# --- Tool List Display ---
    st.markdown("---")
    st.subheader("📚 Available Pre-Built Tools")
    
    tools_list = fetch_tools()
    
    if tools_list:
        # Use a list of expanders or a simple list. An expander is cleaner.
        with st.expander("Show Available Tool Connectors"):
            for tool in tools_list:
                st.markdown(
                    f"**{tool['name']}** (`{tool['category']}`): {tool['description']}"
                )
    else:
        st.caption("Could not load the list of pre-built tools from the backend.")


# Main Content Area (Chat Interface)
st.subheader(f"Chat with: {st.session_state.selected_agent_name}")
st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "error":
        # Display errors distinctly
        st.error(f"**Connection Issue:** {message['content']}")
    else:
        # Use Streamlit's native chat elements
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User input field
if user_prompt := st.chat_input("Ask the agent about products or inventory..."):
    handle_user_input(user_prompt)