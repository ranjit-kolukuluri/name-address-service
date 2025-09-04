# core/services.py
"""
Updated validation service with new input/output format
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
from core.models import NameValidationResult
from utils.logger import logger
from utils.config import Config


class ValidationService:
    """Main validation service with updated format support"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries"):
        self.name_validator = NameValidator(dictionary_path)
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
    
    def validate_names(self, names_data: Dict) -> Dict:
        """
        Validate names using the new format
        
        Input: {"names": [{"uniqueID": "1", "fullName": "Bill Smith", ...}]}
        Output: {"names": [{"uniqueID": "1", "firstName": "Bill", ...}]}
        """
        start_time = time.time()
        
        names = names_data.get('names', [])
        results = []
        
        logger.info(f"Processing {len(names)} name records", "SERVICE")
        
        for name_record in names:
            try:
                # Validate single name record
                result = self.name_validator.validate_name_record(name_record)
                results.append(result)
                
            except Exception as e:
                # Create error result
                error_result = {
                    'uniqueID': name_record.get('uniqueID', ''),
                    'partyTypeCd': '',
                    'prefix': None,
                    'firstName': None,
                    'firstNameStd': None,
                    'middleName': None,
                    'lastName': None,
                    'suffix': None,
                    'fullName': name_record.get('fullName', ''),
                    'inGenderCd': name_record.get('genderCd', ''),
                    'outGenderCd': '',
                    'prefixLt': None,
                    'firstNameLt': None,
                    'middleNameLt': None,
                    'lastNameLt': None,
                    'suffixLt': None,
                    'parseInd': name_record.get('parseInd', ''),
                    'confidenceScore': '0.0',
                    'parseStatus': 'Error',
                    'errorMessage': f'Processing error: {str(e)}'
                }
                results.append(error_result)
                logger.error(f"Error processing name record {name_record.get('uniqueID')}: {e}", "SERVICE")
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Name validation completed in {processing_time}ms", "SERVICE")
        
        return {'names': results}
    
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
            # Create name record for validation
            name_record = {
                'uniqueID': 'temp',
                'fullName': f"{first_name} {last_name}",
                'genderCd': '',
                'partyTypeCd': 'I',
                'parseInd': 'Y'
            }
            
            # Validate name
            name_result = self.name_validator.validate_name_record(name_record)
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
            name_valid = name_result.get('parseStatus') in ['Parsed', 'Not Parsed']
            address_deliverable = address_result.get('deliverable', False)
            
            result['overall_valid'] = name_valid and address_deliverable
            
            # Calculate confidence
            name_confidence = float(name_result.get('confidenceScore', '0')) / 100
            address_confidence = address_result.get('confidence', 0)
            result['overall_confidence'] = (name_confidence + address_confidence) / 2
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(error_msg, "SERVICE")
        
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def process_csv_names(self, df: pd.DataFrame) -> Dict:
        """Process names from CSV DataFrame with new format"""
        
        logger.info(f"Processing CSV with {len(df)} rows", "SERVICE")
        
        # Try to find name column
        name_columns = ['name', 'full_name', 'fullname', 'fullName', 'Name', 'FULL_NAME']
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
        
        # Convert DataFrame to names format
        names_data = []
        for idx, row in df.iterrows():
            full_name = str(row[name_col]).strip()
            
            if full_name and full_name != 'nan':
                name_record = {
                    'uniqueID': str(idx + 1),
                    'fullName': full_name,
                    'genderCd': '',
                    'partyTypeCd': '',
                    'parseInd': 'Y'
                }
                names_data.append(name_record)
        
        if not names_data:
            return {
                'success': False,
                'error': 'No valid names found in CSV'
            }
        
        # Process using new validation
        results = self.validate_names({'names': names_data})
        
        # Convert results for CSV output
        csv_results = []
        successful = 0
        
        for result in results['names']:
            csv_result = {
                'row_number': result['uniqueID'],
                'original_name': result['fullName'],
                'prefix': result['prefix'] or '',
                'first_name': result['firstName'] or '',
                'first_name_std': result['firstNameStd'] or '',
                'middle_name': result['middleName'] or '',
                'last_name': result['lastName'] or '',
                'suffix': result['suffix'] or '',
                'gender': result['outGenderCd'],
                'party_type': result['partyTypeCd'],
                'confidence_score': result['confidenceScore'],
                'parse_status': result['parseStatus'],
                'error_message': result['errorMessage']
            }
            csv_results.append(csv_result)
            
            if result['parseStatus'] in ['Parsed', 'Not Parsed']:
                successful += 1
        
        return {
            'success': True,
            'total_records': len(df),
            'processed_records': len(csv_results),
            'successful_validations': successful,
            'success_rate': successful / len(csv_results) if csv_results else 0,
            'results': csv_results
        }
    
    def get_example_payload(self) -> Dict:
        """Get example payload for testing"""
        return {
            "names": [
                {
                    "uniqueID": "1",
                    "fullName": "Bill Smith",
                    "genderCd": "M",
                    "partyTypeCd": "I",
                    "parseInd": "Y"
                },
                {
                    "uniqueID": "2",
                    "fullName": "Dr. Sarah Johnson-Williams",
                    "genderCd": "",
                    "partyTypeCd": "",
                    "parseInd": "Y"
                },
                {
                    "uniqueID": "3",
                    "fullName": "TechCorp Solutions LLC",
                    "genderCd": "",
                    "partyTypeCd": "O",
                    "parseInd": "N"
                },
                {
                    "uniqueID": "4",
                    "fullName": "Mr. Michael Thompson Jr.",
                    "genderCd": "",
                    "partyTypeCd": "I",
                    "parseInd": "Y"
                }
            ]
        }