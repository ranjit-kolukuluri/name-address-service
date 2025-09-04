# core/services.py
"""
Updated validation service with dictionary integration and enhanced address processing
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
    """Enhanced validation service with dictionary integration and batch address processing"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries"):
        self.name_validator = NameValidator(dictionary_path)
        self.address_validator = AddressValidator()
        self.dictionary_status = self.name_validator.dictionary_loaded
        
        logger.info(f"Validation service initialized - dictionaries: {self.dictionary_status}", "SERVICE")
        
        # Log validation capabilities
        if self.dictionary_status:
            logger.info("Dictionary validation available with AI fallback", "SERVICE")
        else:
            logger.warning("Dictionary not loaded - using AI-only validation", "SERVICE")
    
    def is_name_validation_available(self) -> bool:
        """Check if name validation is available"""
        return True  # Always available (has AI fallback)
    
    def is_address_validation_available(self) -> bool:
        """Check if address validation is available"""
        return self.address_validator.is_configured()
    
    def get_service_status(self) -> Dict:
        """Get enhanced service status"""
        status = {
            'name_validation_available': self.is_name_validation_available(),
            'address_validation_available': self.is_address_validation_available(),
            'api_version': Config.API_VERSION,
            'timestamp': datetime.now().isoformat(),
            'dictionary_status': self.dictionary_status,
            'validation_mode': 'Dictionary + AI' if self.dictionary_status else 'AI Only'
        }
        
        # Add dictionary statistics if loaded
        if self.dictionary_status:
            dict_stats = self._get_dictionary_statistics()
            status['dictionary_statistics'] = dict_stats
        
        return status
    
    def _get_dictionary_statistics(self) -> Dict:
        """Get statistics about loaded dictionaries"""
        stats = {}
        
        validator = self.name_validator
        
        if hasattr(validator, 'first_names_set'):
            stats['first_names_count'] = len(validator.first_names_set)
        
        if hasattr(validator, 'surnames_set'):
            stats['surnames_count'] = len(validator.surnames_set)
        
        if hasattr(validator, 'name_to_gender'):
            stats['gender_mappings_count'] = len(validator.name_to_gender)
        
        if hasattr(validator, 'nickname_to_standard'):
            stats['nickname_mappings_count'] = len(validator.nickname_to_standard)
        
        if hasattr(validator, 'business_words_set'):
            stats['business_words_count'] = len(validator.business_words_set)
        
        if hasattr(validator, 'company_suffixes_set'):
            stats['company_suffixes_count'] = len(validator.company_suffixes_set)
        
        return stats
    
    def validate_names(self, names_data: Dict) -> Dict:
        """
        Enhanced name validation with dictionary lookup and AI fallback
        """
        start_time = time.time()
        
        names = names_data.get('names', [])
        results = []
        
        # Track validation methods used
        method_stats = {
            'deterministic': 0,
            'hybrid': 0,
            'ai_fallback': 0,
            'error': 0
        }
        
        logger.info(f"Processing {len(names)} name records with enhanced validation", "SERVICE")
        
        for name_record in names:
            try:
                # Validate single name record with enhanced validator
                result = self.name_validator.validate_name_record(name_record)
                results.append(result)
                
                # Track validation method
                validation_method = result.get('validationMethod', 'unknown')
                if validation_method in method_stats:
                    method_stats[validation_method] += 1
                else:
                    method_stats['error'] += 1
                
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
                    'errorMessage': f'Processing error: {str(e)}',
                    'validationMethod': 'error'
                }
                results.append(error_result)
                method_stats['error'] += 1
                logger.error(f"Error processing name record {name_record.get('uniqueID')}: {e}", "SERVICE")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log method statistics
        total_processed = len(results)
        if total_processed > 0:
            det_pct = (method_stats['deterministic'] / total_processed) * 100
            hybrid_pct = (method_stats['hybrid'] / total_processed) * 100
            ai_pct = (method_stats['ai_fallback'] / total_processed) * 100
            
            logger.info(
                f"Validation completed in {processing_time}ms - "
                f"Dictionary: {det_pct:.1f}%, Hybrid: {hybrid_pct:.1f}%, "
                f"AI Fallback: {ai_pct:.1f}%",
                "SERVICE"
            )
        
        return {
            'names': results,
            'processing_stats': {
                'total_processed': total_processed,
                'processing_time_ms': processing_time,
                'validation_methods': method_stats,
                'dictionary_available': self.dictionary_status
            }
        }
    
    def validate_addresses(self, addresses_data: Dict) -> Dict:
        """
        Enhanced batch address validation
        """
        start_time = time.time()
        
        addresses = addresses_data.get('addresses', [])
        
        if not self.is_address_validation_available():
            # Return error results for all addresses
            error_results = []
            for addr in addresses:
                error_result = self.address_validator._create_error_result(addr, 'USPS API not configured')
                error_results.append(error_result)
            
            return {
                'addresses': error_results,
                'processing_stats': {
                    'total_processed': len(addresses),
                    'successful': 0,
                    'failed': len(addresses),
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'usps_configured': False
                }
            }
        
        logger.info(f"Processing {len(addresses)} addresses with USPS validation", "SERVICE")
        
        # Validate addresses in batch
        results = self.address_validator.validate_addresses_batch(addresses)
        
        # Calculate success/failure stats
        successful = 0
        failed = 0
        
        for result in results:
            if result.get('errorMsg') is None and result.get('mailabilityScore') == '1':
                successful += 1
            else:
                failed += 1
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Address validation completed in {processing_time}ms - "
            f"Successful: {successful}, Failed: {failed}",
            "SERVICE"
        )
        
        return {
            'addresses': results,
            'processing_stats': {
                'total_processed': len(results),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / len(results)) if results else 0,
                'processing_time_ms': processing_time,
                'usps_configured': True
            }
        }
    
    def validate_single_address(self, address_data: Dict) -> Dict:
        """Validate a single address (legacy method)"""
        logger.info(f"Validating single address", "SERVICE")
        return self.address_validator.validate_address(address_data)
    
    def validate_complete_record(self, first_name: str, last_name: str,
                                street_address: str, city: str, state: str, zip_code: str) -> Dict:
        """Enhanced complete record validation"""
        
        start_time = time.time()
        
        result = {
            'timestamp': datetime.now(),
            'name_result': None,
            'address_result': None,
            'overall_valid': False,
            'overall_confidence': 0.0,
            'processing_time_ms': 0,
            'validation_methods': {
                'name_method': 'unknown',
                'address_method': 'usps_api'
            },
            'errors': [],
            'warnings': []
        }
        
        try:
            # Create name record for enhanced validation
            name_record = {
                'uniqueID': 'temp',
                'fullName': f"{first_name} {last_name}",
                'genderCd': '',
                'partyTypeCd': 'I',
                'parseInd': 'Y'
            }
            
            # Validate name with enhanced validator
            name_result = self.name_validator.validate_name_record(name_record)
            result['name_result'] = name_result
            result['validation_methods']['name_method'] = name_result.get('validationMethod', 'unknown')
            
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
            
            # Enhanced confidence calculation
            name_confidence = float(name_result.get('confidenceScore', '0')) / 100
            address_confidence = address_result.get('confidence', 0)
            
            # Weight confidence based on validation method
            name_method = result['validation_methods']['name_method']
            if 'deterministic' in name_method:
                name_weight = 0.6  # Higher weight for deterministic
            else:
                name_weight = 0.4  # Lower weight for AI
            
            address_weight = 1.0 - name_weight
            result['overall_confidence'] = (name_confidence * name_weight) + (address_confidence * address_weight)
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(error_msg, "SERVICE")
        
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def process_csv_names(self, df: pd.DataFrame) -> Dict:
        """Enhanced CSV processing with validation method tracking"""
        
        logger.info(f"Processing CSV with {len(df)} rows using enhanced validation", "SERVICE")
        
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
        
        # Process using enhanced validation
        validation_result = self.validate_names({'names': names_data})
        results = validation_result['names']
        processing_stats = validation_result.get('processing_stats', {})
        
        # Convert results for CSV output with enhanced information
        csv_results = []
        successful = 0
        method_counts = {
            'deterministic': 0,
            'hybrid': 0,
            'ai_fallback': 0
        }
        
        for result in results:
            validation_method = result.get('validationMethod', 'unknown')
            
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
                'error_message': result['errorMessage'],
                'validation_method': validation_method
            }
            csv_results.append(csv_result)
            
            if result['parseStatus'] in ['Parsed', 'Not Parsed']:
                successful += 1
            
            # Count validation methods
            if validation_method in method_counts:
                method_counts[validation_method] += 1
        
        return {
            'success': True,
            'total_records': len(df),
            'processed_records': len(csv_results),
            'successful_validations': successful,
            'success_rate': successful / len(csv_results) if csv_results else 0,
            'validation_method_breakdown': method_counts,
            'dictionary_available': self.dictionary_status,
            'processing_stats': processing_stats,
            'results': csv_results
        }
    
    def process_csv_addresses(self, df: pd.DataFrame) -> Dict:
        """Process addresses from CSV with automatic format standardization"""
        
        logger.info(f"Processing address CSV with {len(df)} rows", "SERVICE")
        
        try:
            # Standardize CSV format to address format
            standardized_addresses = self.address_validator.standardize_csv_to_address_format(df)
            
            if not standardized_addresses:
                return {
                    'success': False,
                    'error': 'No valid addresses found in CSV'
                }
            
            # Validate addresses using batch processing
            validation_result = self.validate_addresses({'addresses': standardized_addresses})
            results = validation_result['addresses']
            processing_stats = validation_result.get('processing_stats', {})
            
            # Convert results for CSV output
            csv_results = []
            successful = 0
            
            for result in results:
                is_valid = result.get('errorMsg') is None and result.get('mailabilityScore') == '1'
                
                csv_result = {
                    'guid': result['guid'],
                    'input_line1': result['inLine1'] or '',
                    'input_city': result['inLine6'] or '',
                    'input_state': result['inLine7'] or '',
                    'input_zip': result['inLine8'] or '',
                    'validated_line1': result['deliveryAddressLine1'] or '',
                    'validated_city': result['city'] or '',
                    'validated_state': result['stateCd'] or '',
                    'validated_zip': result['zipCdComplete'] or '',
                    'county_name': result['countyName'] or '',
                    'carrier_route': result['carrierRoute'] or '',
                    'congressional_district': result['congressionalDistrict'] or '',
                    'mailability_score': result['mailabilityScore'] or '0',
                    'match_code': result['matchCode'] or '',
                    'result_percentage': result['ResultPercentage'] or '0.00',
                    'is_valid': is_valid,
                    'error_message': result['errorMsg'] or ''
                }
                csv_results.append(csv_result)
                
                if is_valid:
                    successful += 1
            
            return {
                'success': True,
                'total_records': len(df),
                'processed_records': len(csv_results),
                'successful_validations': successful,
                'success_rate': successful / len(csv_results) if csv_results else 0,
                'usps_configured': self.is_address_validation_available(),
                'processing_stats': processing_stats,
                'results': csv_results
            }
            
        except Exception as e:
            logger.error(f"Error processing address CSV: {e}", "SERVICE")
            return {
                'success': False,
                'error': f'CSV processing failed: {str(e)}'
            }
    
    def get_example_payload(self) -> Dict:
        """Get enhanced example payload for testing"""
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
                },
                {
                    "uniqueID": "5",
                    "fullName": "Bob Johnson",
                    "genderCd": "",
                    "partyTypeCd": "",
                    "parseInd": "Y"
                }
            ]
        }
    
    def get_example_address_payload(self) -> Dict:
        """Get example address payload for testing"""
        return {
            "addresses": [
                {
                    "guid": "1",
                    "line1": "1394 N SAINT LOUIS",
                    "line2": None,
                    "line3": None,
                    "line4": None,
                    "line5": None,
                    "city": "BATESVILLE",
                    "stateCd": "AR",
                    "zipCd": "72501",
                    "countryCd": "US",
                    "verificationInd": "Y",
                    "onlyOneAddrInd": "N"
                },
                {
                    "guid": "2",
                    "line1": "123 Main Street",
                    "line2": "Apt 4B",
                    "line3": None,
                    "line4": None,
                    "line5": None,
                    "city": "New York",
                    "stateCd": "NY",
                    "zipCd": "10001",
                    "countryCd": "US",
                    "verificationInd": "Y",
                    "onlyOneAddrInd": "N"
                }
            ]
        }