"""
Enhanced validation logic for names and addresses with dictionary integration and AI fallback
"""

import requests
import re
import time
import sys
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import Config, load_usps_credentials
from utils.logger import logger


class NameValidator:
    """Enhanced name validator with dictionary integration and AI fallback"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries"):
        self.dictionary_path = dictionary_path
        self.dictionary_loaded = False
        
        # Dictionary lookup structures
        self.first_names_set = set()
        self.surnames_set = set()
        self.business_words_set = set()
        self.company_suffixes_set = set()
        self.name_prefixes_set = set()
        self.name_to_gender = {}
        self.nickname_to_standard = {}
        
        # Load dictionaries if available
        self._load_dictionaries()
        
        # AI fallback patterns
        self._initialize_ai_patterns()
        
        logger.info(f"Name validator initialized - dictionaries loaded: {self.dictionary_loaded}", "VALIDATOR")
    
    def _load_dictionaries(self):
        """Load dictionaries from CSV files"""
        try:
            if not os.path.exists(self.dictionary_path):
                logger.warning(f"Dictionary path not found: {self.dictionary_path}", "VALIDATOR")
                return
            
            loaded_count = 0
            
            # Load first names
            first_names_file = os.path.join(self.dictionary_path, "usa_firstnames_infa.csv")
            if os.path.exists(first_names_file):
                try:
                    df = pd.read_csv(first_names_file, encoding='utf-8')
                    if len(df.columns) > 0:
                        name_col = df.columns[0]
                        self.first_names_set = set(df[name_col].str.lower().dropna())
                        loaded_count += 1
                        logger.info(f"Loaded first names: {len(self.first_names_set)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load first names: {e}", "VALIDATOR")
            
            # Load surnames
            surnames_file = os.path.join(self.dictionary_path, "usa_surnames_infa.csv")
            if os.path.exists(surnames_file):
                try:
                    df = pd.read_csv(surnames_file, encoding='utf-8')
                    if len(df.columns) > 0:
                        name_col = df.columns[0]
                        self.surnames_set = set(df[name_col].str.lower().dropna())
                        loaded_count += 1
                        logger.info(f"Loaded surnames: {len(self.surnames_set)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load surnames: {e}", "VALIDATOR")
            
            # Load gender mappings
            gender_file = os.path.join(self.dictionary_path, "usa_gender_infa.csv")
            if os.path.exists(gender_file):
                try:
                    df = pd.read_csv(gender_file, encoding='utf-8')
                    if len(df.columns) >= 2:
                        name_col, gender_col = df.columns[0], df.columns[1]
                        for _, row in df.iterrows():
                            if pd.notna(row[name_col]) and pd.notna(row[gender_col]):
                                self.name_to_gender[row[name_col].lower()] = row[gender_col].upper()
                        loaded_count += 1
                        logger.info(f"Loaded gender mappings: {len(self.name_to_gender)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load gender mappings: {e}", "VALIDATOR")
            
            # Load nicknames
            nicknames_file = os.path.join(self.dictionary_path, "usa_nicknames_infa.csv")
            if os.path.exists(nicknames_file):
                try:
                    df = pd.read_csv(nicknames_file, encoding='utf-8')
                    if len(df.columns) >= 2:
                        nickname_col, standard_col = df.columns[0], df.columns[1]
                        for _, row in df.iterrows():
                            if pd.notna(row[nickname_col]) and pd.notna(row[standard_col]):
                                self.nickname_to_standard[row[nickname_col].lower()] = row[standard_col].title()
                        loaded_count += 1
                        logger.info(f"Loaded nickname mappings: {len(self.nickname_to_standard)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load nicknames: {e}", "VALIDATOR")
            
            # Load business words
            business_file = os.path.join(self.dictionary_path, "usa_business_word_infa.csv")
            if os.path.exists(business_file):
                try:
                    df = pd.read_csv(business_file, encoding='utf-8')
                    if len(df.columns) > 0:
                        word_col = df.columns[0]
                        self.business_words_set = set(df[word_col].str.lower().dropna())
                        loaded_count += 1
                        logger.info(f"Loaded business words: {len(self.business_words_set)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load business words: {e}", "VALIDATOR")
            
            # Load company suffixes
            suffixes_file = os.path.join(self.dictionary_path, "usa_company_sufx_abrv_infa.csv")
            if os.path.exists(suffixes_file):
                try:
                    df = pd.read_csv(suffixes_file, encoding='utf-8')
                    if len(df.columns) > 0:
                        suffix_col = df.columns[0]
                        self.company_suffixes_set = set(df[suffix_col].str.lower().dropna())
                        loaded_count += 1
                        logger.info(f"Loaded company suffixes: {len(self.company_suffixes_set)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load company suffixes: {e}", "VALIDATOR")
            
            # Load name prefixes
            prefixes_file = os.path.join(self.dictionary_path, "usa_name_prefix_NYL.csv")
            if os.path.exists(prefixes_file):
                try:
                    df = pd.read_csv(prefixes_file, encoding='utf-8')
                    if len(df.columns) > 0:
                        prefix_col = df.columns[0]
                        self.name_prefixes_set = set(df[prefix_col].str.lower().dropna())
                        loaded_count += 1
                        logger.info(f"Loaded name prefixes: {len(self.name_prefixes_set)} records", "VALIDATOR")
                except Exception as e:
                    logger.warning(f"Failed to load name prefixes: {e}", "VALIDATOR")
            
            self.dictionary_loaded = loaded_count > 0
            logger.info(f"Dictionary loading complete: {loaded_count} files loaded", "VALIDATOR")
            
        except Exception as e:
            logger.error(f"Error loading dictionaries: {e}", "VALIDATOR")
            self.dictionary_loaded = False
    
    def _initialize_ai_patterns(self):
        """Initialize AI fallback patterns"""
        # Name standardization mappings (fallback)
        self.ai_name_standardizations = {
            'bill': 'william', 'bob': 'robert', 'dick': 'richard', 'jim': 'james',
            'joe': 'joseph', 'mike': 'michael', 'steve': 'steven', 'dave': 'david',
            'tom': 'thomas', 'tony': 'anthony', 'chris': 'christopher', 'matt': 'matthew',
            'dan': 'daniel', 'sam': 'samuel', 'alex': 'alexander', 'ben': 'benjamin',
            'nick': 'nicholas', 'rick': 'richard', 'will': 'william', 'tim': 'timothy',
            'pat': 'patricia', 'sue': 'susan', 'liz': 'elizabeth', 'kate': 'katherine',
            'beth': 'elizabeth', 'anne': 'ann', 'maggie': 'margaret', 'peg': 'margaret',
            'jen': 'jennifer', 'jenn': 'jennifer', 'amy': 'amelia', 'becky': 'rebecca'
        }
        
        # Common prefixes and suffixes (fallback)
        self.ai_prefixes = {
            'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'professor', 'rev', 'reverend',
            'father', 'mother', 'sister', 'brother', 'sir', 'lady', 'lord', 'dame',
            'capt', 'captain', 'col', 'colonel', 'maj', 'major', 'lt', 'lieutenant',
            'sgt', 'sergeant', 'gen', 'general', 'admiral', 'judge', 'justice'
        }
        
        self.ai_suffixes = {
            'jr', 'sr', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
            'md', 'phd', 'edd', 'jd', 'cpa', 'dds', 'dvm', 'rn', 'lpn', 'pa',
            'esq', 'esquire', 'pe', 'cpe', 'cfa', 'mba', 'ms', 'ma', 'bs', 'ba'
        }
        
        # Organization indicators (fallback)
        self.ai_org_indicators = {
            'llc', 'inc', 'corp', 'corporation', 'company', 'ltd', 'limited', 'co.',
            'hospital', 'medical', 'clinic', 'center', 'centre', 'services', 'solutions',
            'group', 'partners', 'associates', 'firm', 'office', 'bank', 'trust',
            'foundation', 'institute', 'university', 'college', 'school', 'academy'
        }
    
    def validate(self, first_name: str, last_name: str) -> Dict:
        """Enhanced validation with dictionary lookup and AI fallback"""
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
                    'confidence': 0.0,
                    'method': 'unknown'
                },
                'last_name': {
                    'found_in_dictionary': False,
                    'confidence': 0.0,
                    'method': 'unknown'
                }
            },
            'validation_method': 'ai_fallback'
        }
        
        # Basic validation
        if not first_name or not first_name.strip():
            result['errors'].append("First name required")
        if not last_name or not last_name.strip():
            result['errors'].append("Last name required")
        
        if result['errors']:
            result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            return result
        
        # Dictionary lookup if available
        if self.dictionary_loaded:
            first_in_dict = first_name.strip().lower() in self.first_names_set
            last_in_dict = last_name.strip().lower() in self.surnames_set
            
            # First name analysis
            if first_in_dict:
                result['analysis']['first_name']['found_in_dictionary'] = True
                result['analysis']['first_name']['confidence'] = 0.95
                result['analysis']['first_name']['method'] = 'dictionary_lookup'
            else:
                # AI fallback for first name
                result['analysis']['first_name']['method'] = 'ai_pattern_matching'
                result['analysis']['first_name']['confidence'] = self._ai_name_confidence(first_name)
            
            # Last name analysis
            if last_in_dict:
                result['analysis']['last_name']['found_in_dictionary'] = True
                result['analysis']['last_name']['confidence'] = 0.95
                result['analysis']['last_name']['method'] = 'dictionary_lookup'
            else:
                # AI fallback for last name
                result['analysis']['last_name']['method'] = 'ai_pattern_matching'
                result['analysis']['last_name']['confidence'] = self._ai_name_confidence(last_name)
            
            # Determine overall validation method
            if first_in_dict and last_in_dict:
                result['validation_method'] = 'deterministic'
            elif first_in_dict or last_in_dict:
                result['validation_method'] = 'hybrid'
            else:
                result['validation_method'] = 'ai_fallback'
        
        else:
            # Pure AI fallback
            result['analysis']['first_name']['confidence'] = self._ai_name_confidence(first_name)
            result['analysis']['first_name']['method'] = 'ai_pattern_matching'
            result['analysis']['last_name']['confidence'] = self._ai_name_confidence(last_name)
            result['analysis']['last_name']['method'] = 'ai_pattern_matching'
            result['validation_method'] = 'ai_fallback'
        
        # Additional validation
        if first_name and len(first_name.strip()) < 2:
            result['warnings'].append("First name seems short")
        if last_name and len(last_name.strip()) < 2:
            result['warnings'].append("Last name seems short")
        
        # Set validity and confidence
        result['valid'] = len(result['errors']) == 0
        
        if result['valid']:
            # Calculate overall confidence
            first_conf = result['analysis']['first_name']['confidence']
            last_conf = result['analysis']['last_name']['confidence']
            result['confidence'] = (first_conf + last_conf) / 2
        else:
            result['confidence'] = 0.0
        
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def _ai_name_confidence(self, name: str) -> float:
        """Calculate confidence for AI pattern matching"""
        if not name:
            return 0.0
        
        confidence = 0.5  # Base confidence for AI
        
        # Length-based confidence
        if 2 <= len(name) <= 15:
            confidence += 0.2
        
        # Character pattern confidence
        if re.match(r'^[A-Za-z\-\']+$', name):
            confidence += 0.1
        
        # Common pattern recognition
        if name.lower() in ['john', 'jane', 'smith', 'johnson', 'williams', 'brown', 'jones']:
            confidence += 0.2
        
        return min(confidence, 0.8)  # Cap AI confidence at 80%
    
    def validate_name_record(self, record: Dict) -> Dict:
        """Enhanced name record validation with new format"""
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
            'parseInd': parse_ind if parse_ind else 'Y',
            'confidenceScore': '0.0',
            'parseStatus': 'Error',
            'errorMessage': 'Processing error',
            'validationMethod': 'unknown'
        }
        
        try:
            # Step 1: Determine if organization or individual
            is_org, org_confidence, org_method = self._determine_organization(full_name, party_type_cd)
            
            if is_org:
                result['partyTypeCd'] = 'O'
                result['outGenderCd'] = ''
                result['parseStatus'] = 'Organization'
                result['errorMessage'] = 'Valid Organization'
                result['confidenceScore'] = f"{org_confidence:.4f}"
                result['validationMethod'] = org_method
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
                    predicted_gender = self._predict_gender(parsed['first_name'])
                    result['outGenderCd'] = predicted_gender
                else:
                    result['outGenderCd'] = gender_cd
                
                # Step 5: Calculate confidence and determine method
                confidence, validation_method = self._calculate_confidence(parsed, result['outGenderCd'])
                result['confidenceScore'] = f"{confidence:.4f}"
                result['validationMethod'] = validation_method
                
                if confidence >= 90:
                    result['parseStatus'] = 'Parsed'
                    result['errorMessage'] = 'Dictionary Validated' if 'deterministic' in validation_method else 'Probably Valid'
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
                result['validationMethod'] = 'no_parse'
            
        except Exception as e:
            logger.error(f"Error validating name record: {e}", "VALIDATOR")
            result['parseStatus'] = 'Error'
            result['errorMessage'] = f'Processing error: {str(e)}'
            result['confidenceScore'] = '0.0'
            result['validationMethod'] = 'error'
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Name validation completed in {processing_time}ms - method: {result.get('validationMethod')}", "VALIDATOR")
        
        return result
    
    def _determine_organization(self, full_name: str, party_type_hint: str = '') -> Tuple[bool, float, str]:
        """Determine if name is organization with dictionary lookup + AI fallback"""
        if not full_name:
            return False, 0.0, 'empty_name'
        
        # If explicitly marked
        if party_type_hint == 'O':
            return True, 99.0, 'explicit_org'
        elif party_type_hint == 'I':
            return False, 99.0, 'explicit_individual'
        
        name_lower = full_name.lower()
        
        # Dictionary lookup first
        if self.dictionary_loaded:
            # Check company suffixes
            if self.company_suffixes_set:
                for suffix in self.company_suffixes_set:
                    if suffix in name_lower:
                        return True, 95.0, 'deterministic_suffix'
            
            # Check business words
            if self.business_words_set:
                name_words = set(name_lower.split())
                if name_words.intersection(self.business_words_set):
                    return True, 92.0, 'deterministic_business_word'
            
            # Check against individual name patterns
            name_parts = name_lower.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                
                if (first_name in self.first_names_set and last_name in self.surnames_set):
                    return False, 94.0, 'deterministic_individual'
        
        # AI fallback
        return self._ai_organization_detection(name_lower)
    
    def _ai_organization_detection(self, name_lower: str) -> Tuple[bool, float, str]:
        """AI fallback for organization detection"""
        org_score = 0
        
        # Pattern matching
        for indicator in self.ai_org_indicators:
            if indicator in name_lower:
                org_score += 10
        
        if re.search(r'\b(llc|inc|corp|ltd)\b', name_lower):
            org_score += 15
        
        # Length-based scoring
        if len(name_lower.split()) > 3:
            org_score += 5
        
        # Personal name patterns (negative scoring)
        personal_patterns = [
            r'\b(mr|mrs|ms|dr)\s+[a-z]+\s+[a-z]+\b',
            r'\b[a-z]+\s+(jr|sr|ii|iii)\b'
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, name_lower):
                org_score -= 8
        
        is_org = org_score > 10
        confidence = min(80.0, 50.0 + abs(org_score) * 2)  # AI confidence capped at 80%
        
        return is_org, confidence, 'ai_pattern_matching'
    
    def _enhanced_parse_name(self, full_name: str) -> Dict[str, str]:
        """Enhanced name parsing with dictionary lookup for prefixes/suffixes"""
        if not full_name or not full_name.strip():
            return {
                'prefix': '', 'first_name': '', 'middle_name': '',
                'last_name': '', 'suffix': ''
            }
        
        # Clean and normalize
        name = re.sub(r'[^\w\s\.]', ' ', full_name)
        name = ' '.join(name.split())
        
        parts = name.split()
        
        prefix = ''
        suffix = ''
        name_parts = parts[:]
        
        # Extract prefix (dictionary lookup first)
        if parts:
            first_part = parts[0].lower().rstrip('.')
            
            if self.dictionary_loaded and self.name_prefixes_set:
                if first_part in self.name_prefixes_set:
                    prefix = parts[0].rstrip('.')
                    name_parts = parts[1:]
            elif first_part in self.ai_prefixes:
                prefix = parts[0].rstrip('.')
                name_parts = parts[1:]
        
        # Extract suffix (dictionary/AI fallback)
        if name_parts:
            last_part = name_parts[-1].lower().rstrip('.')
            
            # Use AI suffixes as fallback
            if last_part in self.ai_suffixes:
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
        """Standardize name with dictionary lookup + AI fallback"""
        if not name:
            return ''
        
        name_lower = name.lower()
        
        # Dictionary lookup first
        if self.dictionary_loaded and self.nickname_to_standard:
            if name_lower in self.nickname_to_standard:
                return self.nickname_to_standard[name_lower]
        
        # AI fallback
        if name_lower in self.ai_name_standardizations:
            return self.ai_name_standardizations[name_lower].title()
        
        return name.title()
    
    def _predict_gender(self, first_name: str) -> str:
        """Predict gender with dictionary lookup + AI fallback"""
        if not first_name:
            return ''
        
        name_lower = first_name.lower()
        
        # Dictionary lookup first
        if self.dictionary_loaded and self.name_to_gender:
            if name_lower in self.name_to_gender:
                return self.name_to_gender[name_lower]
        
        # AI fallback
        return self._ai_gender_prediction(name_lower)
    
    def _ai_gender_prediction(self, name_lower: str) -> str:
        """AI fallback for gender prediction"""
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
        
        # Common names (basic fallback)
        common_female = {
            'mary', 'jennifer', 'patricia', 'linda', 'barbara', 'susan', 'jessica',
            'sarah', 'karen', 'nancy', 'lisa', 'betty', 'helen', 'sandra', 'donna'
        }
        
        common_male = {
            'james', 'john', 'robert', 'michael', 'william', 'david', 'richard',
            'charles', 'joseph', 'thomas', 'christopher', 'daniel', 'paul', 'mark'
        }
        
        if name_lower in common_female:
            return 'F'
        elif name_lower in common_male:
            return 'M'
        
        # Pattern-based prediction
        if gender_score <= -2:
            return 'F'
        elif gender_score >= 2:
            return 'M'
        
        return ''
    
    def _calculate_confidence(self, parsed: Dict, predicted_gender: str) -> Tuple[float, str]:
        """Calculate confidence and determine validation method"""
        
        method_scores = {'deterministic': 0, 'hybrid': 0, 'ai': 0}
        confidence = 50.0  # Base confidence
        
        # Check first name
        if parsed['first_name']:
            if self.dictionary_loaded and parsed['first_name'].lower() in self.first_names_set:
                method_scores['deterministic'] += 1
                confidence += 20
            else:
                method_scores['ai'] += 1
                confidence += 10
        
        # Check last name
        if parsed['last_name']:
            if self.dictionary_loaded and parsed['last_name'].lower() in self.surnames_set:
                method_scores['deterministic'] += 1
                confidence += 20
            else:
                method_scores['ai'] += 1
                confidence += 10
        
        # Check gender prediction
        if predicted_gender:
            if (self.dictionary_loaded and parsed['first_name'] and 
                parsed['first_name'].lower() in self.name_to_gender):
                method_scores['deterministic'] += 1
                confidence += 10
            else:
                method_scores['ai'] += 1
                confidence += 5
        
        # Determine overall method
        if method_scores['deterministic'] > method_scores['ai']:
            overall_method = 'deterministic'
            confidence = min(confidence, 99.0)
        elif method_scores['deterministic'] == method_scores['ai'] and method_scores['deterministic'] > 0:
            overall_method = 'hybrid'
            confidence = min(confidence, 90.0)
        else:
            overall_method = 'ai_fallback'
            confidence = min(confidence, 80.0)
        
        return confidence, overall_method
    
    def parse_full_name(self, full_name: str) -> Dict[str, str]:
        """Parse full name into components (legacy compatibility)"""
        parsed = self._enhanced_parse_name(full_name)
        return {
            'first_name': parsed['first_name'],
            'last_name': parsed['last_name'],
            'middle_name': parsed['middle_name']
        }
    
    def is_organization(self, name: str) -> bool:
        """Check if name appears to be an organization (legacy compatibility)"""
        is_org, _, _ = self._determine_organization(name)
        return is_org
    
    def predict_gender(self, first_name: str) -> str:
        """Simple gender prediction (legacy compatibility)"""
        return self._predict_gender(first_name)


class AddressValidator:
    """USPS Address Validator (unchanged from original)"""
    
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
        """Validate address using USPS API (unchanged from original)"""
        
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