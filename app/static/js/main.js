document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const videoInput = document.getElementById('videoInput');
    const uploadButton = document.getElementById('uploadButton');
    const testVideoButton = document.getElementById('testVideoButton');
    let selectedFile = null;
    let currentStreamUrl = null;

    if (testVideoButton) {
        testVideoButton.addEventListener('click', () => {
            selectedFile = null;
            showVideo('/process-test-video');
        });
    }

    function showProcessingScreen() {
        fetch('/processing')
            .then(response => response.text())
            .then(html => {
                document.querySelector('.form-container').innerHTML = html;
                attachProcessingEventListeners();
            })
            .catch(error => console.error('Error loading processing screen:', error));
    }

    function attachProcessingEventListeners() {
        const cancelButton = document.getElementById('cancelButton');
        const processButton = document.getElementById('processButton');

        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                selectedFile = null;
                resetInterface();
            });
        }

        if (processButton) {
            processButton.addEventListener('click', () => {
                const url = '/upload-video';
                if (selectedFile) {
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    fetch(url, { method: 'POST', body: formData })
                        .then(response => {
                            if (response.ok) {
                                showVideo(url);
                            } else {
                                console.error('Failed to upload video:', response.status);
                            }
                        })
                        .catch(error => console.error('Error uploading video:', error));
                }
            });
        }
    }

    function showVideo(url) {
        const videoContainer = document.getElementById('videoContainer');
        const videoOutput = document.getElementById('videoOutput');
        const closeButton = document.getElementById('closeVideoButton');

        // Clear previous stream
        if (currentStreamUrl) {
            videoOutput.src = '';
        }

        // Calculate available space and set video size
        const containerWidth = document.querySelector('.container').offsetWidth;
        const formWidth = document.querySelector('.form-container').offsetWidth;
        const availableWidth = "auto !important";
        videoOutput.style.maxWidth = `${50}%`;

        videoContainer.style.position = 'absolute';
        videoContainer.style.transform = 'translateY(35%)'; // Center vertically

        videoContainer.style.top = '0'; // Ensure video is on top

        videoContainer.classList.remove('hidden');
        closeButton.classList.remove('hidden');
        currentStreamUrl = url + '?t=' + new Date().getTime();
        videoOutput.src = currentStreamUrl;

        // Attach close button event
        closeButton.onclick = () => {
            videoOutput.src = '';
            currentStreamUrl = null;
            videoContainer.classList.add('hidden');
            closeButton.classList.add('hidden');
        };
    }

    function resetInterface() {
        const videoContainer = document.getElementById('videoContainer');
        const videoOutput = document.getElementById('videoOutput');
        const closeButton = document.getElementById('closeVideoButton');
        videoOutput.src = '';
        currentStreamUrl = null;
        // videoContainer.classList.add('hidden');
        // closeButton.classList.add('hidden');
        fetch('/')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                document.querySelector('.form-container').innerHTML = doc.querySelector('.form-container').innerHTML;
            });
    }
});