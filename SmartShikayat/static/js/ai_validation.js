// Mobile Image Upload Optimization with Compression
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.querySelector('input[type="file"][accept="image/*"]');
    
    if (imageInput) {
        imageInput.addEventListener('change', handleImageUpload);
    }
    
    // Initialize AI feedback buttons
    initializeAIFeedback();
});

async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Show processing indicator
    showProcessingIndicator('Optimizing image...');
    
    try {
        // Compress image for mobile
        const compressedFile = await compressImage(file);
        
        // Show preview
        showImagePreview(compressedFile);
        
        // Update file input with compressed image
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(compressedFile);
        event.target.files = dataTransfer.files;
        
        hideProcessingIndicator();
        
        // Show compression info
        showCompressionInfo(file.size, compressedFile.size);
    } catch (error) {
        console.error('Image compression error:', error);
        hideProcessingIndicator();
    }
}

function compressImage(file, maxWidth = 1920, maxHeight = 1080, quality = 0.8) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const img = new Image();
            
            img.onload = function() {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                // Calculate new dimensions
                if (width > maxWidth || height > maxHeight) {
                    const ratio = Math.min(maxWidth / width, maxHeight / height);
                    width = width * ratio;
                    height = height * ratio;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(function(blob) {
                    const compressedFile = new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    });
                    resolve(compressedFile);
                }, 'image/jpeg', quality);
            };
            
            img.onerror = reject;
            img.src = e.target.result;
        };
        
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function showImagePreview(file) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        let preview = document.getElementById('image-preview');
        
        if (!preview) {
            preview = document.createElement('img');
            preview.id = 'image-preview';
            preview.className = 'image-preview';
            
            const container = document.querySelector('.image-upload-container') || 
                            document.querySelector('input[type="file"]').parentElement;
            container.appendChild(preview);
        }
        
        preview.src = e.target.result;
    };
    
    reader.readAsDataURL(file);
}

function showCompressionInfo(originalSize, compressedSize) {
    const reduction = ((1 - compressedSize / originalSize) * 100).toFixed(1);
    
    let infoDiv = document.getElementById('compression-info');
    
    if (!infoDiv) {
        infoDiv = document.createElement('div');
        infoDiv.id = 'compression-info';
        infoDiv.className = 'image-compression-notice';
        
        const container = document.querySelector('.image-upload-container') || 
                        document.querySelector('input[type="file"]').parentElement;
        container.appendChild(infoDiv);
    }
    
    infoDiv.innerHTML = `
        📸 Image optimized: ${formatBytes(originalSize)} → ${formatBytes(compressedSize)} 
        (${reduction}% smaller)
    `;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showProcessingIndicator(message) {
    let indicator = document.getElementById('ai-processing-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'ai-processing-indicator';
        indicator.className = 'ai-processing';
        document.body.appendChild(indicator);
    }
    
    indicator.innerHTML = `
        <div class="ai-processing-spinner"></div>
        <div class="ai-processing-text">${message}</div>
    `;
    indicator.style.display = 'flex';
}

function hideProcessingIndicator() {
    const indicator = document.getElementById('ai-processing-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// AI Feedback System
function initializeAIFeedback() {
    const feedbackButtons = document.querySelectorAll('.ai-feedback-btn');
    
    feedbackButtons.forEach(button => {
        button.addEventListener('click', function() {
            const feedbackType = this.dataset.feedback;
            const complaintId = this.dataset.complaintId;
            
            // Visual feedback
            feedbackButtons.forEach(btn => btn.classList.remove('selected'));
            this.classList.add('selected');
            
            // Submit feedback
            submitAIFeedback(complaintId, feedbackType);
        });
    });
}

async function submitAIFeedback(complaintId, feedbackType) {
    try {
        const response = await fetch('/complaints/ai-feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                complaint_id: complaintId,
                feedback_type: feedbackType
            })
        });
        
        if (response.ok) {
            showFeedbackSuccess();
        } else {
            showFeedbackError();
        }
    } catch (error) {
        console.error('Feedback submission error:', error);
        showFeedbackError();
    }
}

function showFeedbackSuccess() {
    const message = document.createElement('div');
    message.className = 'alert alert-success';
    message.textContent = '✅ Thank you for your feedback! This helps improve our AI.';
    message.style.position = 'fixed';
    message.style.top = '20px';
    message.style.right = '20px';
    message.style.zIndex = '9999';
    message.style.padding = '15px 20px';
    message.style.borderRadius = '8px';
    message.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    
    document.body.appendChild(message);
    
    setTimeout(() => {
        message.remove();
    }, 3000);
}

function showFeedbackError() {
    const message = document.createElement('div');
    message.className = 'alert alert-danger';
    message.textContent = '❌ Failed to submit feedback. Please try again.';
    message.style.position = 'fixed';
    message.style.top = '20px';
    message.style.right = '20px';
    message.style.zIndex = '9999';
    message.style.padding = '15px 20px';
    message.style.borderRadius = '8px';
    
    document.body.appendChild(message);
    
    setTimeout(() => {
        message.remove();
    }, 3000);
}

// Confidence Score Animation
function animateConfidenceScore(element, targetValue) {
    const duration = 1000;
    const startValue = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = startValue + (targetValue - startValue) * easeOutCubic(progress);
        
        element.style.width = currentValue + '%';
        element.textContent = Math.round(currentValue) + '%';
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize confidence score animations on page load
window.addEventListener('load', function() {
    const confidenceBars = document.querySelectorAll('.confidence-bar-fill');
    
    confidenceBars.forEach(bar => {
        const targetValue = parseFloat(bar.dataset.confidence || 0);
        animateConfidenceScore(bar, targetValue);
    });
});
