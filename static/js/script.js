// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const fileName = document.getElementById('fileName');
const generateBtn = document.getElementById('generateBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingSection = document.getElementById('loadingSection');
const imageCaption = document.getElementById('imageCaption');
const lossDescription = document.getElementById('lossDescription');
const damageTypeDisplay = document.getElementById('damageTypeDisplay');
const downloadBtn = document.getElementById('downloadBtn');
const downloadPDFBtn = document.getElementById('downloadPDFBtn'); // ADD THIS
const errorAlert = document.getElementById('errorAlert');
const errorMessage = document.getElementById('errorMessage');

// Store result data globally
let currentResultData = null;

// Event Listeners
if (uploadArea) {
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
}

if (generateBtn) {
    generateBtn.addEventListener('click', processImage);
}

if (downloadBtn) {
    downloadBtn.addEventListener('click', downloadDescription);
}

if (downloadPDFBtn) {
    downloadPDFBtn.addEventListener('click', downloadPDF); // ADD THIS
}

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFiles(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFiles(file);
    }
}

function handleFiles(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showError('Please select a valid image file (JPEG, PNG, or GIF)');
        return;
    }
    
    // Validate file size (max 16MB)
    if (file.size > 16 * 1024 * 1024) {
        showError('File size too large. Please select an image smaller than 16MB.');
        return;
    }
    
    // Display file name
    fileName.textContent = file.name;
    
    // Preview image
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        previewContainer.classList.remove('hidden');
        generateBtn.disabled = false;
    };
    reader.readAsDataURL(file);
    
    hideError();
}

async function processImage() {
    const file = fileInput.files[0];
    const damageType = document.getElementById('damageType').value;
    const customDamage = document.getElementById('customDamage').value;
    
    // Get user information from form
    const policyHolderName = document.getElementById('policyHolderName').value || '';
    const contactEmail = document.getElementById('contactEmail').value || '';
    const contactPhone = document.getElementById('contactPhone').value || '';
    const propertyAddress = document.getElementById('propertyAddress').value || '';
    const city = document.getElementById('city').value || '';
    const state = document.getElementById('state').value || '';
    const zipCode = document.getElementById('zipCode').value || '';
    
    if (!file) {
        showError('Please select an image file first.');
        return;
    }
    
    // Show loading state
    showLoading();
    generateBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('damage_type', damageType);
    if (customDamage) {
        formData.append('custom_damage', customDamage);
    }
    
    // Add user information to form data
    formData.append('policy_holder_name', policyHolderName);
    formData.append('contact_email', contactEmail);
    formData.append('contact_phone', contactPhone);
    formData.append('property_address', propertyAddress);
    formData.append('city', city);
    formData.append('state', state);
    formData.append('zip_code', zipCode);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Store the complete result data globally
            currentResultData = data;
            displayResults(data);
        } else {
            showError(data.error || 'An error occurred while processing the image.');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideLoading();
        generateBtn.disabled = false;
    }
}

