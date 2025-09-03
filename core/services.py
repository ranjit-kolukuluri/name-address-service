# core/services.py
"""
Main validation service that combines name and address validation
"""

import time
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.validators import NameValidator, AddressValidator
from core.models import ValidationResult, ParsedComponents, Suggestions
from utils.logger import logger
from utils.config import Config


class ValidationService:
    """Main validation service"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries"):
        self.name_validator = NameValidator()
        self.address_validator = AddressValidator()
        logger.info("Validation service initialized", "SERVICE")
    
    def is_name_validation_available(self) -> bool:
        """Check if name validation is available"""
        return True  # Always available
    
    def is_address_validation_available(self) -> bool:
        """Check if address validation is available"""
        return self.address_validator.is_configured()
    
    def get_service_status(self) -> Dict:
        """Get service status"""
        return {
            'name_validation_available': self.is_name_validation_available(),
            'address_validation_available': self.is_address_validation_available(),
            'api_version': Config.API_VERSION,
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_single_name(self, first_name: str, last_name: str) -> Dict:
        """Validate a single name"""
        logger.info(f"Validating name: {first_name} {last_name}", "SERVICE")
        return self.name_validator.validate(first_name, last_name)
    
    def validate_single_address(self, address_data: Dict) -> Dict:
        """Validate a single address"""
        logger.info(f"Validating address: {address_data.get('street_address')}", "SERVICE")
        return self.address_validator.validate_address(address_data)
    
    def validate_complete_record(self, first_name: str, last_name: str,
                                street_address: str, city: str, state: str, zip_code: str) -> Dict:
        """Validate a complete record (name + address)"""
        
        start_time = time.time()
        
        result = {
            'timestamp': datetime.now(),
            'name_result': None,
            'address_result': None,
            'overall_valid': False,
            'overall_confidence': 0.0,
            'processing_time_ms': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate name
            name_result = self.name_validator.validate(first_name, last_name)
            result['name_result'] = name_result
            
            # Validate address
            address_data = {
                'street_address': street_address,
                'city': city,
                'state': state,
                'zip_code': zip_code
            }
            address_result = self.address_validator.validate_address(address_data)
            result['address_result'] = address_result
            
            # Calculate overall results
            name_valid = name_result.get('valid', False)
            address_deliverable = address_result.get('deliverable', False)
            
            result['overall_valid'] = name_valid and address_deliverable
            
            # Calculate confidence
            name_confidence = name_result.get('confidence', 0)
            address_confidence = address_result.get('confidence', 0)
            result['overall_confidence'] = (name_confidence + address_confidence) / 2
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(error_msg, "SERVICE")
        
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def process_api_records(self, records: List[Dict]) -> Dict:
        """Process records from API payload"""
        
        start_time = time.time()
        results = []
        successful_count = 0
        
        logger.info(f"Processing {len(records)} API records", "SERVICE")
        
        for i, record in enumerate(records):
            try:
                result = self._process_single_api_record(record)
                results.append(result)
                
                if result['validation_status'] != 'error':
                    successful_count += 1
                    
            except Exception as e:
                error_result = self._create_error_result(record, str(e))
                results.append(error_result)
                logger.error(f"Error processing record {i+1}: {e}", "SERVICE")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'status': 'success',
            'processed_count': len(results),
            'successful_count': successful_count,
            'results': results,
            'processing_time_ms': processing_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_single_api_record(self, record: Dict) -> Dict:
        """Process a single API record with enhanced AI analysis"""
        
        uniqueid = record['uniqueid']
        name = record['name'].strip()
        gender_hint = record.get('gender', '').strip()
        party_type_hint = record.get('party_type', '').strip()
        parse_ind = record.get('parseInd', '').strip()
        
        # Initialize result with enhanced fields
        result = {
            'uniqueid': uniqueid,
            'name': name,
            'gender': gender_hint,
            'party_type': party_type_hint,
            'parse_indicator': parse_ind,
            'validation_status': 'valid',
            'confidence_score': 0.0,
            'parsed_components': {},
            'suggestions': {},
            'errors': [],
            'warnings': [],
            'ai_analysis': {
                'dictionary_lookup_used': False,
                'ai_fallback_used': False,
                'prediction_method': 'none'
            }
        }
        
        # Enhanced organization detection with AI
        is_org = self.name_validator.is_organization(name)
        
        if is_org:
            # Handle organization with enhanced analysis
            result['party_type'] = 'O'
            result['gender'] = ''
            result['parse_indicator'] = 'N'
            result['parsed_components'] = ParsedComponents(
                organization_name=name
            ).dict()
            result['confidence_score'] = 0.92
            result['ai_analysis'] = {
                'dictionary_lookup_used': True,
                'ai_fallback_used': True,
                'prediction_method': 'organization_detection_ai'
            }
            
        else:
            # Handle individual name with AI enhancement
            result['party_type'] = 'I'
            
            # Parse name if requested
            if parse_ind.upper() == 'Y' or parse_ind == '':
                parsed = self.name_validator.parse_full_name(name)
                result['parsed_components'] = ParsedComponents(**parsed).dict()
                result['parse_indicator'] = 'Y'
                
                # Enhanced validation with AI
                if parsed['first_name'] or parsed['last_name']:
                    validation_result = self.name_validator.validate(
                        parsed['first_name'], parsed['last_name']
                    )
                    
                    result['validation_status'] = 'valid' if validation_result['valid'] else 'warning'
                    result['confidence_score'] = validation_result['confidence']
                    
                    # Add AI analysis info
                    if 'analysis' in validation_result:
                        analysis = validation_result['analysis']
                        first_in_dict = analysis.get('first_name', {}).get('found_in_dictionary', False)
                        last_in_dict = analysis.get('last_name', {}).get('found_in_dictionary', False)
                        
                        result['ai_analysis'] = {
                            'dictionary_lookup_used': first_in_dict or last_in_dict,
                            'ai_fallback_used': not (first_in_dict and last_in_dict),
                            'prediction_method': 'hybrid_dictionary_ai' if (first_in_dict or last_in_dict) else 'pure_ai',
                            'first_name_in_dictionary': first_in_dict,
                            'last_name_in_dictionary': last_in_dict
                        }
                    
                    if validation_result.get('warnings'):
                        result['warnings'].extend(validation_result['warnings'])
                else:
                    result['validation_status'] = 'invalid'
                    result['errors'].append('Could not parse name into valid components')
                    result['confidence_score'] = 0.2
                
                # Enhanced gender prediction with AI analysis
                if not gender_hint and parsed['first_name']:
                    predicted_gender = self.name_validator.predict_gender(parsed['first_name'])
                    if predicted_gender:
                        result['gender'] = predicted_gender
                        result['suggestions'] = Suggestions(
                            gender_prediction=predicted_gender
                        ).dict()
                        
                        # Add gender prediction method info
                        if 'ai_analysis' not in result:
                            result['ai_analysis'] = {}
                        result['ai_analysis']['gender_prediction_method'] = 'dictionary_first_ai_fallback'
            else:
                result['parse_indicator'] = 'N'
                result['parsed_components'] = ParsedComponents(
                    first_name='',
                    last_name='',
                    middle_name=''
                ).dict()
                result['confidence_score'] = 0.6
        
        # Add party type prediction if not provided
        if not party_type_hint and 'suggestions' not in result:
            result['suggestions'] = Suggestions().dict()
        
        if not party_type_hint:
            result['suggestions']['party_type_prediction'] = result['party_type']
        
        return result
    
    def _create_error_result(self, record: Dict, error_message: str) -> Dict:
        """Create error result for failed processing"""
        return {
            'uniqueid': record.get('uniqueid', ''),
            'name': record.get('name', ''),
            'gender': '',
            'party_type': '',
            'parse_indicator': '',
            'validation_status': 'error',
            'confidence_score': 0.0,
            'parsed_components': ParsedComponents().dict(),
            'suggestions': Suggestions().dict(),
            'errors': [error_message],
            'warnings': []
        }
    
    def process_csv_names(self, df: pd.DataFrame) -> Dict:
        """Process names from CSV DataFrame"""
        
        logger.info(f"Processing CSV with {len(df)} rows", "SERVICE")
        
        # Try to find name column
        name_columns = ['name', 'full_name', 'fullname', 'Name', 'FULL_NAME']
        name_col = None
        
        for col in name_columns:
            if col in df.columns:
                name_col = col
                break
        
        if not name_col:
            return {
                'success': False,
                'error': f'Name column not found. Available columns: {list(df.columns)}'
            }
        
        results = []
        successful = 0
        
        for idx, row in df.iterrows():
            full_name = str(row[name_col]).strip()
            
            if full_name and full_name != 'nan':
                parsed = self.name_validator.parse_full_name(full_name)
                
                if parsed['first_name'] or parsed['last_name']:
                    validation = self.name_validator.validate(
                        parsed['first_name'], parsed['last_name']
                    )
                    
                    results.append({
                        'row_number': idx + 1,
                        'original_name': full_name,
                        'first_name': parsed['first_name'],
                        'last_name': parsed['last_name'],
                        'middle_name': parsed['middle_name'],
                        'valid': validation['valid'],
                        'confidence': validation['confidence']
                    })
                    
                    if validation['valid']:
                        successful += 1
        
        return {
            'success': True,
            'total_records': len(df),
            'processed_records': len(results),
            'successful_validations': successful,
            'success_rate': successful / len(results) if results else 0,
            'results': results
        }