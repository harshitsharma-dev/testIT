import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

class AdvancedEntityExtractor:
    def __init__(self):
        self.forwarder_patterns = {
            '1:1': [
                r'1:1\s+forwarder', r'one.*to.*one', r'1-to-1', r'1:1\s+service',
                r'dedicated.*forwarder', r'individual.*forwarder'
            ],
            'N:1': [
                r'n:1\s+forwarder', r'many.*to.*one', r'n-to-1', r'n:1\s+service',
                r'aggregat.*forwarder', r'multiple.*to.*single'
            ]
        }

    def extract_comprehensive_entities(self, text: str) -> Dict[str, Any]:
        """Extract all entities with advanced pattern matching"""
        entities = {
            'user_vlans': [],
            'network_vlans': [],
            'lines': [],
            'uplinks': [1],  # Default uplink
            'user_pbits': [],
            'network_pbits': [],
            'forwarder_type': 'N:1',  # Default
            'protocols': [],
            'is_untagged': False,
            'is_multi_line': False,
            'is_all_lines': False,
            'line_ranges': [],
            'mixed_forwarders': {},
            'traffic_directions': []
        }

        text_lower = text.lower()

        # Enhanced VLAN extraction with context awareness
        self._extract_vlans(text, entities)

        # Enhanced line extraction
        self._extract_lines(text, entities)

        # Enhanced forwarder detection
        self._extract_forwarder_type(text, entities)

        # PBIT extraction from traffic descriptions
        self._extract_pbits(text, entities)

        # Protocol detection
        self._extract_protocols(text, entities)

        # Untagged detection
        self._detect_untagged(text, entities)

        # Mixed forwarder scenarios
        self._detect_mixed_forwarders(text, entities)

        # Uplink extraction
        self._extract_uplinks(text, entities)

        return entities

    def _extract_vlans(self, text: str, entities: Dict):
        """Extract VLANs with context awareness"""
        # User side VLAN patterns
        user_patterns = [
            r'user.*?(?:vlan|tag|identifier).*?(\d+)',
            r'(?:vlan|tag|identifier).*?(\d+).*?(?:on|for).*?line',
            r'upstream.*?(?:vlan|tag|identifier).*?(\d+)',
            r'line\s*\d+.*?(?:vlan|tag|identifier).*?(\d+)'
        ]

        # Network side VLAN patterns
        network_patterns = [
            r'network.*?(?:vlan|tag|identifier).*?(\d+)',
            r'(?:vlan|tag|identifier).*?(\d+).*?(?:on|for).*?uplink',
            r'downstream.*?(?:vlan|tag|identifier).*?(\d+)',
            r'uplink\s*\d+.*?(?:vlan|tag|identifier).*?(\d+)'
        ]

        # Extract user VLANs
        for pattern in user_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['user_vlans'].extend([int(v) for v in matches])

        # Extract network VLANs
        for pattern in network_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['network_vlans'].extend([int(v) for v in matches])

        # Generic VLAN extraction as fallback
        all_vlans = re.findall(r'(?:vlan|tag|identifier)[^a-z]*(\d+)', text, re.IGNORECASE)
        all_vlans = [int(v) for v in all_vlans]

        # If no specific user/network VLANs found, use context
        if not entities['user_vlans'] and not entities['network_vlans'] and all_vlans:
            if len(all_vlans) >= 2:
                entities['user_vlans'] = [all_vlans[0]]
                entities['network_vlans'] = [all_vlans[1]]
            else:
                entities['user_vlans'] = all_vlans

        # Remove duplicates
        entities['user_vlans'] = sorted(list(set(entities['user_vlans'])))
        entities['network_vlans'] = sorted(list(set(entities['network_vlans'])))

    def _extract_lines(self, text: str, entities: Dict):
        """Extract line information with range support"""
        # Check for "all lines" patterns
        all_patterns = [
            r'all\s+(?:16\s+)?lines?', r'all\s+lines?', r'for\s+all\s+lines?',
            r'16\s+lines?', r'every\s+line'
        ]

        for pattern in all_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                entities['is_all_lines'] = True
                entities['lines'] = list(range(1, 17))
                break

        if not entities['is_all_lines']:
            # Extract specific line numbers
            line_matches = re.findall(r'line\s*(\d+)', text, re.IGNORECASE)
            entities['lines'] = sorted([int(l) for l in line_matches])

            # Check for line ranges
            range_matches = re.findall(r'(?:first|lines?)\s*(\d+)', text, re.IGNORECASE)
            if range_matches:
                first_n = int(range_matches[0])
                entities['line_ranges'].append(('first', first_n))
                if 'remaining' in text.lower():
                    entities['line_ranges'].append(('remaining', 16 - first_n))

        # Set multi-line flag
        entities['is_multi_line'] = len(entities['lines']) > 1 or entities['is_all_lines']

        # Default to Line1 if no lines specified
        if not entities['lines']:
            entities['lines'] = [1]

    def _extract_forwarder_type(self, text: str, entities: Dict):
        """Detect forwarder type with context"""
        text_lower = text.lower()

        # Check for explicit forwarder mentions
        for ftype, patterns in self.forwarder_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    entities['forwarder_type'] = ftype
                    return

        # Context-based detection
        if any(word in text_lower for word in ['dedicated', 'individual', 'separate']):
            entities['forwarder_type'] = '1:1'
        elif any(word in text_lower for word in ['aggregate', 'combine', 'single network']):
            entities['forwarder_type'] = 'N:1'

    def _extract_pbits(self, text: str, entities: Dict):
        """Extract PBIT values from traffic descriptions"""
        # Upstream PBIT
        upstream_pbit = re.findall(r'upstream.*?pbit\s*(\d+)', text, re.IGNORECASE)
        if upstream_pbit:
            entities['user_pbits'] = [int(upstream_pbit[0])]

        # Downstream PBIT
        downstream_pbit = re.findall(r'downstream.*?pbit\s*(\d+)', text, re.IGNORECASE)
        if downstream_pbit:
            entities['network_pbits'] = [int(downstream_pbit[0])]

        # Generic PBIT extraction
        if not entities['user_pbits'] and not entities['network_pbits']:
            all_pbits = re.findall(r'pbit\s*(\d+)', text, re.IGNORECASE)
            if all_pbits:
                pbits = [int(p) for p in all_pbits]
                if len(pbits) >= 2:
                    entities['user_pbits'] = [pbits[0]]
                    entities['network_pbits'] = [pbits[1]]
                else:
                    entities['user_pbits'] = pbits

    def _extract_protocols(self, text: str, entities: Dict):
        """Extract protocol information"""
        text_lower = text.lower()

        if any(ipv6 in text_lower for ipv6 in ['ipv6', 'internet protocol version 6']):
            entities['protocols'].append('IPv6')
        if 'pppoe' in text_lower:
            entities['protocols'].append('PPPoE')

    def _detect_untagged(self, text: str, entities: Dict):
        """Detect untagged traffic"""
        entities['is_untagged'] = 'untagged' in text.lower()

    def _detect_mixed_forwarders(self, text: str, entities: Dict):
        """Detect mixed forwarder scenarios"""
        text_lower = text.lower()

        # Enhanced pattern for mixed forwarders
        mixed_patterns = [
            r'first\s+(\d+)\s+lines?.*?1:1.*?(?:remaining|next|last).*?(\d+)?.*?n:1',
            r'(\d+)\s+lines?.*?1:1.*?(?:remaining|next|last).*?(\d+)?.*?n:1'
        ]

        for pattern in mixed_patterns:
            match = re.search(pattern, text_lower)
            if match:
                first_count = int(match.group(1))
                entities['mixed_forwarders'] = {
                    'first_lines': list(range(1, first_count + 1)),
                    'first_type': '1:1',
                    'remaining_lines': list(range(first_count + 1, 17)),
                    'remaining_type': 'N:1'
                }
                break

    def _extract_uplinks(self, text: str, entities: Dict):
        """Extract uplink information"""
        uplink_matches = re.findall(r'uplink\s*(\d+)', text, re.IGNORECASE)
        if uplink_matches:
            entities['uplinks'] = [int(u) for u in uplink_matches]


