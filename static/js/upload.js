// MindWatch - Upload Page JavaScript

// Global variables
let selectedFile = null;
let dragCounter = 0;

// Initialize upload functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
});

function initializeUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    
    if (!uploadArea || !fileInput) return;
    
    // Setup drag and drop
    setupDragAndDrop(uploadArea);
    
    // Setup file input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Setup form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Setup click handler for upload area
    uploadArea.addEventListener('click', function(e) {
        if (e.target === uploadArea || e.target.closest('.upload-area')) {
            fileInput.click();
        }
    });
}

function setupDragAndDrop(uploadArea) {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    dragCounter++;
    document.getElementById('uploadArea').classList.add('dragover');
}

function unhighlight(e) {
    dragCounter--;
    if (dragCounter === 0) {
        document.getElementById('uploadArea').classList.remove('dragover');
    }
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        handleFiles(files);
    }
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    const file = files[0];
    if (validateFile(file)) {
        selectedFile = file;
        displayFileInfo(file);
        
        // Update file input
        const fileInput = document.getElementById('fileInput');
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFiles(files);
    }
}

function validateFile(file) {
    // Check file size (500MB limit)
    const maxSize = 500 * 1024 * 1024; // 500MB in bytes
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 500MB.');
        return false;
    }
    
    // Check file type
    const allowedVideoTypes = ['mp4', 'avi', 'mov', 'mkv', 'wmv'];
    const allowedImageTypes = ['jpg', 'jpeg', 'png', 'bmp', 'tiff'];
    const allowedTypes = [...allowedVideoTypes, ...allowedImageTypes];
    
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
        showError('Invalid file type. Please upload a video (MP4, AVI, MOV) or image (JPG, PNG) file.');
        return false;
    }
    
    return true;
}

function displayFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    
    if (!fileInfo || !fileName || !fileSize) return;
    
    fileName.textContent = file.name;
    fileSize.textContent = `(${MindWatch.formatFileSize(file.size)})`;
    
    // Determine file type and show appropriate icon
    const isVideo = ['mp4', 'avi', 'mov', 'mkv', 'wmv'].includes(
        file.name.split('.').pop().toLowerCase()
    );
    
    const icon = isVideo ? 'fas fa-video' : 'fas fa-image';
    fileName.innerHTML = `<i class="${icon} me-2"></i>${file.name}`;
    
    fileInfo.style.display = 'block';
    
    // Show file preview if it's an image
    if (!isVideo && file.type.startsWith('image/')) {
        showImagePreview(file);
    }
}

function showImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        // Remove existing preview
        const existingPreview = document.querySelector('.image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        // Create preview
        const preview = document.createElement('div');
        preview.className = 'image-preview mt-3 text-center';
        preview.innerHTML = `
            <img src="${e.target.result}" 
                 alt="Preview" 
                 class="img-thumbnail" 
                 style="max-width: 300px; max-height: 200px;">
            <p class="text-muted mt-2">Preview</p>
        `;
        
        document.getElementById('fileInfo').appendChild(preview);
    };
    reader.readAsDataURL(file);
}

function clearFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    
    // Remove preview
    const existingPreview = document.querySelector('.image-preview');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    // Reset upload area
    document.getElementById('uploadArea').classList.remove('dragover');
}

function handleFormSubmit(e) {
    if (!selectedFile) {
        e.preventDefault();
        showError('Please select a file to upload.');
        return false;
    }
    
    // Show loading state
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        MindWatch.showLoading(submitButton);
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
    }
    
    return true;
}

function showError(message) {
    MindWatch.showNotification(message, 'danger', 5000);
}

function showSuccess(message) {
    MindWatch.showNotification(message, 'success', 3000);
}

// Processing functions (used when in processing state)
function updateProgress(progress) {
    const progressElements = document.querySelectorAll('.progress-text');
    const progressValue = Math.round(progress);
    
    progressElements.forEach(element => {
        element.textContent = progressValue + '%';
    });
    
    // Update all progress circles
    document.querySelectorAll('.progress-circle canvas').forEach(canvas => {
        updateProgressCircle(canvas, progress);
    });
}

