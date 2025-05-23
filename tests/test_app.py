import os
import shutil
import pytest
import wave # For creating a dummy WAV file
import numpy as np
import soundfile as sf # For verifying the created WAV file's properties

# Add the project root to sys.path to allow importing app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app # Import the Flask app instance

# Define paths relative to this test file
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_UPLOADS_DIR = os.path.join(TESTS_DIR, '..', 'temp_uploads') # Should match app.py
PROCESSED_AUDIO_DIR = os.path.join(TESTS_DIR, '..', 'processed_audio') # Should match app.py
TEST_AUDIO_FILENAME = 'test_audio.wav'
TEST_AUDIO_FILEPATH = os.path.join(TESTS_DIR, TEST_AUDIO_FILENAME)
DISALLOWED_TEST_FILENAME = 'test_file.txt'
DISALLOWED_TEST_FILEPATH = os.path.join(TESTS_DIR, DISALLOWED_TEST_FILENAME)


def create_dummy_wav(filepath, duration=0.1, freq=440, sample_rate=44100):
    """Creates a simple dummy WAV file for testing."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = 0.5 * np.sin(2 * np.pi * freq * t)
    # Ensure data is in 16-bit PCM format
    audio_data_int16 = (audio_data * 32767).astype(np.int16)
    
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit (2 bytes)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data_int16.tobytes())
    
    # Verify with soundfile that it's readable
    try:
        data, sr = sf.read(filepath)
        assert sr == sample_rate
        assert len(data) > 0
    except Exception as e:
        print(f"Error creating or verifying dummy WAV: {e}")
        raise


class TestApp:
    @classmethod
    def setup_class(cls):
        """Create necessary files for the test class."""
        os.makedirs(TESTS_DIR, exist_ok=True)
        create_dummy_wav(TEST_AUDIO_FILEPATH)
        with open(DISALLOWED_TEST_FILEPATH, 'w') as f:
            f.write("This is not an audio file.")

    @classmethod
    def teardown_class(cls):
        """Remove files created for the test class."""
        if os.path.exists(TEST_AUDIO_FILEPATH):
            os.remove(TEST_AUDIO_FILEPATH)
        if os.path.exists(DISALLOWED_TEST_FILEPATH):
            os.remove(DISALLOWED_TEST_FILEPATH)

    def setup_method(self):
        """Setup test client and directories for each test."""
        self.app = flask_app.test_client()
        self.app.testing = True # Enable testing mode for Flask

        # Ensure clean directories
        if os.path.exists(TEMP_UPLOADS_DIR):
            shutil.rmtree(TEMP_UPLOADS_DIR)
        if os.path.exists(PROCESSED_AUDIO_DIR):
            shutil.rmtree(PROCESSED_AUDIO_DIR)
        
        os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)
        os.makedirs(PROCESSED_AUDIO_DIR, exist_ok=True)
        
        # Re-initialize app.config paths for safety, though Flask should handle this
        # with app context if paths are relative to app.root_path.
        # The app itself uses absolute paths now for static_folder, so this is less critical here.
        flask_app.config['UPLOAD_FOLDER'] = TEMP_UPLOADS_DIR
        flask_app.config['PROCESSED_FOLDER'] = PROCESSED_AUDIO_DIR


    def teardown_method(self):
        """Clean up directories after each test."""
        if os.path.exists(TEMP_UPLOADS_DIR):
            shutil.rmtree(TEMP_UPLOADS_DIR)
        if os.path.exists(PROCESSED_AUDIO_DIR):
            shutil.rmtree(PROCESSED_AUDIO_DIR)

    # --- /upload Endpoint Tests ---
    def test_upload_success(self):
        with open(TEST_AUDIO_FILEPATH, 'rb') as audio_file:
            data = {'file': (audio_file, TEST_AUDIO_FILENAME)}
            response = self.app.post('/upload', data=data, content_type='multipart/form-data')
        
        json_data = response.get_json()
        assert response.status_code == 200
        assert json_data['message'] == "File uploaded successfully"
        assert json_data['filename'] == TEST_AUDIO_FILENAME
        assert os.path.exists(os.path.join(TEMP_UPLOADS_DIR, TEST_AUDIO_FILENAME))

    def test_upload_no_file_part(self):
        # No 'file' key in the data
        response = self.app.post('/upload', data={}, content_type='multipart/form-data')
        json_data = response.get_json()
        assert response.status_code == 400
        assert "No file part" in json_data['error']

    def test_upload_no_selected_file(self):
        # 'file' key present, but no actual file (empty filename)
        data = {'file': (None, '')} # This simulates an empty file submission
        response = self.app.post('/upload', data=data, content_type='multipart/form-data')
        json_data = response.get_json()
        assert response.status_code == 400
        assert "No selected file" in json_data['error']
        
    def test_upload_disallowed_file_type(self):
        with open(DISALLOWED_TEST_FILEPATH, 'rb') as txt_file:
            data = {'file': (txt_file, DISALLOWED_TEST_FILENAME)}
            response = self.app.post('/upload', data=data, content_type='multipart/form-data')
        
        json_data = response.get_json()
        assert response.status_code == 400
        assert "File type not allowed" in json_data['error']
        assert not os.path.exists(os.path.join(TEMP_UPLOADS_DIR, DISALLOWED_TEST_FILENAME))

    # --- /enhance Endpoint Tests ---
    def test_enhance_success(self):
        # 1. Upload the file first
        with open(TEST_AUDIO_FILEPATH, 'rb') as audio_file:
            upload_data = {'file': (audio_file, TEST_AUDIO_FILENAME)}
            upload_response = self.app.post('/upload', data=upload_data, content_type='multipart/form-data')
        assert upload_response.status_code == 200
        uploaded_filename = upload_response.get_json()['filename']

        # 2. Call /enhance
        enhance_payload = {'filename': uploaded_filename}
        response = self.app.post('/enhance', json=enhance_payload)
        
        json_data = response.get_json()
        assert response.status_code == 200
        assert json_data['message'] == "Audio enhanced successfully"
        assert 'enhanced_filename' in json_data
        assert json_data['enhanced_filename'].startswith('enhanced_')
        assert json_data['enhanced_filename'].endswith('.wav') # Ensure it's WAV
        
        enhanced_filepath = os.path.join(PROCESSED_AUDIO_DIR, json_data['enhanced_filename'])
        assert os.path.exists(enhanced_filepath)
        
        # Check if the enhanced file is a valid audio file and has content
        try:
            data, sr = sf.read(enhanced_filepath)
            assert len(data) > 0 # Basic check that it's not empty
        except Exception as e:
            pytest.fail(f"Enhanced file is not a valid audio file or is empty: {e}")


    def test_enhance_file_not_found_in_temp(self):
        # Try to enhance a file that wasn't uploaded
        enhance_payload = {'filename': 'non_existent_audio.wav'}
        response = self.app.post('/enhance', json=enhance_payload)
        
        json_data = response.get_json()
        assert response.status_code == 404 # Or as per your app's error for this
        assert "Original file not found" in json_data['error']

    def test_enhance_missing_filename_payload(self):
        response = self.app.post('/enhance', json={}) # Empty JSON payload
        json_data = response.get_json()
        assert response.status_code == 400
        assert "Missing filename in JSON payload" in json_data['error']

    # --- Static File Serving Test ---
    def test_serve_enhanced_file(self):
        # 1. Upload and Enhance
        with open(TEST_AUDIO_FILEPATH, 'rb') as audio_file:
            upload_data = {'file': (audio_file, TEST_AUDIO_FILENAME)}
            self.app.post('/upload', data=upload_data, content_type='multipart/form-data')
        
        enhance_payload = {'filename': TEST_AUDIO_FILENAME}
        enhance_response = self.app.post('/enhance', json=enhance_payload)
        enhanced_file_url = enhance_response.get_json()['enhanced_file_url']

        # 2. Try to GET the served file
        # The URL from response will be like /processed_audio/enhanced_test_audio.wav
        # The test client handles the base URL (localhost)
        serve_response = self.app.get(enhanced_file_url)
        assert serve_response.status_code == 200
        assert serve_response.content_length > 0 
        # Check if content type indicates an audio file (might be generic for WAV like 'audio/wav' or 'application/octet-stream')
        assert 'audio' in serve_response.content_type or 'octet-stream' in serve_response.content_type
        
        # Verify filename in Content-Disposition
        assert 'filename=' in serve_response.headers.get('Content-Disposition', '')
        assert enhance_response.get_json()['enhanced_filename'] in serve_response.headers.get('Content-Disposition', '')

    def test_enhance_disallowed_file_type_indirectly(self):
        # Simulate a disallowed file being somehow placed in temp_uploads
        # and then an attempt to enhance it.
        # This tests the allowed_file check within the /enhance route itself.
        disallowed_temp_filepath = os.path.join(TEMP_UPLOADS_DIR, DISALLOWED_TEST_FILENAME)
        with open(DISALLOWED_TEST_FILEPATH, 'r') as src, open(disallowed_temp_filepath, 'w') as dst:
            dst.write(src.read()) # "Copy" the disallowed file to temp_uploads

        enhance_payload = {'filename': DISALLOWED_TEST_FILENAME}
        response = self.app.post('/enhance', json=enhance_payload)
        
        json_data = response.get_json()
        assert response.status_code == 400 
        assert "Invalid filename or disallowed type" in json_data['error']
        
    def test_upload_filename_security(self):
        # Test secure_filename behavior (though it's part of Werkzeug)
        malicious_filename = "../../../etc/passwd.wav" 
        # This is a basic check; secure_filename will sanitize it.
        # The goal is to ensure the app doesn't try to use raw, unsafe paths.
        expected_sanitized_filename = "etc_passwd.wav" # Werkzeug's secure_filename behavior

        with open(TEST_AUDIO_FILEPATH, 'rb') as audio_file:
            data = {'file': (audio_file, malicious_filename)}
            response = self.app.post('/upload', data=data, content_type='multipart/form-data')
        
        json_data = response.get_json()
        assert response.status_code == 200
        assert json_data['filename'] == expected_sanitized_filename
        assert os.path.exists(os.path.join(TEMP_UPLOADS_DIR, expected_sanitized_filename))
        assert not os.path.exists(os.path.join(TEMP_UPLOADS_DIR, malicious_filename)) # Should not create this path
        assert not os.path.exists(os.path.abspath(os.path.join(TEMP_UPLOADS_DIR, malicious_filename))) # Double check absolute