class IntelligentConfigGenerator:
    def __init__(self):
        self.entity_extractor = AdvancedEntityExtractor()

    def generate_configuration(self, input_text: str) -> str:
        """Generate complete configuration from input text"""
        entities = self.entity_extractor.extract_comprehensive_entities(input_text)

        # Generate VSI configuration
        vsi_config = self._generate_vsi_configuration(entities)

        # Generate traffic configuration
        traffic_config = self._generate_traffic_configuration(entities, vsi_config)

        return vsi_config + "\n" + traffic_config

    def _generate_vsi_configuration(self, entities: Dict) -> str:
        """Generate VSI configuration based on entities"""
        lines = ["Entity1 = DUT", "Entity1 Keywords ="]

        if entities['mixed_forwarders']:
            return self._generate_mixed_forwarder_config(entities, lines)
        elif entities['is_all_lines'] or entities['is_multi_line']:
            return self._generate_multi_line_config(entities, lines)
        else:
            return self._generate_single_line_config(entities, lines)

    def _generate_single_line_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate single line configuration"""
        line = entities['lines'][0] if entities['lines'] else 1
        forwarder_type = entities['forwarder_type']

        # Determine VLANs
        if entities['is_untagged']:
            user_vlan = "No"
            user_pbit = "No"
            network_vlan = 101
            network_pbit = 0
        else:
            user_vlan = entities['user_vlans'][0] if entities['user_vlans'] else (700 if forwarder_type == '1:1' else 100)
            network_vlan = self._determine_network_vlan(user_vlan, forwarder_type, entities)
            user_pbit = entities['user_pbits'][0] if entities['user_pbits'] else 0
            network_pbit = entities['network_pbits'][0] if entities['network_pbits'] else user_pbit

        # UserVSI
        lines.append(f"UserVSI-1 = VLAN={user_vlan}, PBIT={user_pbit}")
        lines.append(f"UserVSI-1 Parent = Line{line}")

        # NetworkVSI
        lines.append(f"NetworkVSI-1 = VLAN={network_vlan}, PBIT={network_pbit}")
        lines.append(f"NetworkVSI-1 Parent = Uplink{entities['uplinks'][0]}")

        # Forwarder
        lines.append(f"Forwarder = {forwarder_type}")

        return "\n".join(lines)

    def _generate_multi_line_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate multi-line configuration"""
        target_lines = entities['lines'] if not entities['is_all_lines'] else list(range(1, 17))
        forwarder_type = entities['forwarder_type']

        # Generate UserVSI entries for all lines
        for i, line in enumerate(target_lines):
            if entities['is_untagged']:
                user_vlan = "No"
                user_pbit = "No"
            else:
                if entities['user_vlans']:
                    user_vlan = entities['user_vlans'][i] if i < len(entities['user_vlans']) else entities['user_vlans'][0]
                else:
                    user_vlan = 100 + i + 1  # Default pattern: 101, 102, 103...

                user_pbit = entities['user_pbits'][i] if i < len(entities['user_pbits']) else (entities['user_pbits'][0] if entities['user_pbits'] else 0)

            lines.append(f"UserVSI-{i+1} = VLAN={user_vlan}, PBIT={user_pbit}")
            lines.append(f"UserVSI-{i+1} Parent = Line{line}")

        # Generate NetworkVSI entries based on forwarder type
        if forwarder_type == '1:1':
            # 1:1 forwarder: one NetworkVSI per UserVSI
            for i, line in enumerate(target_lines):
                if entities['is_untagged']:
                    network_vlan = 100 + i + 1
                    network_pbit = 0
                else:
                    if entities['network_vlans']:
                        network_vlan = entities['network_vlans'][i] if i < len(entities['network_vlans']) else entities['network_vlans'][0]
                    else:
                        # For 1:1 all lines: first line same VLAN, others +1000
                        user_vlan = entities['user_vlans'][i] if i < len(entities['user_vlans']) else (100 + i + 1)
                        if i == 0:
                            network_vlan = user_vlan  # Same VLAN for first line
                        else:
                            network_vlan = user_vlan + 900  # Pattern: 102->1002, 103->1003

                    network_pbit = entities['network_pbits'][i] if i < len(entities['network_pbits']) else (entities['network_pbits'][0] if entities['network_pbits'] else 0)

                lines.append(f"NetworkVSI-{i+1} = VLAN={network_vlan}, PBIT={network_pbit}")
                lines.append(f"NetworkVSI-{i+1} Parent = Uplink{entities['uplinks'][0]}")
                lines.append(f"Forwarder-{i+1} 1:1")
        else:
            # N:1 forwarder: single NetworkVSI for all UserVSIs
            if entities['is_untagged']:
                network_vlan = 1000
                network_pbit = 0
            else:
                network_vlan = entities['network_vlans'][0] if entities['network_vlans'] else 1000
                network_pbit = entities['network_pbits'][0] if entities['network_pbits'] else 0

            lines.append(f"NetworkVSI-1 = VLAN={network_vlan}, PBIT={network_pbit}")
            lines.append(f"NetworkVSI-1 Parent = Uplink{entities['uplinks'][0]}")
            lines.append("Forwarder N:1")

        return "\n".join(lines)

    def _generate_mixed_forwarder_config(self, entities: Dict, lines: List[str]) -> str:
        """Generate mixed forwarder configuration"""
        mixed = entities['mixed_forwarders']
        first_lines = mixed['first_lines']
        remaining_lines = mixed['remaining_lines']

        # Generate UserVSI for all 16 lines
        for i in range(1, 17):
            user_vlan = 100 + i
            lines.append(f"UserVSI-{i} = VLAN={user_vlan}, PBIT=0")
            lines.append(f"UserVSI-{i} Parent = Line{i}")

        # Generate NetworkVSI for first 8 lines (1:1 forwarder)
        for i in first_lines:
            network_vlan = 1000 + i  # Pattern: 1001, 1002, 1003...
            lines.append(f"NetworkVSI-{i} = VLAN={network_vlan}, PBIT=0")
            lines.append(f"NetworkVSI-{i} Parent = Uplink1")
            lines.append(f"Forwarder-{i} 1:1")

        # Generate NetworkVSI for remaining 8 lines (N:1 forwarder)
        network_vlan = 1009  # Single network VLAN for N:1
        lines.append(f"NetworkVSI-9 = VLAN={network_vlan}, PBIT=0")
        lines.append(f"NetworkVSI-9 Parent = Uplink1")
        lines.append("Forwarder-9 N:1")

        return "\n".join(lines)

    def _determine_network_vlan(self, user_vlan, forwarder_type: str, entities: Dict) -> int:
        """Determine network VLAN based on forwarder type and context"""
        if entities['network_vlans']:
            return entities['network_vlans'][0]

        if forwarder_type == '1:1':
            # For 1:1, network VLAN = user VLAN (same VLAN)
            return user_vlan
        else:
            # For N:1, network VLAN = user VLAN + offset or specific pattern
            if isinstance(user_vlan, int):
                if user_vlan < 200:
                    return user_vlan + 100  # e.g., 100 -> 200
                else:
                    return user_vlan + 1000  # e.g., 110 -> 1110
            return 1000  # Default for N:1

    def _parse_vsi_configuration(self, vsi_config: str) -> Dict:
        """Parse VSI configuration to extract VLAN mappings"""
        vsi_mappings = {
            'user_vlans': {},  # line_num -> vlan
            'network_vlans': {},  # vsi_num -> vlan
            'forwarder_map': {}  # line_num -> network_vsi_num
        }

        lines = vsi_config.split('\n')
        
        for line in lines:
            line = line.strip()

            # Parse UserVSI
            if line.startswith('UserVSI-'):
                match = re.search(r'UserVSI-(\d+)\s*=\s*VLAN=([^,]+),\s*PBIT=(\d+)', line)
                if match:
                    vsi_num = int(match.group(1))
                    vlan = match.group(2)
                    vsi_mappings['user_vlans'][vsi_num] = vlan

            elif line.startswith('NetworkVSI-'):
                match = re.search(r'NetworkVSI-(\d+)\s*=\s*VLAN=([^,]+),\s*PBIT=(\d+)', line)
                if match:
                    vsi_num = int(match.group(1))
                    vlan = match.group(2)
                    vsi_mappings['network_vlans'][vsi_num] = vlan

        return vsi_mappings

    def _generate_traffic_configuration(self, entities: Dict, vsi_config: str) -> str:
        """Generate traffic equipment configuration with VLAN consistency"""
        lines = []

        # Parse VSI configuration to get VLAN mappings
        vsi_mappings = self._parse_vsi_configuration(vsi_config)

        # Determine which lines to generate traffic for
        target_lines = entities['lines'] if not entities['is_all_lines'] else list(range(1, 17))
        is_multi_line = len(target_lines) > 1

        # Upstream traffic configuration
        lines.extend(self._generate_upstream_traffic(entities, target_lines, is_multi_line, vsi_mappings))

        # Downstream traffic configuration
        lines.extend(self._generate_downstream_traffic(entities, target_lines, is_multi_line, vsi_mappings))

        return "\n".join(lines)

    def _generate_upstream_traffic(self, entities: Dict, target_lines: List[int], is_multi_line: bool, vsi_mappings: Dict) -> List[str]:
        """Generate upstream traffic configuration"""
        lines = ["Test Eqpt - Upstream", "Entity2 = User Side Traffic Eqpt", "Entity2 Keywords=", "NumPackets To Generate = 100"]

        # User side packets
        for i, line in enumerate(target_lines):
            # Get user VLAN from VSI mapping or fallback
            if (i+1) in vsi_mappings['user_vlans']:
                user_vlan = vsi_mappings['user_vlans'][i+1]
                user_pbit = 0
            elif entities['is_untagged']:
                user_vlan = "No"
                user_pbit = "No"
            else:
                user_vlan = entities['user_vlans'][i] if i < len(entities['user_vlans']) else (100 + i + 1)
                user_pbit = entities['user_pbits'][i] if i < len(entities['user_pbits']) else (entities['user_pbits'][0] if entities['user_pbits'] else 0)

            # Generate MAC addresses
            if is_multi_line:
                src_mac = f"99:02:03:04:{i+1:02d}:11"
                dst_mac = f"98:0A:0B:0C:{i+1:02d}:0C"
                lines.append(f"Packet Line{line} L2 Header ")
            else:
                src_mac = "99:02:03:04:05:06"
                dst_mac = "98:0A:0B:0C:0D:0E"
                lines.append("Packet  L2 Header ")

            lines.append(f"Src MAC = {src_mac}")
            lines.append(f"Dst MAC = {dst_mac}")

            if entities['is_untagged']:
                lines.append(f"VLAN = {user_vlan}, PBIT ={user_pbit}")
            else:
                lines.append(f"VLAN = {user_vlan}, PBIT ={user_pbit}")

            # Add protocol headers
            for protocol in entities['protocols']:
                if protocol == 'IPv6':
                    lines.append("L3 Header= Ipv6")
                elif protocol == 'PPPoE':
                    lines.append("Next Header= PPPoE")

        # Network side reception
        lines.extend(["Entity3 = Network Side Traffic Eqpt", "Entity3 Keywords=", "NumPackets To Recieve = 100"])

        for i, line in enumerate(target_lines):
            # Determine network VLAN based on forwarder type and VSI mapping
            network_vlan = self._get_network_vlan_for_traffic(entities, i, target_lines, vsi_mappings)
            network_pbit = entities['network_pbits'][i] if i < len(entities['network_pbits']) else (entities['network_pbits'][0] if entities['network_pbits'] else 0)

            if is_multi_line:
                src_mac = f"99:02:03:04:{i+1:02d}:11"
                dst_mac = f"98:0A:0B:0C:{i+1:02d}:0C"
                lines.append(f"Packet Line{line} L2 Header ")
            else:
                src_mac = "99:02:03:04:05:06"
                dst_mac = "98:0A:0B:0C:0D:0E"
                lines.append("Packet L2 Header ")

            lines.append(f"Src MAC = {src_mac}")
            lines.append(f"Dst MAC = {dst_mac}")
            lines.append(f"VLAN = {network_vlan}, PBIT ={network_pbit}")

            # Add protocol headers
            for protocol in entities['protocols']:
                if protocol == 'IPv6':
                    lines.append("L3 Header= Ipv6")
                elif protocol == 'PPPoE':
                    lines.append("Next Header= PPPoE")

        return lines

    def _generate_downstream_traffic(self, entities: Dict, target_lines: List[int], is_multi_line: bool, vsi_mappings: Dict) -> List[str]:
        """Generate downstream traffic configuration"""
        lines = ["Test Eqpt - Downstream", "Entity3 = Network Side Traffic Eqpt", "Entity3 Keywords=", "NumPackets To Generate = 100"]

        # Network side packets (swapped MACs)
        for i, line in enumerate(target_lines):
            network_vlan = self._get_network_vlan_for_traffic(entities, i, target_lines, vsi_mappings)
            network_pbit = entities['network_pbits'][i] if i < len(entities['network_pbits']) else (entities['network_pbits'][0] if entities['network_pbits'] else 0)

            if is_multi_line:
                src_mac = f"98:0A:0B:0C:{i+1:02d}:0C"
                dst_mac = f"99:02:03:04:{i+1:02d}:11"
                lines.append(f"Packet Line{line} L2 Header ")
            else:
                src_mac = "98:0A:0B:0C:0D:0E"
                dst_mac = "99:02:03:04:05:06"
                lines.append("Packet L2 Header ")

            lines.append(f"Src MAC = {src_mac}")
            lines.append(f"Dst MAC = {dst_mac}")
            lines.append(f"VLAN = {network_vlan}, PBIT ={network_pbit}")

            # Add protocol headers
            for protocol in entities['protocols']:
                if protocol == 'IPv6':
                    lines.append("L3 Header = Ipv6")
                elif protocol == 'PPPoE':
                    lines.append("Next Header= PPPoE")

        # User side reception
        lines.extend(["Entity2 = User Side Traffic Eqpt", "Entity2 Keywords=", "NumPackets To Recieve = 100"])

        for i, line in enumerate(target_lines):
            # Get user VLAN from VSI mapping
            if (i+1) in vsi_mappings['user_vlans']:
                user_vlan = vsi_mappings['user_vlans'][i+1]
                user_pbit = entities['network_pbits'][i] if i < len(entities['network_pbits']) else (entities['network_pbits'][0] if entities['network_pbits'] else 0)
            elif entities['is_untagged']:
                user_vlan = "No"
                user_pbit = "No"
            else:
                user_vlan = entities['user_vlans'][i] if i < len(entities['user_vlans']) else (100 + i + 1)
                user_pbit = entities['network_pbits'][i] if i < len(entities['network_pbits']) else (entities['network_pbits'][0] if entities['network_pbits'] else 0)

            if is_multi_line:
                src_mac = f"98:0A:0B:0C:{i+1:02d}:0C"
                dst_mac = f"99:02:03:04:{i+1:02d}:11"
                lines.append(f"Packet Line{line} L2 Header ")
            else:
                src_mac = "98:0A:0B:0C:0D:0E"
                dst_mac = "99:02:03:04:05:06"
                lines.append("Packet L2 Header ")

            lines.append(f"Src MAC = {src_mac}")
            lines.append(f"Dst MAC = {dst_mac}")

            if entities['is_untagged']:
                lines.append(f"VLAN = {user_vlan}, PBIT ={user_pbit}")
            else:
                lines.append(f"VLAN = {user_vlan}, PBIT ={user_pbit}")

            # Add protocol headers
            for protocol in entities['protocols']:
                if protocol == 'IPv6':
                    lines.append("L3 Header = Ipv6")
                elif protocol == 'PPPoE':
                    lines.append("Next Header= PPPoE")

        return lines

    def _get_network_vlan_for_traffic(self, entities: Dict, line_index: int, target_lines: List[int], vsi_mappings: Dict) -> int:
        """Get network VLAN for traffic generation with VSI consistency"""
        # Check if mixed forwarders
        if entities['mixed_forwarders']:
            line_num = target_lines[line_index]
            if line_num <= 8:
                # 1:1 forwarder for first 8 lines
                return 1000 + line_num  # 1001, 1002, 1003...
            else:
                # N:1 forwarder for remaining 8 lines
                return 1009

        # Check VSI mappings first
        if entities['forwarder_type'] == '1:1':
            vsi_num = line_index + 1
            if vsi_num in vsi_mappings['network_vlans']:
                return int(vsi_mappings['network_vlans'][vsi_num])
        else:
            # N:1 - use NetworkVSI-1
            if 1 in vsi_mappings['network_vlans']:
                return int(vsi_mappings['network_vlans'][1])

        # Fallback logic
        if entities['is_untagged']:
            return 101 if len(target_lines) == 1 else 1000

        if entities['network_vlans']:
            return entities['network_vlans'][0] if entities['forwarder_type'] == 'N:1' else (entities['network_vlans'][line_index] if line_index < len(entities['network_vlans']) else entities['network_vlans'][0])

        if entities['forwarder_type'] == '1:1':
            user_vlan = entities['user_vlans'][line_index] if line_index < len(entities['user_vlans']) else (100 + line_index + 1)
            if line_index == 0 and len(target_lines) > 1:
                return user_vlan  # Same VLAN for first line
            else:
                return user_vlan + 900  # Pattern for other lines
        else:
            # For N:1, single network VLAN
            base_vlan = entities['user_vlans'][0] if entities['user_vlans'] else 100
            return base_vlan + 100 if base_vlan < 200 else 1000
