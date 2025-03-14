from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin
cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'))
firebase_admin.initialize_app(cred)
db = firestore.client()
bucket = storage.bucket()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-visuals', methods=['POST'])
def generate_visuals():
    try:
        data = request.get_json()
        
        # Extract scene descriptions
        scenes = data.get('scenes', [])
        
        # TODO: Implement Stable Diffusion integration
        # For now, return mock image URLs
        mock_visuals = {
            "scenes": [
                {
                    "scene_number": scene.get('scene_number'),
                    "image_url": f"https://storage.googleapis.com/{bucket.name}/mock_scene_{scene.get('scene_number')}.png"
                }
                for scene in scenes
            ]
        }
        
        return jsonify(mock_visuals), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 