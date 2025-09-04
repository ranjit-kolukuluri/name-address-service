# test_new_format.py
"""
Test script for the new enhanced name validation format
"""

import json
import requests
import sys
from pathlib import Path

# Add parent directory to path
current_file = Path(__file__).resolve()
parent_dir = current_file.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from core.services import ValidationService


def test_validation_service():
    """Test the validation service directly"""
    print("🔬 Testing Enhanced Validation Service")
    print("=" * 50)
    
    # Initialize service
    service = ValidationService()
    
    # Test cases
    test_cases = [
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
            "partyTypeCd": "",
            "parseInd": "Y"
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
            "fullName": "Jennifer",
            "genderCd": "",
            "partyTypeCd": "",
            "parseInd": "Y"
        }
    ]
    
    # Process test cases
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['fullName']}")
        print("-" * 30)
        
        # Create input payload
        input_data = {"names": [test_case]}
        
        # Validate
        result = service.validate_names(input_data)
        
        if result['names']:
            name_result = result['names'][0]
            
            print(f"✅ Input: {test_case['fullName']}")
            print(f"🏷️  Party Type: {name_result['partyTypeCd']}")
            print(f"👤 Gender: {name_result['inGenderCd']} → {name_result['outGenderCd']}")
            print(f"📊 Confidence: {name_result['confidenceScore']}%")
            print(f"📝 Status: {name_result['parseStatus']} - {name_result['errorMessage']}")
            
            if name_result['parseInd'] == 'Y' and name_result['partyTypeCd'] == 'I':
                print(f"🔍 Parsed Components:")
                if name_result['prefix']:
                    print(f"   Prefix: {name_result['prefix']}")
                print(f"   First: {name_result['firstName']} → {name_result['firstNameStd']}")
                if name_result['middleName']:
                    print(f"   Middle: {name_result['middleName']}")
                print(f"   Last: {name_result['lastName']}")
                if name_result['suffix']:
                    print(f"   Suffix: {name_result['suffix']}")


def test_api_endpoint():
    """Test the API endpoint (if running)"""
    print("\n\n🌐 Testing API Endpoint")
    print("=" * 50)
    
    api_url = "http://localhost:8000/api/v2/validate-names"
    
    test_payload = {
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
                "fullName": "Microsoft Corporation",
                "genderCd": "",
                "partyTypeCd": "",
                "parseInd": "Y"
            }
        ]
    }
    
    try:
        response = requests.post(api_url, json=test_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response successful!")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running. Start with: cd api && python main.py")
    except Exception as e:
        print(f"❌ API Test Error: {e}")


def test_example_from_requirements():
    """Test the exact example from requirements"""
    print("\n\n📋 Testing Requirements Example")
    print("=" * 50)
    
    service = ValidationService()
    
    # Exact input from requirements
    input_data = {
        "names": [
            {
                "uniqueID": "1",
                "fullName": "Bill SMith",  # Note: deliberate typo in requirements
                "genderCd": "M",
                "partyTypeCd": "I",
                "parseInd": "Y"
            }
        ]
    }
    
    print("📥 Input:")
    print(json.dumps(input_data, indent=2))
    
    # Process
    result = service.validate_names(input_data)
    
    print("\n📤 Output:")
    print(json.dumps(result, indent=2))
    
    # Verify output format matches requirements
    if result['names']:
        name_result = result['names'][0]
        required_fields = [
            'uniqueID', 'partyTypeCd', 'prefix', 'firstName', 'firstNameStd',
            'middleName', 'lastName', 'suffix', 'fullName', 'inGenderCd',
            'outGenderCd', 'prefixLt', 'firstNameLt', 'middleNameLt',
            'lastNameLt', 'suffixLt', 'parseInd', 'confidenceScore',
            'parseStatus', 'errorMessage'
        ]
        
        print("\n✅ Field Validation:")
        for field in required_fields:
            if field in name_result:
                print(f"   ✓ {field}: {name_result[field]}")
            else:
                print(f"   ❌ Missing: {field}")


def demonstrate_ai_features():
    """Demonstrate AI enhancement features"""
    print("\n\n🤖 AI Enhancement Demonstration")
    print("=" * 50)
    
    service = ValidationService()
    
    ai_test_cases = [
        {
            "description": "Gender Prediction",
            "name": "Jennifer Adams",
            "genderCd": "",  # Empty for AI prediction
            "partyTypeCd": "I",
            "parseInd": "Y"
        },
        {
            "description": "Organization Detection",
            "name": "Advanced Medical Solutions Inc",
            "genderCd": "",
            "partyTypeCd": "",  # Empty for AI detection
            "parseInd": "Y"
        },
        {
            "description": "Name Standardization",
            "name": "Bill Johnson",
            "genderCd": "",
            "partyTypeCd": "I",
            "parseInd": "Y"
        },
        {
            "description": "Prefix/Suffix Extraction",
            "name": "Dr. Robert Smith Jr.",
            "genderCd": "",
            "partyTypeCd": "I",
            "parseInd": "Y"
        }
    ]
    
    for i, test_case in enumerate(ai_test_cases, 1):
        print(f"\n🎯 AI Feature {i}: {test_case['description']}")
        print(f"   Input: {test_case['name']}")
        
        input_data = {
            "names": [
                {
                    "uniqueID": str(i),
                    "fullName": test_case['name'],
                    "genderCd": test_case['genderCd'],
                    "partyTypeCd": test_case['partyTypeCd'],
                    "parseInd": test_case['parseInd']
                }
            ]
        }
        
        result = service.validate_names(input_data)
        
        if result['names']:
            name_result = result['names'][0]
            
            print(f"   🔍 AI Analysis:")
            print(f"      Party Type: {name_result['partyTypeCd']}")
            print(f"      Gender: {name_result['outGenderCd']}")
            print(f"      Confidence: {name_result['confidenceScore']}%")
            
            if name_result['firstName'] and name_result['firstNameStd']:
                if name_result['firstName'] != name_result['firstNameStd']:
                    print(f"      Standardization: {name_result['firstName']} → {name_result['firstNameStd']}")
            
            if name_result['prefix'] or name_result['suffix']:
                extracted = []
                if name_result['prefix']:
                    extracted.append(f"Prefix: {name_result['prefix']}")
                if name_result['suffix']:
                    extracted.append(f"Suffix: {name_result['suffix']}")
                print(f"      Extracted: {', '.join(extracted)}")


if __name__ == "__main__":
    print("🚀 Enhanced Name Validator Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_validation_service()
    test_example_from_requirements()
    demonstrate_ai_features()
    test_api_endpoint()
    
    print("\n\n✅ Test Suite Complete!")
    print("\nTo run the application:")
    print("  Streamlit UI: streamlit run ui/app.py")
    print("  FastAPI:      cd api && python main.py")
    print("  Both:         ./run.sh")