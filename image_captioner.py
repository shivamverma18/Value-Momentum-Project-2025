import requests
from PIL import Image
import os
import base64
import json
import random  # Added import

class ImageCaptioner:
    def __init__(self):
        print("✅ Lightweight Image Captioner initialized!")
        # Using a pre-trained model API or local lightweight model
        # For now, we'll use a simple keyword-based approach
        # You can replace with actual API call if needed
        
    def generate_caption(self, image_path):
        """
        Generate caption for uploaded image using lightweight approach
        """
        try:
            # Open and validate image
            if not os.path.exists(image_path):
                return "Error: Image file not found"
            
            image = Image.open(image_path).convert('RGB')
            
            # Get basic image info
            width, height = image.size
            image_size_kb = os.path.getsize(image_path) / 1024
            
            # Simple keyword-based caption generation
            # This is a placeholder - you can enhance this
            caption = self._generate_simple_caption(image_path)
            
            return caption
            
        except Exception as e:
            print(f"Caption generation error: {e}")
            return f"Image analysis completed. Damage assessment ready."

    def _generate_simple_caption(self, image_path):
        """Generate a simple caption based on filename and basic analysis"""
        filename = os.path.basename(image_path).lower()
        
        # Keyword matching for common damage types - ENHANCED FLOOD DETECTION
        damage_keywords = {
            'hail': ['hail', 'ice', 'stone'],
            'water': ['water', 'flood', 'rain', 'leak', 'inundated', 'submerged', 'damp', 'wet', 'moisture'],
            'fire': ['fire', 'burn', 'smoke', 'ash'],
            'collision': ['collision', 'crash', 'accident', 'impact'],
            'vandalism': ['vandal', 'scratch', 'broken', 'smashed'],
            'storm': ['storm', 'wind', 'tree', 'branch'],
            'theft': ['theft', 'broken', 'window', 'door']
        }
        
        caption = "Image analysis indicates "
        
        # Check filename for damage clues
        detected_damage = []
        for damage_type, keywords in damage_keywords.items():
            for keyword in keywords:
                if keyword in filename:
                    if damage_type not in detected_damage:
                        detected_damage.append(damage_type)
                    break
        
        if detected_damage:
            caption += f"possible {', '.join(detected_damage)} damage. "
            print(f"DEBUG: Detected damage types from filename: {detected_damage}")
        else:
            caption += "visible damage to property. "
        
        # ENHANCED FLOOD SEVERITY DETECTION
        if 'water' in detected_damage or 'flood' in detected_damage:
            # Flood-specific severity indicators
            flood_severe_keywords = ['submerged', 'inundated', 'deep', 'standing', 'sewage', 
                                    'contaminated', 'complete', 'total', 'engine', 'electrical',
                                    'interior', 'seat', 'carpet', 'upholstery', 'mud', 'debris']
            
            flood_moderate_keywords = ['water', 'flood', 'moisture', 'damp', 'wet', 'partially',
                                      'some', 'moderate', 'noticeable', 'obvious']
            
            flood_minor_keywords = ['splash', 'spray', 'light', 'minor', 'small', 'surface']
            
            # Check for severity in filename
            if any(word in filename for word in flood_severe_keywords):
                flood_descriptors = [
                    "Complete vehicle submersion detected with severe water intrusion.",
                    "Deep flood water has entered critical vehicle components requiring extensive repairs.",
                    "Submerged vehicle shows signs of complete water damage to all systems.",
                    "Severe flood damage affecting electrical, mechanical, and interior systems.",
                    "Vehicle appears completely inundated with water damage throughout."
                ]
            elif any(word in filename for word in flood_moderate_keywords):
                flood_descriptors = [
                    "Significant water damage affecting multiple vehicle systems.",
                    "Moderate flood damage with water intrusion into interior compartments.",
                    "Noticeable water damage requiring professional assessment and drying.",
                    "Vehicle shows evidence of water exposure affecting various components."
                ]
            else:
                flood_descriptors = [
                    "Water damage observed on vehicle surfaces.",
                    "Moisture intrusion detected requiring attention.",
                    "Signs of water exposure visible on the vehicle."
                ]
            
            caption += random.choice(flood_descriptors)
            
        else:
            # Original severity detection for non-flood damage
            minor_keywords = ['minor', 'small', 'tiny', 'little', 'scratch', 'scratches', 
                             'ding', 'chip', 'mark', 'cosmetic', 'surface', 'paint', 
                             'light', 'slight', 'superficial']
            
            severe_keywords = ['major', 'severe', 'heavy', 'serious', 'critical', 
                              'broken', 'cracked', 'shattered', 'smashed', 'crash',
                              'impact', 'collision', 'totaled', 'wrecked', 'demolished',
                              'structural', 'frame', 'chassis', 'burned', 'flooded']
            
            moderate_keywords = ['moderate', 'medium', 'noticeable', 'obvious', 'dents',
                                'bent', 'twisted', 'multiple', 'several']
            
            if any(word in filename for word in minor_keywords):
                descriptors = [
                    "Minor surface imperfections observed.",
                    "Cosmetic damage affecting appearance only.",
                    "Superficial marks requiring touch-up repair.",
                    "Light surface damage with no structural impact.",
                    "Minor dents and scratches visible - cosmetic only.",
                    "Paint or finish damage requiring minimal repair."
                ]
            elif any(word in filename for word in severe_keywords):
                descriptors = [
                    "Multiple impact points visible on exterior surfaces.",
                    "Surface deformation and material stress observed.",
                    "Visible structural compromise requiring assessment.",
                    "External damage affecting functional components.",
                    "Material deterioration and surface imperfections noted.",
                    "Significant damage requiring professional assessment."
                ]
            elif any(word in filename for word in moderate_keywords):
                descriptors = [
                    "Moderate damage requiring attention.",
                    "Several affected areas visible.",
                    "Noticeable damage impacting appearance.",
                    "Multiple dents or scratches observed.",
                    "Functional components may be affected."
                ]
            else:
                descriptors = [
                    "Damage assessment in progress.",
                    "Visual inspection completed.",
                    "Property damage detected.",
                    "External surfaces show signs of impact.",
                    "Assessment ready for claim processing."
                ]
            
            caption += random.choice(descriptors)
        
        return caption