function displayResults(data) {
    imageCaption.textContent = data.image_caption;
    lossDescription.textContent = data.loss_description;
    damageTypeDisplay.textContent = data.damage_type;
    
    // Display user information in results
    displayUserInformation(data);
    
    // Store data for download
    downloadBtn.setAttribute('data-description', data.loss_description);
    downloadBtn.setAttribute('data-damage-type', data.damage_type);
    
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function displayUserInformation(data) {
    // Create or update user info display section
    let userInfoSection = document.getElementById('userInfoSection');
    if (!userInfoSection) {
        userInfoSection = document.createElement('div');
        userInfoSection.id = 'userInfoSection';
        userInfoSection.className = 'user-info-section';
        userInfoSection.innerHTML = `
            <h3>Claim Information</h3>
            <p><strong>Policy Holder:</strong> <span id="policyHolderDisplay">${data.policy_holder_name || 'Not specified'}</span></p>
            <p><strong>Contact Information:</strong> <span id="contactInfoDisplay">
                ${data.contact_email || ''} ${data.contact_phone || ''}
            </span></p>
            <p><strong>Location:</strong> <span id="locationDisplay">
                ${data.property_address || ''}
                ${data.city ? ', ' + data.city : ''}
                ${data.state ? ', ' + data.state : ''}
                ${data.zip_code ? ' ' + data.zip_code : ''}
            </span></p>
        `;
        
        // Insert after damage type display
        const damageTypeSection = document.querySelector('.damage-type-section');
        if (damageTypeSection) {
            damageTypeSection.after(userInfoSection);
        }
    } else {
        // Update existing display
        document.getElementById('policyHolderDisplay').textContent = data.policy_holder_name || 'Not specified';
        document.getElementById('contactInfoDisplay').textContent = 
            `${data.contact_email || ''} ${data.contact_phone || ''}`.trim() || 'Not provided';
        
        const locationParts = [
            data.property_address,
            data.city,
            data.state,
            data.zip_code
        ].filter(part => part && part.trim());
        
        document.getElementById('locationDisplay').textContent = 
            locationParts.join(', ') || 'Not specified';
    }
}

async function downloadDescription() {
    const description = downloadBtn.getAttribute('data-description');
    const damageType = downloadBtn.getAttribute('data-damage-type');
    
    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                damage_type: damageType
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `loss_description_${damageType.replace(' ', '_')}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            showError('Failed to download file.');
        }
    } catch (error) {
        showError('Download error: ' + error.message);
    }
}

// NEW FUNCTION: Download PDF with all data
async function downloadPDF() {
    if (!currentResultData) {
        showError('No data available. Please generate a description first.');
        return;
    }
    
    try {
        // Prepare all data for PDF generation
        const pdfData = {
            description: currentResultData.loss_description,
            damage_type: currentResultData.damage_type,
            severity_score: currentResultData.severity_score,
            severity_level: currentResultData.severity_level,
            affected_components: currentResultData.affected_components,
            repair_level: currentResultData.repair_level,
            cost_range: currentResultData.cost_range,
            policy_holder_name: currentResultData.policy_holder_name || '',
            contact_info: formatContactInfo(currentResultData.contact_email, currentResultData.contact_phone),
            location: formatLocation(
                currentResultData.property_address,
                currentResultData.city,
                currentResultData.state,
                currentResultData.zip_code
            ),
            image_data: currentResultData.image_data
        };
        
        console.log('Sending PDF data:', pdfData);
        
        const response = await fetch('/download-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(pdfData)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `ClaimInsight_${currentResultData.damage_type.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0,10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            const errorData = await response.json();
            showError('Failed to generate PDF: ' + (errorData.error || 'Unknown error'));
        }
    } catch (error) {
        showError('PDF download error: ' + error.message);
    }
}

// Helper function to format contact info
function formatContactInfo(email, phone) {
    const parts = [];
    if (email) parts.push(email);
    if (phone) parts.push(phone);
    return parts.join(' | ') || 'Not provided';
}

// Helper function to format location
function formatLocation(address, city, state, zipCode) {
    const parts = [];
    if (address) parts.push(address);
    if (city) parts.push(city);
    if (state) parts.push(state);
    if (zipCode) parts.push(zipCode);
    return parts.join(', ') || 'Not specified';
}

function showLoading() {
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

function hideLoading() {
    loadingSection.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorAlert.classList.remove('hidden');
    errorAlert.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    errorAlert.classList.add('hidden');
}

// Custom damage type handling
document.getElementById('damageType').addEventListener('change', function() {
    const customDamageGroup = document.getElementById('customDamageGroup');
    if (this.value === 'Other') {
        customDamageGroup.classList.remove('hidden');
    } else {
        customDamageGroup.classList.add('hidden');
    }
});

// Initialize upload container
function initializeUploadContainer() {
    const uploadContainer = document.getElementById('uploadContainer');
    const imageSection = document.querySelector('.image-section');
    
    // Reset file input
    fileInput.value = '';
    
    // Hide preview and show upload area
    previewContainer.classList.add('hidden');
    imageSection.style.display = 'none';
    
    // Enable upload area
    uploadContainer.style.display = 'flex';
    uploadContainer.style.cursor = 'pointer';
    
    // Reset generate button
    generateBtn.disabled = true;
    
    // Clear any existing results
    resultsSection.classList.add('hidden');
    
    // Clear stored data
    currentResultData = null;
}

// Sidebar functions
function openSidebar() {
    document.getElementById('sidebar').style.right = '0';
}

function closeSidebar() {
    document.getElementById('sidebar').style.right = '-400px';
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Loss Description Generator initialized');
    
    // Add PDF download button if not exists
    if (!document.getElementById('downloadPDFBtn')) {
        const downloadPDFBtn = document.createElement('button');
        downloadPDFBtn.id = 'downloadPDFBtn';
        downloadPDFBtn.className = 'btn btn-primary mt-3';
        downloadPDFBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Download PDF Report';
        
        // Insert after the text download button
        if (downloadBtn && downloadBtn.parentNode) {
            downloadBtn.parentNode.insertBefore(downloadPDFBtn, downloadBtn.nextSibling);
        }
        
        // Add event listener
        downloadPDFBtn.addEventListener('click', downloadPDF);
    }
});