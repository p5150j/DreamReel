from flask import Flask, request, jsonify
import requests
import json
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Set up logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ollama_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# System prompt for Llama3.3
system_prompt = """IMPORTANT: Return ONLY the JSON structure below. Do not add any explanatory text, introductions, or additional formatting before or after the JSON. The response must start with { and end with }.

CRITICAL: GENERATE EXACTLY 2 SEQUENCES PER CHUNK. NO MORE, NO LESS.

CRITICAL: DO NOT USE MARKDOWN, BULLET POINTS, OR ANY TEXT FORMATTING. RETURN ONLY PURE JSON.

CRITICAL FIELD NAMES - USE THESE EXACTLY:
- "sequence_number" (not "shot" or "sequence")
- "clip_duration" (not "duration")
- "clip_action" (not "shot" or "action")
- "voice_narration" (not "narration")
- "type" (must be either "b-roll" or "character")
- "pose" (only in sequence items, never in character section)
- "environment" (not "location" or "setting")
- "atmosphere" (not "mood" or "tone")
- "negative_prompt" (not "negative" or "exclude")

STRUCTURE CHECKLIST:
1. Start with {
2. Character section must have ONLY: base_traits, facial_features, distinctive_features, clothing
3. Sequence array must start with [
4. Each sequence must have ALL fields in this order:
   - sequence_number
   - clip_duration
   - clip_action
   - voice_narration
   - type
   - pose (if type is "character")
   - environment
   - atmosphere
   - negative_prompt
5. Sequence array must end with ]
6. Root object must end with }

Return this exact JSON structure with your story content:

{
    "character": {
        "base_traits": "(mid-30s asian woman:1.4)",
        "facial_features": "(determined brown eyes:1.3)",
        "distinctive_features": "(small scar on left cheek:1.4)",
        "clothing": "(hiking gear:1.2)"
    },
    "sequence": [
        {
            "sequence_number": 1,
            "clip_duration": 3.0625,
            "clip_action": "ESTABLISHING SHOT: camera slowly panning right",
            "voice_narration": "Where is my ducky?",
            "type": "b-roll",
            "environment": "EXT. COLORADO MOUNTAINS - DAY",
            "atmosphere": "(8k uhd:1.4), (photorealistic:1.4), (cinematic lighting:1.3), (film grain:1.2), (cinematic color grading:1.3)",
            "negative_prompt": "(worst quality:1.4), (low quality:1.4), (blurry:1.2), (deformed:1.4), (distorted:1.4), (bad anatomy:1.4), (bad proportions:1.4), (multiple people:1.8), (wrong face:1.8), (different person:1.8), (duplicate body parts:1.4), (missing limbs:1.4)"
        },
        {
            "sequence_number": 2,
            "clip_duration": 3.0625,
            "clip_action": "MEDIUM SHOT: character walking through snow",
            "voice_narration": "The snow is deep",
            "type": "character",
            "pose": "[previous character traits], (walking through deep snow:1.4)",
            "environment": "EXT. COLORADO MOUNTAINS - DAY",
            "atmosphere": "(8k uhd:1.4), (photorealistic:1.4), (cinematic lighting:1.3), (film grain:1.2), (cinematic color grading:1.3)",
            "negative_prompt": "(worst quality:1.4), (low quality:1.4), (blurry:1.2), (deformed:1.4), (distorted:1.4), (bad anatomy:1.4), (bad proportions:1.4), (multiple people:1.8), (wrong face:1.8), (different person:1.8), (duplicate body parts:1.4), (missing limbs:1.4)"
        }
    ]
}"""

app = Flask(__name__)

