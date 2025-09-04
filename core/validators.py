"""
Enhanced validation logic for names and addresses with AI-based detection
"""

import requests
import re
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import Config, load_usps_credentials
from utils.logger import logger


class NameValidator:
    """Enhanced name validator with AI-based detection and standardization"""
    
    def __init__(self, dictionary_path: str = None):
        self.dictionary_path = dictionary_path
        self.first_names: Set[str] = set()
        self.last_names: Set[str] = set()
        self.dictionary_loaded = False
        
        # Name standardization mappings
        self.name_standardizations = {
            'bill': 'william', 'bob': 'robert', 'dick': 'richard', 'jim': 'james',
            'joe': 'joseph', 'mike': 'michael', 'steve': 'steven', 'dave': 'david',
            'tom': 'thomas', 'tony': 'anthony', 'chris': 'christopher', 'matt': 'matthew',
            'dan': 'daniel', 'sam': 'samuel', 'alex': 'alexander', 'ben': 'benjamin',
            'nick': 'nicholas', 'rick': 'richard', 'will': 'william', 'tim': 'timothy',
            'pat': 'patricia', 'sue': 'susan', 'liz': 'elizabeth', 'kate': 'katherine',
            'beth': 'elizabeth', 'anne': 'ann', 'maggie': 'margaret', 'peg': 'margaret',
            'jen': 'jennifer', 'jenn': 'jennifer', 'amy': 'amelia', 'becky': 'rebecca'
        }
        
        # Common prefixes and suffixes
        self.prefixes = {
            'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'professor', 'rev', 'reverend',
            'father', 'mother', 'sister', 'brother', 'sir', 'lady', 'lord', 'dame',
            'capt', 'captain', 'col', 'colonel', 'maj', 'major', 'lt', 'lieutenant',
            'sgt', 'sergeant', 'gen', 'general', 'admiral', 'judge', 'justice'
        }
        
        self.suffixes = {
            'jr', 'sr', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
            'md', 'phd', 'edd', 'jd', 'cpa', 'dds', 'dvm', 'rn', 'lpn', 'pa',
            'esq', 'esquire', 'pe', 'cpe', 'cfa', 'mba', 'ms', 'ma', 'bs', 'ba'
        }
        
        # Organization indicators
        self.org_indicators = {
            'llc', 'inc', 'corp', 'corporation', 'company', 'ltd', 'limited', 'co.',
            'hospital', 'medical', 'clinic', 'center', 'centre', 'services', 'solutions',
            'group', 'partners', 'associates', 'firm', 'office', 'bank', 'trust',
            'foundation', 'institute', 'university', 'college', 'school', 'academy',
            'department', 'ministry', 'bureau', 'agency', 'authority', 'commission',
            'committee', 'council', 'board', 'society', 'association', 'union',
            'federation', 'confederation', 'alliance', 'consortium', 'cooperative'
        }
        
        if dictionary_path:
            self._load_dictionaries()
        
        logger.info(f"Name validator initialized - dictionary: {self.dictionary_loaded}", "VALIDATOR")
    
    def _load_dictionaries(self):
        """Load name dictionaries from files"""
        try:
            if not self.dictionary_path or not os.path.exists(self.dictionary_path):
                logger.warning(f"Dictionary path not found: {self.dictionary_path}", "VALIDATOR")
                return
            
            # Try to load first names
            first_names_file = os.path.join(self.dictionary_path, "first_names.txt")
            if os.path.exists(first_names_file):
                with open(first_names_file, 'r', encoding='utf-8') as f:
                    self.first_names = {line.strip().lower() for line in f if line.strip()}
                logger.info(f"Loaded {len(self.first_names)} first names", "VALIDATOR")
            
            # Try to load last names
            last_names_file = os.path.join(self.dictionary_path, "last_names.txt")
            if os.path.exists(last_names_file):
                with open(last_names_file, 'r', encoding='utf-8') as f:
                    self.last_names = {line.strip().lower() for line in f if line.strip()}
                logger.info(f"Loaded {len(self.last_names)} last names", "VALIDATOR")
            
            self.dictionary_loaded = len(self.first_names) > 0 or len(self.last_names) > 0
            
        except Exception as e:
            logger.error(f"Error loading dictionaries: {e}", "VALIDATOR")
            self.dictionary_loaded = False
    
    def validate(self, first_name: str, last_name: str) -> Dict:
        """Validate name components with dictionary lookup (legacy method)"""
        start_time = time.time()
        
        result = {
            'valid': False,
            'confidence': 0.0,
            'errors': [],
            'warnings': [],
            'suggestions': {},
            'normalized': {
                'first_name': first_name.strip().title() if first_name else '',
                'last_name': last_name.strip().title() if last_name else ''
            },
            'analysis': {
                'first_name': {
                    'found_in_dictionary': False,
                    'confidence': 0.0
                },
                'last_name': {
                    'found_in_dictionary': False,
                    'confidence': 0.0
                }
            }
        }
        
        # Basic validation
        if not first_name or not first_name.strip():
            result['errors'].append("First name required")
        if not last_name or not last_name.strip():
            result['errors'].append("Last name required")
        
        # Dictionary lookup if available
        if self.dictionary_loaded and first_name:
            first_in_dict = first_name.strip().lower() in self.first_names
            result['analysis']['first_name']['found_in_dictionary'] = first_in_dict
            result['analysis']['first_name']['confidence'] = 0.9 if first_in_dict else 0.5
        
        if self.dictionary_loaded and last_name:
            last_in_dict = last_name.strip().lower() in self.last_names
            result['analysis']['last_name']['found_in_dictionary'] = last_in_dict
            result['analysis']['last_name']['confidence'] = 0.9 if last_in_dict else 0.5
        
        # Additional validation
        if first_name and len(first_name.strip()) < 2:
            result['warnings'].append("First name seems short")
        if last_name and len(last_name.strip()) < 2:
            result['warnings'].append("Last name seems short")
        
        # Set validity and confidence
        result['valid'] = len(result['errors']) == 0
        
        if result['valid']:
            # Calculate confidence based on dictionary lookup
            first_conf = result['analysis']['first_name'].get('confidence', 0.6)
            last_conf = result['analysis']['last_name'].get('confidence', 0.6)
            result['confidence'] = (first_conf + last_conf) / 2
        else:
            result['confidence'] = 0.0
        
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def validate_name_record(self, record: Dict) -> Dict:
        """Validate a complete name record with new format"""
        start_time = time.time()
        
        unique_id = record.get('uniqueID', '')
        full_name = record.get('fullName', '').strip()
        gender_cd = record.get('genderCd', '').strip().upper()
        party_type_cd = record.get('partyTypeCd', '').strip().upper()
        parse_ind = record.get('parseInd', '').strip().upper()
        
        # Initialize result structure
        result = {
            'uniqueID': unique_id,
            'partyTypeCd': '',
            'prefix': None,
            'firstName': None,
            'firstNameStd': None,
            'middleName': None,
            'lastName': None,
            'suffix': None,
            'fullName': full_name,
            'inGenderCd': gender_cd,
            'outGenderCd': '',
            'prefixLt': None,
            'firstNameLt': None,
            'middleNameLt': None,
            'lastNameLt': None,
            'suffixLt': None,
            'parseInd': parse_ind if parse_ind else 'Y',  # Default to parse
            'confidenceScore': '0.0',
            'parseStatus': 'Error',
            'errorMessage': 'Processing error'
        }
        
        try:
            # Step 1: Determine if organization or individual
            is_org = self._is_organization_ai(full_name, party_type_cd)
            
            if is_org:
                result['partyTypeCd'] = 'O'
                result['outGenderCd'] = ''
                result['parseStatus'] = 'Organization'
                result['errorMessage'] = 'Valid Organization'
                result['confidenceScore'] = '95.0'
                return result
            else:
                result['partyTypeCd'] = 'I'
            
            # Step 2: Parse the name if indicated
            if result['parseInd'] == 'Y':
                parsed = self._enhanced_parse_name(full_name)
                
                result['prefix'] = parsed['prefix']
                result['firstName'] = parsed['first_name']
                result['middleName'] = parsed['middle_name']
                result['lastName'] = parsed['last_name']
                result['suffix'] = parsed['suffix']
                
                # Create literal (uppercase) versions
                result['prefixLt'] = parsed['prefix'].upper() if parsed['prefix'] else None
                result['firstNameLt'] = parsed['first_name'].upper() if parsed['first_name'] else None
                result['middleNameLt'] = parsed['middle_name'].upper() if parsed['middle_name'] else None
                result['lastNameLt'] = parsed['last_name'].upper() if parsed['last_name'] else None
                result['suffixLt'] = parsed['suffix'].upper() if parsed['suffix'] else None
                
                # Step 3: Standardize first name
                if parsed['first_name']:
                    result['firstNameStd'] = self._standardize_name(parsed['first_name'])
                
                # Step 4: Predict gender if not provided
                if not gender_cd and parsed['first_name']:
                    predicted_gender = self._predict_gender_ai(parsed['first_name'])
                    result['outGenderCd'] = predicted_gender
                else:
                    result['outGenderCd'] = gender_cd
                
                # Step 5: Calculate confidence and status
                confidence = self._calculate_confidence(parsed, result['outGenderCd'])
                result['confidenceScore'] = f"{confidence:.4f}"
                
                if confidence >= 90:
                    result['parseStatus'] = 'Parsed'
                    result['errorMessage'] = 'Probably Valid'
                elif confidence >= 70:
                    result['parseStatus'] = 'Parsed'
                    result['errorMessage'] = 'Possibly Valid'
                else:
                    result['parseStatus'] = 'Warning'
                    result['errorMessage'] = 'Low Confidence'
                    
            else:
                # No parsing requested
                result['parseStatus'] = 'Not Parsed'
                result['errorMessage'] = 'Parsing not requested'
                result['confidenceScore'] = '80.0'
                result['outGenderCd'] = gender_cd
            
        except Exception as e:
            logger.error(f"Error validating name record: {e}", "VALIDATOR")
            result['parseStatus'] = 'Error'
            result['errorMessage'] = f'Processing error: {str(e)}'
            result['confidenceScore'] = '0.0'
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Name validation completed in {processing_time}ms", "VALIDATOR")
        
        return result
    
    def parse_full_name(self, full_name: str) -> Dict[str, str]:
        """Parse full name into components (legacy method)"""
        if not full_name or not full_name.strip():
            return {'first_name': '', 'last_name': '', 'middle_name': ''}
        
        # Clean the name
        name = full_name.strip()
        
        # Remove common titles and suffixes
        titles = ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'rev']
        suffixes = ['jr', 'sr', 'iii', 'iv', 'md', 'phd', 'cpa', 'esq']
        
        # Simple parsing logic
        parts = name.split()
        clean_parts = []
        
        for part in parts:
            part_lower = part.lower().rstrip('.')
            if part_lower not in titles and part_lower not in suffixes:
                clean_parts.append(part)
        
        if len(clean_parts) == 0:
            return {'first_name': '', 'last_name': '', 'middle_name': ''}
        elif len(clean_parts) == 1:
            return {'first_name': clean_parts[0], 'last_name': '', 'middle_name': ''}
        elif len(clean_parts) == 2:
            return {'first_name': clean_parts[0], 'last_name': clean_parts[1], 'middle_name': ''}
        else:
            return {
                'first_name': clean_parts[0],
                'last_name': clean_parts[-1],
                'middle_name': ' '.join(clean_parts[1:-1])
            }
    
    def _enhanced_parse_name(self, full_name: str) -> Dict[str, str]:
        """Enhanced name parsing with prefix/suffix extraction"""
        if not full_name or not full_name.strip():
            return {
                'prefix': '', 'first_name': '', 'middle_name': '',
                'last_name': '', 'suffix': ''
            }
        
        # Clean and normalize
        name = re.sub(r'[^\w\s\.]', ' ', full_name)  # Remove special chars except dots
        name = ' '.join(name.split())  # Normalize whitespace
        
        parts = name.split()
        
        prefix = ''
        suffix = ''
        name_parts = parts[:]
        
        # Extract prefix
        if parts and parts[0].lower().rstrip('.') in self.prefixes:
            prefix = parts[0].rstrip('.')
            name_parts = parts[1:]
        
        # Extract suffix
        if name_parts and name_parts[-1].lower().rstrip('.') in self.suffixes:
            suffix = name_parts[-1].rstrip('.')
            name_parts = name_parts[:-1]
        
        # Parse remaining name parts
        if len(name_parts) == 0:
            return {'prefix': prefix, 'first_name': '', 'middle_name': '', 
                   'last_name': '', 'suffix': suffix}
        elif len(name_parts) == 1:
            return {'prefix': prefix, 'first_name': name_parts[0], 'middle_name': '', 
                   'last_name': '', 'suffix': suffix}
        elif len(name_parts) == 2:
            return {'prefix': prefix, 'first_name': name_parts[0], 'middle_name': '', 
                   'last_name': name_parts[1], 'suffix': suffix}
        else:
            return {
                'prefix': prefix,
                'first_name': name_parts[0],
                'middle_name': ' '.join(name_parts[1:-1]),
                'last_name': name_parts[-1],
                'suffix': suffix
            }
    
    def _standardize_name(self, name: str) -> str:
        """Standardize common nickname to formal name"""
        if not name:
            return ''
        
        name_lower = name.lower()
        return self.name_standardizations.get(name_lower, name).title()
    
    def _predict_gender_ai(self, first_name: str) -> str:
        """AI-enhanced gender prediction"""
        if not first_name:
            return ''
        
        name_lower = first_name.lower()
        
        # Dictionary lookup first (if available)
        if self.dictionary_loaded and name_lower in self.first_names:
            # In a real implementation, you'd have gender data in the dictionary
            # For now, use pattern-based prediction
            pass
        
        # Pattern-based gender prediction
        gender_score = 0
        
        # Female patterns
        if name_lower.endswith(('a', 'ia', 'ana', 'ella', 'ina', 'lyn', 'lynn', 'elle', 'ette')):
            gender_score -= 3
        
        if name_lower.endswith(('y', 'ie', 'ey')):
            gender_score -= 1
        
        # Male patterns
        if name_lower.endswith(('er', 'on', 'an', 'en', 'son', 'ton', 'man')):
            gender_score += 2
        
        if name_lower.endswith(('ck', 'x', 'z')):
            gender_score += 1
        
        # Common names
        common_female = {
            'mary', 'jennifer', 'patricia', 'linda', 'barbara', 'susan', 'jessica',
            'sarah', 'karen', 'nancy', 'lisa', 'betty', 'helen', 'sandra', 'donna',
            'carol', 'ruth', 'sharon', 'michelle', 'laura', 'sarah', 'kimberly',
            'deborah', 'dorothy', 'amy', 'angela', 'ashley', 'brenda', 'emma'
        }
        
        common_male = {
            'james', 'john', 'robert', 'michael', 'william', 'david', 'richard',
            'charles', 'joseph', 'thomas', 'christopher', 'daniel', 'paul', 'mark',
            'donald', 'steven', 'kenneth', 'andrew', 'joshua', 'kevin', 'brian',
            'george', 'edward', 'ronald', 'timothy', 'matthew', 'anthony', 'ryan'
        }
        
        if name_lower in common_female:
            return 'F'
        elif name_lower in common_male:
            return 'M'
        
        # Use pattern scoring
        if gender_score <= -2:
            return 'F'
        elif gender_score >= 2:
            return 'M'
        
        return ''  # Unknown
    
    def _is_organization_ai(self, full_name: str, party_type_hint: str = '') -> bool:
        """AI-enhanced organization detection"""
        if not full_name:
            return False
        
        # If explicitly marked as organization
        if party_type_hint == 'O':
            return True
        elif party_type_hint == 'I':
            return False
        
        name_lower = full_name.lower()
        
        # Check for organization indicators
        org_score = 0
        
        # Direct organization keywords
        for indicator in self.org_indicators:
            if indicator in name_lower:
                org_score += 10
        
        # Pattern matching
        if re.search(r'\b(llc|inc|corp|ltd)\b', name_lower):
            org_score += 15
        
        if re.search(r'\b(hospital|medical|clinic|center|services|solutions)\b', name_lower):
            org_score += 12
        
        if re.search(r'\b(group|partners|associates|firm)\b', name_lower):
            org_score += 10
        
        # Length-based scoring (organizations tend to be longer)
        if len(full_name.split()) > 3:
            org_score += 5
        
        # Check for common personal name patterns
        personal_patterns = [
            r'\b(mr|mrs|ms|dr)\s+[a-z]+\s+[a-z]+\b',
            r'\b[a-z]+\s+(jr|sr|ii|iii)\b',
            r'\b[a-z]+\s+[a-z]+(\s+[a-z]+)?\b'  # First Last or First Middle Last
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, name_lower):
                org_score -= 8
        
        return org_score > 10
    
    def _calculate_confidence(self, parsed: Dict, predicted_gender: str) -> float:
        """Calculate confidence score for the validation"""
        confidence = 50.0  # Base confidence
        
        # Name parsing quality
        if parsed['first_name']:
            confidence += 20
        if parsed['last_name']:
            confidence += 20
        
        # Dictionary lookup bonus
        if self.dictionary_loaded:
            if parsed['first_name'] and parsed['first_name'].lower() in self.first_names:
                confidence += 15
            if parsed['last_name'] and parsed['last_name'].lower() in self.last_names:
                confidence += 15
        
        # Gender prediction confidence
        if predicted_gender:
            confidence += 10
        
        # Name length and structure
        if parsed['first_name'] and len(parsed['first_name']) >= 2:
            confidence += 5
        if parsed['last_name'] and len(parsed['last_name']) >= 2:
            confidence += 5
        
        # Prefix/suffix presence
        if parsed['prefix']:
            confidence += 3
        if parsed['suffix']:
            confidence += 2
        
        return min(confidence, 99.9995)  # Cap at max confidence
    
    def is_organization(self, name: str) -> bool:
        """Check if name appears to be an organization (legacy method)"""
        return self._is_organization_ai(name)
    
    def predict_gender(self, first_name: str) -> str:
        """Simple gender prediction (legacy method)"""
        return self._predict_gender_ai(first_name)


