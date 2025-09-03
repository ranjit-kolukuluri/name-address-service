# minimal_app.py
"""
Minimal working app to test basic functionality
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Minimal Validator",
    page_icon="⚡",
    layout="wide"
)

# Apply basic styling
st.markdown("""
<style>
.main { font-family: 'Inter', sans-serif; }
.header {
    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
    padding: 2rem; border-radius: 16px; margin-bottom: 2rem;
    text-align: center; color: white;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('''
<div class="header">
    <h1>⚡ Minimal Name Validator</h1>
    <p>Basic validation without external dependencies</p>
</div>
''', unsafe_allow_html=True)

# Simple name validation function
def simple_name_validation(first_name: str, last_name: str):
    """Simple name validation without dependencies"""
    errors = []
    warnings = []
    
    if not first_name.strip():
        errors.append("First name is required")
    elif len(first_name.strip()) < 2:
        warnings.append("First name seems short")
    
    if not last_name.strip():
        errors.append("Last name is required")
    elif len(last_name.strip()) < 2:
        warnings.append("Last name seems short")
    
    valid = len(errors) == 0
    confidence = 0.8 if valid else 0.2
    
    return {
        'valid': valid,
        'confidence': confidence,
        'errors': errors,
        'warnings': warnings,
        'normalized': {
            'first_name': first_name.strip().title(),
            'last_name': last_name.strip().title()
        },
        'timestamp': datetime.now()
    }

# Simple organization detection
def is_organization(name: str) -> bool:
    """Simple organization detection"""
    if not name:
        return False
    
    name_lower = name.lower()
    org_indicators = ['llc', 'inc', 'corp', 'company', 'ltd']
    return any(indicator in name_lower for indicator in org_indicators)

# Parse full name
def parse_full_name(full_name: str):
    """Simple full name parsing"""
    if not full_name:
        return {'first_name': '', 'last_name': '', 'middle_name': ''}
    
    parts = full_name.strip().split()
    
    if len(parts) == 0:
        return {'first_name': '', 'last_name': '', 'middle_name': ''}
    elif len(parts) == 1:
        return {'first_name': parts[0], 'last_name': '', 'middle_name': ''}
    elif len(parts) == 2:
        return {'first_name': parts[0], 'last_name': parts[1], 'middle_name': ''}
    else:
        return {
            'first_name': parts[0],
            'last_name': parts[-1],
            'middle_name': ' '.join(parts[1:-1])
        }

# Main tabs
tab1, tab2, tab3 = st.tabs(["👤 Name Validation", "🧪 API Testing", "📊 Info"])

with tab1:
    st.header("Single Name Validation")
    
    with st.form("name_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", placeholder="Enter first name")
        
        with col2:
            last_name = st.text_input("Last Name", placeholder="Enter last name")
        
        submitted = st.form_submit_button("🔍 Validate Name", type="primary")
        
        if submitted:
            if first_name or last_name:
                result = simple_name_validation(first_name, last_name)
                
                # Display results
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    status = "✅ Valid" if result['valid'] else "❌ Invalid"
                    st.metric("Status", status)
                
                with col4:
                    st.metric("Confidence", f"{result['confidence']:.1%}")
                
                with col5:
                    st.metric("Issues", len(result['errors']) + len(result['warnings']))
                
                # Normalized name
                if result['valid']:
                    normalized = result['normalized']
                    st.success(f"**Normalized:** {normalized['first_name']} {normalized['last_name']}")
                
                # Errors and warnings
                if result['errors']:
                    st.error("**Errors:**")
                    for error in result['errors']:
                        st.write(f"- {error}")
                
                if result['warnings']:
                    st.warning("**Warnings:**")
                    for warning in result['warnings']:
                        st.write(f"- {warning}")
            else:
                st.warning("Please enter at least one name")

with tab2:
    st.header("API Testing")
    
    # Full name parsing
    st.subheader("Full Name Parsing")
    full_name = st.text_input("Full Name", placeholder="Enter full name to parse")
    
    if full_name:
        parsed = parse_full_name(full_name)
        is_org = is_organization(full_name)
        
        st.write("**Parsed Components:**")
        st.json(parsed)
        
        st.write(f"**Organization:** {'Yes' if is_org else 'No'}")
    
    # JSON API simulation
    st.subheader("JSON API Simulation")
    
    default_payload = {
        "records": [
            {
                "uniqueid": "001",
                "name": "John Michael Smith",
                "parseInd": "Y"
            },
            {
                "uniqueid": "002",
                "name": "TechCorp Solutions LLC",
                "parseInd": "Y"
            }
        ]
    }
    
    json_input = st.text_area(
        "JSON Payload:",
        value=json.dumps(default_payload, indent=2),
        height=200
    )
    
    if st.button("🚀 Process JSON", type="primary"):
        try:
            payload = json.loads(json_input)
            records = payload.get('records', [])
            
            results = []
            for record in records:
                name = record.get('name', '')
                parsed = parse_full_name(name)
                is_org = is_organization(name)
                
                if is_org:
                    result = {
                        'uniqueid': record.get('uniqueid'),
                        'name': name,
                        'party_type': 'O',
                        'validation_status': 'valid',
                        'confidence_score': 0.9,
                        'parsed_components': {'organization_name': name}
                    }
                else:
                    validation = simple_name_validation(parsed['first_name'], parsed['last_name'])
                    result = {
                        'uniqueid': record.get('uniqueid'),
                        'name': name,
                        'party_type': 'I',
                        'validation_status': 'valid' if validation['valid'] else 'invalid',
                        'confidence_score': validation['confidence'],
                        'parsed_components': parsed
                    }
                
                results.append(result)
            
            response = {
                'status': 'success',
                'processed_count': len(results),
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
            st.success("✅ JSON processed successfully!")
            st.json(response)
            
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON format")
        except Exception as e:
            st.error(f"❌ Processing error: {str(e)}")

with tab3:
    st.header("System Information")
    
    import sys
    from pathlib import Path
    
    st.write("**App Status:** ✅ Working")
    st.write(f"**Python Version:** {sys.version}")
    st.write(f"**Streamlit Version:** {st.__version__}")
    st.write(f"**Current Directory:** {Path.cwd()}")
    st.write(f"**File Location:** {Path(__file__).parent}")
    
    st.subheader("Available Features")
    st.write("✅ Basic name validation")
    st.write("✅ Full name parsing")
    st.write("✅ Organization detection")
    st.write("✅ JSON API simulation")
    st.write("❌ USPS address validation (requires full app)")
    
    st.subheader("Test Results")
    test_result = simple_name_validation("John", "Smith")
    st.json(test_result)

st.markdown("---")
st.info("💡 This minimal app tests basic functionality. If this works, the issue is in the full app initialization.")