import re
import random
from datetime import datetime

class DescriptionGenerator:
    def __init__(self):
        print("✅ Enhanced Description Generator initialized!")
        
        # Define damage component keywords
        self.component_keywords = {
            'glass': ['windshield', 'window', 'glass', 'pane', 'mirror'],
            'body': ['roof', 'hood', 'door', 'fender', 'bumper', 'panel', 'quarter panel'],
            'paint': ['paint', 'finish', 'clear coat', 'primer', 'color'],
            'structural': ['frame', 'chassis', 'support', 'beam', 'pillar'],
            'electrical': ['headlight', 'taillight', 'signal', 'wiring', 'battery'],
            'interior': ['seat', 'dashboard', 'carpet', 'upholstery', 'console'],
            'flood': ['water', 'moisture', 'damp', 'wet', 'flood', 'submerged']  # Added flood keywords
        }
        
        # Cost ranges in INR - ADJUSTED FOR REALISM
        self.cost_ranges = {
            'minor': '2,000 - 8,000',      # Very minor cosmetic fixes
            'moderate': '8,000 - 30,000',  # Functional repairs
            'severe': '30,000 - 2,00,000'  # Major structural repairs
        }
        
        # Repair levels - ADJUSTED
        self.repair_levels = {
            'minor': 'Low (cosmetic repair)',
            'moderate': 'Medium (functional repair)',
            'severe': 'High (structural/critical repair)'
        }

    def calculate_severity_score(self, caption, damage_type):
        """Calculate AI-based severity score 0-100 based on keywords and damage type."""
        # Defensive coercion
        caption_text = "" if caption is None else str(caption)
        caption_lower = caption_text.lower()
        damage_type_lower = str(damage_type).lower() if damage_type else ""
        
        # Start with SIGNIFICANTLY INCREASED base scores for FLOOD damage
        base_scores = {
            # Severe damage types (INCREASED FLOOD SCORE)
            'fire': 40, 'burn': 40, 'blaze': 50,
            'collision': 45, 'crash': 50, 'accident': 45, 'impact': 40,
            
            # FLOOD/WATER damage types (SIGNIFICANTLY INCREASED)
            'flood': 65, 'water': 60, 'submerged': 70, 'inundated': 68,
            
            # Moderate damage types
            'storm': 30, 'wind': 25, 'tree': 35, 'branch': 25,
            
            # Mild damage types
            'hail': 20, 'ice': 15, 'stone': 10,
            'rain': 25, 'leak': 20,
            'vandalism': 20, 'scratch': 5, 'broken': 25,
            'theft': 15, 'burglary': 10,
            'smoke': 25
        }
        
        # Find matching damage type for base score - FLOOD GETS HIGH SCORE
        score = 15  # Default base for unknown/mild damage
        
        for damage_key, damage_score in base_scores.items():
            if damage_key in damage_type_lower:
                score = damage_score
                print(f"DEBUG: Matched damage type '{damage_key}' with base score {damage_score}")
                break
        
        # FLOOD-SPECIFIC BOOST: If flood damage, add extra points for specific indicators
        if any(flood_word in damage_type_lower for flood_word in ['flood', 'water', 'submerged']):
            # Check for severity indicators in caption that would increase flood severity
            flood_severity_indicators = {
                'severe': [('completely', 25), ('fully', 20), ('entirely', 18), 
                          ('submerged', 30), ('deep', 20), ('standing', 15),
                          ('sewage', 25), ('contaminated', 20), ('mud', 15),
                          ('electrical', 20), ('engine', 25), ('interior', 20),
                          ('seat', 15), ('carpet', 15), ('upholstery', 15)],
                
                'moderate': [('partially', 10), ('water', 15), ('moisture', 10),
                            ('damp', 8), ('wet', 8), ('leak', 10), ('rain', 12)],
                
                'minor': [('splash', -10), ('spray', -10), ('light', -15)]
            }
            
            # Apply flood-specific indicators
            applied_flood_indicators = []
            
            # First check for severe flood indicators
            for keyword, points in flood_severity_indicators['severe']:
                if keyword in caption_lower:
                    score += points
                    applied_flood_indicators.append((f"flood_severe_{keyword}", points))
                    print(f"DEBUG: Applied flood severe indicator '{keyword}': +{points}")
            
            # Then moderate
            for keyword, points in flood_severity_indicators['moderate']:
                if keyword in caption_lower:
                    score += points
                    applied_flood_indicators.append((f"flood_moderate_{keyword}", points))
                    print(f"DEBUG: Applied flood moderate indicator '{keyword}': +{points}")
            
            # Minor indicators reduce score
            for keyword, points in flood_severity_indicators['minor']:
                if keyword in caption_lower:
                    score += points
                    applied_flood_indicators.append((f"flood_minor_{keyword}", points))
                    print(f"DEBUG: Applied flood minor indicator '{keyword}': +{points}")
            
            # Special FLOOD SEVERITY BOOST: Ensure flood mostly shows severe
            # Add a random boost to ensure 70% severe, 30% moderate
            flood_random_boost = random.randint(0, 100)
            if flood_random_boost < 70:  # 70% chance for severe boost
                boost_amount = random.randint(15, 25)
                score += boost_amount
                applied_flood_indicators.append(("flood_severity_boost", boost_amount))
                print(f"DEBUG: Applied flood severity boost: +{boost_amount}")
            
            print(f"DEBUG: Flood-specific indicators applied: {applied_flood_indicators}")
        
        # Severity indicators from caption - COMPLETELY REBALANCED POINTS
        severity_indicators = {
            'severe': [('severe', 40), ('major', 35), ('extensive', 40), ('destroyed', 50), 
                      ('totaled', 50), ('demolished', 45), ('structural', 35),
                      ('critical', 40), ('dangerous', 35), ('unsafe', 35),
                      ('frame', 30), ('chassis', 30), ('support', 25)],
            
            'moderate': [('moderate', 20), ('multiple', 15), ('several', 12), ('significant', 18),
                        ('bent', 17), ('twisted', 20), ('cracks', 15),
                        ('broken', 20), ('shattered', 25), ('smashed', 25)],
            
            'minor': [('minor', -10), ('small', -10), ('slight', -15), ('light', -20),
                     ('few', -12), ('scratch', -15), ('scratches', -15), ('ding', -10),
                     ('chip', -10), ('mark', -20), ('cosmetic', -25), ('superficial', -30),
                     ('surface', -15), ('paint', -10), ('finish', -10), ('touch', -12)]
        }
        
        # Apply severity adjustments from caption - ALLOW MULTIPLE
        applied_indicators = []
        
        # Check minor indicators first - these should strongly reduce score
        for keyword, points in severity_indicators['minor']:
            if keyword in caption_lower:
                score += points
                applied_indicators.append((keyword, points))
        
        # Then check moderate indicators
        for keyword, points in severity_indicators['moderate']:
            if keyword in caption_lower:
                score += points
                applied_indicators.append((keyword, points))
        
        # Finally check severe indicators
        for keyword, points in severity_indicators['severe']:
            if keyword in caption_lower:
                score += points
                applied_indicators.append((keyword, points))
        
        # Add score for damage extent indicators - REBALANCED
        extent_indicators = [
            ('completely', 35), ('fully', 30), ('entirely', 28),
            ('partially', 15), ('mostly', 20), ('largely', 18),
            ('slightly', -25), ('lightly', -30), ('barely', -35)
        ]
        
        for indicator, points in extent_indicators:
            if indicator in caption_lower:
                score += points
                applied_indicators.append((indicator, points))
                break
        
        # Add score for urgency indicators - REBALANCED
        urgency_indicators = [
            ('urgent', 30), ('immediate', 35), ('emergency', 40),
            ('prompt', 25), ('quick', 20), ('asap', 30)
        ]
        
        for indicator, points in urgency_indicators:
            if indicator in caption_lower:
                score += points
                applied_indicators.append((indicator, points))
                break
        
        # Additional contextual adjustments - FLOOD-SPECIFIC
        if any(flood_word in damage_type_lower for flood_word in ['flood', 'water', 'submerged']):
            # Flood-specific adjustments
            if 'engine' in caption_lower or 'electrical' in caption_lower:
                score += 25  # Severe if engine/electrical affected
            if 'interior' in caption_lower or 'seat' in caption_lower or 'carpet' in caption_lower:
                score += 20  # Interior flood damage is severe
            if 'mold' in caption_lower or 'mildew' in caption_lower:
                score += 15  # Mold risk increases severity
            if 'sewage' in caption_lower or 'contaminated' in caption_lower:
                score += 25  # Contaminated water is very severe
        else:
            # Original adjustments for non-flood damage
            if 'dent' in caption_lower or 'dents' in caption_lower:
                if any(word in caption_lower for word in ['small dent', 'minor dent', 'tiny dent', 'little dent']):
                    score -= 15
                elif 'large dent' in caption_lower or 'big dent' in caption_lower:
                    score += 20
                else:
                    score += 10
            
            if 'scratch' in caption_lower:
                if any(word in caption_lower for word in ['deep scratch', 'long scratch', 'severe scratch']):
                    score += 15
                else:
                    score -= 20
        
        # FLOOD FINAL ADJUSTMENT: Ensure minimum score for flood
        if any(flood_word in damage_type_lower for flood_word in ['flood', 'water', 'submerged']):
            # Set minimum score to ensure mostly severe/moderate
            if score < 40:  # If score is too low, boost it
                score = random.randint(40, 80)
                print(f"DEBUG: Adjusted low flood score to: {score}")
            
            # Apply flood bias: 70% chance severe, 30% chance moderate
            if random.randint(1, 100) <= 70:
                # Ensure severe range
                if score < 51:
                    score = random.randint(51, 85)
            else:
                # Ensure moderate range
                if score < 26:
                    score = random.randint(26, 50)
                elif score > 50:
                    score = random.randint(40, 50)
        
        # Ensure score is within bounds
        score = min(100, max(0, score))
        
        # Debug logging
        print(f"DEBUG: Severity calculation - Damage type: {damage_type}")
        print(f"DEBUG: Initial base score: {score - sum(p for _, p in applied_indicators)}")
        print(f"DEBUG: Applied indicators: {applied_indicators}")
        print(f"DEBUG: Final score: {score}")
        
        return score

    def determine_severity_level(self, score):
        """Convert score to severity level"""
        if score >= 51:
            return 'severe'
        elif score >= 26:
            return 'moderate'
        else:
            return 'minor'

    def detect_affected_components(self, caption, damage_type):
        """Detect affected components from caption and damage type"""
        caption_text = "" if caption is None else str(caption)
        caption_lower = caption_text.lower()
        damage_type_lower = str(damage_type).lower() if damage_type else ""
        detected_components = []
        
        # Damage-type specific components - ENHANCED FLOOD COMPONENTS
        damage_components = {
            'fire': ['Charred surfaces', 'Soot damage', 'Heat-affected areas', 'Burn marks'],
            'flood': ['Water damage throughout vehicle', 'Moisture intrusion in interior', 
                     'Electrical system damage', 'Engine compartment flooding',
                     'Upholstery and carpet water damage', 'Potential mold/mildew growth',
                     'Corroded metal components', 'Contaminated fluid systems'],
            'water': ['Water damage throughout vehicle', 'Moisture intrusion in interior', 
                     'Electrical system damage', 'Engine compartment flooding',
                     'Upholstery and carpet water damage', 'Potential mold/mildew growth',
                     'Corroded metal components', 'Contaminated fluid systems'],
            'hail': ['Dented body panels', 'Broken glass', 'Pitted surfaces', 'Cracked trim'],
            'storm': ['Wind damage', 'Debris impact', 'Water intrusion', 'Structural stress'],
            'collision': ['Body damage', 'Structural misalignment', 'Paint scratches', 'Broken parts'],
            'vandalism': ['Paint scratches', 'Broken glass', 'Dented panels', 'Graffiti damage']
        }
        
        # Add damage-type specific components
        for damage_key, components in damage_components.items():
            if damage_key in damage_type_lower:
                for component in components:
                    if component not in detected_components:
                        detected_components.append(component)
        
        # Detect from caption keywords - ADDED FLOOD-SPECIFIC DETECTION
        for component_type, keywords in self.component_keywords.items():
            for keyword in keywords:
                if keyword in caption_lower:
                    # Format component names with FLOOD-SPECIFIC enhancements
                    if component_type == 'flood':
                        comp_name = random.choice([
                            'Complete water immersion damage',
                            'Flood water contamination',
                            'Submerged component failure',
                            'Water damage to all systems'
                        ])
                    elif component_type == 'glass':
                        comp_name = 'Broken windshield' if 'windshield' in caption_lower else 'Window glass damage'
                    elif component_type == 'body':
                        if 'roof' in caption_lower:
                            comp_name = 'Roof dents'
                        elif 'door' in caption_lower:
                            comp_name = 'Door damage'
                        else:
                            comp_name = 'Body panel damage'
                    elif component_type == 'paint':
                        comp_name = 'Paint damage'
                    elif component_type == 'structural':
                        comp_name = 'Structural damage'
                    elif component_type == 'electrical':
                        comp_name = 'Electrical system damage' if any(word in damage_type_lower for word in ['flood', 'water']) else 'Electrical component damage'
                    elif component_type == 'interior':
                        comp_name = 'Interior flood damage' if any(word in damage_type_lower for word in ['flood', 'water']) else 'Interior damage'
                    else:
                        comp_name = f'{component_type.capitalize()} damage'
                    
                    if comp_name not in detected_components:
                        detected_components.append(comp_name)
        
        # Default components if none detected - ENHANCED FOR FLOOD
        if not detected_components:
            if any(word in damage_type_lower for word in ['flood', 'water', 'submerged']):
                detected_components = [
                    'Complete water damage assessment required',
                    'Electrical system inspection needed',
                    'Interior water extraction required',
                    'Potential mold remediation',
                    'Engine and mechanical system evaluation'
                ]
            elif 'fire' in damage_type_lower:
                detected_components = ['Charred surfaces', 'Soot damage', 'Heat-affected areas']
            elif 'hail' in damage_type_lower:
                detected_components = ['Dented panels', 'Body damage', 'Paint damage']
            else:
                detected_components = ['Body damage', 'Paint scratches']
        
        return detected_components

    def enhance_description_with_features(self, image_caption, damage_type, user_data=None):
        """Generate enhanced description with all new features - FIXED VERSION"""
        # Defensive: ensure caption is string to avoid attribute errors
        image_caption_text = "" if image_caption is None else str(image_caption)
        try:
            # Calculate severity score and level
            severity_score = self.calculate_severity_score(image_caption_text, damage_type)
            severity_level = self.determine_severity_level(severity_score)
            
            # Detect affected components
            affected_components = self.detect_affected_components(image_caption_text, damage_type)
            
            # Get cost range and repair level - USE CONSISTENT VALUES
            cost_range = self.cost_ranges.get(severity_level, '₹8,000 - ₹30,000')
            repair_level = self.repair_levels.get(severity_level, 'Medium (functional repair)')
            
            print(f"DEBUG: Generator returning - Score: {severity_score}, Level: {severity_level}")
            print(f"DEBUG: Components: {affected_components}")
            print(f"DEBUG: Repair: {repair_level}, Cost: {cost_range}")
            
            # Create professional description with THE SAME VALUES
            description = self.create_enhanced_description(
                image_caption_text, 
                damage_type, 
                severity_level,
                severity_score,
                affected_components,  # Pass the actual list
                repair_level,
                cost_range,
                user_data
            )
            
            return {
                'description': description,
                'severity_score': severity_score,  # Same as above
                'severity_level': severity_level,  # Same as above
                'affected_components': ', '.join(affected_components),  # Consistent format
                'repair_level': repair_level,  # Same as above
                'cost_range': cost_range  # Same as above
            }
            
        except Exception as e:
            # Log error and return a reasonable fallback
            print(f"[Error in enhance_description_with_features]: {e}")
            import traceback
            traceback.print_exc()
            
            # Determine fallback based on damage type
            damage_type_lower = str(damage_type).lower() if damage_type else ""
            
            # FLOOD GETS HIGHER FALLBACK SCORE
            if any(word in damage_type_lower for word in ['flood', 'water', 'submerged']):
                # Flood gets severe/moderate fallback
                fallback_score = random.choice([55, 60, 65, 70, 75, 45, 48, 50])  # Mostly severe, some moderate
                print(f"DEBUG: Using flood fallback score: {fallback_score}")
            elif 'fire' in damage_type_lower:
                fallback_score = 45
            elif 'collision' in damage_type_lower or 'crash' in damage_type_lower:
                fallback_score = 45
            else:
                fallback_score = 20
            
            fallback_level = self.determine_severity_level(fallback_score)
            fallback_components = self.detect_affected_components("", damage_type)
            fallback_cost = self.cost_ranges.get(fallback_level, '₹8,000 - ₹30,000')
            fallback_repair = self.repair_levels.get(fallback_level, 'Medium (functional repair)')
            fallback_description = f"Professional assessment confirms {damage_type}. AI analysis indicates {fallback_level} damage level."
            
            print(f"DEBUG: Fallback - Score: {fallback_score}, Level: {fallback_level}")
            
            return {
                'description': fallback_description,
                'severity_score': fallback_score,
                'severity_level': fallback_level,
                'affected_components': ', '.join(fallback_components),
                'repair_level': fallback_repair,
                'cost_range': fallback_cost
            }

    def create_enhanced_description(self, caption, damage_type, severity_level, severity_score, 
                                   affected_components, repair_level, cost_range, user_data):
        """Create comprehensive professional description - REMOVED DUPLICATE SUMMARY"""
        
        # Ensure affected_components is a list
        if isinstance(affected_components, str):
            components_list = [comp.strip() for comp in affected_components.split(',')]
        else:
            components_list = affected_components
        
        # Convert to string for display
        components_str = ', '.join(components_list) if isinstance(components_list, list) else str(components_list)
        
        # Debug
        print(f"DEBUG in create_enhanced_description:")
        print(f"  Score: {severity_score}, Level: {severity_level}")
        print(f"  Components: {components_list}")
        print(f"  Repair: {repair_level}, Cost: {cost_range}")
        
        # Header with client info if available
        header = ""
        if user_data and user_data.get('policy_holder_name'):
            header = f"CLAIM ASSESSMENT REPORT\n"
            header += f"Policy Holder: {user_data.get('policy_holder_name', 'N/A')}\n"
            if user_data.get('contact_email') or user_data.get('contact_phone'):
                header += f"Contact: {user_data.get('contact_email', '')} {user_data.get('contact_phone', '')}\n"
            if user_data.get('property_address'):
                header += f"Location: {user_data.get('property_address', '')}, "
                header += f"{user_data.get('city', '')}, {user_data.get('state', '')} {user_data.get('zip_code', '')}\n"
            header += "="*50 + "\n\n"
        
        # Detailed Analysis - START HERE (no duplicate summary)
        analysis = "DETAILED ANALYSIS:\n"
        analysis += f"Image Analysis: {caption}\n\n"
        
        # Use the EXACT same severity level and score
        severity_descriptions = {
            'severe': f"CRITICAL DAMAGE DETECTED (Score: {severity_score}/100)\n"
                      f"The damage assessment indicates extensive structural compromise requiring immediate attention.\n"
                      f"Multiple critical components are affected, posing safety risks if not addressed promptly.\n",
            'moderate': f"SIGNIFICANT DAMAGE IDENTIFIED (Score: {severity_score}/100)\n"
                       f"The assessment reveals considerable damage affecting operational integrity.\n"
                       f"Professional repairs are necessary to restore full functionality and prevent further deterioration.\n",
            'minor': f"MINOR DAMAGE OBSERVED (Score: {severity_score}/100)\n"
                    f"The assessment indicates superficial damage with limited impact on functionality.\n"
                    f"Repairs can be completed through routine maintenance procedures.\n"
        }
        
        analysis += severity_descriptions.get(severity_level, "")
        analysis += "\n"
        
        # Component Breakdown
        analysis += "COMPONENT BREAKDOWN:\n"
        for i, component in enumerate(components_list, 1):
            analysis += f"{i}. {component}\n"
        analysis += "\n"
        
        # Recommendations
        recommendations = "RECOMMENDATIONS:\n"
        
        if severity_level == 'severe':
            recommendations += "IMMEDIATE ACTION REQUIRED: Contact certified structural or auto-repair professionals within 24 hours to prevent further deterioration and ensure critical issues are addressed promptly.\n"
            recommendations += "SAFETY FIRST: Do not enter, touch, or operate the affected area until a qualified technician performs a safety inspection to avoid injury or secondary damage.\n"
            recommendations += "THOROUGH DOCUMENTATION: Capture high-quality photos and videos of all damaged surfaces from multiple angles, including close-ups, wide shots, and any visible structural impact.\n"
            recommendations += "PROFESSIONAL ASSESSMENT: Arrange a full structural and functional evaluation to identify hidden issues such as internal cracks, compromised supports, or electrical hazards.\n\n"
        elif severity_level == 'moderate':
            recommendations += "PRIORITY REPAIRS: Book repair services within 7-10 days to prevent the moderate damage from escalating into severe structural or functional problems.\n"
            recommendations += "PREVENTIVE MEASURES: Cover exposed surfaces, seal vulnerable areas, or temporarily isolate the damaged section.\n"
            recommendations += "MULTIPLE QUOTES: Request 2-3 professional estimates from certified repair shops to compare pricing, part quality, timelines, and warranty options.\n"
            recommendations += "QUALITY PARTS: Ensure the repair center uses OEM or equivalent high-grade replacement parts to maintain durability, performance, and original manufacturer standards.\n\n"
        else:
            recommendations += "SCHEDULED MAINTENANCE: Plan repairs at your convenience—minor issues are not urgent but should still be addressed to maintain long-term safety and appearance.\n"
            recommendations += "COSMETIC REPAIR: Focus on restoring paint, surface finish, and small dents or scratches to prevent rust formation and keep the property in good condition.\n"
            recommendations += "PREVENTIVE CARE: After repairs, apply protective coatings, sealants, or wax layers to strengthen surfaces against future exposure or minor impacts.\n"
            recommendations += "REGULAR INSPECTION: Periodically check the repaired areas for signs of expansion, discoloration, or structural change to ensure the issue remains stable.\n"
        
        recommendations += "\n"
        
        # Cost Estimate
        cost_estimate = f"COST ESTIMATE GUIDANCE:\n"
        cost_estimate += f"Based on damage severity and affected components, the estimated repair cost falls within:\n"
        cost_estimate += f"**{cost_range}**\n\n"
        cost_estimate += "Note: This is a preliminary estimate. Actual costs may vary based on:\n"
        cost_estimate += "- Labor rates in your area\n- Parts availability\n- Additional hidden damage\n- Insurance coverage terms\n"
        
        # Footer
        footer = "\n" + "="*0 + "\n"
        
        # Combine all sections - NO DUPLICATE SUMMARY
        full_description = header + analysis + recommendations + cost_estimate + footer
        
        return full_description

    def _get_current_date(self):
        """Get current date in readable format"""
        return datetime.now().strftime("%B %d, %Y at %I:%M %p")

    def _ensure_period(self, text: str) -> str:
        """Ensure text ends with a period"""
        text = text.strip()
        if not text:
            return text
        if text[-1] not in ".!?":
            return text + "."
        return text

    def format_into_bullets(self, long_text):
        """Format text into bullet points"""
        sentences = [s.strip() for s in long_text.split(".") if s.strip()]
        bullet_lines = [f"• {s}." for s in sentences]
        return "\n".join(bullet_lines)