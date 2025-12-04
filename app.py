from flask import Flask, render_template, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from PIL import Image
import os
import tempfile
import uuid
from datetime import datetime
from image_captioner import ImageCaptioner
from description_generator import DescriptionGenerator
import json
import base64
import cv2
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from textwrap import wrap
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-make-it-random'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize models (cached)
captioner = None
desc_generator = None

# Ensure upload and history directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

HISTORY_FILE = 'data/detection_history.json'

# Initialize history file if it doesn't exist
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_models():
    """Initialize models only when needed"""
    global captioner, desc_generator
    if captioner is None or desc_generator is None:
        captioner = ImageCaptioner()
        desc_generator = DescriptionGenerator()
    return captioner, desc_generator

def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def add_to_history(entry):
    history = load_history()
    history.append(entry)
    save_history(history)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/history')
def history():
    history_data = load_history()
    history_data.reverse()  # Show most recent first
    return render_template('history.html', history=history_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        damage_type = request.form.get('damage_type', 'Unknown Damage')
        custom_damage = request.form.get('custom_damage', '')
        
        # New fields from form
        policy_holder_name = request.form.get('policy_holder_name', '')
        contact_email = request.form.get('contact_email', '')
        contact_phone = request.form.get('contact_phone', '')
        property_address = request.form.get('property_address', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        zip_code = request.form.get('zip_code', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            temp_path = os.path.join('uploads', f"{file_id}_{filename}")
            file.save(temp_path)
            
            # Validate image
            try:
                with Image.open(temp_path) as img:
                    img.verify()
            except Exception:
                os.remove(temp_path)
                return jsonify({'error': 'Invalid image file'}), 400
            
            # Load models
            captioner, desc_generator = get_models()
            
            # Process image (captioner might return None or empty string)
            try:
                image_caption = captioner.generate_caption(temp_path)
            except Exception as e:
                print("DEBUG: captioner.generate_caption failed:", str(e))
                image_caption = ""
            
            # Defensive: coerce to string and trim
            image_caption = "" if image_caption is None else str(image_caption).strip()
            
            # If caption is empty or too short, use a light image heuristic fallback
            if not image_caption or len(image_caption) < 6:
                try:
                    img_cv = cv2.imread(temp_path)
                    if img_cv is not None:
                        mean_red = float(img_cv[:, :, 2].mean())
                        mean_gray = float(cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY).mean())
                        if mean_red > (mean_gray * 1.15) and mean_red > 80:
                            image_caption = "visible fire damage, charred surfaces and soot; burned areas and structural charring visible"
                        else:
                            image_caption = "visible property damage; signs of surface damage and debris"
                    else:
                        image_caption = "visible property damage; signs of surface damage and debris"
                except Exception as e:
                    print("DEBUG: fallback image heuristic failed:", str(e))
                    image_caption = "visible property damage; signs of surface damage and debris"
            
            # Use custom damage type if provided
            final_damage_type = custom_damage if custom_damage else damage_type
            
            # Generate description with enhanced features
            try:
                enhanced_data = desc_generator.enhance_description_with_features(
                    image_caption, 
                    final_damage_type,
                    {
                        'policy_holder_name': policy_holder_name,
                        'contact_email': contact_email,
                        'contact_phone': contact_phone,
                        'property_address': property_address,
                        'city': city,
                        'state': state,
                        'zip_code': zip_code
                    }
                )
            except Exception as e:
                print("ERROR: enhance_description_with_features failed:", str(e))
                import traceback
                traceback.print_exc()
                os.remove(temp_path)
                return jsonify({'error': 'Description generation failed', 'details': str(e)}), 500
            
            # Store original image data in base64 format
            image = cv2.imread(temp_path)
            _, buffer = cv2.imencode('.jpg', image)
            image_data = base64.b64encode(buffer).decode('utf-8')
            
            # Create result data with all fields
            result_data = {
                'success': True,
                'image_caption': image_caption,
                'damage_type': final_damage_type,
                'loss_description': enhanced_data['description'],
                'severity_score': enhanced_data['severity_score'],
                'severity_level': enhanced_data['severity_level'],
                'affected_components': enhanced_data['affected_components'],
                'repair_level': enhanced_data['repair_level'],
                'cost_range': enhanced_data['cost_range'],
                'policy_holder_name': policy_holder_name,
                'contact_email': contact_email,
                'contact_phone': contact_phone,
                'property_address': property_address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': filename,
                'image_data': image_data
            }
            
            # Add to history
            history_entry = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'damage_type': final_damage_type,
                'image_caption': image_caption,
                'loss_description': enhanced_data['description'],
                'severity_score': enhanced_data['severity_score'],
                'severity_level': enhanced_data['severity_level'],
                'affected_components': enhanced_data['affected_components'],
                'repair_level': enhanced_data['repair_level'],
                'cost_range': enhanced_data['cost_range'],
                'policy_holder_name': policy_holder_name,
                'contact_email': contact_email,
                'contact_phone': contact_phone,
                'property_address': property_address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'image_data': image_data
            }
            add_to_history(history_entry)
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return jsonify(result_data)
        
        else:
            return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or JPEG.'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

def draw_text_with_wrapping(p, text, x, y, max_width, font_name, font_size, line_spacing=14):
    """Draw text with automatic word wrapping"""
    words = text.split()
    lines = []
    current_line = []
    
    # Calculate available width in points
    p.setFont(font_name, font_size)
    
    for word in words:
        # Check if adding this word would exceed the max width
        test_line = ' '.join(current_line + [word])
        text_width = p.stringWidth(test_line, font_name, font_size)
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw each line
    current_y = y
    for line in lines:
        p.drawString(x, current_y, line)
        current_y -= line_spacing
    
    return current_y  # Return new Y position

def draw_recommendation_item(p, index, title, description, x, y, max_width, font_name, font_size):
    """Draw a single recommendation item with proper wrapping"""
    # Draw the number and title in bold
    title_text = f"{index}. {title}:"
    p.setFont(f"{font_name}-Bold", font_size)
    p.drawString(x, y, title_text)
    
    # Calculate where description should start
    title_width = p.stringWidth(title_text, f"{font_name}-Bold", font_size)
    
    # Draw description with wrapping
    p.setFont(font_name, font_size)
    
    # Wrap the description
    words = description.split()
    lines = []
    current_line = []
    
    # First line starts after title
    available_width = max_width - title_width
    
    # Handle first line specially
    if words:
        # Try to fit as many words as possible on first line
        first_line_words = []
        for word in words:
            test_line = ' '.join(first_line_words + [word])
            if p.stringWidth(test_line, font_name, font_size) <= available_width:
                first_line_words.append(word)
            else:
                break
        
        if first_line_words:
            lines.append(' '.join(first_line_words))
            remaining_words = words[len(first_line_words):]
        else:
            remaining_words = words
        
        # Handle remaining words
        if remaining_words:
            current_line = []
            for word in remaining_words:
                test_line = ' '.join(current_line + [word])
                if p.stringWidth(test_line, font_name, font_size) <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
    else:
        lines.append("")
    
    # Draw each line
    current_y = y
    for i, line in enumerate(lines):
        if i == 0:
            # First line starts after title
            p.drawString(x + title_width, current_y, line)
        else:
            # Subsequent lines are indented
            p.drawString(x + 20, current_y - (i * 14), line)
    
    # Calculate total height used
    height_used = max(20, (len(lines) * 14))
    return y - height_used - 10  # Return new Y position

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Download description as enhanced PDF file with image"""
    try:
        data = request.get_json()
        
        # Extract all data
        description = data.get('description', 'No description available.')
        damage_type = data.get('damage_type', 'Unknown Damage')
        
        # Extract severity score
        severity_score = data.get('severity_score')
        if severity_score is None:
            score_match = re.search(r'Score:\s*(\d+)/100', description)
            if score_match:
                severity_score = int(score_match.group(1))
            else:
                score_match = re.search(r'(\d+)/100', description)
                if score_match:
                    severity_score = int(score_match.group(1))
                else:
                    score_match = re.search(r'AI Severity Score:\s*(\d+)/100', description)
                    if score_match:
                        severity_score = int(score_match.group(1))
                    else:
                        severity_score = 60
        
        # Extract severity level
        severity_level = data.get('severity_level')
        if severity_level is None:
            level_match = re.search(r'\((\w+)\)', description)
            if level_match:
                severity_level = level_match.group(1).lower()
            else:
                if severity_score >= 61:
                    severity_level = 'severe'
                elif severity_score >= 31:
                    severity_level = 'moderate'
                else:
                    severity_level = 'minor'
        
        # Extract affected components
        affected_components = data.get('affected_components')
        if affected_components is None:
            comp_match = re.search(r'Affected Components:\s*([^\n]+)', description)
            if comp_match:
                affected_components = comp_match.group(1).strip()
            else:
                comp_section_match = re.search(r'COMPONENT BREAKDOWN:(.*?)(?:\n\n|\Z)', description, re.DOTALL)
                if comp_section_match:
                    comp_text = comp_section_match.group(1)
                    comp_items = re.findall(r'\d+\.\s*([^\n]+)', comp_text)
                    if comp_items:
                        affected_components = ', '.join(comp_items)
                    else:
                        if 'fire' in damage_type.lower():
                            affected_components = 'Charred surfaces, Soot damage, Heat-affected areas'
                        elif 'flood' in damage_type.lower() or 'water' in damage_type.lower():
                            affected_components = 'Water damage, Moisture intrusion, Mold risk areas'
                        elif 'hail' in damage_type.lower():
                            affected_components = 'Dented panels, Body damage, Paint damage'
                        else:
                            affected_components = 'Body damage, Paint scratches'
                else:
                    if 'fire' in damage_type.lower():
                        affected_components = 'Charred surfaces, Soot damage, Heat-affected areas'
                    elif 'flood' in damage_type.lower() or 'water' in damage_type.lower():
                        affected_components = 'Water damage, Moisture intrusion, Mold risk areas'
                    elif 'hail' in damage_type.lower():
                        affected_components = 'Dented panels, Body damage, Paint damage'
                    else:
                        affected_components = 'Body damage, Paint scratches'
        
        # Extract repair level
        repair_level = data.get('repair_level')
        if repair_level is None:
            repair_match = re.search(r'Repair Complexity:\s*([^\n]+)', description)
            if repair_match:
                repair_level = repair_match.group(1).strip()
            else:
                if severity_level == 'severe':
                    repair_level = 'High (structural or critical)'
                elif severity_level == 'moderate':
                    repair_level = 'Medium (multiple parts)'
                else:
                    repair_level = 'Low (simple repair)'
        
        # Extract cost range
        cost_range = data.get('cost_range')
        if cost_range is None:
            cost_match = re.search(r'Estimated Cost Range:\s*([^\n]+)', description)
            if cost_match:
                cost_range = cost_match.group(1).strip()
            else:
                if severity_level == 'severe':
                    cost_range = '₹40,000 - ₹2,00,000'
                elif severity_level == 'moderate':
                    cost_range = '₹10,000 - ₹40,000'
                else:
                    cost_range = '₹3,000 - ₹10,000'
        
        # Extract other data
        policy_holder_name = data.get('policy_holder_name', '')
        contact_email = data.get('contact_email', '')
        contact_phone = data.get('contact_phone', '')
        property_address = data.get('property_address', '')
        city = data.get('city', '')
        state = data.get('state', '')
        zip_code = data.get('zip_code', '')
        image_data = data.get('image_data', '')
        
        # Ensure description is a string
        if description is None:
            description = 'No description available.'
        else:
            description = str(description)
        
        # Ensure damage_type is a string
        damage_type = str(damage_type) if damage_type else 'Unknown Damage'
        
        # Format contact info
        contact_info = []
        if contact_email:
            contact_info.append(contact_email)
        if contact_phone:
            contact_info.append(contact_phone)
        contact_info = ' | '.join(contact_info) if contact_info else 'To be provided by claimant'
        
        # Format location info
        location_parts = []
        if property_address:
            location_parts.append(property_address)
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        if zip_code:
            location_parts.append(zip_code)
        location_info = ', '.join(location_parts) if location_parts else 'To be provided by claimant'
        
        # Clean up empty values
        if not policy_holder_name or policy_holder_name == 'Not specified':
            policy_holder_name = 'To be provided by claimant'
        
        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Set up colors
        primary_color = (0/255, 119/255, 182/255)  # Blue
        accent_color = (72/255, 202/255, 228/255)  # Light Blue
        success_color = (76/255, 175/255, 80/255)  # Green
        warning_color = (255/255, 152/255, 0/255)  # Orange
        danger_color = (244/255, 67/255, 54/255)  # Red
        
        # Set severity color based on level
        if severity_level == 'severe':
            severity_color = danger_color
        elif severity_level == 'moderate':
            severity_color = warning_color
        else:
            severity_color = success_color
        
        # ========== PAGE 1: COVER PAGE ==========
        
        # 1. HEADER WITH BACKGROUND
        p.setFillColorRGB(*primary_color)
        p.rect(0, height-120, width, 120, fill=1, stroke=0)
        
        # Logo/Title
        p.setFillColorRGB(1, 1, 1)
        p.setFont("Helvetica-Bold", 28)
        p.drawCentredString(width/2, height-60, "CLAIM INSIGHT")
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height-85, "AI-Powered Insurance Claim Assessment Report")
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, height-100, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        
        # 2. DAMAGE IMAGE SECTION (if available)
        y = height - 180
        
        if image_data and image_data.strip():
            try:
                # Add image title
                p.setFillColorRGB(*primary_color)
                p.setFont("Helvetica-Bold", 16)
                p.drawString(50, y, "DAMAGE IMAGE")
                y -= 20
                
                # Decode and add image
                img_data = base64.b64decode(image_data)
                img_file = BytesIO(img_data)
                
                # Use PIL to get image dimensions
                from PIL import Image as PILImage
                img = PILImage.open(img_file)
                img_width, img_height = img.size
                
                # Calculate dimensions to fit (max 400x300)
                max_width = 400
                max_height = 250
                aspect = img_width / img_height
                
                if aspect > max_width/max_height:
                    display_width = max_width
                    display_height = display_width / aspect
                else:
                    display_height = max_height
                    display_width = display_height * aspect
                
                # Center the image
                x_position = (width - display_width) / 2
                
                # Reset file pointer
                img_file.seek(0)
                p.drawImage(ImageReader(img_file), x_position, y-display_height, 
                          width=display_width, height=display_height)
                y -= display_height + 30
                
            except Exception as e:
                print(f"Error adding image to PDF: {e}")
                # Add placeholder if image fails
                p.setFillColorRGB(0.9, 0.9, 0.9)
                p.rect(50, y-150, width-100, 150, fill=1, stroke=0)
                p.setFillColorRGB(0.6, 0.6, 0.6)
                p.setFont("Helvetica", 12)
                p.drawCentredString(width/2, y-80, "Damage Image")
                p.drawCentredString(width/2, y-100, "(Image not available in PDF)")
                y -= 180
        else:
            # No image available
            p.setFillColorRGB(0.9, 0.9, 0.9)
            p.rect(50, y-150, width-100, 150, fill=1, stroke=0)
            p.setFillColorRGB(0.6, 0.6, 0.6)
            p.setFont("Helvetica", 12)
            p.drawCentredString(width/2, y-80, "Damage Image")
            p.drawCentredString(width/2, y-100, "(Image reference available in system)")
            y -= 180
        
        # 3. EXECUTIVE SUMMARY BOX
        summary_box_height = 120
        p.setFillColorRGB(0.95, 0.95, 0.95)
        p.rect(50, y-summary_box_height, width-100, summary_box_height, fill=1, stroke=0)
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(70, y-30, "EXECUTIVE SUMMARY")
        
        summary_y = y - 50
        
        # Summary details
        summary_items = [
            ("Damage Type:", damage_type),
            ("Severity Level:", f"{severity_level.upper()} ({severity_score}/100)"),
            ("Estimated Cost Range:", cost_range),
            ("Report Status:", "READY FOR CLAIM PROCESSING")
        ]
        
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 10)
        for label, value in summary_items:
            p.setFont("Helvetica-Bold", 10)
            p.drawString(70, summary_y, label)
            p.setFont("Helvetica", 10)
            p.drawString(180, summary_y, value)
            summary_y -= 20
        
        # 4. QUICK RESPONSE RECOMMENDATION
        summary_y -= 20
        p.setFillColorRGB(*severity_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, summary_y, "RECOMMENDED ACTION:")
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 10)
        
        if severity_level == 'severe':
            action = "IMMEDIATE PROFESSIONAL INTERVENTION REQUIRED - Contact repair services within 24 hours"
        elif severity_level == 'moderate':
            action = "SCHEDULE PROFESSIONAL ASSESSMENT - Arrange inspection within 7 days"
        else:
            action = "ROUTINE REPAIR SCHEDULING - Plan repairs at convenience"
        
        # Draw action with wrapping
        summary_y = draw_text_with_wrapping(p, action, 50, summary_y - 15, width-100, "Helvetica", 10)
        
        # Footer for page 1
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.setFont("Helvetica", 8)
        p.drawString(50, 30, "Page 1 of 3 - Confidential Insurance Document")
        p.drawString(width-150, 30, "ClaimInsight AI System")
        
        # ========== PAGE 2: DETAILED ASSESSMENT ==========
        p.showPage()
        
        # Page 2 Header
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width/2, height-50, "DETAILED ASSESSMENT REPORT")
        p.setFillColorRGB(0.3, 0.3, 0.3)
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, height-70, f"Claim Reference: CI-{datetime.now().strftime('%Y%m%d%H%M')}")
        
        y = height - 100
        
        # 1. CLAIM INFORMATION SECTION
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "1. CLAIM INFORMATION")
        y -= 25
        
        claim_info = [
            ("Policy Holder:", policy_holder_name),
            ("Contact Information:", contact_info),
            ("Incident Location:", location_info),
            ("Date of Assessment:", datetime.now().strftime('%B %d, %Y')),
            ("Assessment ID:", f"CI-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        ]
        
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 10)
        for label, value in claim_info:
            p.setFont("Helvetica-Bold", 10)
            p.drawString(70, y, label)
            p.setFont("Helvetica", 10)
            
            # Draw value with wrapping
            y = draw_text_with_wrapping(p, str(value), 200, y, width-250, "Helvetica", 10, 14)
            
            y -= 8
        
        y -= 10
        
        # 2. DAMAGE ASSESSMENT SECTION
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "2. DAMAGE ASSESSMENT SUMMARY")
        y -= 25
        
        # Severity indicator with color box
        p.setFillColorRGB(*severity_color)
        p.roundRect(70, y-5, 150, 20, 5, fill=1, stroke=0)
        p.setFillColorRGB(1, 1, 1)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(75, y, f"{severity_level.upper()} DAMAGE")
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 10)
        p.drawString(230, y, f"Score: {severity_score}/100")
        y -= 35
        
        assessment_details = [
            ("Damage Type:", damage_type),
            ("Affected Components:", affected_components),
            ("Repair Complexity:", repair_level),
            ("Estimated Cost Range:", cost_range)
        ]
        
        for label, value in assessment_details:
            p.setFont("Helvetica-Bold", 10)
            p.drawString(70, y, label)
            p.setFont("Helvetica", 10)
            
            # Draw value with wrapping
            y = draw_text_with_wrapping(p, str(value), 200, y, width-250, "Helvetica", 10, 14)
            
            y -= 8
        
        y -= 20
        
        # 3. DETAILED ANALYSIS SECTION
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "3. DETAILED ANALYSIS")
        y -= 30
        
        # Clean and parse description
        clean_description = str(description).replace('\r\n', '\n').replace('\r', '\n')
        
        # Find DETAILED ANALYSIS section
        if "DETAILED ANALYSIS:" in clean_description:
            analysis_start = clean_description.find("DETAILED ANALYSIS:")
            analysis_end = clean_description.find("COMPONENT BREAKDOWN:", analysis_start)
            if analysis_end == -1:
                analysis_end = clean_description.find("RECOMMENDATIONS:", analysis_start)
            
            if analysis_end == -1:
                analysis_text = clean_description[analysis_start + len("DETAILED ANALYSIS:"):].strip()
            else:
                analysis_text = clean_description[analysis_start + len("DETAILED ANALYSIS:"):analysis_end].strip()
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in analysis_text.split('\n\n') if p.strip()]
            
            p.setFillColorRGB(0, 0, 0)
            p.setFont("Helvetica", 10)
            
            for paragraph in paragraphs:
                # Draw paragraph with wrapping
                y = draw_text_with_wrapping(p, paragraph, 70, y, width-140, "Helvetica", 10, 14)
                y -= 10  # Space between paragraphs
        
        y -= 20
        
        # 4. COMPONENT BREAKDOWN SECTION
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "4. COMPONENT BREAKDOWN")
        y -= 25
        
        if "COMPONENT BREAKDOWN:" in clean_description:
            comp_start = clean_description.find("COMPONENT BREAKDOWN:")
            comp_end = clean_description.find("RECOMMENDATIONS:", comp_start)
            
            if comp_end == -1:
                comp_text = clean_description[comp_start + len("COMPONENT BREAKDOWN:"):].strip()
            else:
                comp_text = clean_description[comp_start + len("COMPONENT BREAKDOWN:"):comp_end].strip()
            
            # Split into lines
            comp_lines = [line.strip() for line in comp_text.split('\n') if line.strip()]
            
            p.setFillColorRGB(0, 0, 0)
            p.setFont("Helvetica", 10)
            
            for line in comp_lines:
                # Check if line is numbered
                if re.match(r'^\d+\.', line):
                    # Draw numbered item
                    p.drawString(70, y, line)
                else:
                    # Draw regular line
                    y = draw_text_with_wrapping(p, line, 70, y, width-140, "Helvetica", 10, 14)
                y -= 15
        
        # Footer for page 2
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.setFont("Helvetica", 8)
        p.drawString(50, 30, "Page 2 of 3 - Confidential Insurance Document")
        p.drawString(width-150, 30, "ClaimInsight AI System")
        
        # ========== PAGE 3: RECOMMENDATIONS ==========
        p.showPage()
        
        # Page 3 Header
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width/2, height-50, "RECOMMENDATIONS & COST ESTIMATE")
        p.setFillColorRGB(0.3, 0.3, 0.3)
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, height-70, f"Claim Reference: CI-{datetime.now().strftime('%Y%m%d%H%M')}")
        
        y = height - 100
        
        # # RECOMMENDATIONS SECTION
        # p.setFillColorRGB(*primary_color)
        # p.setFont("Helvetica-Bold", 16)
        # p.drawString(50, y, "RECOMMENDATIONS")
        # y -= 25
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "RECOMMENDATIONS:")
        y -= 20
        
        # Extract recommendations from description
        if "RECOMMENDATIONS:" in clean_description:
            rec_start = clean_description.find("RECOMMENDATIONS:")
            cost_start = clean_description.find("COST ESTIMATE GUIDANCE:", rec_start)
            
            if cost_start == -1:
                rec_text = clean_description[rec_start + len("RECOMMENDATIONS:"):].strip()
            else:
                rec_text = clean_description[rec_start + len("RECOMMENDATIONS:"):cost_start].strip()
            
            # Split into lines
            rec_lines = [line.strip() for line in rec_text.split('\n') if line.strip()]
            
            # Draw each recommendation with proper wrapping
            for i, line in enumerate(rec_lines, 1):
                if ':' in line:
                    # Split title and description
                    title_part, desc_part = line.split(':', 1)
                    title = title_part.strip()
                    description = desc_part.strip()
                    
                    # Draw with wrapping
                    y = draw_recommendation_item(p, i, title, description, 70, y, width-140, "Helvetica", 10)
                else:
                    # Draw as-is
                    p.setFont("Helvetica", 10)
                    p.drawString(70, y, line)
                    y -= 20
                
                # Check if we need a new page
                if y < 150:
                    p.showPage()
                    y = height - 50
                    p.setFillColorRGB(0, 0, 0)
        
        y -= 30
        
        # # COST ESTIMATE SECTION
        # p.setFillColorRGB(*primary_color)
        # p.setFont("Helvetica-Bold", 16)
        # p.drawString(50, y, "COST ESTIMATE GUIDANCE")
        # y -= 25
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "COST ESTIMATE GUIDANCE:")
        y -= 20
        
        # Extract cost estimate
        if "COST ESTIMATE GUIDANCE:" in clean_description:
            cost_start = clean_description.find("COST ESTIMATE GUIDANCE:")
            
            if cost_start != -1:
                cost_text = clean_description[cost_start + len("COST ESTIMATE GUIDANCE:"):].strip()
                
                # Split into lines
                cost_lines = [line.strip() for line in cost_text.split('\n') if line.strip()]
                
                p.setFillColorRGB(0, 0, 0)
                p.setFont("Helvetica", 10)
                
                for line in cost_lines:
                    if line.startswith('**') and line.endswith('**'):
                        # Bold text (cost range)
                        p.setFont("Helvetica-Bold", 14)
                        p.drawCentredString(width/2, y, line.strip('*'))
                        p.setFont("Helvetica", 10)
                        y -= 25
                    elif line.startswith('- ') or line.startswith('• '):
                        # Bullet point
                        p.drawString(70, y, line)
                        y -= 15
                    elif line.lower().startswith('note:'):
                        # Note text
                        p.setFont("Helvetica-Oblique", 9)
                        y = draw_text_with_wrapping(p, line, 70, y, width-140, "Helvetica-Oblique", 9, 12)
                        p.setFont("Helvetica", 10)
                        y -= 10
                    else:
                        # Regular text
                        y = draw_text_with_wrapping(p, line, 70, y, width-140, "Helvetica", 10, 14)
                        y -= 5
                    
                    # Check if we need a new page
                    if y < 100:
                        p.showPage()
                        y = height - 50
                        p.setFillColorRGB(0, 0, 0)
                        p.setFont("Helvetica", 10)
        
        # Final disclaimer
        y = max(y, 120)  # Ensure we have space
        y -= 20
        
        p.setFillColorRGB(0.7, 0.7, 0.7)
        p.setFont("Helvetica", 8)
        p.drawString(50, y, "="*100)
        y -= 20
        
        disclaimer_lines = [
            "IMPORTANT DISCLAIMER:",
            "This report is generated by ClaimInsight AI Assessment System and is for preliminary assessment purposes only.",
            "The estimated costs are approximate and may vary based on actual repair requirements, labor rates, and parts availability.",
            "A physical inspection by a certified professional is recommended for accurate assessment and claim processing."
        ]
        
        for line in disclaimer_lines:
            p.drawCentredString(width/2, y, line)
            y -= 12
        
        # Footer for page 3
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.setFont("Helvetica", 8)
        p.drawString(50, 30, "Page 3 of 3 - Confidential Insurance Document")
        p.drawString(width-150, 30, "ClaimInsight AI System")

        # Save PDF
        p.save()

        buffer.seek(0)
        
        # Create a better filename
        timestamp_str = datetime.now().strftime('%Y%m%dT%H%M%S')
        safe_damage_type = damage_type.replace(' ', '_')
        filename = f"ClaimInsight_{safe_damage_type}_{timestamp_str}.pdf"
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    except Exception as e:
        print("PDF generation error:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"error": "PDF generation failed", "details": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask app on http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)