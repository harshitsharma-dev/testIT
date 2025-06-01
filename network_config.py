# Enhanced Network Configuration Generator - Advanced Implementation from Jupyter Notebook
import pandas as pd
import numpy as np
import re
import os
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Install and import spaCy for advanced NLP
try:
    import spacy
    from spacy.matcher import Matcher
    from spacy.util import filter_spans

    # Try to load English model
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
        print("✅ spaCy English model loaded successfully")
    except OSError:
        print("⚠️ spaCy English model not found. Installing...")
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"],
                      capture_output=True)
        try:
            nlp = spacy.load("en_core_web_sm")
            SPACY_AVAILABLE = True
            print("✅ spaCy English model installed and loaded")
        except:
            SPACY_AVAILABLE = False
            print("❌ spaCy model installation failed. Using regex fallback.")
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ spaCy not available. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "spacy"], capture_output=True)
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
        print("✅ spaCy installed and loaded")
    except:
        SPACY_AVAILABLE = False
        print("❌ spaCy installation failed. Using regex fallback.")

# For interactive input
try:
    import ipywidgets as widgets
    from IPython.display import display, HTML, clear_output
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False

print("📚 Enhanced libraries imported successfully")

# ULTIMATE FIXED Advanced NLP Entity Extraction Engine (COMPLETE ENGLISH FIX)
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

        # FIXED: Service count patterns with better group handling
        self.service_count_patterns = [
            # Pattern 1: "8 Services per line 1" -> groups: (service_count, line_num)
            {
                'pattern': r'(?:configure\s+)?(\d+)\s+services?\s+per\s+line\s+(\d+)',
                'groups': ['service_count', 'line_num']
            },
            # Pattern 2: "8 Services of type 1:1 per line 2" -> groups: (service_count, service_type, line_num)
            {
                'pattern': r'(?:configure\s+)?(\d+)\s+services?\s+of\s+type\s+(1:1|n:1)\s+per\s+line\s+(\d+)',
                'groups': ['service_count', 'service_type', 'line_num']
            },
            # Pattern 3: "three 1:1 services for line 1" -> groups: (service_type, line_num)
            {
                'pattern': r'(?:create\s+)?(?:three|3)\s+(1:1|n:1)\s+services?\s+for\s+line\s+(\d+)',
                'groups': ['service_type', 'line_num'],
                'service_count': 3
            },
            # Pattern 4: "Create three 1:1 services for line 1" -> groups: (service_type, line_num)
            {
                'pattern': r'(?:create\s+)?(?:three|3)\s+services?\s+(?:of\s+type\s+)?(1:1|n:1)\s+(?:for\s+)?line\s+(\d+)',
                'groups': ['service_type', 'line_num'],
                'service_count': 3
            },
            # Pattern 5: "Create Three N:1 services for line 1 and line 2" -> groups: (service_type, line_num1, line_num2)
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

        # FIXED: Enhanced untagged patterns - CASE INSENSITIVE
        self.untagged_patterns = [
            r'untagged\s+(?:vlan|traffic)',
            r'untagged.*?vlan.*?id',
            r'vlan.*?untagged',
            r'no\s+vlan',
            r'untagged',
            r'valn',  # CRITICAL: Handle typo "Valn" instead of "VLAN"
            r'untagged\s+valn',  # Handle "untagged Valn ID"
        ]

        # Enhanced discretization patterns
        self.discretization_patterns = [
            r'(?:first|initial)\s+(\d+)\s+lines?.*?(1:1|n:1).*?(?:remaining|rest|next|last).*?lines?.*?(1:1|n:1)',
            r'(\d+)\s+lines?.*?(1:1|n:1).*?(?:remaining|rest|next|last).*?lines?.*?(1:1|n:1)',
            r'(1:1|n:1)\s+forwarder.*?(?:first|initial)\s+(\d+)\s+lines?.*?(?:and|,).*?(1:1|n:1)\s+forwarder.*?(?:remaining|rest)',
        ]
        
        if SPACY_AVAILABLE:
            try:
                # Load spaCy model
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except (OSError, ImportError):
                print("Warning: spaCy model 'en_core_web_sm' not found. Using basic pattern matching.")
                self.nlp = None
        else:
            print("Warning: spaCy not available. Using basic pattern matching.")
            
        # Download required NLTK data
        if NLTK_AVAILABLE:
            try:
                import nltk
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                try:
                    nltk.download('punkt', quiet=True)
                except:
                    print("Warning: Could not download NLTK punkt tokenizer.")
                
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                try:
                    nltk.download('stopwords', quiet=True)
                except:
                    print("Warning: Could not download NLTK stopwords.")
    
    def setup_patterns(self):
        """Setup enhanced pattern matching"""
        self.vlan_patterns = [
            r'(?:vlan|VLAN)\s*(?:id|ID)?\s*(?:=|:)?\s*(\d+)',
            r'(?:customer|user)\s*vlan\s*(\d+)',
            r'(?:network|provider)\s*vlan\s*(\d+)',
            r'(?:outer|inner)\s*vlan\s*(\d+)',
            r'(?:s-vlan|c-vlan)\s*(\d+)',
            r'tagged?\s*(?:with|as)?\s*vlan\s*(\d+)',
            r'vlan\s*(\d+)\s*(?:tagged|untagged)',
            r'(?:on|in)\s*vlan\s*(\d+)',
            r'(\d+)\s*(?:as|is)\s*(?:the\s*)?vlan',
        ]
        
        self.line_patterns = [
            r'(?:line|LINE)\s*(?:=|:)?\s*(\d+)',
            r'(?:on|using)\s*line\s*(\d+)',
            r'line\s*(\d+)\s*(?:is|will|should)',
            r'(?:all|every)\s*(?:lines?|LINE)',
            r'lines?\s*(\d+)\s*(?:to|through|-)\s*(\d+)',
            r'(?:multiple|several)\s*lines?',
            r'(?:single|one)\s*line',
        ]
        
        self.forwarder_patterns = {
            '1:1': [
                r'1:1\s*(?:forwarder|service)',
                r'one.?to.?one',
                r'dedicated\s*(?:forwarder|service)',
                r'individual\s*(?:mapping|forwarder)',
                r'direct\s*(?:mapping|forwarding)',
                r'separate\s*(?:forwarder|service)',
                r'isolated\s*(?:forwarder|service)',
            ],
            'N:1': [
                r'n:1\s*(?:forwarder|service)',
                r'many.?to.?one',
                r'aggregat\w*\s*(?:forwarder|service)',
                r'(?:multiple|several).+(?:single|one)\s*(?:forwarder|service)',
                r'shared\s*(?:forwarder|service)',
                r'common\s*(?:forwarder|service)',
                r'consolidated\s*(?:forwarder|service)',
            ]
        }
        
        self.protocol_patterns = [
            r'(?:using|with|via)\s*(tcp|udp|icmp|arp|dhcp|dns|http|https|ftp|ssh|telnet)',
            r'(tcp|udp|icmp|arp|dhcp|dns|http|https|ftp|ssh|telnet)\s*(?:protocol|traffic)',
            r'(?:protocol|traffic)\s*(?:is|:)?\s*(tcp|udp|icmp|arp|dhcp|dns|http|https|ftp|ssh|telnet)',
        ]
        
        self.pbit_patterns = [
            r'(?:pbit|p-bit|priority)\s*(?:=|:)?\s*(\d+)',
            r'(?:cos|class)\s*(?:=|:)?\s*(\d+)',
            r'priority\s*(\d+)',
            r'(?:high|low|medium)\s*priority',
            r'(?:best.?effort|background|excellent.?effort|critical|voice|video|network.?control)',
        ]

    def setup_templates(self):
        """Setup configuration templates"""
        self.config_templates = {
            'user_vlan': {
                'single': "vlan {vlan_id}\n name User_VLAN_{vlan_id}\n",
                'multiple': "! User VLANs\n{vlan_configs}"
            },
            'network_vlan': {
                'single': "vlan {vlan_id}\n name Network_VLAN_{vlan_id}\n",
                'multiple': "! Network VLANs\n{vlan_configs}"
            },
            'forwarder': {
                '1:1': "ethernet cfm forwarder {forwarder_id} 1:1\n",
                'N:1': "ethernet cfm forwarder {forwarder_id} N:1\n"
            },
            'line_config': {
                'single': "interface ethernet 1/{line_id}\n",
                'multiple': "! Line configurations\n{line_configs}",
                'range': "interface range ethernet 1/{start_line}-1/{end_line}\n"
            }
        }

    def extract_entities_with_nlp(self, text: str) -> Dict[str, Any]:
        """Enhanced entity extraction using NLP"""
        entities = {
            'user_vlans': [],
            'network_vlans': [],
            'lines': [],
            'uplinks': [1],
            'user_pbits': [],
            'network_pbits': [],
            'forwarder_type': 'N:1',
            'protocols': [],
            'is_untagged': False,
            'is_multi_line': False,
            'is_all_lines': False,
            'line_ranges': [],
            'confidence_scores': {},
            'context_keywords': [],
            'traffic_patterns': []
        }
        
        # Basic pattern matching
        self._extract_vlans_enhanced(text, entities)
        self._extract_lines_enhanced(text, entities)
        self._extract_forwarder_type_enhanced(text, entities)
        self._extract_protocols_enhanced(text, entities)
        self._extract_pbits_enhanced(text, entities)
        
        # NLP-based analysis if spaCy is available
        if self.nlp:
            self._nlp_analysis(text, entities)
        
        # Context analysis
        self._analyze_context(text, entities)
        
        return entities

    def _extract_vlans_enhanced(self, text: str, entities: Dict[str, Any]):
        """Enhanced VLAN extraction with context awareness"""
        text_lower = text.lower()
        
        # Extract all VLAN numbers
        all_vlans = set()
        for pattern in self.vlan_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    vlan_id = int(match.group(1))
                    if 1 <= vlan_id <= 4094:  # Valid VLAN range
                        all_vlans.add(vlan_id)
                except (ValueError, IndexError):
                    continue
        
        # Context-based classification
        for vlan in all_vlans:
            context = self._get_vlan_context(text, str(vlan))
            
            if any(keyword in context for keyword in ['customer', 'user', 'client', 'c-vlan', 'inner']):
                entities['user_vlans'].append(vlan)
            elif any(keyword in context for keyword in ['network', 'provider', 's-vlan', 'outer', 'transport']):
                entities['network_vlans'].append(vlan)
            else:
                # Default classification based on common patterns
                if vlan < 100:
                    entities['user_vlans'].append(vlan)
                else:
                    entities['network_vlans'].append(vlan)
        
        # Remove duplicates and sort
        entities['user_vlans'] = sorted(list(set(entities['user_vlans'])))
        entities['network_vlans'] = sorted(list(set(entities['network_vlans'])))
        
        # Check for untagged traffic
        entities['is_untagged'] = bool(re.search(r'untagged|no.?tag|native', text_lower))

    def _extract_lines_enhanced(self, text: str, entities: Dict[str, Any]):
        """Enhanced line extraction"""
        text_lower = text.lower()
        
        # Check for "all lines" patterns
        if re.search(r'(?:all|every)\s*(?:lines?|ports?)', text_lower):
            entities['is_all_lines'] = True
            entities['lines'] = list(range(1, 25))  # Assume max 24 lines
            return
        
        # Extract specific line numbers
        line_numbers = set()
        
        for pattern in self.line_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) == 1:
                        line_id = int(match.group(1))
                        if 1 <= line_id <= 48:  # Valid line range
                            line_numbers.add(line_id)
                    elif len(match.groups()) == 2:
                        # Range pattern
                        start_line = int(match.group(1))
                        end_line = int(match.group(2))
                        if 1 <= start_line <= end_line <= 48:
                            entities['line_ranges'].append((start_line, end_line))
                            line_numbers.update(range(start_line, end_line + 1))
                except (ValueError, IndexError):
                    continue
        
        # Check for multiple lines indication
        if re.search(r'(?:multiple|several|many)\s*(?:lines?|ports?)', text_lower):
            entities['is_multi_line'] = True
            if not line_numbers:
                line_numbers = {1, 2}  # Default multiple lines
        
        entities['lines'] = sorted(list(line_numbers)) if line_numbers else [1]

    def _extract_forwarder_type_enhanced(self, text: str, entities: Dict[str, Any]):
        """Enhanced forwarder type detection"""
        text_lower = text.lower()
        
        # Score different forwarder types
        scores = {'1:1': 0, 'N:1': 0}
        
        for fwd_type, patterns in self.forwarder_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                scores[fwd_type] += matches
        
        # Additional heuristics
        if re.search(r'(?:each|every|individual|separate|dedicated)', text_lower):
            scores['1:1'] += 2
        
        if re.search(r'(?:shared|common|aggregate|multiple.+single)', text_lower):
            scores['N:1'] += 2
        
        # Determine forwarder type
        if scores['1:1'] > scores['N:1']:
            entities['forwarder_type'] = '1:1'
        else:
            entities['forwarder_type'] = 'N:1'
        
        entities['confidence_scores']['forwarder'] = max(scores.values()) / (sum(scores.values()) + 1)

    def _extract_protocols_enhanced(self, text: str, entities: Dict[str, Any]):
        """Enhanced protocol extraction"""
        protocols = set()
        
        for pattern in self.protocol_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                protocol = match.group(1).upper()
                protocols.add(protocol)
        
        entities['protocols'] = sorted(list(protocols))

    def _extract_pbits_enhanced(self, text: str, entities: Dict[str, Any]):
        """Enhanced P-bit extraction"""
        text_lower = text.lower()
        pbits = set()
        
        for pattern in self.pbit_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    if match.group(1).isdigit():
                        pbit = int(match.group(1))
                        if 0 <= pbit <= 7:
                            pbits.add(pbit)
                except (ValueError, IndexError, AttributeError):
                    continue
        
        # Map priority keywords to P-bit values
        priority_map = {
            'best.?effort': [0, 1],
            'background': [1],
            'excellent.?effort': [2],
            'critical': [3, 4],
            'voice': [5],
            'video': [4],
            'network.?control': [6, 7],
            'high': [5, 6, 7],
            'medium': [3, 4],
            'low': [0, 1, 2]
        }
        
        for priority, pbit_values in priority_map.items():
            if re.search(priority, text_lower):
                pbits.update(pbit_values)
        
        entities['user_pbits'] = sorted(list(pbits))
        entities['network_pbits'] = sorted(list(pbits))

    def _nlp_analysis(self, text: str, entities: Dict[str, Any]):
        """Perform NLP analysis using spaCy"""
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['CARDINAL', 'ORDINAL']:
                # Look for numbers that might be VLANs or lines
                try:
                    num = int(ent.text)
                    if 1 <= num <= 4094 and 'vlan' in ent.sent.text.lower():
                        if num not in entities['user_vlans'] and num not in entities['network_vlans']:
                            entities['user_vlans'].append(num)
                    elif 1 <= num <= 48 and 'line' in ent.sent.text.lower():
                        if num not in entities['lines']:
                            entities['lines'].append(num)
                except ValueError:
                    continue
        
        # Extract key phrases
        key_phrases = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:
                key_phrases.append(chunk.text.lower())
        
        entities['context_keywords'] = key_phrases

    def _analyze_context(self, text: str, entities: Dict[str, Any]):
        """Analyze context for better understanding"""
        text_lower = text.lower()
        
        # Traffic pattern analysis
        traffic_patterns = []
        
        if re.search(r'(?:upstream|uplink|to.?network)', text_lower):
            traffic_patterns.append('upstream')
        
        if re.search(r'(?:downstream|to.?customer|to.?user)', text_lower):
            traffic_patterns.append('downstream')
        
        if re.search(r'(?:bidirectional|both.?ways|two.?way)', text_lower):
            traffic_patterns.extend(['upstream', 'downstream'])
        
        entities['traffic_patterns'] = traffic_patterns
        
        # Quality of Service indicators
        qos_indicators = []
        if re.search(r'(?:qos|quality.?of.?service)', text_lower):
            qos_indicators.append('qos_enabled')
        
        if re.search(r'(?:priority|prioritize)', text_lower):
            qos_indicators.append('priority_marking')
        
        entities['qos_indicators'] = qos_indicators

    def _get_vlan_context(self, text: str, vlan_str: str) -> str:
        """Get context around VLAN mention"""
        sentences = text.split('.')
        for sentence in sentences:
            if vlan_str in sentence:
                return sentence.lower()
        return ""

    def generate_configuration(self, text: str) -> Dict[str, Any]:
        """Generate network configuration from input text"""
        # Extract entities
        entities = self.extract_entities_with_nlp(text)
        
        # Generate configuration sections
        config_sections = {
            'user_vlans': self._generate_vlan_config(entities['user_vlans'], 'user'),
            'network_vlans': self._generate_vlan_config(entities['network_vlans'], 'network'),
            'forwarders': self._generate_forwarder_config(entities),
            'interfaces': self._generate_interface_config(entities),
            'qos': self._generate_qos_config(entities),
            'summary': self._generate_summary(entities)
        }
        
        # Combine all sections
        full_config = self._combine_configurations(config_sections)
        
        return {
            'success': True,
            'entities': entities,
            'configuration': full_config,
            'sections': config_sections,
            'metadata': {
                'total_vlans': len(entities['user_vlans']) + len(entities['network_vlans']),
                'total_lines': len(entities['lines']),
                'forwarder_type': entities['forwarder_type'],
                'protocols': entities['protocols'],
                'confidence_scores': entities.get('confidence_scores', {})
            }
        }

    def _generate_vlan_config(self, vlans: List[int], vlan_type: str) -> str:
        """Generate VLAN configuration"""
        if not vlans:
            return f"! No {vlan_type} VLANs configured\n"
        
        config_lines = [f"! {vlan_type.title()} VLAN Configuration"]
        
        for vlan in vlans:
            config_lines.extend([
                f"vlan {vlan}",
                f" name {vlan_type.title()}_VLAN_{vlan}",
                f" state active",
                ""
            ])
        
        return "\n".join(config_lines)

    def _generate_forwarder_config(self, entities: Dict[str, Any]) -> str:
        """Generate forwarder configuration"""
        config_lines = ["! Forwarder Configuration"]
        
        forwarder_type = entities['forwarder_type']
        lines = entities['lines']
        user_vlans = entities['user_vlans']
        network_vlans = entities['network_vlans']
        
        if forwarder_type == '1:1':
            # One forwarder per line/VLAN combination
            forwarder_id = 1
            for line in lines:
                for user_vlan in user_vlans:
                    for network_vlan in network_vlans:
                        config_lines.extend([
                            f"ethernet cfm forwarder {forwarder_id} 1:1",
                            f" line {line}",
                            f" user-vlan {user_vlan}",
                            f" network-vlan {network_vlan}",
                            f" uplink 1",
                            ""
                        ])
                        forwarder_id += 1
        else:
            # N:1 forwarder
            config_lines.extend([
                f"ethernet cfm forwarder 1 N:1",
                f" lines {' '.join(map(str, lines))}" if len(lines) > 1 else f" line {lines[0]}",
                f" user-vlans {' '.join(map(str, user_vlans))}" if user_vlans else " ! No user VLANs",
                f" network-vlans {' '.join(map(str, network_vlans))}" if network_vlans else " ! No network VLANs",
                f" uplink 1",
                ""
            ])
        
        return "\n".join(config_lines)

    def _generate_interface_config(self, entities: Dict[str, Any]) -> str:
        """Generate interface configuration"""
        config_lines = ["! Interface Configuration"]
        
        lines = entities['lines']
        user_vlans = entities['user_vlans']
        
        for line in lines:
            config_lines.extend([
                f"interface ethernet 1/{line}",
                f" description \"Line {line} - User Traffic\"",
                f" switchport mode trunk" if not entities['is_untagged'] else f" switchport mode access",
            ])
            
            if user_vlans and not entities['is_untagged']:
                config_lines.append(f" switchport trunk allowed vlan {','.join(map(str, user_vlans))}")
            elif user_vlans and entities['is_untagged']:
                config_lines.append(f" switchport access vlan {user_vlans[0]}")
            
            config_lines.extend([
                f" no shutdown",
                ""
            ])
        
        return "\n".join(config_lines)

    def _generate_qos_config(self, entities: Dict[str, Any]) -> str:
        """Generate QoS configuration"""
        if not entities.get('user_pbits') and not entities.get('qos_indicators'):
            return "! No QoS configuration required\n"
        
        config_lines = ["! QoS Configuration"]
        
        if entities.get('user_pbits'):
            config_lines.extend([
                "class-map match-any USER_TRAFFIC",
                f" match cos {' '.join(map(str, entities['user_pbits']))}",
                "",
                "policy-map USER_POLICY",
                " class USER_TRAFFIC",
                "  priority percent 50",
                ""
            ])
        
        return "\n".join(config_lines)

    def _generate_summary(self, entities: Dict[str, Any]) -> str:
        """Generate configuration summary"""
        summary_lines = [
            "! Configuration Summary",
            f"! User VLANs: {entities['user_vlans'] if entities['user_vlans'] else 'None'}",
            f"! Network VLANs: {entities['network_vlans'] if entities['network_vlans'] else 'None'}",
            f"! Lines: {entities['lines']}",
            f"! Forwarder Type: {entities['forwarder_type']}",
            f"! Protocols: {entities['protocols'] if entities['protocols'] else 'Not specified'}",
            f"! Traffic Patterns: {entities.get('traffic_patterns', ['Not specified'])}",
            ""
        ]
        return "\n".join(summary_lines)

    def _combine_configurations(self, sections: Dict[str, str]) -> str:
        """Combine all configuration sections"""
        full_config = [
            "! Generated Network Configuration",
            "! " + "="*50,
            "",
            sections['summary'],
            sections['user_vlans'],
            sections['network_vlans'],
            sections['interfaces'],
            sections['forwarders'],
            sections['qos'],
            "! End of Configuration"
        ]
        
        return "\n".join(full_config)

