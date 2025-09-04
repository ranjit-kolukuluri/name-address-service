# ui/app.py
"""
Updated Streamlit UI for name and address validation with new format
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from core.services import ValidationService
from utils.logger import logger


class ValidatorApp:
    """Enhanced Streamlit application with new format support"""
    
    def __init__(self):
        self.service = ValidationService()
        
        # Initialize session state
        if 'validation_results' not in st.session_state:
            st.session_state.validation_results = []
        
        if 'processing_stats' not in st.session_state:
            st.session_state.processing_stats = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0
            }
    
    def apply_styling(self):
        """Apply enhanced CSS styling"""
        st.markdown("""
        <style>
        .main {
            font-family: 'Inter', sans-serif;
        }
        
        .header {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        }
        
        .title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .status-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            display: inline-block;
            margin: 0.5rem;
        }
        
        .status-warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            display: inline-block;
            margin: 0.5rem;
        }
        
        .result-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .confidence-high {
            color: #059669;
            font-weight: bold;
        }
        
        .confidence-medium {
            color: #d97706;
            font-weight: bold;
        }
        
        .confidence-low {
            color: #dc2626;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render enhanced application header"""
        name_available = self.service.is_name_validation_available()
        address_available = self.service.is_address_validation_available()
        
        st.markdown('''
        <div class="header">
            <div class="title">Name & Address Validator v2.0</div>
            <div class="subtitle">Enhanced AI-powered validation with intelligent detection</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            status_html = ""
            if name_available:
                status_html += '<span class="status-success">✓ AI Name Validation Ready</span>'
            else:
                status_html += '<span class="status-warning">⚠ Name Service Unavailable</span>'
            
            if address_available:
                status_html += '<span class="status-success">✓ USPS API Connected</span>'
            else:
                status_html += '<span class="status-warning">⚠ USPS API Not Configured</span>'
            
            st.markdown(f'<div style="text-align: center;">{status_html}</div>', unsafe_allow_html=True)
    
    def render_name_validation(self):
        """Render enhanced name validation interface"""
        st.markdown("## 👤 Enhanced Name Validation with AI")
        
        # Single name validation
        with st.expander("Single Name Validation", expanded=True):
            with st.form("single_name_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    full_name = st.text_input("Full Name", placeholder="Enter full name (e.g., Dr. William Smith Jr.)")
                
                with col2:
                    col2a, col2b, col2c = st.columns(3)
                    
                    with col2a:
                        gender_cd = st.selectbox("Gender", ["", "M", "F"], help="Leave empty for AI prediction")
                    
                    with col2b:
                        party_type_cd = st.selectbox("Party Type", ["", "I", "O"], help="I=Individual, O=Organization, empty=AI detection")
                    
                    with col2c:
                        parse_ind = st.selectbox("Parse", ["Y", "N"], help="Y=Parse name components")
                
                submitted = st.form_submit_button("🔍 Validate Name", type="primary")
                
                if submitted and full_name:
                    with st.spinner("Processing with AI..."):
                        # Create name record
                        name_record = {
                            'uniqueID': '1',
                            'fullName': full_name,
                            'genderCd': gender_cd,
                            'partyTypeCd': party_type_cd,
                            'parseInd': parse_ind
                        }
                        
                        # Validate using new format
                        result = self.service.validate_names({'names': [name_record]})
                        
                        if result['names']:
                            self._display_enhanced_name_result(result['names'][0])
        
        # Enhanced API Testing
        with st.expander("Enhanced API Testing (v2.0 Format)"):
            st.markdown("### Test New API Format")
            
            # Get example payload
            default_payload = self.service.get_example_payload()
            
            json_input = st.text_area(
                "JSON Payload (v2.0 Format):",
                value=json.dumps(default_payload, indent=2),
                height=300
            )
            
            if st.button("🚀 Test Enhanced API", type="primary"):
                try:
                    payload = json.loads(json_input)
                    
                    with st.spinner("Processing with AI enhancements..."):
                        result = self.service.validate_names(payload)
                        
                        st.success("✅ API request processed successfully")
                        
                        # Display results in a nice format
                        for name_result in result['names']:
                            self._display_enhanced_name_result(name_result)
                        
                        # Show raw JSON for developers
                        with st.expander("Raw JSON Response"):
                            st.json(result)
                        
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Enhanced CSV Upload
        with st.expander("Enhanced CSV Upload"):
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.success(f"✅ File uploaded: {len(df)} rows")
                    
                    # Show preview
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    if st.button("🔄 Process with AI Enhancement", type="primary"):
                        with st.spinner("Processing CSV with AI..."):
                            result = self.service.process_csv_names(df)
                            
                            if result['success']:
                                st.success(f"✅ Processed {result['processed_records']} names")
                                st.write(f"Success rate: {result['success_rate']:.1%}")
                                
                                if result['results']:
                                    # Create enhanced results DataFrame
                                    results_df = pd.DataFrame(result['results'])
                                    st.dataframe(results_df, use_container_width=True)
                                    
                                    # Download button
                                    csv = results_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Results",
                                        data=csv,
                                        file_name=f"validated_names_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                            else:
                                st.error(f"❌ {result['error']}")
                                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
    
    def render_address_validation(self):
        """Render address validation interface (unchanged)"""
        st.markdown("## 🏠 Address Validation")
        
        # Check if service is available
        if not self.service:
            st.error("❌ Address validation service not available")
            return
        
        try:
            if not self.service.is_address_validation_available():
                st.warning("⚠️ USPS API not configured. Please set USPS_CLIENT_ID and USPS_CLIENT_SECRET.")
                return
        except Exception as e:
            st.error(f"Error checking USPS configuration: {e}")
            return
        
        with st.form("address_form"):
            # Name fields
            st.markdown("**Contact Information**")
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", placeholder="Enter first name")
            
            with col2:
                last_name = st.text_input("Last Name", placeholder="Enter last name")
            
            # Address fields
            st.markdown("**Address Information**")
            street_address = st.text_input(
                "Street Address",
                placeholder="123 Main Street, Apt 4B"
            )
            
            col3, col4, col5 = st.columns([3, 1, 2])
            
            with col3:
                city = st.text_input("City", placeholder="Enter city")
            
            with col4:
                state = st.text_input("State", placeholder="CA", max_chars=2)
            
            with col5:
                zip_code = st.text_input("ZIP Code", placeholder="12345")
            
            submitted = st.form_submit_button("🔍 Validate Address", type="primary")
            
            if submitted:
                # Check required fields
                if not all([first_name, last_name, street_address, city, state, zip_code]):
                    st.error("❌ All fields are required")
                else:
                    with st.spinner("Validating with USPS..."):
                        result = self.service.validate_complete_record(
                            first_name, last_name, street_address, city, state, zip_code
                        )
                        self._display_address_result(result)
    
    def render_monitoring(self):
        """Render enhanced monitoring dashboard"""
        st.markdown("## 📊 System Monitoring & Analytics")
        
        # Service status
        status = self.service.get_service_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name_status = "✅ Enhanced AI Ready" if status['name_validation_available'] else "❌ Unavailable"
            st.metric("Name Service", name_status)
        
        with col2:
            addr_status = "✅ USPS Connected" if status['address_validation_available'] else "❌ Unavailable"
            st.metric("Address Service", addr_status)
        
        with col3:
            st.metric("API Version", f"v{status['api_version']}")
        
        # Processing stats
        stats = st.session_state.processing_stats
        
        st.markdown("### Processing Statistics")
        col4, col5, col6, col7 = st.columns(4)
        
        with col4:
            st.metric("Total Processed", stats['total_processed'])
        
        with col5:
            st.metric("Successful", stats['successful'])
        
        with col6:
            st.metric("Failed", stats['failed'])
        
        with col7:
            success_rate = (stats['successful'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Feature showcase
        st.markdown("### AI Enhancement Features")
        col8, col9 = st.columns(2)
        
        with col8:
            st.markdown("""
            **🤖 Intelligent Detection:**
            - Smart gender prediction from names
            - Organization vs Individual classification
            - Nickname standardization (Bill → William)
            - Prefix/suffix extraction
            """)
        
        with col9:
            st.markdown("""
            **📊 Enhanced Accuracy:**
            - Multi-factor confidence scoring
            - Dictionary-based validation
            - Pattern recognition algorithms
            - Real-time error detection
            """)
        
        # Recent logs
        recent_logs = logger.get_recent_logs(10)
        
        if recent_logs:
            st.markdown("### Recent Activity")
            
            log_data = []
            for log in recent_logs:
                log_data.append({
                    'Time': log['timestamp'].strftime('%H:%M:%S'),
                    'Level': log['level'],
                    'Category': log['category'],
                    'Message': log['message'][:100] + ('...' if len(log['message']) > 100 else '')
                })
            
            logs_df = pd.DataFrame(log_data)
            st.dataframe(logs_df, use_container_width=True)
        
        # Clear stats button
        if st.button("🗑️ Clear Statistics"):
            st.session_state.processing_stats = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0
            }
            st.session_state.validation_results = []
            logger.clear()
            st.success("Statistics cleared!")
            st.rerun()
    
    def _display_enhanced_name_result(self, result: dict):
        """Display enhanced name validation result"""
        
        # Determine confidence level for styling
        confidence = float(result.get('confidenceScore', '0'))
        if confidence >= 90:
            confidence_class = "confidence-high"
            confidence_icon = "🟢"
        elif confidence >= 70:
            confidence_class = "confidence-medium"
            confidence_icon = "🟡"
        else:
            confidence_class = "confidence-low"
            confidence_icon = "🔴"
        
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        
        # Header with confidence
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### {result['fullName']}")
        
        with col2:
            st.markdown(f"**Party Type:** {result['partyTypeCd']}")
        
        with col3:
            st.markdown(f"**Status:** {result['parseStatus']}")
        
        # Confidence and error message
        st.markdown(f"""
        {confidence_icon} **Confidence:** <span class="{confidence_class}">{confidence}%</span>  
        **Message:** {result['errorMessage']}
        """, unsafe_allow_html=True)
        
        # Parsed components (if individual)
        if result['partyTypeCd'] == 'I' and result['parseInd'] == 'Y':
            st.markdown("#### 🔍 Parsed Components")
            
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            
            with comp_col1:
                if result['prefix']:
                    st.write(f"**Prefix:** {result['prefix']}")
                st.write(f"**First Name:** {result['firstName'] or 'N/A'}")
                if result['firstNameStd'] and result['firstNameStd'] != result['firstName']:
                    st.write(f"**Standardized:** {result['firstNameStd']}")
            
            with comp_col2:
                if result['middleName']:
                    st.write(f"**Middle Name:** {result['middleName']}")
                st.write(f"**Last Name:** {result['lastName'] or 'N/A'}")
            
            with comp_col3:
                if result['suffix']:
                    st.write(f"**Suffix:** {result['suffix']}")
                
                # Gender prediction
                gender_display = result['outGenderCd'] if result['outGenderCd'] else 'Unknown'
                if result['outGenderCd'] and not result['inGenderCd']:
                    gender_display += " (AI Predicted)"
                st.write(f"**Gender:** {gender_display}")
        
        # Literal (uppercase) versions
        if result['parseInd'] == 'Y':
            with st.expander("📝 Literal Formats"):
                literal_parts = []
                if result['prefixLt']:
                    literal_parts.append(f"Prefix: {result['prefixLt']}")
                if result['firstNameLt']:
                    literal_parts.append(f"First: {result['firstNameLt']}")
                if result['middleNameLt']:
                    literal_parts.append(f"Middle: {result['middleNameLt']}")
                if result['lastNameLt']:
                    literal_parts.append(f"Last: {result['lastNameLt']}")
                if result['suffixLt']:
                    literal_parts.append(f"Suffix: {result['suffixLt']}")
                
                if literal_parts:
                    st.write(" | ".join(literal_parts))
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update stats
        st.session_state.processing_stats['total_processed'] += 1
        if result['parseStatus'] in ['Parsed', 'Not Parsed']:
            st.session_state.processing_stats['successful'] += 1
        else:
            st.session_state.processing_stats['failed'] += 1
    
    def _display_address_result(self, result: dict):
        """Display address validation result (unchanged)"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_status = "✅ Valid" if result['overall_valid'] else "❌ Invalid"
            st.metric("Overall Status", overall_status)
        
        with col2:
            name_result = result.get('name_result', {})
            name_status = "✅ Valid" if name_result.get('parseStatus') in ['Parsed', 'Not Parsed'] else "❌ Invalid"
            st.metric("Name", name_status)
        
        with col3:
            address_result = result.get('address_result', {})
            address_status = "✅ Deliverable" if address_result.get('deliverable', False) else "❌ Not Deliverable"
            st.metric("Address", address_status)
        
        with col4:
            confidence = result.get('overall_confidence', 0)
            st.metric("Confidence", f"{confidence:.1%}")
        
        # USPS results
        if address_result.get('success') and address_result.get('standardized'):
            st.markdown("### 📮 USPS Standardized Address")
            standardized = address_result['standardized']
            
            st.success(f"""
            **Standardized Address:**
            {standardized['street_address']}
            {standardized['city']}, {standardized['state']} {standardized['zip_code']}
            """)
            
            # Metadata
            if address_result.get('metadata'):
                with st.expander("📊 Address Details"):
                    metadata = address_result['metadata']
                    
                    st.write(f"**Business:** {'Yes' if metadata.get('business') else 'No'}")
                    st.write(f"**Vacant:** {'Yes' if metadata.get('vacant') else 'No'}")
                    st.write(f"**DPV Confirmation:** {metadata.get('dpv_confirmation', 'N/A')}")
        
        # Update stats
        st.session_state.processing_stats['total_processed'] += 1
        if result['overall_valid']:
            st.session_state.processing_stats['successful'] += 1
        else:
            st.session_state.processing_stats['failed'] += 1
    
    def run(self):
        """Main application entry point"""
        # Configure page
        st.set_page_config(
            page_title="Name & Address Validator v2.0",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply styling
        self.apply_styling()
        
        # Render header
        self.render_header()
        
        # Main tabs
        name_tab, address_tab, monitoring_tab = st.tabs([
            "🤖 Enhanced Name Validation",
            "🏠 Address Validation", 
            "📊 Monitoring & Analytics"
        ])
        
        with name_tab:
            self.render_name_validation()
        
        with address_tab:
            self.render_address_validation()
        
        with monitoring_tab:
            self.render_monitoring()


def main():
    """Application entry point"""
    try:
        app = ValidatorApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logger.error(f"Application error: {e}", "APP")


if __name__ == "__main__":
    main()