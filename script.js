document.addEventListener('DOMContentLoaded', () => {
    const audioUpload = document.getElementById('audioUpload');
    const enhanceButton = document.getElementById('enhanceButton');
    const originalPlayer = document.getElementById('originalPlayer');
    const enhancedPlayer = document.getElementById('enhancedPlayer');
    const downloadButton = document.getElementById('downloadButton');

    const originalPlayerSection = originalPlayer.closest('.player-section');
    const enhancedPlayerSection = enhancedPlayer.closest('.player-section');

    let uploadedFilename = null; // To store the name of the uploaded file

    // Initial states
    function setInitialState() {
        if (originalPlayerSection) {
            originalPlayerSection.style.display = 'none';
        }
        if (enhancedPlayerSection) {
            enhancedPlayerSection.style.display = 'none'; // CSS should also handle this
        }
        if (downloadButton) {
            downloadButton.style.display = 'none'; // CSS should also handle this
            downloadButton.disabled = true;
        }
        if (enhanceButton) {
            enhanceButton.disabled = true; // Disabled until a file is uploaded
        }
        uploadedFilename = null;
        if(audioUpload) audioUpload.value = ''; // Clear file input
        if(originalPlayer) originalPlayer.src = '';
        if(enhancedPlayer) enhancedPlayer.src = '';

    }

    setInitialState(); // Call on page load

    // --- File Upload Logic ---
    if (audioUpload) {
        audioUpload.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (!file) {
                return;
            }

            // Reset UI for new upload
            setInitialState(); 
            // Show original player section once a file is selected for upload
            if (originalPlayerSection) {
                 originalPlayerSection.style.display = 'block';
            }


            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok) {
                    uploadedFilename = result.filename; // Store filename from backend
                    originalPlayer.src = URL.createObjectURL(file); // Display original audio
                    if (originalPlayerSection) {
                        originalPlayerSection.style.display = 'block'; // Ensure it's visible
                    }
                    enhanceButton.disabled = false; // Enable enhance button
                    alert('File uploaded successfully: ' + uploadedFilename);
                } else {
                    alert('Error uploading file: ' + result.error);
                    setInitialState(); // Reset on error
                }
            } catch (error) {
                console.error('Upload error:', error);
                alert('Network error during file upload. Please try again.');
                setInitialState(); // Reset on error
            }
        });
    }

    // --- Enhance Vocals Logic ---
    if (enhanceButton) {
        enhanceButton.addEventListener('click', async () => {
            if (!uploadedFilename) {
                alert('Please upload an audio file first.');
                return;
            }

            enhanceButton.disabled = true; // Disable during processing
            alert('Enhancing audio... please wait.');

            try {
                const response = await fetch('/enhance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ filename: uploadedFilename }),
                });

                const result = await response.json();

                if (response.ok) {
                    enhancedPlayer.src = result.enhanced_file_url;
                    if (enhancedPlayerSection) {
                        enhancedPlayerSection.style.display = 'block';
                    }
                    
                    downloadButton.href = result.enhanced_file_url;
                    // Set the download attribute to suggest a filename to the browser
                    downloadButton.setAttribute('download', result.enhanced_filename || 'enhanced_audio.wav');
                    downloadButton.style.display = 'inline-block'; // Make button visible
                    downloadButton.disabled = false; // Enable download button
                    
                    alert('Audio enhanced successfully! You can now play or download it.');
                } else {
                    alert('Error enhancing audio: ' + result.error);
                     // Keep enhance button enabled if enhancement fails, allowing user to retry
                    enhanceButton.disabled = false;
                }
            } catch (error) {
                console.error('Enhance error:', error);
                alert('Network error during audio enhancement. Please try again.');
                 // Keep enhance button enabled if enhancement fails, allowing user to retry
                enhanceButton.disabled = false;
            }
        });
    }
});
