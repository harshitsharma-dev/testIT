import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Tuple, Optional
import warnings
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from collections import defaultdict, Counter

warnings.filterwarnings('ignore')

class EnhancedNetworkConfigGenerator:
    """
    Enhanced Network Configuration Generator with advanced NLP and pattern recognition
    """
    
    def __init__(self):
        self.setup_nlp()
        self.setup_patterns()
        self.setup_templates()
        
    def setup_nlp(self):
        """Initialize NLP components"""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model 'en_core_web_sm' not found. Using basic pattern matching.")
            self.nlp = None
            
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
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

# For backward compatibility
class IntelligentConfigGenerator(EnhancedNetworkConfigGenerator):
    """Backward compatibility wrapper"""
    pass
