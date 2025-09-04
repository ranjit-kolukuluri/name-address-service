#!/usr/bin/env python3
"""
Simple setup script for dictionary integration
"""

import os
import sys
from pathlib import Path

def setup_directory():
    """Create dictionary directory if it doesn't exist"""
    dictionary_path = "/Users/t93uyz8/Documents/name_dictionaries"
    
    print("📁 Setting up dictionary directory...")
    
    if not os.path.exists(dictionary_path):
        try:
            os.makedirs(dictionary_path, exist_ok=True)
            print(f"✅ Created directory: {dictionary_path}")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            return False
    else:
        print(f"✅ Directory already exists: {dictionary_path}")
    
    # Check for existing CSV files
    csv_files = list(Path(dictionary_path).glob("*.csv"))
    print(f"📊 Found {len(csv_files)} CSV files in directory")
    
    if len(csv_files) == 0:
        print("⚠️  No dictionary files found")
        print("   Run 'python test_dictionary_integration.py' to create sample files")
        print("   Or place your CSV files in the dictionary directory")
    
    return True

def test_imports():
    """Test that all required modules can be imported"""
    print("\n🔍 Testing imports...")
    
    try:
        from core.services import ValidationService
        from core.validators import NameValidator
        print("✅ Core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False

def test_basic_functionality():
    """Test basic validation functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from core.services import ValidationService
        
        service = ValidationService()
        print(f"✅ Service initialized - Dictionary: {'Loaded' if service.dictionary_status else 'Not loaded'}")
        
        # Test a simple validation
        test_record = {
            "uniqueID": "test",
            "fullName": "John Smith",
            "genderCd": "",
            "partyTypeCd": "",
            "parseInd": "Y"
        }
        
        result = service.validate_names({'names': [test_record]})
        
        if result['names']:
            name_result = result['names'][0]
            method = name_result.get('validationMethod', 'unknown')
            confidence = name_result.get('confidenceScore', '0')
            
            print(f"✅ Test validation successful")
            print(f"   Method: {method}")
            print(f"   Confidence: {confidence}%")
            return True
        else:
            print("❌ Test validation failed - no results")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_next_steps():
    """Show next steps to the user"""
    print("\n🚀 Next Steps:")
    print("=" * 30)
    print("1. Place your dictionary CSV files in:")
    print("   /Users/t93uyz8/Documents/name_dictionaries/")
    print()
    print("2. Test the dictionary integration:")
    print("   python test_dictionary_integration.py")
    print()
    print("3. Start the applications:")
    print("   python api/main.py          # API on port 8000")
    print("   streamlit run ui/app.py     # UI on port 8501")
    print()
    print("4. Or use the run script:")
    print("   ./run.sh")
    print()
    print("📚 Expected dictionary files:")
    expected_files = [
        "usa_firstnames_infa.csv",
        "usa_surnames_infa.csv", 
        "usa_gender_infa.csv",
        "usa_nicknames_infa.csv",
        "usa_business_word_infa.csv",
        "usa_company_sufx_abrv_infa.csv",
        "usa_name_prefix_NYL.csv"
    ]
    
    for file in expected_files:
        print(f"   • {file}")

def main():
    """Main setup function"""
    print("🤖 Dictionary Integration Setup")
    print("=" * 40)
    print()
    
    # Check if we're in the right directory
    if not Path("core").exists() or not Path("ui").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   The directory should contain 'core/', 'ui/', and 'api/' folders")
        sys.exit(1)
    
    success = True
    
    # Setup directory
    if not setup_directory():
        success = False
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test functionality
    if not test_basic_functionality():
        success = False
    
    print("\n" + "=" * 40)
    
    if success:
        print("✅ Dictionary integration setup completed successfully!")
        show_next_steps()
    else:
        print("❌ Setup encountered some issues")
        print("   Please check the error messages above and try again")
        print("   Make sure you're in the project root directory")

if __name__ == "__main__":
    main()