def parse_json_response(response_text: str) -> Dict:
    """Parse JSON response using json module."""
    try:
        # Debug: Print the full response text
        logger.debug(f"Full response text: {response_text}")
        
        # Parse the JSON directly
        parsed_json = json.loads(response_text)
        logger.debug(f"Successfully parsed JSON: {parsed_json}")
        
        return parsed_json
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.error(f"Error occurred at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
        raise

def validate_and_fix_sequence(sequence):
    """Validate and fix sequence fields to ensure correct field names."""
    required_fields = {
        "sequence_number": int,
        "clip_duration": float,
        "clip_action": str,
        "voice_narration": str,
        "type": str,
        "environment": str,
        "atmosphere": str,
        "negative_prompt": str
    }
    
    # Fix common field name issues
    field_mappings = {
        "voice_nadration": "voice_narration",
        "shot": "clip_action",
        "duration": "clip_duration",
        "narration": "voice_narration",
        "location": "environment",
        "setting": "environment",
        "mood": "atmosphere",
        "tone": "atmosphere",
        "negative": "negative_prompt",
        "exclude": "negative_prompt"
    }
    
    # Create a new sequence with correct field names
    fixed_sequence = {}
    for key, value in sequence.items():
        # Fix field name if needed
        fixed_key = field_mappings.get(key, key)
        fixed_sequence[fixed_key] = value
    
    # Add missing required fields with defaults
    for field, field_type in required_fields.items():
        if field not in fixed_sequence:
            if field == "type":
                fixed_sequence[field] = "b-roll"
            elif field == "clip_duration":
                fixed_sequence[field] = 3.0625
            elif field == "sequence_number":
                fixed_sequence[field] = len(fixed_sequence) + 1
            else:
                fixed_sequence[field] = ""
    
    return fixed_sequence

def generate_story_chunk(prompt, previous_sequences=None):
    """Generate a chunk of the story using Llama 3.3"""
    try:
        # Construct the full prompt with previous sequences if any
        full_prompt = prompt
        if previous_sequences:
            full_prompt += "\nPrevious sequences:\n"
            for seq in previous_sequences:
                full_prompt += f"- {seq['voice_narration']}\n"
        
        # Add the system prompt
        full_prompt = system_prompt + "\n\n" + full_prompt
        
        # Log the full prompt for debugging
        logging.debug("================================================================================")
        logging.debug("Full prompt being sent to Llama 3.3:")
        logging.debug(full_prompt)
        logging.debug("================================================================================")
        
        # Make the API call to Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.3",
                "prompt": full_prompt,
                "stream": False
            }
        )
        
        # Log the raw response for debugging
        logging.debug("================================================================================")
        logging.debug("Raw response from Llama 3.3:")
        logging.debug(response.text)
        logging.debug("================================================================================")
        
        response.raise_for_status()
        response_text = response.json()['response']
        parsed_json = parse_json_response(response_text)
        
        # Validate and fix sequences
        if 'sequence' in parsed_json:
            parsed_json['sequence'] = [validate_and_fix_sequence(seq) for seq in parsed_json['sequence']]
        
        return parsed_json
    except Exception as e:
        logger.error(f"Error generating story chunk: {str(e)}")
        raise

@app.route('/test-model', methods=['POST'])
def test_model():
    try:
        # Get request data
        data = request.get_json(force=True)
        logger.debug(f"Received request data: {data}")
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Please provide a prompt', 'status': 'error'}), 400
        
        # Extract parameters
        prompt = data.get('prompt')
        
        # Calculate number of chunks needed (aiming for 8 sequences total)
        # With 2 sequences per chunk, we need 4 chunks
        total_chunks = 4  # This will generate ~8 sequences
        
        # Generate first chunk
        first_chunk = generate_story_chunk(prompt)
        final_story = first_chunk
        
        # Generate subsequent chunks with continuity
        for chunk_num in range(2, total_chunks + 1):
            previous_sequence = final_story['sequence'][-1]
            chunk = generate_story_chunk(
                prompt,
                previous_sequences=[previous_sequence]
            )
            
            # Append new sequences while maintaining character consistency
            final_story['sequence'].extend(chunk['sequence'])
            
            # Log progress
            logger.debug(f"Generated chunk {chunk_num} with {len(chunk['sequence'])} sequences")
            logger.debug(f"Total sequences so far: {len(final_story['sequence'])}")
        
        # Log final story length
        logger.debug(f"Final story contains {len(final_story['sequence'])} sequences")
        
        return jsonify(final_story)
            
    except Exception as e:
        logger.error(f"Error testing model: {str(e)}")
        return jsonify({
            'error': f"Error: {str(e)}",
            'status': 'error'
        }), 500

# Add a health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check if Ollama API is available
        response = requests.get("http://localhost:11434/api/version")
        response.raise_for_status()
        
        return jsonify({
            'status': 'healthy',
            'ollama_status': 'connected'
        })
    except:
        return jsonify({
            'status': 'degraded',
            'ollama_status': 'disconnected',
            'error': 'Cannot connect to Ollama API'
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True) 