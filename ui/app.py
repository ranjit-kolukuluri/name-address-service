# ui/app.py
"""
Updated Streamlit UI for name and address validation with enhanced address processing
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
    """Enhanced Streamlit application with dictionary integration and batch address processing"""
    
    def __init__(self):
        self.service = ValidationService()
        
        # Initialize session state
        if 'validation_results' not in st.session_state:
            st.session_state.validation_results = []
        
        if 'processing_stats' not in st.session_state:
            st.session_state.processing_stats = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'deterministic': 0,
                'hybrid': 0,
                'ai_fallback': 0
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
        
        .method-deterministic {
            background: #10b981;
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .method-hybrid {
            background: #f59e0b;
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .method-ai {
            background: #8b5cf6;
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .result-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .address-card {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
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
        
        .dict-status {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render enhanced application header"""
        name_available = self.service.is_name_validation_available()
        address_available = self.service.is_address_validation_available()
        dict_status = self.service.dictionary_status
        
        st.markdown('''
        <div class="header">
            <div class="title">Name & Address Validator v2.0</div>
            <div class="subtitle">Enhanced with Dictionary Integration + AI Fallback + Batch Address Processing</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Status indicators with dictionary info
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            status_html = ""
            if name_available:
                if dict_status:
                    status_html += '<span class="status-success">✓ Dictionary + AI Validation Ready</span>'
                else:
                    status_html += '<span class="status-warning">⚠ AI-Only Mode (No Dictionaries)</span>'
            else:
                status_html += '<span class="status-warning">⚠ Name Service Unavailable</span>'
            
            if address_available:
                status_html += '<span class="status-success">✓ USPS Batch Processing Ready</span>'
            else:
                status_html += '<span class="status-warning">⚠ USPS API Not Configured</span>'
            
            st.markdown(f'<div style="text-align: center;">{status_html}</div>', unsafe_allow_html=True)
        
        # Dictionary status info
        if dict_status:
            stats = self.service._get_dictionary_statistics()
            st.markdown(f'''
            <div class="dict-status">
                <strong>📚 Dictionary Status:</strong> Loaded<br>
                <strong>First Names:</strong> {stats.get('first_names_count', 0):,} | 
                <strong>Surnames:</strong> {stats.get('surnames_count', 0):,} | 
                <strong>Gender Mappings:</strong> {stats.get('gender_mappings_count', 0):,}
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="dict-status">
                <strong>📚 Dictionary Status:</strong> Not Available<br>
                <strong>Validation Mode:</strong> AI Pattern Matching Only<br>
                <strong>Note:</strong> Place dictionary CSV files in <code>/Users/t93uyz8/Documents/name_dictionaries</code> for enhanced accuracy
            </div>
            ''', unsafe_allow_html=True)
    
    def render_name_validation(self):
        """Render enhanced name validation interface"""
        st.markdown("## 👤 Enhanced Name Validation")
        
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
                    with st.spinner("Processing with enhanced validation..."):
                        # Create name record
                        name_record = {
                            'uniqueID': '1',
                            'fullName': full_name,
                            'genderCd': gender_cd,
                            'partyTypeCd': party_type_cd,
                            'parseInd': parse_ind
                        }
                        
                        # Validate using enhanced format
                        result = self.service.validate_names({'names': [name_record]})
                        
                        if result['names']:
                            self._display_enhanced_name_result(result['names'][0])
                            
                            # Show processing stats if available
                            if 'processing_stats' in result:
                                stats = result['processing_stats']
                                with st.expander("📊 Processing Details"):
                                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                                    with col_stats1:
                                        st.metric("Processing Time", f"{stats['processing_time_ms']}ms")
                                    with col_stats2:
                                        st.metric("Dictionary Available", "Yes" if stats['dictionary_available'] else "No")
                                    with col_stats3:
                                        method_used = result['names'][0].get('validationMethod', 'unknown')
                                        st.metric("Method Used", method_used.replace('_', ' ').title())
        
        # Enhanced API Testing
        with st.expander("Enhanced API Testing"):
            st.markdown("### Test Enhanced API Format")
            
            # Get example payload
            default_payload = self.service.get_example_payload()
            
            json_input = st.text_area(
                "JSON Payload (Enhanced Format):",
                value=json.dumps(default_payload, indent=2),
                height=300
            )
            
            if st.button("🚀 Test Enhanced API", type="primary"):
                try:
                    payload = json.loads(json_input)
                    
                    with st.spinner("Processing with dictionary lookup + AI fallback..."):
                        result = self.service.validate_names(payload)
                        
                        st.success("✅ API request processed successfully")
                        
                        # Display results with method information
                        for name_result in result['names']:
                            self._display_enhanced_name_result(name_result)
                        
                        # Show processing statistics
                        if 'processing_stats' in result:
                            stats = result['processing_stats']
                            with st.expander("📈 Processing Statistics"):
                                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                                
                                with col_stat1:
                                    st.metric("Total Processed", stats['total_processed'])
                                
                                with col_stat2:
                                    methods = stats.get('validation_methods', {})
                                    st.metric("Dictionary", methods.get('deterministic', 0))
                                
                                with col_stat3:
                                    st.metric("Hybrid", methods.get('hybrid', 0))
                                
                                with col_stat4:
                                    st.metric("AI Fallback", methods.get('ai_fallback', 0))
                        
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
                    
                    if st.button("🔄 Process with Enhanced Validation", type="primary"):
                        with st.spinner("Processing CSV with dictionary lookup + AI fallback..."):
                            result = self.service.process_csv_names(df)
                            
                            if result['success']:
                                st.success(f"✅ Processed {result['processed_records']} names")
                                st.write(f"Success rate: {result['success_rate']:.1%}")
                                
                                # Show method breakdown
                                if 'validation_method_breakdown' in result:
                                    method_breakdown = result['validation_method_breakdown']
                                    col_method1, col_method2, col_method3 = st.columns(3)
                                    
                                    with col_method1:
                                        st.metric("Dictionary Validated", method_breakdown.get('deterministic', 0))
                                    
                                    with col_method2:
                                        st.metric("Hybrid Validation", method_breakdown.get('hybrid', 0))
                                    
                                    with col_method3:
                                        st.metric("AI Fallback", method_breakdown.get('ai_fallback', 0))
                                
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
        """Render enhanced address validation interface (no name fields)"""
        st.markdown("## 🏠 Enhanced Address Validation")
        
        # Check if service is available
        if not self.service.is_address_validation_available():
            st.warning("⚠️ USPS API not configured. Please set USPS_CLIENT_ID and USPS_CLIENT_SECRET.")
            st.info("📝 Note: Address validation features are available but require USPS API credentials.")
        
        # Single address validation
        with st.expander("Single Address Validation", expanded=True):
            with st.form("address_form"):
                st.markdown("**Address Information**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    line1 = st.text_input("Address Line 1", placeholder="123 Main Street")
                    city = st.text_input("City", placeholder="Enter city")
                
                with col2:
                    line2 = st.text_input("Address Line 2 (Optional)", placeholder="Apt 4B, Suite 200")
                    col2a, col2b = st.columns(2)
                    
                    with col2a:
                        state_cd = st.text_input("State", placeholder="CA", max_chars=2)
                    
                    with col2b:
                        zip_cd = st.text_input("ZIP Code", placeholder="12345")
                
                submitted = st.form_submit_button("🔍 Validate Address", type="primary")
                
                if submitted:
                    # Check required fields
                    if not all([line1, city, state_cd, zip_cd]):
                        st.error("❌ Address Line 1, City, State, and ZIP Code are required")
                    else:
                        with st.spinner("Validating with USPS..."):
                            # Create address record
                            address_record = {
                                'guid': '1',
                                'line1': line1,
                                'line2': line2 if line2 else None,
                                'line3': None,
                                'line4': None,
                                'line5': None,
                                'city': city,
                                'stateCd': state_cd.upper(),
                                'zipCd': zip_cd,
                                'countryCd': 'US',
                                'verificationInd': 'Y',
                                'onlyOneAddrInd': 'N'
                            }
                            
                            # Validate using enhanced format
                            result = self.service.validate_addresses({'addresses': [address_record]})
                            
                            if result['addresses']:
                                self._display_enhanced_address_result(result['addresses'][0])
                                
                                # Show processing stats
                                if 'processing_stats' in result:
                                    stats = result['processing_stats']
                                    with st.expander("📊 Processing Details"):
                                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                                        with col_stats1:
                                            st.metric("Processing Time", f"{stats['processing_time_ms']}ms")
                                        with col_stats2:
                                            st.metric("USPS Configured", "Yes" if stats['usps_configured'] else "No")
                                        with col_stats3:
                                            st.metric("Success Rate", f"{stats.get('success_rate', 0):.1%}")
        
        # Enhanced Address API Testing
        with st.expander("Enhanced Address API Testing"):
            st.markdown("### Test Enhanced Address API Format")
            
            # Get example address payload
            default_payload = self.service.get_example_address_payload()
            
            json_input = st.text_area(
                "JSON Payload (Enhanced Address Format):",
                value=json.dumps(default_payload, indent=2),
                height=300
            )
            
            if st.button("🚀 Test Enhanced Address API", type="primary"):
                try:
                    payload = json.loads(json_input)
                    
                    with st.spinner("Processing with USPS batch validation..."):
                        result = self.service.validate_addresses(payload)
                        
                        st.success("✅ Address API request processed successfully")
                        
                        # Display results
                        for address_result in result['addresses']:
                            self._display_enhanced_address_result(address_result)
                        
                        # Show processing statistics
                        if 'processing_stats' in result:
                            stats = result['processing_stats']
                            with st.expander("📈 Processing Statistics"):
                                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                                
                                with col_stat1:
                                    st.metric("Total Processed", stats['total_processed'])
                                
                                with col_stat2:
                                    st.metric("Successful", stats['successful'])
                                
                                with col_stat3:
                                    st.metric("Failed", stats['failed'])
                                
                                with col_stat4:
                                    st.metric("Success Rate", f"{stats.get('success_rate', 0):.1%}")
                        
                        # Show raw JSON for developers
                        with st.expander("Raw JSON Response"):
                            st.json(result)
                        
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Enhanced CSV Upload for Addresses
        with st.expander("CSV Address Upload with Auto-Standardization"):
            st.markdown("### Upload CSV with Address Data")
            st.info("📋 **Supported formats**: The system automatically detects and standardizes various CSV formats including columns like 'address', 'street', 'city', 'state', 'zip', etc.")
            
            uploaded_file = st.file_uploader("Choose address CSV file", type=['csv'], key="address_csv")
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.success(f"✅ File uploaded: {len(df)} rows")
                    
                    # Show preview
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    # Show detected columns
                    st.write("**Detected Columns:**")
                    col_info = []
                    for col in df.columns:
                        col_info.append(f"• `{col}`")
                    st.write(" | ".join(col_info))
                    
                    if st.button("🔄 Process with Auto-Standardization & USPS Validation", type="primary", key="process_addresses"):
                        with st.spinner("Standardizing CSV format and validating with USPS..."):
                            result = self.service.process_csv_addresses(df)
                            
                            if result['success']:
                                st.success(f"✅ Processed {result['processed_records']} addresses")
                                st.write(f"Success rate: {result['success_rate']:.1%}")
                                
                                # Show processing stats
                                col_addr1, col_addr2, col_addr3 = st.columns(3)
                                
                                with col_addr1:
                                    st.metric("Total Addresses", result['total_records'])
                                
                                with col_addr2:
                                    st.metric("Valid Addresses", result['successful_validations'])
                                
                                with col_addr3:
                                    st.metric("USPS Configured", "Yes" if result['usps_configured'] else "No")
                                
                                if result['results']:
                                    # Create enhanced results DataFrame
                                    results_df = pd.DataFrame(result['results'])
                                    st.dataframe(results_df, use_container_width=True)
                                    
                                    # Download button
                                    csv = results_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Address Results",
                                        data=csv,
                                        file_name=f"validated_addresses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                            else:
                                st.error(f"❌ {result['error']}")
                                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
    
    def render_monitoring(self):
        """Render enhanced monitoring dashboard"""
        st.markdown("## 📊 System Monitoring & Analytics")
        
        # Service status
        status = self.service.get_service_status()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            name_status = "✅ Enhanced Ready" if status['name_validation_available'] else "❌ Unavailable"
            st.metric("Name Service", name_status)
        
        with col2:
            addr_status = "✅ USPS Batch Ready" if status['address_validation_available'] else "❌ Unavailable"
            st.metric("Address Service", addr_status)
        
        with col3:
            dict_status = "✅ Loaded" if status['dictionary_status'] else "❌ Not Available"
            st.metric("Dictionaries", dict_status)
        
        with col4:
            st.metric("API Version", f"v{status['api_version']}")
        
        # Enhanced processing stats
        stats = st.session_state.processing_stats
        
        st.markdown("### Processing Statistics")
        col5, col6, col7, col8, col9 = st.columns(5)
        
        with col5:
            st.metric("Total Processed", stats['total_processed'])
        
        with col6:
            st.metric("Successful", stats['successful'])
        
        with col7:
            st.metric("Dictionary", stats['deterministic'])
        
        with col8:
            st.metric("Hybrid", stats['hybrid'])
        
        with col9:
            st.metric("AI Fallback", stats['ai_fallback'])
        
        # Dictionary information
        if status['dictionary_status'] and 'dictionary_statistics' in status:
            st.markdown("### Dictionary Information")
            dict_stats = status['dictionary_statistics']
            
            col10, col11, col12 = st.columns(3)
            
            with col10:
                st.metric("First Names", f"{dict_stats.get('first_names_count', 0):,}")
                st.metric("Surnames", f"{dict_stats.get('surnames_count', 0):,}")
            
            with col11:
                st.metric("Gender Mappings", f"{dict_stats.get('gender_mappings_count', 0):,}")
                st.metric("Nickname Mappings", f"{dict_stats.get('nickname_mappings_count', 0):,}")
            
            with col12:
                st.metric("Business Words", f"{dict_stats.get('business_words_count', 0):,}")
                st.metric("Company Suffixes", f"{dict_stats.get('company_suffixes_count', 0):,}")
        
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
                'failed': 0,
                'deterministic': 0,
                'hybrid': 0,
                'ai_fallback': 0
            }
            st.session_state.validation_results = []
            logger.clear()
            st.success("Statistics cleared!")
            st.rerun()
    
    def _display_enhanced_name_result(self, result: dict):
        """Display enhanced name validation result with method information"""
        
        # Determine confidence level for styling
        confidence = float(result.get('confidenceScore', '0'))
        validation_method = result.get('validationMethod', 'unknown')
        
        if confidence >= 90:
            confidence_class = "confidence-high"
            confidence_icon = "🟢"
        elif confidence >= 70:
            confidence_class = "confidence-medium"
            confidence_icon = "🟡"
        else:
            confidence_class = "confidence-low"
            confidence_icon = "🔴"
        
        # Method styling
        if 'deterministic' in validation_method:
            method_class = "method-deterministic"
            method_label = "Dictionary"
        elif 'hybrid' in validation_method:
            method_class = "method-hybrid"
            method_label = "Hybrid"
        else:
            method_class = "method-ai"
            method_label = "AI Fallback"
        
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        
        # Header with confidence and method
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### {result['fullName']}")
        
        with col2:
            st.markdown(f"**Party Type:** {result['partyTypeCd']}")
        
        with col3:
            st.markdown(f"**Status:** {result['parseStatus']}")
        
        # Confidence and method information
        st.markdown(f"""
        {confidence_icon} **Confidence:** <span class="{confidence_class}">{confidence:.2f}%</span>  
        **Method:** <span class="{method_class}">{method_label}</span>  
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
                    gender_display += " (Predicted)"
                st.write(f"**Gender:** {gender_display}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update stats
        st.session_state.processing_stats['total_processed'] += 1
        if result['parseStatus'] in ['Parsed', 'Not Parsed']:
            st.session_state.processing_stats['successful'] += 1
        else:
            st.session_state.processing_stats['failed'] += 1
        
        # Update method stats
        if 'deterministic' in validation_method:
            st.session_state.processing_stats['deterministic'] += 1
        elif 'hybrid' in validation_method:
            st.session_state.processing_stats['hybrid'] += 1
        else:
            st.session_state.processing_stats['ai_fallback'] += 1
    
    def _display_enhanced_address_result(self, result: dict):
        """Display enhanced address validation result"""
        
        # Determine validation status
        is_valid = result.get('errorMsg') is None and result.get('mailabilityScore') == '1'
        match_code = result.get('matchCode', 'Unknown')
        result_percentage = result.get('ResultPercentage', '0.00')
        
        if is_valid:
            status_icon = "🟢"
            status_class = "confidence-high"
            status_text = "Valid & Deliverable"
        elif result.get('errorMsg'):
            status_icon = "🔴"
            status_class = "confidence-low"
            status_text = "Error"
        else:
            status_icon = "🟡"
            status_class = "confidence-medium"
            status_text = "Invalid/Undeliverable"
        
        st.markdown('<div class="address-card">', unsafe_allow_html=True)
        
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            input_addr = f"{result.get('inLine1', '')} {result.get('inLine2', '')}".strip()
            st.markdown(f"### {input_addr}")
        
        with col2:
            st.markdown(f"**Match Code:** {match_code}")
        
        with col3:
            st.markdown(f"**GUID:** {result.get('guid', 'N/A')}")
        
        # Status and confidence
        st.markdown(f"""
        {status_icon} **Status:** <span class="{status_class}">{status_text}</span>  
        **Result Percentage:** {result_percentage}%  
        **Mailability Score:** {result.get('mailabilityScore', '0')}
        """, unsafe_allow_html=True)
        
        # Error message if present
        if result.get('errorMsg'):
            st.error(f"❌ Error: {result['errorMsg']}")
        
        # Address details if validated successfully
        if is_valid:
            st.markdown("#### 📮 Validated Address")
            
            addr_col1, addr_col2 = st.columns(2)
            
            with addr_col1:
                st.write("**Input Address:**")
                st.write(f"{result.get('inLine1', '')}")
                if result.get('inLine2'):
                    st.write(f"{result.get('inLine2', '')}")
                st.write(f"{result.get('inLine6', '')}, {result.get('inLine7', '')} {result.get('inLine8', '')}")
            
            with addr_col2:
                st.write("**Standardized Address:**")
                st.write(f"{result.get('deliveryAddressLine1', '')}")
                if result.get('deliveryAddressLine2'):
                    st.write(f"{result.get('deliveryAddressLine2', '')}")
                st.write(f"{result.get('city', '')}, {result.get('stateCd', '')} {result.get('zipCdComplete', '')}")
            
            # Additional details
            with st.expander("📊 Additional Address Details"):
                detail_col1, detail_col2, detail_col3 = st.columns(3)
                
                with detail_col1:
                    if result.get('countyName'):
                        st.write(f"**County:** {result['countyName']}")
                    if result.get('carrierRoute'):
                        st.write(f"**Carrier Route:** {result['carrierRoute']}")
                
                with detail_col2:
                    if result.get('congressionalDistrict'):
                        st.write(f"**Congressional District:** {result['congressionalDistrict']}")
                    if result.get('residentialDeliveryIndicator'):
                        is_residential = result['residentialDeliveryIndicator'] == 'Y'
                        st.write(f"**Type:** {'Residential' if is_residential else 'Business'}")
                
                with detail_col3:
                    if result.get('zipCd4'):
                        st.write(f"**ZIP+4:** {result['zipCd4']}")
                    if result.get('deliveryPointCd'):
                        st.write(f"**Delivery Point:** {result['deliveryPointCd']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update stats
        st.session_state.processing_stats['total_processed'] += 1
        if is_valid:
            st.session_state.processing_stats['successful'] += 1
        else:
            st.session_state.processing_stats['failed'] += 1
    
    def run(self):
        """Main application entry point"""
        # Configure page
        st.set_page_config(
            page_title="Enhanced Name & Address Validator v2.0",
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
            "🏠 Enhanced Address Validation", 
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