class AddressValidator:
    """USPS Address Validator (unchanged)"""
    
    def __init__(self):
        self.client_id, self.client_secret = load_usps_credentials()
        self._access_token = None
        self._token_expires_at = 0
        logger.info(f"Address validator initialized - configured: {self.is_configured()}", "VALIDATOR")
    
    def is_configured(self) -> bool:
        """Check if USPS credentials are available"""
        return bool(self.client_id and self.client_secret)
    
    def get_access_token(self) -> Optional[str]:
        """Get USPS access token"""
        if not self.is_configured():
            return None
        
        # Check cached token
        if (self._access_token and time.time() < (self._token_expires_at - 300)):
            return self._access_token
        
        # Get new token
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'addresses'
            }
            
            response = requests.post(Config.USPS_AUTH_URL, headers=headers, data=data, timeout=15)
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self._token_expires_at = time.time() + expires_in
                logger.info("USPS token obtained", "USPS")
                return self._access_token
            else:
                logger.error(f"USPS auth failed: {response.status_code}", "USPS")
                return None
                
        except Exception as e:
            logger.error(f"USPS auth error: {e}", "USPS")
            return None
    
    def validate_address(self, address_data: Dict) -> Dict:
        """Validate address using USPS API"""
        
        if not self.is_configured():
            return {
                'success': False,
                'error': 'USPS API not configured',
                'deliverable': False
            }
        
        access_token = self.get_access_token()
        if not access_token:
            return {
                'success': False,
                'error': 'Failed to get access token',
                'deliverable': False
            }
        
        # Extract address components
        street_address = address_data.get('street_address', '').strip()
        city = address_data.get('city', '').strip()
        state = address_data.get('state', '').strip().upper()
        zip_code = str(address_data.get('zip_code', '')).strip()
        
        # Basic validation
        if not all([street_address, city, state, zip_code]):
            missing = []
            if not street_address: missing.append('street_address')
            if not city: missing.append('city')
            if not state: missing.append('state')
            if not zip_code: missing.append('zip_code')
            
            return {
                'success': False,
                'error': f"Missing required fields: {', '.join(missing)}",
                'deliverable': False
            }
        
        # Parse street address for apartment/unit
        street_parts = self._parse_street_address(street_address)
        
        # Build query parameters
        params = {
            'streetAddress': street_parts['street'].upper(),
            'city': city.upper(),
            'state': state.upper(),
            'ZIPCode': zip_code[:5]
        }
        
        if street_parts['unit']:
            params['secondaryAddress'] = street_parts['unit'].upper()
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(Config.USPS_VALIDATE_URL, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                return self._parse_success_response(response.json())
            elif response.status_code == 400:
                return {
                    'success': False,
                    'error': 'Invalid address format',
                    'deliverable': False
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': 'Address not found',
                    'deliverable': False
                }
            else:
                return {
                    'success': False,
                    'error': f'API error: HTTP {response.status_code}',
                    'deliverable': False
                }
                
        except Exception as e:
            logger.error(f"USPS validation error: {e}", "USPS")
            return {
                'success': False,
                'error': 'Validation request failed',
                'deliverable': False
            }
    
    def _parse_street_address(self, address: str) -> Dict[str, str]:
        """Parse street address into main and unit components"""
        if not address:
            return {'street': '', 'unit': ''}
        
        # Normalize whitespace
        address = ' '.join(address.split())
        
        # Common unit patterns
        unit_patterns = [
            r'\s+(apartment|apt|suite|ste|unit|#)\s*\.?\s*([a-z0-9\-]+)$',
            r'\s+([0-9]+[a-z]{1,2})$',  # Like "4B", "12A"
            r'\s+#([a-z0-9\-]+)$'       # "#123"
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                unit_start = match.start()
                street_part = address[:unit_start].strip()
                unit_part = match.group(0).strip()
                return {'street': street_part, 'unit': unit_part}
        
        return {'street': address, 'unit': ''}
    
    def _parse_success_response(self, response_data: Dict) -> Dict:
        """Parse successful USPS response"""
        
        if not response_data.get('address'):
            return {
                'success': False,
                'error': 'No address data in response',
                'deliverable': False
            }
        
        address = response_data.get('address', {})
        additional_info = response_data.get('additionalInfo', {})
        
        # Check deliverability
        dpv_confirmation = additional_info.get('DPVConfirmation', '')
        is_deliverable = dpv_confirmation in ['Y', 'D']
        
        # Build standardized address
        street_address = address.get('streetAddress', '')
        if address.get('secondaryAddress'):
            street_address += f" {address.get('secondaryAddress')}"
        
        zip_code = address.get('ZIPCode', '')
        if address.get('ZIPPlus4'):
            zip_code += f"-{address.get('ZIPPlus4')}"
        
        standardized = {
            'street_address': street_address.strip(),
            'city': address.get('city', ''),
            'state': address.get('state', ''),
            'zip_code': zip_code
        }
        
        metadata = {
            'business': additional_info.get('business', 'N') == 'Y',
            'vacant': additional_info.get('vacant', 'N') == 'Y',
            'centralized': additional_info.get('centralDeliveryPoint', 'N') == 'Y',
            'carrier_route': additional_info.get('carrierRoute', ''),
            'delivery_point': additional_info.get('deliveryPoint', ''),
            'dpv_confirmation': dpv_confirmation
        }
        
        return {
            'success': True,
            'valid': is_deliverable,
            'deliverable': is_deliverable,
            'standardized': standardized,
            'metadata': metadata,
            'confidence': 0.95 if is_deliverable else 0.3,
            'validation_method': 'usps_api_v3'
        }