# Advanced NLP Entity Extractor
class AdvancedNLPEntityExtractor:
    def __init__(self):
        self.setup_patterns()
        self.setup_entity_rules()

    def setup_patterns(self):
        """Setup enhanced pattern matching for entity extraction"""
        self.vlan_patterns = [
            r'vlan\s*(\d+)',
            r'(?:user|customer)\s*vlan\s*(\d+)',
            r'(?:network|provider)\s*vlan\s*(\d+)',
            r'tagged?\s*(?:with|as)?\s*vlan\s*(\d+)',
        ]
        
        self.line_patterns = [
            r'(?:line|port)\s*(\d+)',
            r'all\s*(?:16|sixteen)\s*lines',
            r'(?:line\s*)?(\d+)\s*(?:and|&|\+)\s*(?:line\s*)?(\d+)',
            r'lines?\s*(\d+)(?:\s*(?:to|-|through)\s*(\d+))?',
        ]
        
        self.service_patterns = [
            r'(\d+)\s*services?',
            r'multiple\s*services?',
            r'different\s*(?:services?|pbit)',
        ]
        
        self.forwarder_patterns = [
            r'1:1\s*forwarder',
            r'N:1\s*forwarder',
            r'forwarder\s*(?:type\s*)?(?:is\s*)?([1N]:[1N])',
        ]

    def setup_entity_rules(self):
        """Setup entity extraction rules"""
        self.entity_defaults = {
            'lines': [],
            'user_vlans': [],
            'network_vlans': [],
            'user_pbits': [],
            'network_pbits': [],
            'protocols': [],
            'uplinks': [1],
            'forwarder_type': '1:1',
            'is_untagged': False,
            'is_multi_line': False,
            'is_all_lines': False,
            'is_multi_service': False,
            'service_count': 1,
            'confidence_scores': {}
        }

    def extract_comprehensive_entities(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive entities with advanced NLP"""
        entities = self.entity_defaults.copy()
        text_lower = text.lower()
        
        # Extract lines
        self._extract_lines_advanced(text, entities)
        
        # Extract VLANs
        self._extract_vlans_advanced(text, entities)
        
        # Extract forwarder type
        self._extract_forwarder_type_advanced(text, entities)
        
        # Extract services
        self._extract_services_advanced(text, entities)
        
        # Extract PBITs
        self._extract_pbits_advanced(text, entities)
        
        # Extract protocols
        self._extract_protocols_advanced(text, entities)
        
        # Post-processing
        self._post_process_entities(entities, text)
        
        return entities

    def _extract_lines_advanced(self, text: str, entities: Dict[str, Any]):
        """Advanced line extraction"""
        text_lower = text.lower()
        
        # Check for all lines
        if re.search(r'all\s*(?:16|sixteen)\s*lines', text_lower):
            entities['lines'] = list(range(1, 17))
            entities['is_all_lines'] = True
            return
        
        # Extract specific lines
        lines_found = set()
        for pattern in self.line_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    if match.group(2):  # Range pattern
                        start_line = int(match.group(1))
                        end_line = int(match.group(2))
                        lines_found.update(range(start_line, end_line + 1))
                    else:
                        line_num = int(match.group(1))
                        if 1 <= line_num <= 48:
                            lines_found.add(line_num)
                except (ValueError, IndexError):
                    continue
        
        if lines_found:
            entities['lines'] = sorted(list(lines_found))
        else:
            entities['lines'] = [1]  # Default

    def _extract_vlans_advanced(self, text: str, entities: Dict[str, Any]):
        """Advanced VLAN extraction"""
        # Extract VLAN numbers
        vlans_found = set()
        for pattern in self.vlan_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    vlan_id = int(match.group(1))
                    if 1 <= vlan_id <= 4094:
                        vlans_found.add(vlan_id)
                except (ValueError, IndexError):
                    continue
        
        # Classify VLANs as user or network based on context
        for vlan in vlans_found:
            context = self._get_vlan_context(text, str(vlan))
            if 'user' in context or 'customer' in context:
                entities['user_vlans'].append(vlan)
            else:
                entities['network_vlans'].append(vlan)
        
        # Check for untagged
        entities['is_untagged'] = bool(re.search(r'untagged|no.?tag', text.lower()))

    def _extract_forwarder_type_advanced(self, text: str, entities: Dict[str, Any]):
        """Advanced forwarder type extraction"""
        text_lower = text.lower()
        
        for pattern in self.forwarder_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if '1:1' in match.group(0):
                    entities['forwarder_type'] = '1:1'
                elif 'n:1' in match.group(0):
                    entities['forwarder_type'] = 'N:1'
                break

    def _extract_services_advanced(self, text: str, entities: Dict[str, Any]):
        """Advanced service extraction"""
        text_lower = text.lower()
        
        # Check for multiple services
        for pattern in self.service_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities['is_multi_service'] = True
                try:
                    if match.group(1) and match.group(1).isdigit():
                        entities['service_count'] = int(match.group(1))
                except (IndexError, ValueError):
                    entities['service_count'] = 2  # Default for multiple
                break
        
        # Check for different PBIT per service
        if re.search(r'different\s*(?:pbit|priority)', text_lower):
            entities['different_pbit_per_service'] = True

    def _extract_pbits_advanced(self, text: str, entities: Dict[str, Any]):
        """Advanced PBIT extraction"""
        text_lower = text.lower()
        
        # Check for PBIT range
        if re.search(r'all\s*pbit|pbit\s*(?:0-7|range)', text_lower):
            entities['all_pbit_range'] = True
            return
        
        # Extract specific PBITs
        pbit_pattern = r'(?:pbit|priority)\s*(\d+)'
        matches = re.finditer(pbit_pattern, text_lower)
        for match in matches:
            try:
                pbit = int(match.group(1))
                if 0 <= pbit <= 7:
                    entities['user_pbits'].append(pbit)
            except (ValueError, IndexError):
                continue

    def _extract_protocols_advanced(self, text: str, entities: Dict[str, Any]):
        """Advanced protocol extraction"""
        protocols = []
        if 'ipv6' in text.lower():
            protocols.append('IPv6')
        if 'pppoe' in text.lower():
            protocols.append('PPPoE')
        entities['protocols'] = protocols

    def _get_vlan_context(self, text: str, vlan_str: str) -> str:
        """Get context around VLAN mention"""
        sentences = text.split('.')
        for sentence in sentences:
            if vlan_str in sentence:
                return sentence.lower()
        return ""

    def _post_process_entities(self, entities: Dict[str, Any], text: str):
        """Post-process extracted entities"""
        # Set multi-line flags
        entities['is_multi_line'] = len(entities['lines']) > 1
        entities['is_all_lines'] = len(entities['lines']) == 16
        
        # Ensure default values
        if not entities['user_pbits'] and not entities.get('all_pbit_range'):
            entities['user_pbits'] = [0]
        
        if not entities['network_pbits'] and not entities.get('all_pbit_range'):
            entities['network_pbits'] = [0]


# Enhanced Intelligent Configuration Generator with complete implementation
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

    def _generate_multi_service_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate multi-service configuration"""
        service_count = entities.get('service_count', 1)
        service_type = entities.get('service_type', entities['forwarder_type'])
        target_lines = entities['lines']

        if len(target_lines) == 1:
            line_num = target_lines[0]
            return self._generate_single_line_multi_service(entities, lines, line_num, service_count, service_type)
        else:
            return self._generate_multi_line_multi_service(entities, lines, target_lines, service_count, service_type)

    def _generate_single_line_multi_service(self, entities: Dict, lines: List[str], line_num: int, service_count: int, service_type: str) -> str:
        """Generate multiple services on a single line"""
        vsi_counter = 1

        for service_idx in range(service_count):
            user_vlan = 101 + service_idx
            network_vlan = user_vlan if service_type == '1:1' else user_vlan

            # Determine PBIT
            if entities.get('different_pbit_per_service'):
                pbit_values = [0, 2, 5]
                user_pbit = pbit_values[service_idx % len(pbit_values)]
                network_pbit = user_pbit
            elif entities.get('all_pbit_range'):
                user_pbit = "0,1,2,3,4,5,6,7"
                network_pbit = user_pbit
            else:
                user_pbit = 0
                network_pbit = 0

            # Generate UserVSI
            lines.append(f"UserVSI-{vsi_counter} = VLAN={user_vlan}, PBIT={user_pbit}")
            lines.append(f"UserVSI-{vsi_counter} Parent = Line{line_num}")

            # Generate NetworkVSI
            lines.append(f"NetworkVSI-{vsi_counter} = VLAN={network_vlan}, PBIT={network_pbit}")
            lines.append(f"NetworkVSI-{vsi_counter} Parent = Uplink{entities['uplinks'][0]}")

            # Generate Forwarder
            if service_idx < service_count - 1:
                lines.append(f"Forwarder-{vsi_counter} {service_type}")
            else:
                lines.append(f"Forwarder {service_type}")

            vsi_counter += 1

        return "\n".join(lines)

    def _generate_multi_line_multi_service(self, entities: Dict, lines: List[str], target_lines: List[int], service_count: int, service_type: str) -> str:
        """Generate services across multiple lines"""
        vsi_counter = 1

        for service_idx in range(service_count):
            user_vlan = 101 + service_idx
            network_vlan = user_vlan

            if entities.get('different_pbit_per_service'):
                pbit_values = [0, 2, 5]
                pbit = pbit_values[service_idx % len(pbit_values)]
            else:
                pbit = 0

            # Create UserVSI for each line
            for line_num in target_lines:
                lines.append(f"UserVSI-{vsi_counter} = VLAN={user_vlan}, PBIT={pbit}")
                lines.append(f"UserVSI-{vsi_counter} Parent = Line{line_num}")
                vsi_counter += 1

            # Create single NetworkVSI for this service
            lines.append(f"NetworkVSI-{service_idx + 1} = VLAN={network_vlan}, PBIT={pbit}")
            lines.append(f"NetworkVSI-{service_idx + 1} Parent = Uplink{entities['uplinks'][0]}")

            if service_idx < service_count - 1:
                lines.append(f"Forwarder-{service_idx + 1} {service_type}")
            else:
                lines.append(f"Forwarder-{service_idx + 1} 1:1")

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

    def _generate_single_line_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate single line configuration"""
        line_num = entities['lines'][0] if entities['lines'] else 1
        forwarder_type = entities['forwarder_type']

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

    def _get_user_vlan(self, entities: Dict, index: int, line_num: int) -> str:
        """Get user VLAN"""
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
        
        return str(101 + index)

    def _get_network_vlan(self, entities: Dict, line_num: int, forwarder_type: str) -> str:
        """Get network VLAN"""
        if entities['network_vlans']:
            return str(entities['network_vlans'][0])
        
        if forwarder_type == '1:1':
            # Use same as user VLAN for transparent 1:1
            user_vlan = self._get_user_vlan(entities, 0, line_num)
            return user_vlan if user_vlan != "No" else "1001"
        else:
            return "1000"

    def _get_network_vlan_for_group(self, entities: Dict, target_lines: List[int], forwarder_type: str) -> str:
        """Get network VLAN for a group of lines"""
        if entities['network_vlans']:
            return str(entities['network_vlans'][0])
        return "1000"

    def _get_user_pbit(self, entities: Dict, index: int) -> str:
        """Get user PBIT"""
        if entities['is_untagged']:
            return "No"

        if entities.get('all_pbit_range'):
            return "0,1,2,3,4,5,6,7"

        if entities['user_pbits']:
            if index < len(entities['user_pbits']):
                return str(entities['user_pbits'][index])
            else:
                return str(entities['user_pbits'][0])

        return "0"

    def _get_network_pbit(self, entities: Dict, index: int) -> str:
        """Get network PBIT"""
        if entities['is_untagged']:
            return "No"

        if entities.get('all_pbit_range'):
            return "0,1,2,3,4,5,6,7"

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

        # Parse VSI config to understand VLAN mappings
        vsi_mappings = self._parse_vsi_configuration(vsi_config)

        # Upstream traffic
        lines.extend(self._generate_upstream_traffic(entities, target_lines, is_multi_line, vsi_mappings))

        # Downstream traffic
        lines.extend(self._generate_downstream_traffic(entities, target_lines, is_multi_line, vsi_mappings))

        return "\n".join(lines)

    def _parse_vsi_configuration(self, vsi_config: str) -> Dict:
        """Parse VSI configuration to extract mappings"""
        mappings = {
            'user_vlans': {},
            'network_vlans': {},
            'line_to_user_vsi': {},
        }

        lines = vsi_config.split('\n')
        for line in lines:
            line = line.strip()

            # Parse UserVSI
            if line.startswith('UserVSI-'):
                match = re.search(r'UserVSI-(\d+)\s*=\s*VLAN=([^,]+),\s*PBIT=(\w+)', line)
                if match:
                    vsi_num = int(match.group(1))
                    vlan = match.group(2)
                    pbit = match.group(3)
                    mappings['user_vlans'][vsi_num] = {'vlan': vlan, 'pbit': pbit}

            elif line.startswith('UserVSI-') and 'Parent' in line:
                match = re.search(r'UserVSI-(\d+)\s*Parent\s*=\s*Line(\d+)', line)
                if match:
                    vsi_num = int(match.group(1))
                    line_num = int(match.group(2))
                    mappings['line_to_user_vsi'][line_num] = vsi_num

            # Parse NetworkVSI
            elif line.startswith('NetworkVSI-'):
                match = re.search(r'NetworkVSI-(\d+)\s*=\s*VLAN=([^,]+),\s*PBIT=(\w+)', line)
                if match:
                    vsi_num = int(match.group(1))
                    vlan = match.group(2)
                    pbit = match.group(3)
                    mappings['network_vlans'][vsi_num] = {'vlan': vlan, 'pbit': pbit}

        return mappings

    def _generate_upstream_traffic(self, entities: Dict, target_lines: List[int], is_multi_line: bool, vsi_mappings: Dict) -> List[str]:
        """Generate upstream traffic configuration"""
        lines = [
            "Test Eqpt - Upstream",
            "Entity2 = User Side Traffic Eqpt",
            "Entity2 Keywords=",
            "NumPackets To Generate = 100"
        ]

        for i, line_num in enumerate(target_lines):
            # Get VLAN and PBIT from VSI mappings
            if line_num in vsi_mappings['line_to_user_vsi']:
                vsi_num = vsi_mappings['line_to_user_vsi'][line_num]
                if vsi_num in vsi_mappings['user_vlans']:
                    user_info = vsi_mappings['user_vlans'][vsi_num]
                    user_vlan = user_info['vlan']
                    user_pbit = user_info['pbit']
                else:
                    user_vlan = str(101 + i)
                    user_pbit = "0"
            else:
                user_vlan = str(101 + i)
                user_pbit = "0"

            # Generate packet header
            src_mac = f"99:02:03:04:{i+1:02d}:11"
            dst_mac = f"98:0A:0B:0C:{i+1:02d}:0C"
            
            lines.append(f"Packet Line{line_num} L2 Header")
            lines.append(f"Src MAC = {src_mac}")
            lines.append(f"Dst MAC = {dst_mac}")

            if entities['is_untagged']:
                lines.append("VLAN=No, PBIT=No")
            else:
                lines.append(f"VLAN = {user_vlan}, PBIT = {user_pbit}")

            # Add protocol headers
            for protocol in entities['protocols']:
                if protocol == 'IPv6':
                    lines.append("L3 Header = Ipv6")
                elif protocol == 'PPPoE':
                    lines.append("Next Header = PPPoE")

        return lines

    def _generate_downstream_traffic(self, entities: Dict, target_lines: List[int], is_multi_line: bool, vsi_mappings: Dict) -> List[str]:
        """Generate downstream traffic configuration"""
        lines = [
            "",
            "Test Eqpt - Downstream",
            "Entity3 = Network Side Traffic Eqpt",
            "Entity3 Keywords=",
            "NumPackets To Generate = 100"
        ]

        for i, line_num in enumerate(target_lines):
            # Get network VLAN and PBIT
            network_vlan, network_pbit = self._get_network_traffic_vlan_pbit(entities, line_num, i, vsi_mappings)

            # Generate packet header
            src_mac = f"11:12:13:14:{i+1:02d}:CC"
            dst_mac = f"AA:BB:CC:DD:{i+1:02d}:EE"
            
            lines.append(f"Packet Line{line_num} L2 Header")
            lines.append(f"Src MAC = {src_mac}")
            lines.append(f"Dst MAC = {dst_mac}")
            lines.append(f"VLAN = {network_vlan}, PBIT = {network_pbit}")

            # Add protocol headers
            for protocol in entities['protocols']:
                if protocol == 'IPv6':
                    lines.append("L3 Header = Ipv6")
                elif protocol == 'PPPoE':
                    lines.append("Next Header = PPPoE")

        return lines

    def _get_network_traffic_vlan_pbit(self, entities: Dict, line_num: int, index: int, vsi_mappings: Dict) -> Tuple[str, str]:
        """Get network VLAN and PBIT for traffic generation"""
        if entities['forwarder_type'] == '1:1':
            vsi_num = index + 1
            if vsi_num in vsi_mappings['network_vlans']:
                network_info = vsi_mappings['network_vlans'][vsi_num]
                return network_info['vlan'], network_info['pbit']
            return str(1000 + line_num), "0"
        else:
            # N:1 - use NetworkVSI-1
            if 1 in vsi_mappings['network_vlans']:
                network_info = vsi_mappings['network_vlans'][1]
                return network_info['vlan'], network_info['pbit']
            return "1000", "0"
