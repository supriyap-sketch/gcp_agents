import os
import json
from flask import Flask, request, jsonify, make_response
from google.cloud import aiplatform


# --- CONFIGURATION (UPDATE THESE VALUES) ---
# You must set these based on your GCP project.
PROJECT_ID = "stately-moon-480119-h9"
REGION = "global"  # e.g., 'us-central1'
# The full resource path for your deployed custom agent.
# Example format: projects/PROJECT_ID/locations/REGION/agents/AGENT_ID
CUSTOM_AGENT_RESOURCE_NAME = "projects/stately-moon-480119-h9/locations/global/agents/16e30e05-6c68-461f-921e-2d81f73541ed" 
# -------------------------------------------

# Initialize Flask App
app = Flask(__name__)

# Initialize Vertex AI Client (required for chat and agent interaction)
try:
    aiplatform.init(project=PROJECT_ID, location=REGION)
    print("Vertex AI client initialized successfully.")
except Exception as e:
    print(f"Error initializing Vertex AI client: {e}")
    # Flask will still start, but the chat endpoint will fail if the client is needed.

# --- Agent Definitions ---
# This list simulates available agents, combining your custom agent with mock examples.
AVAILABLE_AGENTS = [
    {
        "id": "product-agent-custom",
        "name": "Product Inventory & Catalog Agent (Custom)",
        "description": "Custom agent leveraging ProductCatalogTool (RAG) and ProductInventoryTool (Cloud Function).",
        "type": "Custom Agent",
        "resource_name": CUSTOM_AGENT_RESOURCE_NAME
    },
    {
        "id": "free-agent-financial",
        "name": "Financial Analysis Assistant",
        "description": "Pre-built agent for general financial queries and market trends (Mock).",
        "type": "Vertex AI Agent",
        "resource_name": "mock-financial-agent" # Mock ID for demonstration
    },
    {
        "id": "free-agent-code",
        "name": "Code Generation Helper",
        "description": "Pre-built agent for generating Python snippets and debugging code (Mock).",
        "type": "Vertex AI Agent",
        "resource_name": "mock-code-agent" # Mock ID for demonstration
    },
]
# --- Tool Definitions ---
# This list contains the pre-built tools available in the Vertex AI Agent Builder ecosystem.
PRE_BUILT_TOOLS = [
    {
        "name": "Vertex AI Search",
        "category": "Vertex AI Native",
        "description": "Grounding with your private data stores.",
        "type": "RAG Tool"
    },
    {
        "name": "Grounding with Google Search",
        "category": "Vertex AI Native",
        "description": "Real-time, public information search.",
        "type": "Search Tool"
    },
    {
        "name": "Cloud SQL - PostgreSQL",
        "category": "GCP Connector",
        "description": "Connects to a PostgreSQL database on Google Cloud SQL.",
        "type": "Database Connector"
    },
    {
        "name": "Google Calendar",
        "category": "Google Connector",
        "description": "Manages schedules and events via Google Calendar.",
        "type": "Productivity Connector"
    },
    {
        "name": "Jira Cloud",
        "category": "Third-Party Connector",
        "description": "Interacts with Jira for issue and project management.",
        "type": "Productivity Connector"
    },
    {
        "name": "Oracle DB",
        "category": "Third-Party Connector",
        "description": "Connects to an Oracle Database instance.",
        "type": "Database Connector"
    },
    # You can add the rest of the tools here (Monday.com, Zendesk, etc.)
]

# --- Flask Routes ---

@app.route('/', methods=['GET'])
def home():
    """Simple status check for the API root path."""
    return jsonify({
        "status": "Agent Dashboard API is Running",
        "endpoints": ["/api/v1/agents", "/api/v1/chat"]
    })


@app.route('/api/v1/agents', methods=['GET'])
def list_agents():
    """Endpoint to return the list of available agents to the frontend."""
    return jsonify(AVAILABLE_AGENTS)

@app.route('/api/v1/tools', methods=['GET'])
def list_tools():
    """Endpoint to return the list of available pre-built tools to the frontend."""
    return jsonify(PRE_BUILT_TOOLS)

@app.route('/api/v1/chat', methods=['POST'])
def chat_with_agent():
    """
    Endpoint to receive a user query and forward it to the selected Vertex AI agent.
    """
    data = request.get_json()
    agent_id = data.get('agentId')
    user_prompt = data.get('prompt')
    history = data.get('history', []) # Conversation history

    if not agent_id or not user_prompt:
        return make_response(jsonify({"error": "Missing agentId or prompt"}), 400)

    # Find the agent configuration
    agent_config = next((a for a in AVAILABLE_AGENTS if a['id'] == agent_id), None)

    if not agent_config or agent_config['type'] != 'Custom Agent':
        # For non-custom/mock agents, return a simulated response
        return jsonify({
            "response": f"Selected agent '{agent_config['name']}' is running in mock mode. You asked: '{user_prompt}'"
        })
    
    # --- REAL VERTEX AI AGENT INTERACTION LOGIC ---
    try:
        # Note: We use the `ChatServiceClient` for deployed Agent Builder Agents
        client = aiplatform.gapic.ChatServiceClient(client_options={"api_endpoint": f"{REGION}-aiplatform.googleapis.com"})
        
        # Format conversation history for the API (assuming 'history' is [{role: user/model, text: str}])
        # The specific format might vary slightly based on your Agent Builder deployment's SDK/API version.
        # This implementation uses the simpler `predict` on a deployed agent.

        # 1. Start or resume the conversation (session)
        # You often need to manage a conversation session. For simplicity here, we create a temporary one,
        # but in a real app, you would manage a session ID.
        
        # Simulating the required 'location' parameter for the API call
        # The actual method call signature can be complex and depends on the specific Agent Builder deployment type.
        # For this example, we'll abstract the complexity with a placeholder interaction.
        
        print(f"Attempting to chat with custom agent: {agent_config['resource_name']}")

        # --- Placeholder for Actual Agent Engine API Call ---
        # NOTE: The actual implementation requires more detailed setup (like creating a session,
        # handling streams, and managing the Agent Engine SDK).
        # We will use a mock response to ensure the frontend works, but the structure is ready
        # for you to insert the official Agent Builder client call once you look up the exact API method.
        #
        # You would typically use a method like `client.predict()` or similar on the deployed agent resource.

        # MOCK RESPONSE for the custom agent:
        final_response = (
            f"**Response from your Custom Product Agent ({agent_config['name']}):** "
            f"I have successfully processed your request: '{user_prompt}'. "
            f"If this were live, I would now be consulting the RAG tool (ProductCatalogTool) or the "
            f"Cloud Function (ProductInventoryTool) using my defined tools."
        )
        # --- End Placeholder ---


        return jsonify({
            "response": final_response
        })

    except Exception as e:
        # Catch any errors from Vertex AI calls (e.g., authentication, API failure)
        return make_response(jsonify({"error": f"Vertex AI Agent Error: {str(e)}. Check ADC and agent configuration."}), 500)


if __name__ == '__main__':
    # Use a dynamic port if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run the Flask app
    print(f"Flask API running on http://127.0.0.1:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)