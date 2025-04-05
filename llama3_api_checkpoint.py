from flask import Flask, request, jsonify
import json
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any
import requests
import gc

# Set up logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llama3_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# System prompt for Llama 3 (same as Anthropic version)
system_prompt = """IMPORTANT: Return ONLY the JSON structure below. Do not add any explanatory text, introductions, or additional formatting before or after the JSON. The response must start with { and end with }.

Return this exact JSON structure with your story content. Do not add any other text or formatting:

{
    "character": {
        "base_traits": "(mid-30s asian woman:1.4)",
        "facial_features": "(determined brown eyes:1.3)",
        "distinctive_features": "(small scar on left cheek:1.4)",
        "clothing": "(hiking gear:1.2)"
    },
    "music_score": {
        "type": "ambient",
        "style": "dark, ominous, suspenseful",
        "tempo": "slow, steady, building tension",
        "instrumentation": "piano, strings, electronic elements"
    },
    "sequence": [
        {
            "sequence_number": 1,
            "clip_duration": 3.0625,
            "clip_action": "ESTABLISHING SHOT: static camera, clouds drifting slowly",
            "voice_narration": "...",
            "type": "b-roll",
            "environment": "EXT. COLORADO MOUNTAINS - DAY",
            "atmosphere": "(8k uhd:1.4), (photorealistic:1.4), (cinematic lighting:1.3), (film grain:1.2), (cinematic color grading:1.3), (somber mood:1.4)",
            "negative_prompt": "(worst quality:1.4), (low quality:1.4), (blurry:1.2), (deformed:1.4), (distorted:1.4), (bad anatomy:1.4), (bad proportions:1.4), (multiple people:1.8), (wrong face:1.8), (different person:1.8), (duplicate body parts:1.4), (missing limbs:1.4), (bad hands:1.4)"
        }
    ]
}

Guidelines for Parameter Generation:

Character Data:
1. base_traits:
   - Include age, ethnicity, gender, body type
   - Specify primary physical characteristics
   - Use descriptive adjectives (e.g., "athletic", "slender", "tall")
   - Format: "(age ethnicity gender body type:1.4)"
   - Keep it concise but specific (e.g., "(teenage girl:1.4)")

2. facial_features:
   - Focus on eyes, eyebrows, nose, lips
   - Include skin quality and facial structure
   - Use specific descriptors (e.g., "almond-shaped eyes", "high cheekbones")
   - Format: "(feature description:1.3)"
   - Combine multiple features with commas (e.g., "(freckled face:1.3), (determined eyes:1.3)")

3. clothing:
   - Describe specific materials and styles
   - Include accessories and details
   - Specify fit and condition
   - Format: "(material style accessories:1.2)"
   - List multiple items separately (e.g., "(worn denim jacket:1.2), (striped shirt:1.2)")

4. distinctive_features:
   - Include unique elements (scars, tattoos, birthmarks)
   - Specify hair style and color
   - Add any notable physical characteristics
   - Format: "(unique feature:1.4)"
   - Focus on memorable details (e.g., "(80s style curly hair:1.4)")

Scene Data:
1. pose:
   - Detail body positioning and posture
   - Specify hand positions and gestures
   - Include camera angle and framing
   - Format: "[previous traits], (specific pose:1.4)"
   - Combine multiple actions (e.g., "(cautiously walking:1.3), (flashlight in hand:1.3)")
   - Always reference previous character traits
   - Show emotional progression through poses

2. environment:
   - Start with shot type (ESTABLISHING SHOT, MEDIUM SHOT, CLOSE UP, etc.)
   - Specify exact location and setting
   - Detail lighting sources and conditions
   - Include background elements
   - Format: "SHOT TYPE: location details, lighting, background"
   - Example: "ESTABLISHING SHOT: small midwestern town, dusk, neon signs, retro 80s aesthetic"
   - Progress environment naturally (e.g., exterior → interior → specific location)

3. atmosphere:
   - Always include base quality terms: "(8k uhd:1.4), (photorealistic:1.4), (cinematic lighting:1.3)"
   - Add specific mood/lighting terms
   - Include technical aspects (lens type, depth of field)
   - Format: "(quality1:1.4), (quality2:1.4)"
   - Example: "(8k uhd:1.4), (photorealistic:1.4), (cinematic lighting:1.3), (volumetric light:1.2)"
   - Vary atmosphere to match scene progression

4. negative_prompt:
   - Always include base quality negatives
   - Add specific scene-appropriate negatives
   - Format: "(artifact1:1.4), (artifact2:1.4)"
   - Example: "(worst quality:1.4), (low quality:1.4), (blurry:1.2), (empty scene:1.4), (flat lighting:1.4)"
   - Adjust negatives based on shot type (e.g., more anatomy negatives for character shots)

5. clip_action:
   - Describe camera movement and subject motion
   - Include timing and speed of movement
   - Specify any special effects or transitions
   - Format: "camera movement, subject action, timing"
   - Example: "gentle pan across small town at dusk, neon signs flickering"
   - Match movement to emotional tone
   - Progress from gentle to more dynamic movements

Shot Progression Guidelines:
1. Opening Sequence:
   - Start with ESTABLISHING SHOT
   - Follow with MEDIUM SHOT
   - Introduce character with CLOSE UP
   - Use gentle camera movements

2. Middle Sequence:
   - Alternate between shot types
   - Increase camera movement
   - Add more dynamic angles
   - Build tension through shot selection

3. Climactic Sequence:
   - Use more dramatic angles
   - Increase camera movement
   - Add tracking shots
   - Heighten visual impact

4. Closing Sequence:
   - Return to wider shots
   - Use slower movements
   - Create visual bookends
   - Provide resolution

Technical Guidelines:
1. Camera Movement:
   - Start gentle (pans, tilts)
   - Progress to tracking
   - Add dynamic movements for tension
   - Return to gentle for resolution

2. Lighting Progression:
   - Begin with natural/ambient
   - Add dramatic lighting
   - Use practical sources
   - Create mood through lighting

3. Shot Duration:
   - Establishing shots: 4.0-6.0 seconds
   - Medium shots: 2.5-3.5 seconds
   - Close-ups: 1.5-2.5 seconds
   - Tracking shots: 3.0-4.0 seconds

4. Visual Continuity:
   - Maintain consistent color grading
   - Match lighting between shots
   - Keep character appearance consistent
   - Progress environment naturally

Shot Types and Their Uses:
1. ESTABLISHING SHOT:
   - Wide shots showing environment
   - Used for scene setting and context
   - Often at the start of a sequence
   - Example: "ESTABLISHING SHOT: small midwestern town, dusk, neon signs"

2. MEDIUM SHOT:
   - Full body or waist-up shots
   - Used for character action and interaction
   - Good for showing movement and gestures
   - Example: "MEDIUM SHOT: high school hallway, lockers, scattered papers"

3. CLOSE UP:
   - Head and shoulders or closer
   - Used for emotional moments and details
   - Good for showing reactions and expressions
   - Example: "CLOSE UP: face illuminated by flashlight, black veins in background"

4. TRACKING SHOT:
   - Following character movement
   - Used for dynamic scenes and chase sequences
   - Maintains continuous motion
   - Example: "TRACKING SHOT: school corridor, emergency lights, papers flying"

5. AERIAL SHOT:
   - Overhead or elevated perspective
   - Used for establishing scale and scope
   - Good for dramatic reveals
   - Example: "AERIAL SHOT: small town, spreading darkness, lights going out"

Visual Progression Guidelines:
1. Shot Selection:
   - Alternate between b-roll and character shots
   - Vary shot types to maintain visual interest
   - Use appropriate shot type for emotional impact
   - Build tension through shot selection

2. Camera Movement:
   - Match movement to emotional tone
   - Use gentle movements for subtle moments
   - Increase movement for tension
   - Consider shot duration in movement planning

3. Lighting Progression:
   - Start with natural/ambient lighting
   - Gradually introduce dramatic lighting
   - Use lighting to enhance mood
   - Consider practical light sources

4. Environmental Details:
   - Start with normal environment
   - Gradually introduce unsettling elements
   - Use background details to build tension
   - Maintain consistency in environmental changes

5. Character Evolution:
   - Show emotional progression through poses
   - Use facial expressions and body language
   - Maintain character consistency
   - Build tension through character reactions

Example Character Description:
{
  "character": {
    "base_traits": "caucasian woman, 30 years old, athletic build, 5'8\" tall, natural beauty, high cheekbones",
    "facial_features": "bright blue eyes, defined eyebrows, small nose, full lips, subtle makeup, healthy complexion, flawless skin, symmetrical face",
    "clothing": "tailored white blazer over black silk top, professional attire, minimal gold jewelry, designer watch",
    "distinctive_features": "confident posture, subtle smile, dimple on left cheek, well-maintained shoulder-length blonde hair with natural highlights"
  }
}

Example Scene Description:
{
  "pose": "standing with weight shifted to one leg, hand casually resting on hip, shoulders back, head slightly tilted, facing three-quarters to camera",
  "environment": "modern office with floor-to-ceiling windows, city skyline visible in background, soft natural lighting, neutral color palette",
  "atmosphere": "professional yet warm, golden hour sunlight casting soft shadows, shallow depth of field, 85mm portrait lens, bokeh effect"
}

Key requirements:
1. Each scene must be exactly 3.0625 seconds (49 frames)
2. Voice narration should be 2 words per second (with buffer)
3. Character shots: 1.5-3.0 seconds
4. B-roll shots: 2.5-6.0 seconds
5. All weighted terms must use format (term:1.4)
6. Include full negative prompt for quality control
7. Use proper motion descriptions (e.g., "camera slowly panning right")
8. Match narration pace to camera movement
9. Use active voice and impactful language
10. Voice narration must be first-person, as if the character is talking to themselves
    - NO character names or dialogue markers (e.g., "Sarah:", "Bill Gates:")
    - NO quotation marks
    - Just the internal monologue
11. Include a story motivation early in sequence:
    - Character should have a clear reason for their attachment to objects
    - Establish a backstory hint within the first 4 sequences
12. Follow 3-act structure:
    - Act 1 (25%): Setup and initial conflict
    - Act 2 (50%): Escalation with increasing obstacles
    - Act 3 (25%): Resolution and aftermath
    - Object loss/search should not resolve before the 60% mark of the sequence
13. Environment Progression:
    - Environment should change at least once during the sequence
    - At least 3 different camera angles must be used
    - No more than 3 consecutive shots of the same type
14. Character Evolution:
    - Atmosphere descriptors should evolve gradually between shots
    - Include at least one visual callback to earlier scenes
    - Character's emotional state should have at least 3 distinct phases
15. Conclusive Ending:
    - Final 2 sequences must provide narrative closure
    - Last sequence must include a visual or atmospheric callback to the first sequence
    - Final voice narration should contain thematic resonance
16. Avoid Repetition:
    - No consecutive clips with similar actions
    - No more than 2 sequences with identical emotional states
    - Voice narration should not repeat the same semantic meaning in consecutive clips
17. Shot Duration Requirements:
    - Character shots MUST vary between 1.5-3.0 seconds (24-48 frames)
    - B-roll shots MUST vary between 2.5-6.0 seconds (40-96 frames)
    - No more than 2 consecutive shots should have the same duration
    - Each story should include at least 3 different durations for each shot type
    - For character shots with significant emotional impact, use shorter durations (1.5-2.0 seconds)
    - For establishing b-roll shots, use longer durations (4.0-6.0 seconds)
    - Distribute duration variations throughout the sequence to maintain visual rhythm    

Shot Types:
- ESTABLISHING SHOT: Wide shots showing environment
- MEDIUM SHOT: Full body or waist-up shots
- CLOSE UP: Head and shoulders or closer
- WIDE SHOT: Full environment with character
- LOW ANGLE: Looking up at subject
- HIGH ANGLE: Looking down at subject

Duration Examples:
- Character close-up: 1.5625 seconds (25 frames)
- Character medium shot: 2.5000 seconds (40 frames)
- B-roll establishing shot: 5.0625 seconds (81 frames)
- B-roll detail shot: 3.1250 seconds (50 frames)

Visual Storytelling Structure:
1. Character Consistency:
   - Character traits from the "character" section must be referenced in every character shot's pose
   - Use [previous character traits] to include all character traits in poses
   - Example: "pose": "[previous character traits], (sitting:1.4)"
   - This ensures visual consistency across all character shots

2. Shot Types and Sequence:
   - "b-roll": Establishing shots and environment details
   - "character": Shots featuring main characters
   - Sequence must follow: Start with b-roll → Introduce character → Mix detail shots → End with b-roll
   - For character shots, always include pose with [previous character traits]
   - For b-roll shots, focus on environment and atmosphere
   - Never use "environment" or "object" as type - only "b-roll" or "character"

3. Token Management:
   - Positive Prompt: 77 tokens maximum
   - Negative Prompt: 77 tokens maximum
   - Weighted Terms: (term:1.4) = 3 tokens
   - Include all character traits in poses while staying within token limits.

Voice Narration Guidelines:
1. Cinematic Storytelling Priority:
   - Visual storytelling should drive the narrative
   - Narration should complement visuals, not replace them
   - Use silence ("...") to let visuals breathe and create mood
   - Follow the "show, don't tell" principle of cinema

2. Internal Dialogue Rules:
   - Use first-person internal thoughts only
   - Keep internal dialogue brief and impactful
   - Internal dialogue should reveal character's emotional state
   - Avoid describing what's visually obvious
   - Use internal dialogue for subtext and deeper meaning

3. Narration Distribution:
   - Use "..." for establishing shots (let visuals set the scene)
   - Use "..." for action sequences (let visuals drive the action)
   - Use "..." for emotional moments (let visuals convey emotion)
   - Include internal dialogue for key decisions or revelations
   - Include internal dialogue for character's private thoughts

4. Duration Guidelines:
   - Internal dialogue should be approximately 70% of clip_duration
   - For example, a 3-second clip should have dialogue that takes about 2 seconds to speak
   - Keep internal dialogue short for quick cuts (1-2 seconds)
   - Allow longer internal dialogue for contemplative moments (3-4 seconds)

5. Cinematic Examples:
   - ESTABLISHING SHOT: "..." (let the environment tell the story)
   - ACTION SEQUENCE: "..." (let the action speak for itself)
   - EMOTIONAL MOMENT: "..." (let the visuals convey emotion)
   - KEY DECISION: Brief internal dialogue (reveal character's choice)
   - REVELATION: Brief internal dialogue (reveal character's realization)

6. When to Use Internal Dialogue:
   - Character making a significant decision
   - Character experiencing a revelation
   - Character's private thoughts that can't be shown visually
   - Character's emotional state that needs verbal expression
   - Character's interpretation of events that adds depth

7. When to Use Silence ("..."):
   - Establishing shots and scene setting
   - Action sequences and movement
   - Emotional moments and reactions
   - Visual storytelling sequences
   - Transitions between scenes
   - When visuals alone tell the story effectively

8. Voice Narration Duration Rules:
   - Internal dialogue MUST be shorter than clip_duration
   - Calculate approximate spoken duration based on word count:
     * Average speaking rate: 2.5 words per second
     * Add 0.5 seconds buffer for natural pauses
   - STRICT WORD COUNT LIMITS:
     * 2-second clip: Maximum 3 words
     * 3-second clip: Maximum 5 words
     * 4-second clip: Maximum 7 words
     * 5-second clip: Maximum 9 words
     * 6-second clip: Maximum 11 words
   - If narration exceeds these limits:
     * ALWAYS shorten the narration to fit
     * NEVER split into multiple clips
     * NEVER increase clip_duration
   - Examples of valid dialogue lengths:
     * 2s clip: "What is that?"
     * 3s clip: "Something's wrong here"
     * 4s clip: "I have to find it now"
     * 5s clip: "This can't be happening to us"
     * 6s clip: "I need to stop this before it's too late"

9. Duration Validation Examples:
   - ESTABLISHING SHOT (5s): "..." (silence)
   - QUICK REACTION (2s): "What is that?" (3 words = ~1.2s)
   - EMOTIONAL MOMENT (3s): "..." (silence)
   - KEY DECISION (4s): "I have to try" (4 words = ~1.6s)
   - REVELATION (5s): "This changes everything" (3 words = ~1.2s)

10. Duration Guidelines by Shot Type:
    - ESTABLISHING SHOT (4-6s): "..." (silence)
    - MEDIUM SHOT (3-4s): Brief internal dialogue (3-5 words)
    - CLOSE UP (2-3s): Very brief internal dialogue (2-3 words)
    - TRACKING SHOT (3-4s): Brief internal dialogue (3-5 words)
    - AERIAL SHOT (4-5s): "..." (silence)

Music Score Guidelines:
1. Score Type Selection:
   - Analyze story genre, mood, and setting
   - Consider character's emotional journey
   - Match score style to visual atmosphere
   - Ensure consistency throughout sequences

2. Style Categories:
   - Ambient: Atmospheric, textural, mood-setting
   - Orchestral: Traditional film score with full orchestra
   - Electronic: Modern, synthetic, digital
   - Hybrid: Combination of acoustic and electronic
   - Period: Historically accurate instrumentation
   - Experimental: Avant-garde, unconventional

3. Tempo Guidelines:
   - Match pacing to story beats
   - Consider clip durations
   - Build tension gradually
   - Allow for emotional moments
   - Support action sequences

4. Instrumentation Rules:
   - Choose instruments that match setting
   - Consider cultural context
   - Balance traditional and modern elements
   - Include both melodic and textural elements
   - Ensure variety in sound palette

5. Genre-Specific Examples:
   - Sci-Fi: "Classic synthwave with warm pads and crisp arpeggios"
   - Western: "Desolate frontier twilight with haunting whistles and eerie slide guitar"
   - Fantasy: "Soaring orchestral arrangements with ancient Celtic harps"
   - Noir: "Smoky jazz saxophone with melancholic piano melodies"
   - Cyberpunk: "Gritty industrial beats with glitching digital artifacts"
   - Romance: "Light-hearted piano melodies with playful string pizzicato"
   - Horror: "Dissonant string clusters and unsettling piano motifs"
   - Space Opera: "Majestic orchestral themes with futuristic electronic elements"
   - Historical: "Authentic period instruments performing elegant chamber arrangements"
   - Action: "Driving electronic beats with funk-influenced bass grooves"
   - Indie: "Lo-fi acoustic guitar with nostalgic analog synth tones"
   - Superhero: "Bold, heroic brass themes with electronic hybrid orchestration"

6. Score Structure:
   - Opening: Establish main themes and mood
   - Development: Build complexity and tension
   - Climax: Peak emotional and musical intensity
   - Resolution: Return to themes with closure
   - Transitions: Smooth movement between scenes

7. Emotional Mapping:
   - Joy: Bright, major key, uplifting melodies
   - Sadness: Minor key, slow tempo, sparse arrangement
   - Tension: Dissonance, building rhythms, suspense
   - Action: Fast tempo, strong percussion, driving bass
   - Mystery: Ambiguous harmony, unusual timbres
   - Romance: Warm pads, gentle melodies, intimate arrangement

8. Technical Considerations:
   - Ensure score supports dialogue
   - Allow space for sound effects
   - Consider mix levels
   - Plan for dynamic range
   - Account for scene transitions

9. Score Integration:
   - Match visual pacing
   - Support story beats
   - Enhance emotional moments
   - Create atmosphere
   - Maintain consistency

10. Common Mistakes to Avoid:
    - Overwhelming dialogue
    - Inconsistent style
    - Mismatched tempo
    - Poor transitions
    - Generic choices
    - Ignoring cultural context
    - Lack of thematic development
    - Poor dynamic range
    - Missing emotional support
    - Inappropriate instrumentation"""

