import os
from flask import Flask, request, jsonify, send_from_directory # Added send_from_directory
from werkzeug.utils import secure_filename
import soundfile as sf
import noisereduce as nr
import numpy as np
import librosa # For robust audio loading and sample rate detection

# Define PROCESSED_FOLDER before using it in Flask app initialization
PROCESSED_FOLDER_NAME = 'processed_audio'

# Initialize Flask app to serve static files from PROCESSED_FOLDER_NAME
# under the URL path /processed_audio
# Use an absolute path for static_folder to avoid ambiguity.
static_dir = os.path.abspath(PROCESSED_FOLDER_NAME)
app = Flask(__name__, static_folder=static_dir, static_url_path=f'/{PROCESSED_FOLDER_NAME}')

UPLOAD_FOLDER = 'temp_uploads'
# PROCESSED_FOLDER config key for consistency in other parts of the app if needed,
# but Flask's static serving uses the 'static_folder' argument passed above.
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER_NAME # Align with the static_folder name

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}

# Ensure the upload and processed folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True) # Use app.config for consistency

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return jsonify({"message": "File uploaded successfully", "filename": filename}), 200
        except Exception as e:
            return jsonify({"error": f"Could not save file: {str(e)}"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

@app.route('/enhance', methods=['POST'])
def enhance_audio():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({"error": "Missing filename in JSON payload"}), 400

    filename = data['filename']
    if not allowed_file(filename): # Reuse validation, though file should be uploaded already
        return jsonify({"error": "Invalid filename or disallowed type"}), 400
        
    original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    enhanced_filename = f"enhanced_{secure_filename(filename)}"
    enhanced_filepath = os.path.join(app.config['PROCESSED_FOLDER'], enhanced_filename)

    if not os.path.exists(original_filepath):
        return jsonify({"error": f"Original file not found: {filename}"}), 404

    try:
        # Load audio file using librosa for robustness with formats and getting sample rate
        audio_data, sample_rate = librosa.load(original_filepath, sr=None, mono=True)
        
        # Ensure audio_data is float for noisereduce if it's not already
        if audio_data.dtype != np.float32 and audio_data.dtype != np.float64:
             audio_data = audio_data.astype(np.float32)


        # Perform noise reduction
        # Note: noisereduce works best with stationary noise.
        # Parameters might need tuning depending on the audio.
        reduced_noise_audio = nr.reduce_noise(y=audio_data, sr=sample_rate)
        
        # Save the enhanced audio file using soundfile
        # Ensure the output format matches the input or choose a default like WAV
        # If original filename was mp3, enhanced_filepath will be enhanced_audio.mp3
        # soundfile will try to determine format from extension. For MP3, LAME might be needed.
        # For simplicity, we'll try to save with the same extension.
        # If soundfile can't write a specific format (e.g. mp3 without LAME), it will fail.
        # A common robust approach is to save as WAV.
        
        # Let's ensure the output is always WAV for consistency and broad compatibility,
        # as soundfile has excellent WAV support built-in.
        enhanced_filename_wav = f"enhanced_{os.path.splitext(secure_filename(filename))[0]}.wav"
        enhanced_filepath_wav = os.path.join(app.config['PROCESSED_FOLDER'], enhanced_filename_wav)

        sf.write(enhanced_filepath_wav, reduced_noise_audio, sample_rate)
        
        return jsonify({
            "message": "Audio enhanced successfully", 
            "enhanced_filename": enhanced_filename_wav,
            "enhanced_file_url": f"/processed_audio/{enhanced_filename_wav}" # Added for convenience
        }), 200

    except FileNotFoundError:
        return jsonify({"error": f"File not found during processing: {filename}"}), 404
    except Exception as e:
        app.logger.error(f"Error enhancing audio {filename}: {str(e)}")
        return jsonify({"error": f"Error processing audio: {str(e)}"}), 500

# Removed the explicit /processed_audio/<path:filename> route
# as Flask's static file handling will now manage this.

if __name__ == '__main__':
    # When static_folder is set as above, Flask automatically creates a route
    # for static_url_path. So, requests to /processed_audio/somefile.wav
    # will serve 'somefile.wav' from the 'processed_audio' directory.
    
    # If you also need to serve index.html, style.css, script.js from a different
    # static directory (e.g., a root 'static' folder for general web assets),
    # you would typically use a Blueprint for one of them or serve index.html
    # via a specific route and have its assets in a standard 'static' folder.
    # This solution strictly addresses serving the 'processed_audio' directory.
    
    # Add routes for serving frontend files from the root directory
    @app.route('/')
    def index():
        return send_from_directory(app.root_path, 'index.html')

    @app.route('/<path:filename>')
    def serve_static_from_root(filename):
        # Serve script.js and style.css from the root directory
        if filename in ['style.css', 'script.js']:
            return send_from_directory(app.root_path, filename)
        # For other files, it might be an attempt to access processed_audio,
        # which is handled by the static_folder configuration.
        # If not found by static_folder, Flask will 404 automatically.
        # This explicit 404 is a fallback but might not be strictly necessary
        # if static_url_path for processed_audio doesn't overlap.
        # However, to be safe and avoid serving unintended files:
        return jsonify({"error": "File not found"}), 404


    app.run(debug=True)
