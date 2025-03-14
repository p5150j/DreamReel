from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-script', methods=['POST'])
def generate_script():
    try:
        data = request.get_json()
        
        # Extract user preferences
        genre = data.get('genre')
        theme = data.get('theme')
        visual_style = data.get('visualStyle')
        
        # TODO: Implement LLM integration for script generation
        # For now, return a mock response
        mock_script = {
            "title": f"{genre} Story",
            "scenes": [
                {
                    "scene_number": 1,
                    "description": f"Opening scene in {visual_style} style",
                    "dialogue": "Sample dialogue for scene 1"
                },
                {
                    "scene_number": 2,
                    "description": f"Main scene in {visual_style} style",
                    "dialogue": "Sample dialogue for scene 2"
                }
            ]
        }
        
        return jsonify(mock_script), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 