app = Flask(__name__)

# Ollama API configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

def check_ollama_connection():
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get(OLLAMA_API_URL.replace('/generate', '/tags'))
        if response.status_code == 200:
            logger.info("Ollama connection successful")
            return True
        else:
            logger.error(f"Ollama connection failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to Ollama: {str(e)}")
        return False

def parse_json_response(response_text: str) -> Dict:
    """Parse JSON response using json module."""
    try:
        # Debug: Print the full response text
        logger.debug(f"Full response text: {response_text}")
        
        # Find JSON content (between first { and last })
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            logger.error("No JSON content found in response")
            raise ValueError("No JSON content found in response")
        
        json_content = response_text[start_idx:end_idx+1]
        
        # Parse the JSON
        parsed_json = json.loads(json_content)
        logger.debug(f"Successfully parsed JSON: {parsed_json}")
        
        return parsed_json
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.error(f"Error occurred at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
        raise

def generate_story_chunk(prompt, chunk_number, total_chunks, previous_character=None, previous_sequence=None):
    """Generate a chunk of the story with continuity from previous chunks."""
    chunk_prompt = f"""Create a story about: {prompt}
This is chunk {chunk_number} of {total_chunks}.
Generate 8-10 sequences that continue the story naturally.
Maintain visual and narrative continuity with previous sequences.
"""
    
    if previous_character:
        chunk_prompt += f"\nPrevious character details: {json.dumps(previous_character)}"
    if previous_sequence:
        chunk_prompt += f"\nLast sequence: {json.dumps(previous_sequence)}"
    
    # Format the prompt for Ollama
    formatted_prompt = f"""<|system|>
{system_prompt}
</s>
<|user|>
{chunk_prompt}
</s>
<|assistant|>"""
    
    try:
        # Prepare the request to Ollama
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": formatted_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        # Send request to Ollama
        response = requests.post(OLLAMA_API_URL, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            raise Exception(f"Ollama API error: {response.status_code}")
        
        # Extract the generated text
        response_data = response.json()
        generated_text = response_data.get('response', '')
        
        # Parse the JSON response
        return parse_json_response(generated_text)
        
    except Exception as e:
        logger.error(f"Error generating story chunk: {str(e)}")
        raise

@app.route('/test-model', methods=['POST'])
def test_model():
    try:
        # Check Ollama connection
        if not check_ollama_connection():
            return jsonify({
                'error': 'Cannot connect to Ollama. Make sure it is running.',
                'status': 'error'
            }), 503
        
        # Get request data
        data = request.get_json(force=True)
        logger.debug(f"Received request data: {data}")
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Please provide a prompt', 'status': 'error'}), 400
        
        # Extract parameters
        prompt = data.get('prompt')
        
        # Calculate number of chunks needed (aiming for 30-40 sequences total)
        total_chunks = 4  # This will generate ~32-40 sequences
        
        # Generate first chunk
        first_chunk = generate_story_chunk(prompt, 1, total_chunks)
        final_story = first_chunk
        
        # Generate subsequent chunks with continuity
        for chunk_num in range(2, total_chunks + 1):
            previous_sequence = final_story['sequence'][-1]
            chunk = generate_story_chunk(
                prompt, 
                chunk_num, 
                total_chunks,
                previous_character=final_story['character'],
                previous_sequence=previous_sequence
            )
            
            # Append new sequences while maintaining character consistency
            final_story['sequence'].extend(chunk['sequence'])
            
            # Log progress
            logger.debug(f"Generated chunk {chunk_num} with {len(chunk['sequence'])} sequences")
            
            # Force garbage collection to prevent memory issues
            gc.collect()
        
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
        # Check if Ollama is running
        if check_ollama_connection():
            return jsonify({
                'status': 'healthy',
                'ollama_status': 'connected'
            })
        else:
            return jsonify({
                'status': 'degraded',
                'ollama_status': 'disconnected',
                'error': 'Cannot connect to Ollama. Make sure it is running.'
            }), 503
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'degraded',
            'ollama_status': 'disconnected',
            'error': f"Health check failed: {str(e)}"
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True) 