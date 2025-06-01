from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
import re
import os
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Initialize Flask app
app = Flask(__name__)

# Global variables for spaCy (will try to import if available)
SPACY_AVAILABLE = False
nlp = None

# Try to load spaCy for advanced NLP
try:
    import spacy
    from spacy.matcher import Matcher
    from spacy.util import filter_spans
    
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
        print("✅ spaCy English model loaded successfully")
    except OSError:
        SPACY_AVAILABLE = False
        print("⚠️ spaCy English model not found. Using regex fallback.")
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ spaCy not available. Using regex fallback.")

# Enhanced NLP Entity Extraction Engine
class AdvancedNLPEntityExtractor:
    def __init__(self):
        self.spacy_available = SPACY_AVAILABLE
        if self.spacy_available:
            self.nlp = nlp
            self.matcher = Matcher(self.nlp.vocab)
            self._setup_spacy_patterns()

        # Enhanced VLAN patterns
        self.vlan_patterns = [
            r'vlan\s+id\s+(\d+)',           # VLAN ID 101
            r'vlan-tag\s+(\d+)',            # VLAN-TAG 101
            r'vlan\s+identifier\s+(\d+)',   # VLAN Identifier 110
            r'vlan\s+tag\s+(\d+)',          # VLAN TAG 110
            r'vlan\s+(\d+)',                # VLAN 100
            r'identifier\s+(\d+)',          # Identifier 110
            r'tag\s+(\d+)',                 # TAG 110
        ]

        # Enhanced multiple line patterns
        self.line_patterns = [
            r'line\s*number\s*(\d+)',       # "line number 10"
            r'for\s+line\s*number\s*(\d+)', # "for line number 10"
            r'line\s*(\d+)',                # Line4, Line10, etc.
            r'on\s+line\s*(\d+)',          # on Line4
            r'for\s+line\s*(\d+)',         # for line 10
            r'per\s+line\s*(\d+)',         # per line 1
        ]

        # Enhanced multiple line detection
        self.multiple_line_patterns = [
            r'line\s+(\d+)\s+and\s+line\s+(\d+)',  # "line 1 and line 2"
            r'line\s+(\d+)(?:\s*,\s*line\s+(\d+))*(?:\s+and\s+line\s+(\d+))?',  # "line 4, line 8, line 12 and line 16"
            r'any\s+(\d+)\s+lines?',  # "any 2 lines"
        ]

        # Service count patterns with better group handling
        self.service_count_patterns = [
            {
                'pattern': r'(?:configure\s+)?(\d+)\s+services?\s+per\s+line\s+(\d+)',
                'groups': ['service_count', 'line_num']
            },
            {
                'pattern': r'(?:configure\s+)?(\d+)\s+services?\s+of\s+type\s+(1:1|n:1)\s+per\s+line\s+(\d+)',
                'groups': ['service_count', 'service_type', 'line_num']
            },
            {
                'pattern': r'(?:create\s+)?(?:three|3)\s+(1:1|n:1)\s+services?\s+for\s+line\s+(\d+)',
                'groups': ['service_type', 'line_num'],
                'service_count': 3
            },
            {
                'pattern': r'(?:create\s+)?(?:three|3)\s+services?\s+(?:of\s+type\s+)?(1:1|n:1)\s+(?:for\s+)?line\s+(\d+)',
                'groups': ['service_type', 'line_num'],
                'service_count': 3
            },
            {
                'pattern': r'(?:create\s+)?(?:three|3)\s+(n:1|1:1)\s+services?\s+for\s+line\s+(\d+)\s+and\s+line\s+(\d+)',
                'groups': ['service_type', 'line_num1', 'line_num2'],
                'service_count': 3
            },
        ]

        # All lines detection patterns
        self.all_lines_patterns = [
            r'all\s+16\s+lines',            # "all 16 lines"
            r'all\s+lines',                 # "all lines"
            r'all\s+(?:the\s+)?lines',     # "all the lines"
            r'every\s+line',                # "every line"
            r'for\s+all\s+lines',          # "for all lines"
            r'(?:all\s+)?sixteen\s+lines', # "sixteen lines"
        ]

        self.pbit_patterns = [
            r'pbit\s+(\d+)',
            r'p-bit\s+(\d+)',
            r'priority\s+(?:bit\s+)?(\d+)',
            r'all\s+pbit',                  # "all Pbit" -> 0-7
            r'different\s+pbit',            # "different pbit" -> unique per service
        ]

        self.forwarder_patterns = [
            r'(1:1)\s+forwarder',
            r'(n:1)\s+forwarder',
            r'forwarder\s+(1:1|n:1)',
            r'type\s+(1:1|n:1)',
            r'of\s+type\s+(1:1|n:1)',
        ]

        # Enhanced protocol patterns
        self.protocol_patterns = [
            r'ipv6|internet\s+protocol\s+version\s+6|v6\s+traffic',
            r'pppoe|ppp\s+over\s+ethernet|ppp\s+traffic',
        ]

        # VLAN translation patterns - CASE INSENSITIVE
        self.vlan_translation_patterns = [
            r'with\s+vlan\s+translation',
            r'without\s+vlan\s+translation',
            r'vlan\s+translation',
        ]

        # Enhanced untagged patterns - CASE INSENSITIVE
        self.untagged_patterns = [
            r'untagged\s+(?:vlan|traffic)',
            r'untagged.*?vlan.*?id',
            r'vlan.*?untagged',
            r'no\s+vlan',
            r'untagged',
            r'valn',  # Handle typo "Valn" instead of "VLAN"
            r'untagged\s+valn',  # Handle "untagged Valn ID"
        ]

        # Enhanced discretization patterns
        self.discretization_patterns = [
            r'(?:first|initial)\s+(\d+)\s+lines?.*?(1:1|n:1).*?(?:remaining|rest|next|last).*?lines?.*?(1:1|n:1)',
            r'(\d+)\s+lines?.*?(1:1|n:1).*?(?:remaining|rest|next|last).*?lines?.*?(1:1|n:1)',
            r'(1:1|n:1)\s+forwarder.*?(?:first|initial)\s+(\d+)\s+lines?.*?(?:and|,).*?(1:1|n:1)\s+forwarder.*?(?:remaining|rest)',
        ]

    def _setup_spacy_patterns(self):
        """Setup spaCy patterns for entity recognition"""
        if not self.spacy_available:
            return

        # Enhanced spaCy patterns
        vlan_patterns = [
            [{"LOWER": "vlan"}, {"IS_DIGIT": True}],
            [{"LOWER": "vlan"}, {"LOWER": "id"}, {"IS_DIGIT": True}],
            [{"LOWER": "vlan"}, {"LOWER": "identifier"}, {"IS_DIGIT": True}],
            [{"LOWER": "vlan"}, {"LOWER": "tag"}, {"IS_DIGIT": True}],
            [{"LOWER": "vlan-tag"}, {"IS_DIGIT": True}],
            [{"LOWER": "identifier"}, {"IS_DIGIT": True}],
            [{"LOWER": "tag"}, {"IS_DIGIT": True}],
        ]

        line_patterns = [
            [{"LOWER": "line"}, {"IS_DIGIT": True}],
            [{"LOWER": "line"}, {"LOWER": "number"}, {"IS_DIGIT": True}],
            [{"LOWER": "on"}, {"LOWER": "line"}, {"IS_DIGIT": True}],
            [{"LOWER": "for"}, {"LOWER": "line"}, {"IS_DIGIT": True}],
            [{"LOWER": "per"}, {"LOWER": "line"}, {"IS_DIGIT": True}],
        ]

        service_patterns = [
            [{"IS_DIGIT": True}, {"LOWER": "services"}, {"LOWER": "per"}, {"LOWER": "line"}, {"IS_DIGIT": True}],
            [{"IS_DIGIT": True}, {"LOWER": "service"}, {"LOWER": "per"}, {"LOWER": "line"}, {"IS_DIGIT": True}],
            [{"LOWER": "three"}, {"LOWER": "services"}],
        ]

        pbit_patterns = [
            [{"LOWER": "pbit"}, {"IS_DIGIT": True}],
            [{"LOWER": "p-bit"}, {"IS_DIGIT": True}],
            [{"LOWER": "priority"}, {"LOWER": "bit"}, {"IS_DIGIT": True}],
            [{"LOWER": "all"}, {"LOWER": "pbit"}],
        ]

        # Add patterns to matcher
        self.matcher.add("VLAN", vlan_patterns)
        self.matcher.add("LINE", line_patterns)
        self.matcher.add("SERVICE", service_patterns)
        self.matcher.add("PBIT", pbit_patterns)

    def extract_comprehensive_entities(self, text: str) -> Dict[str, Any]:
        """Extract all entities with enhanced logic"""
        text_clean = self._preprocess_text(text)

        entities = {
            'user_vlans': [],
            'network_vlans': [],
            'lines': [],
            'line_forwarder_map': {},
            'uplinks': [1],
            'user_pbits': [],
            'network_pbits': [],
            'forwarder_type': 'N:1',
            'protocols': [],
            'is_untagged': False,
            'is_multi_line': False,
            'is_all_lines': False,
            'discretization_config': {},
            'traffic_directions': ['bidirectional'],
            'mixed_forwarders': {},
            'line_specific_vlans': {},
            'line_specific_pbits': {},
            'has_vlan_translation': None,
            # Enhanced service support
            'is_multi_service': False,
            'service_count': 0,
            'service_type': None,
            'services_per_line': {},
            'all_pbit_range': False,
            'different_pbit_per_service': False,
            'specific_lines': [],
            'any_lines_scenario': False,
        }

        # Enhanced entity extraction
        self._extract_with_comprehensive_regex(text_clean, entities)

        # Post-process and validate
        self._post_process_entities(entities)

        return entities

    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for better extraction"""
        if pd.isna(text) or text == 'nan':
            return ""

        text = str(text).lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s:,.-]', ' ', text)
        return text.strip()

    def _post_process_entities(self, entities: Dict):
        """Enhanced post-processing"""
        # Handle empty text case
        if not any([entities['user_vlans'], entities['network_vlans'],
                   entities['lines'], entities['user_pbits'], entities['network_pbits'],
                   entities.get('is_multi_service', False)]):
            entities['lines'] = [1]
            entities['user_vlans'] = []
            entities['network_vlans'] = []
            entities['user_pbits'] = [0]
            entities['network_pbits'] = [0]
            return

        # Ensure PBIT defaults
        if not entities['user_pbits'] and not entities['all_pbit_range']:
            entities['user_pbits'] = [0]

        if not entities['network_pbits'] and not entities['all_pbit_range']:
            entities['network_pbits'] = [0]        # Set flags
        entities['is_multi_line'] = len(entities['lines']) > 1
        entities['is_all_lines'] = len(entities['lines']) == 16

        if len(set(entities['line_forwarder_map'].values())) > 1:
            entities['mixed_forwarders'] = entities['discretization_config']

    def _extract_with_comprehensive_regex(self, text: str, entities: Dict):
        """Enhanced comprehensive regex extraction with CASE INSENSITIVE matching"""
        text_lower = text.lower()

        # CRITICAL FIX: Check for VLAN translation FIRST (before untagged detection)
        if re.search(r'with\s+vlan\s+translation', text_lower, re.IGNORECASE):
            entities['has_vlan_translation'] = True
        elif re.search(r'without\s+vlan\s+translation', text_lower, re.IGNORECASE):
            entities['has_vlan_translation'] = False

        # Enhanced service count detection
        service_detected = self._extract_service_patterns(text_lower, entities)
        if service_detected:
            return

        # Enhanced multiple line detection
        self._extract_multiple_lines(text_lower, entities)

        # Extract VLANs
        all_vlans = []
        for pattern in self.vlan_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            all_vlans.extend([int(v) for v in matches if v.isdigit()])

        # Remove duplicates while preserving order
        seen = set()
        unique_vlans = []
        for vlan in all_vlans:
            if vlan not in seen:
                unique_vlans.append(vlan)
                seen.add(vlan)

        self._categorize_vlans_by_context(text, unique_vlans, entities)

        # Enhanced PBIT detection
        self._extract_enhanced_pbits(text_lower, entities)

        # Extract other entities
        self._extract_forwarders_regex(text, entities)
        self._extract_protocols_regex(text, entities)

        # CRITICAL FIX: Only detect untagged if no VLAN translation context AND case insensitive
        if entities['has_vlan_translation'] is None:
            self._detect_untagged_regex(text, entities)

    def _extract_service_patterns(self, text: str, entities: Dict) -> bool:
        """Extract service patterns with proper group handling"""
        for pattern_info in self.service_count_patterns:
            pattern = pattern_info['pattern']
            groups = pattern_info['groups']

            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, str):
                        match = (match,)

                    # Parse based on group configuration
                    parsed_data = {}
                    for i, group_name in enumerate(groups):
                        if i < len(match):
                            parsed_data[group_name] = match[i]

                    # Handle service count
                    if 'service_count' in parsed_data:
                        try:
                            service_count = int(parsed_data['service_count'])
                        except ValueError:
                            continue
                    else:
                        service_count = pattern_info.get('service_count', 1)

                    # Handle service type
                    service_type = parsed_data.get('service_type', entities.get('forwarder_type', 'N:1')).upper()

                    # Handle line numbers
                    lines = []
                    if 'line_num' in parsed_data:
                        lines.append(int(parsed_data['line_num']))
                    if 'line_num1' in parsed_data:
                        lines.append(int(parsed_data['line_num1']))
                    if 'line_num2' in parsed_data:
                        lines.append(int(parsed_data['line_num2']))

                    # Check for "different pbit" in multi-service
                    if re.search(r'different\s+pbit', text, re.IGNORECASE):
                        entities['different_pbit_per_service'] = True

                    # Update entities
                    entities['is_multi_service'] = True
                    entities['service_count'] = service_count
                    entities['service_type'] = service_type
                    entities['forwarder_type'] = service_type
                    entities['lines'] = lines

                    for line_num in lines:
                        entities['services_per_line'][line_num] = service_count

                    return True
        return False

    def _extract_multiple_lines(self, text: str, entities: Dict):
        """Enhanced multiple line detection"""
        # Check for "all lines" patterns first
        for pattern in self.all_lines_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                entities['lines'] = list(range(1, 17))
                entities['is_all_lines'] = True
                entities['is_multi_line'] = True
                return

        # Check for specific multiple line patterns
        lines_found = set()

        # "line 1 and line 2"
        match = re.search(r'line\s+(\d+)\s+and\s+line\s+(\d+)', text, re.IGNORECASE)
        if match:
            line1, line2 = int(match.group(1)), int(match.group(2))
            lines_found.update([line1, line2])

        # "line 4, line 8, line 12 and line 16"
        matches = re.findall(r'line\s+(\d+)', text, re.IGNORECASE)
        if len(matches) > 1:
            lines_found.update([int(l) for l in matches])

        # "any 2 lines" - use special flag and default lines
        if re.search(r'any\s+(\d+)\s+lines?', text, re.IGNORECASE):
            match = re.search(r'any\s+(\d+)\s+lines?', text, re.IGNORECASE)
            count = int(match.group(1))
            if count == 2:
                lines_found.update([5, 13])  # Default for "any 2 lines"
                entities['any_lines_scenario'] = True

        # If multiple lines found, update entities
        if len(lines_found) > 1:
            entities['lines'] = sorted(list(lines_found))
            entities['is_multi_line'] = True
            entities['specific_lines'] = sorted(list(lines_found))
            return

        # Fall back to single line patterns
        if not lines_found:
            for pattern in self.line_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                lines_found.update([int(l) for l in matches if l.isdigit()])

        # Default to line 1 if nothing found
        if not lines_found:
            lines_found.add(1)

        entities['lines'] = sorted(list(lines_found))
        entities['is_multi_line'] = len(lines_found) > 1

    def _categorize_vlans_by_context(self, text: str, vlans: List[int], entities: Dict):
        """Enhanced VLAN categorization"""
        if not vlans:
            return

        text_lower = text.lower()
        sentences = re.split(r'[.!?\n]+', text_lower)

        user_vlans = []
        network_vlans = []

        for vlan in vlans:
            vlan_str = str(vlan)
            assigned = False

            for sentence in sentences:
                if vlan_str in sentence:
                    if any(indicator in sentence for indicator in ['user side', 'upstream', 'line', 'customer']):
                        user_vlans.append(vlan)
                        assigned = True
                        break
                    elif any(indicator in sentence for indicator in ['network side', 'downstream', 'uplink', 'provider']):
                        network_vlans.append(vlan)
                        assigned = True
                        break

            if not assigned:
                if len(user_vlans) <= len(network_vlans):
                    user_vlans.append(vlan)
                else:
                    network_vlans.append(vlan)

        entities['user_vlans'] = sorted(list(set(user_vlans)))
        entities['network_vlans'] = sorted(list(set(network_vlans)))

    def _extract_enhanced_pbits(self, text: str, entities: Dict):
        """Enhanced PBIT extraction with range support"""
        # Check for "all pbit"
        if re.search(r'all\s+pbit', text, re.IGNORECASE):
            entities['all_pbit_range'] = True
            entities['user_pbits'] = list(range(8))  # 0-7
            entities['network_pbits'] = list(range(8))
            return

        # Check for "different pbit"
        if re.search(r'different\s+pbit', text, re.IGNORECASE):
            entities['different_pbit_per_service'] = True
            return

        # Regular PBIT extraction
        all_pbits = []
        for pattern in self.pbit_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_pbits.extend([int(p) for p in matches if p.isdigit()])

        self._categorize_pbits_by_context(text, all_pbits, entities)

    def _categorize_pbits_by_context(self, text: str, pbits: List[int], entities: Dict):
        """Enhanced PBIT categorization"""
        if not pbits:
            return

        text_lower = text.lower()
        sentences = re.split(r'[.!?\n]+', text_lower)

        user_pbits = []
        network_pbits = []

        for i, pbit in enumerate(pbits):
            pbit_str = str(pbit)
            assigned = False

            for sentence in sentences:
                if f'pbit {pbit_str}' in sentence or f'pbit={pbit_str}' in sentence:
                    if any(word in sentence for word in ['upstream', 'user', 'send upstream']):
                        user_pbits.append(pbit)
                        assigned = True
                        break
                    elif any(word in sentence for word in ['downstream', 'network', 'send downstream']):
                        network_pbits.append(pbit)
                        assigned = True
                        break

            if not assigned:
                if i % 2 == 0:
                    user_pbits.append(pbit)
                else:
                    network_pbits.append(pbit)

        entities['user_pbits'] = sorted(list(set(user_pbits)))
        entities['network_pbits'] = sorted(list(set(network_pbits)))

    def _extract_forwarders_regex(self, text: str, entities: Dict):
        """Extract forwarder type using regex"""
        text_lower = text.lower()

        one_to_one_count = len(re.findall(r'1\s*:\s*1', text_lower, re.IGNORECASE))
        n_to_one_count = len(re.findall(r'n\s*:\s*1', text_lower, re.IGNORECASE))

        if one_to_one_count > n_to_one_count:
            entities['forwarder_type'] = '1:1'
        elif n_to_one_count > 0:
            entities['forwarder_type'] = 'N:1'
        else:
            if any(word in text_lower for word in ['dedicated', 'individual', 'separate']):
                entities['forwarder_type'] = '1:1'
            else:
                entities['forwarder_type'] = 'N:1'

    def _extract_protocols_regex(self, text: str, entities: Dict):
        """Enhanced protocol extraction"""
        text_lower = text.lower()
        protocols = []

        if re.search(r'ipv6|internet\s+protocol\s+version\s+6|v6\s+traffic', text_lower, re.IGNORECASE):
            protocols.append('IPv6')
        if re.search(r'pppoe|ppp\s+over\s+ethernet|ppp\s+traffic', text_lower, re.IGNORECASE):
            protocols.append('PPPoE')

        entities['protocols'] = protocols

    def _detect_untagged_regex(self, text: str, entities: Dict):
        """Enhanced untagged detection"""
        text_lower = text.lower()

        # Don't treat "without VLAN translation" as untagged
        if entities.get('has_vlan_translation') is False:
            return

        for pattern in self.untagged_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                entities['is_untagged'] = True
                return

print("📚 Flask application with NLP entity extraction initialized")

@app.route('/')
def index():
    """Main page with input form"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_configuration():
    """API endpoint to generate configuration from input text"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '')
        minimal = data.get('minimal', False)
        
        if not input_text.strip():
            return jsonify({
                'success': False,
                'error': 'Input text is required'
            })
        
        # Initialize the configuration generator
        generator = IntelligentConfigGenerator()
        
        # Generate configuration
        vsi_config = generator.generate_configuration(input_text, minimal=minimal)
        
        # Extract entities for additional info
        entities = generator.entity_extractor.extract_comprehensive_entities(input_text)
        
        return jsonify({
            'success': True,
            'configuration': vsi_config,
            'entities': entities,
            'input_text': input_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """API endpoint to analyze input text and extract entities"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '')
        
        if not input_text.strip():
            return jsonify({
                'success': False,
                'error': 'Input text is required'
            })
        
        # Initialize entity extractor
        extractor = AdvancedNLPEntityExtractor()
        
        # Extract entities
        entities = extractor.extract_comprehensive_entities(input_text)
        
        return jsonify({
            'success': True,
            'entities': entities,
            'input_text': input_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Enhanced Intelligent Configuration Generator
class IntelligentConfigGenerator:
    def __init__(self):
        self.entity_extractor = AdvancedNLPEntityExtractor()

    def generate_configuration(self, input_text: str, minimal: bool = False) -> str:
        """Generate complete configuration from input text"""
        entities = self.entity_extractor.extract_comprehensive_entities(input_text)

        # Generate VSI configuration
        vsi_config = self._generate_vsi_configuration(entities)

        if minimal:
            return vsi_config

        # Generate traffic configuration
        traffic_config = self._generate_traffic_configuration(entities, vsi_config)

        return vsi_config + "\n" + traffic_config

    def _generate_vsi_configuration(self, entities: Dict) -> str:
        """Generate VSI configuration"""
        lines = ["Entity1 = DUT", "Entity1 Keywords ="]

        # Check for multi-service configurations
        if entities.get('is_multi_service'):
            return self._generate_multi_service_config(entities, lines)
        elif entities['is_all_lines'] or entities['is_multi_line']:
            return self._generate_multi_line_config(entities, lines)
        else:
            return self._generate_single_line_config(entities, lines)

    def _generate_single_line_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate single line configuration"""
        line_num = entities['lines'][0] if entities['lines'] else 1
        forwarder_type = entities['forwarder_type']

        # Determine VLANs and PBITs
        user_vlan = self._get_user_vlan(entities, 0, line_num)
        user_pbit = self._get_user_pbit(entities, 0)
        network_vlan = self._get_network_vlan(entities, line_num, forwarder_type)
        network_pbit = self._get_network_pbit(entities, 0)

        # UserVSI
        lines.append(f"UserVSI-1 = VLAN={user_vlan}, PBIT={user_pbit}")
        lines.append(f"UserVSI-1 Parent = Line{line_num}")

        # NetworkVSI
        lines.append(f"NetworkVSI-1 = VLAN={network_vlan}, PBIT={network_pbit}")
        lines.append(f"NetworkVSI-1 Parent = Uplink{entities['uplinks'][0]}")

        # Forwarder
        lines.append(f"Forwarder = {forwarder_type}")

        return "\n".join(lines)

    def _generate_multi_line_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate multi-line configuration"""
        target_lines = entities['lines']
        forwarder_type = entities['forwarder_type']

        # Generate UserVSI for each line
        for i, line_num in enumerate(target_lines):
            user_vlan = self._get_user_vlan(entities, i, line_num)
            user_pbit = self._get_user_pbit(entities, i)

            lines.append(f"UserVSI-{i+1} = VLAN={user_vlan}, PBIT={user_pbit}")
            lines.append(f"UserVSI-{i+1} Parent = Line{line_num}")

        # Generate NetworkVSI
        if forwarder_type == '1:1':
            for i, line_num in enumerate(target_lines):
                network_vlan = self._get_network_vlan(entities, line_num, forwarder_type)
                network_pbit = self._get_network_pbit(entities, i)

                lines.append(f"NetworkVSI-{i+1} = VLAN={network_vlan}, PBIT={network_pbit}")
                lines.append(f"NetworkVSI-{i+1} Parent = Uplink{entities['uplinks'][0]}")
                lines.append(f"Forwarder-{i+1} 1:1")
        else:  # N:1
            network_vlan = self._get_network_vlan_for_group(entities, target_lines, forwarder_type)
            network_pbit = self._get_network_pbit(entities, 0)

            lines.append(f"NetworkVSI-1 = VLAN={network_vlan}, PBIT={network_pbit}")
            lines.append(f"NetworkVSI-1 Parent = Uplink{entities['uplinks'][0]}")
            lines.append("Forwarder = N:1")

        return "\n".join(lines)

    def _generate_multi_service_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate multi-service configuration"""
        service_count = entities.get('service_count', 1)
        service_type = entities.get('service_type', entities['forwarder_type'])
        target_lines = entities['lines']

        vsi_counter = 1
        for service_idx in range(service_count):
            user_vlan = 101 + service_idx
            network_vlan = user_vlan

            # Generate UserVSI for each line
            for line_num in target_lines:
                lines.append(f"UserVSI-{vsi_counter} = VLAN={user_vlan}, PBIT=0")
                lines.append(f"UserVSI-{vsi_counter} Parent = Line{line_num}")
                vsi_counter += 1

            # Generate NetworkVSI
            lines.append(f"NetworkVSI-{service_idx + 1} = VLAN={network_vlan}, PBIT=0")
            lines.append(f"NetworkVSI-{service_idx + 1} Parent = Uplink{entities['uplinks'][0]}")

            # Generate Forwarder
            if service_idx < service_count - 1:
                lines.append(f"Forwarder-{service_idx + 1} {service_type}")
            else:
                lines.append(f"Forwarder-{service_idx + 1} {service_type}")

        return "\n".join(lines)

    def _get_user_vlan(self, entities: Dict, index: int, line_num: int) -> str:
        """Get user VLAN with intelligent defaults"""
        if entities['is_untagged']:
            return "No"

        if entities['user_vlans']:
            if index < len(entities['user_vlans']):
                return str(entities['user_vlans'][index])
            else:
                return str(entities['user_vlans'][0])

        # Smart defaults
        if entities['forwarder_type'] == '1:1' and not entities['is_all_lines'] and not entities['is_multi_line']:
            return "700"
        elif entities['is_all_lines']:
            return str(101 + index)
        elif entities.get('is_multi_line'):
            return str(101 + index)
        else:
            return "100"

    def _get_user_pbit(self, entities: Dict, index: int) -> str:
        """Get user PBIT for specific index"""
        if entities['is_untagged']:
            return "No"

        if entities['user_pbits']:
            if index < len(entities['user_pbits']):
                return str(entities['user_pbits'][index])
            else:
                return str(entities['user_pbits'][0])

        return "0"

    def _get_network_vlan(self, entities: Dict, line_num: int, forwarder_type: str) -> int:
        """Get network VLAN with correct logic"""
        if entities['network_vlans']:
            return entities['network_vlans'][0]

        if entities['is_untagged']:
            return 101

        if forwarder_type == '1:1':
            if not entities['is_all_lines'] and not entities['is_multi_line'] and not entities['user_vlans']:
                return 700
            else:
                return 1000 + line_num
        else:
            return 1000

    def _get_network_vlan_for_group(self, entities: Dict, group_lines: List[int], forwarder_type: str) -> int:
        """Get network VLAN for group of lines"""
        if entities['network_vlans']:
            return entities['network_vlans'][0]

        return 1000

    def _get_network_pbit(self, entities: Dict, index: int) -> str:
        """Get network PBIT with inheritance from user PBIT"""
        if entities['network_pbits']:
            if index < len(entities['network_pbits']):
                return str(entities['network_pbits'][index])
            else:
                return str(entities['network_pbits'][0])

        # Inherit from user PBIT if network PBIT not specified
        if entities['user_pbits']:
            if index < len(entities['user_pbits']):
                return str(entities['user_pbits'][index])
            else:
                return str(entities['user_pbits'][0])

        return "0"

    def _generate_traffic_configuration(self, entities: Dict, vsi_config: str) -> str:
        """Generate traffic configuration"""
        lines = []
        target_lines = entities['lines']
        is_multi_line = len(target_lines) > 1

        # Upstream traffic
        lines.extend([
            "Test Eqpt - Upstream",
            "Entity2 = User Side Traffic Eqpt",
            "Entity2 Keywords=",
            "NumPackets To Generate = 100"
        ])

        for i, line_num in enumerate(target_lines):
            user_vlan = self._get_user_vlan(entities, i, line_num)
            user_pbit = self._get_user_pbit(entities, i)

            if is_multi_line:
                lines.append(f"Packet Line{line_num} L2 Header")
                lines.append(f"Src MAC = 99:02:03:04:{line_num:02d}:11")
                lines.append(f"Dst MAC = 98:0A:0B:0C:{line_num:02d}:0C")
            else:
                lines.append("Packet L2 Header")
                lines.append("Src MAC = 99:02:03:04:05:06")
                lines.append("Dst MAC = 98:0A:0B:0C:0D:0E")

            if entities['is_untagged']:
                lines.append("VLAN=No, PBIT=No")
            else:
                lines.append(f"VLAN = {user_vlan}, PBIT = {user_pbit}")

        # Network side reception
        lines.extend([
            "Entity3 = Network Side Traffic Eqpt",
            "Entity3 Keywords=",
            "NumPackets To Recieve = 100"
        ])

        # Downstream traffic (similar structure)
        lines.extend([
            "Test Eqpt - Downstream",
            "Entity3 = Network Side Traffic Eqpt",
            "Entity3 Keywords=",
            "NumPackets To Generate = 100"
        ])

        # User side reception
        lines.extend([
            "Entity2 = User Side Traffic Eqpt",
            "Entity2 Keywords=",
            "NumPackets To Recieve = 100"
        ])

        return "\n".join(lines)

if __name__ == '__main__':
    print("🚀 Starting Network Configuration Generator Flask Server")
    print("📋 Available endpoints:")
    print("   GET  /                - Web interface") 
    print("   POST /api/generate    - Generate configuration from text")
    print("   POST /api/analyze     - Analyze text and extract entities")
    print("\n🌐 Server running in production mode")
    print("🛑 Press Ctrl+C to stop the server")
    
    # Run in production mode for deployment
    app.run(debug=False, host='0.0.0.0', port=10000)