function updateProgressCircle(canvas, progress) {
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = (Math.min(canvas.width, canvas.height) / 2) - 10;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw background circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 8;
    ctx.stroke();
    
    // Draw progress arc
    if (progress > 0) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, -Math.PI / 2, (-Math.PI / 2) + (progress / 100) * 2 * Math.PI);
        ctx.strokeStyle = '#007bff';
        ctx.lineWidth = 8;
        ctx.lineCap = 'round';
        ctx.stroke();
    }
}

function updateStatus(status) {
    const statusText = document.getElementById('statusText');
    const statusDetails = document.getElementById('statusDetails');
    
    if (!statusText) return;
    
    const statusMessages = {
        'starting': {
            text: 'Preparing analysis...',
            details: 'Initializing AI model and processing pipeline'
        },
        'analyzing': {
            text: 'Analyzing content...',
            details: 'Detecting student activities and behaviors'
        },
        'generating_report': {
            text: 'Generating report...',
            details: 'Creating comprehensive analysis report'
        },
        'completed': {
            text: 'Analysis complete!',
            details: 'Your results are ready for viewing'
        },
        'error': {
            text: 'Processing failed',
            details: 'An error occurred during processing'
        }
    };
    
    const statusInfo = statusMessages[status] || {
        text: 'Processing...',
        details: 'Please wait while we analyze your file'
    };
    
    statusText.textContent = statusInfo.text;
    if (statusDetails) {
        statusDetails.textContent = statusInfo.details;
    }
    
    // Update overlay if it exists
    const overlayStatusText = document.getElementById('overlayStatusText');
    const overlayStatusDetails = document.getElementById('overlayStatusDetails');
    
    if (overlayStatusText) {
        overlayStatusText.textContent = statusInfo.text;
    }
    if (overlayStatusDetails) {
        overlayStatusDetails.textContent = statusInfo.details;
    }
}

// Progress checking function
function startProgressChecking(sessionId) {
    const checkInterval = setInterval(() => {
        fetch(`/progress/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                updateProgress(data.progress || 0);
                updateStatus(data.status || 'processing');
                
                if (data.status === 'completed') {
                    clearInterval(checkInterval);
                    showSuccess('Analysis completed successfully!');
                    
                    // Redirect to results after a delay
                    setTimeout(() => {
                        window.location.href = '/results';
                    }, 2000);
                } else if (data.status === 'error') {
                    clearInterval(checkInterval);
                    showError(data.error || 'Processing failed. Please try again.');
                    
                    // Show retry button
                    showRetryOption();
                }
            })
            .catch(error => {
                console.error('Progress check error:', error);
                // Continue checking, might be a temporary network issue
            });
    }, 2000); // Check every 2 seconds
    
    // Store interval ID for cleanup
    window.progressInterval = checkInterval;
}

function showRetryOption() {
    const statusText = document.getElementById('statusText');
    const statusDetails = document.getElementById('statusDetails');
    
    if (statusText) {
        statusText.innerHTML = `
            Processing Failed
            <button class="btn btn-primary btn-sm ms-3" onclick="retryProcessing()">
                <i class="fas fa-redo me-2"></i>Retry
            </button>
        `;
    }
    
    if (statusDetails) {
        statusDetails.textContent = 'You can try uploading the file again or contact support if the problem persists.';
    }
}

function retryProcessing() {
    // Clear previous state and redirect to upload
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
    }
    
    window.location.href = '/upload';
}

// File type detection helpers
function getFileType(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const videoExtensions = ['mp4', 'avi', 'mov', 'mkv', 'wmv'];
    const imageExtensions = ['jpg', 'jpeg', 'png', 'bmp', 'tiff'];
    
    if (videoExtensions.includes(extension)) {
        return 'video';
    } else if (imageExtensions.includes(extension)) {
        return 'image';
    } else {
        return 'unknown';
    }
}

function getFileIcon(filename) {
    const type = getFileType(filename);
    return type === 'video' ? 'fas fa-video' : 
           type === 'image' ? 'fas fa-image' : 
           'fas fa-file';
}

// Initialize progress circles on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any existing progress circles
    document.querySelectorAll('.progress-circle canvas').forEach(canvas => {
        updateProgressCircle(canvas, 0);
    });
});

// Cleanup function
window.addEventListener('beforeunload', function() {
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
    }
});

// Export functions for global use
window.UploadManager = {
    validateFile,
    displayFileInfo,
    clearFile,
    updateProgress,
    updateStatus,
    startProgressChecking,
    getFileType,
    getFileIcon
};
