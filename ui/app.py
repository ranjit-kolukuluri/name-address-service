# ui/app.py
"""
Complete Professional Streamlit UI for name and address validation with enhanced functionality
"""

import streamlit as st
import pandas as pd
import json
import time
import re
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
    """Complete Professional Streamlit application with all validation functionality"""
    
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
        
        if 'address_stats' not in st.session_state:
            st.session_state.address_stats = {
                'total_validated': 0,
                'successful': 0,
                'failed': 0
            }
    
    def apply_styling(self):
        """Apply enhanced professional CSS styling"""
        st.markdown("""
        <style>
        /* Main application styling */
        .main {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        /* Professional header */
        .header {
            background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='3'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.3;
        }
        
        .title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            letter-spacing: -0.025em;
            position: relative;
            z-index: 1;
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }
        
        /* Professional status indicators */
        .status-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            display: inline-flex;
            align-items: center;
            margin: 0.5rem;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .status-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        .status-warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            display: inline-flex;
            align-items: center;
            margin: 0.5rem;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .status-warning:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        /* Professional method badges */
        .method-deterministic {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 700;
            display: inline-block;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .method-hybrid {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 700;
            display: inline-block;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .method-ai {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 700;
            display: inline-block;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Professional result cards */
        .result-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
        }
        
        .result-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* Professional confidence indicators */
        .confidence-high {
            color: #059669;
            font-weight: 700;
            font-size: 1.1rem;
        }
        
        .confidence-medium {
            color: #d97706;
            font-weight: 700;
            font-size: 1.1rem;
        }
        
        .confidence-low {
            color: #dc2626;
            font-weight: 700;
            font-size: 1.1rem;
        }
        
        /* Professional dictionary status */
        .dict-status {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border: 1px solid #0ea5e9;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Professional form styling */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .stSelectbox > div > div > div {
            border-radius: 8px;
            border: 2px solid #e2e8f0;
        }
        
        /* Professional button styling */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        /* Professional metrics */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        [data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        /* Professional tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        /* Professional file uploader */
        .stFileUploader > div {
            border-radius: 12px;
            border: 2px dashed #cbd5e1;
            transition: all 0.3s ease;
        }
        
        .stFileUploader > div:hover {
            border-color: #3b82f6;
            background: #f8fafc;
        }
        
        /* Professional dataframe styling */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Professional expander */
        .streamlit-expanderHeader {
            border-radius: 8px;
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            font-weight: 600;
        }
        
        /* Professional progress bar */
        .stProgress > div > div > div {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border-radius: 4px;
        }
        
        /* Professional alerts */
        .stAlert {
            border-radius: 12px;
            border: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render enhanced professional application header"""
        name_available = self.service.is_name_validation_available()
        address_available = self.service.is_address_validation_available()
        dict_status = self.service.dictionary_status
        
        st.markdown('''
        <div class="header">
            <div class="title">🚀 Name & Address Validator</div>
            <div class="subtitle">Enterprise-Grade Validation • Dictionary Intelligence • USPS Integration</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Professional status indicators
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            status_html = ""
            if name_available:
                if dict_status:
                    status_html += '<span class="status-success">🎯 Enhanced Name Validation Active</span>'
                else:
                    status_html += '<span class="status-warning">⚡ AI-Only Name Validation</span>'
            
            if address_available:
                status_html += '<span class="status-success">📮 USPS Address Validation Ready</span>'
            else:
                status_html += '<span class="status-warning">📮 USPS API Configuration Required</span>'
            
            st.markdown(f'<div style="text-align: center;">{status_html}</div>', unsafe_allow_html=True)
        
        # Professional dictionary status panel
        if dict_status:
            stats = self.service._get_dictionary_statistics()
            st.markdown(f'''
            <div class="dict-status">
                <div style="display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 2rem;">
                    <div><strong>📚 Dictionary Engine:</strong> <span style="color: #059669;">Active</span></div>
                    <div><strong>👥 Names:</strong> {stats.get('first_names_count', 0):,}</div>
                    <div><strong>👤 Surnames:</strong> {stats.get('surnames_count', 0):,}</div>
                    <div><strong>⚧ Gender Maps:</strong> {stats.get('gender_mappings_count', 0):,}</div>
                    <div><strong>🏢 Business Terms:</strong> {stats.get('business_words_count', 0):,}</div>
                </div>
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
        """Render professional address validation interface with pre-validation toggle"""
        st.markdown("## 🏠 Address Validation")
        
        # Professional status bar
        self._render_address_status_bar()
        
        # Create tabs for different validation types
        single_tab, csv_tab = st.tabs(["📍 Single Address", "📊 Batch CSV Processing"])
        
        # =========================================================================
        # TAB 1: SINGLE ADDRESS VALIDATION
        # =========================================================================
        
        with single_tab:
            self._render_single_address_validation()
        
        # =========================================================================
        # TAB 2: PROFESSIONAL BATCH CSV PROCESSING
        # =========================================================================
        
        with csv_tab:
            self._render_professional_csv_processing()
    
    def _render_address_status_bar(self):
        """Render professional status bar"""
        if not self.service.is_address_validation_available():
            st.error("🚫 **USPS API Not Configured** - Address validation unavailable", icon="⚠️")
            with st.expander("📖 Setup Instructions"):
                st.code("""
# Set environment variables:
export USPS_CLIENT_ID="your_client_id"
export USPS_CLIENT_SECRET="your_client_secret"

# Or create .env file:
echo 'USPS_CLIENT_ID=your_id' > .env
echo 'USPS_CLIENT_SECRET=your_secret' >> .env
                """)
            return False
        else:
            st.success("✅ **USPS API Connected** - Ready for address validation", icon="🔗")
            return True
    
    def _render_single_address_validation(self):
        """Render professional single address validation"""
        st.markdown("### 🎯 Single Address Validation")
        
        # Professional form layout
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); 
                        padding: 2rem; border-radius: 12px; margin: 1rem 0;">
            """, unsafe_allow_html=True)
            
            with st.form("single_address_form", clear_on_submit=False):
                # Address input grid
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    line1 = st.text_input(
                        "🏠 Street Address*", 
                        placeholder="123 Main Street",
                        help="Primary street address (required)"
                    )
                    line2 = st.text_input(
                        "🏢 Unit/Apartment", 
                        placeholder="Apt 4B, Suite 200, etc.",
                        help="Secondary address line (optional)"
                    )
                
                with col2:
                    city = st.text_input(
                        "🏙️ City*", 
                        placeholder="New York",
                        help="City name (required)"
                    )
                    
                    col2a, col2b = st.columns(2)
                    with col2a:
                        state_cd = st.text_input(
                            "🗺️ State*", 
                            placeholder="NY",
                            max_chars=2,
                            help="2-letter state code"
                        )
                    with col2b:
                        zip_cd = st.text_input(
                            "📮 ZIP Code*", 
                            placeholder="10001",
                            help="ZIP or ZIP+4 code"
                        )
                
                # Professional submit button
                col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
                with col_submit2:
                    submitted = st.form_submit_button(
                        "🔍 Validate with USPS", 
                        type="primary",
                        use_container_width=True
                    )
                
                if submitted:
                    self._process_single_address(line1, line2, city, state_cd, zip_cd)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_professional_csv_processing(self):
        """Render professional CSV processing with pre-validation toggle"""
        st.markdown("### 📊 Professional Batch Processing")
        
        # Professional info panel
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                        padding: 1.5rem; border-radius: 12px; border-left: 4px solid #3b82f6;">
                <h4 style="margin: 0; color: #1e40af;">🚀 Intelligent Processing Pipeline</h4>
                <p style="margin: 0.5rem 0 0 0; color: #1e40af;">
                    ✅ Auto-detects any CSV format  •  ✅ Pre-validates data quality  •  ✅ USPS batch verification
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # File upload section
        st.markdown("#### 📁 Upload CSV Files")
        uploaded_files = st.file_uploader(
            "Select multiple CSV files with address data",
            type=['csv'],
            accept_multiple_files=True,
            key="professional_csv_upload",
            help="Supports any CSV format - columns will be auto-detected"
        )
        
        if uploaded_files:
            st.success(f"📄 **{len(uploaded_files)} file(s) uploaded** - Ready for processing")
            
            # Process files for pre-validation
            with st.spinner("🔍 Analyzing uploaded files..."):
                file_analysis = self._analyze_uploaded_files(uploaded_files)
            
            if file_analysis['valid_files']:
                # Pre-validation toggle section
                st.markdown("#### 🔍 Data Quality Pre-Analysis")
                
                # Toggle buttons for viewing valid/invalid addresses
                col_toggle1, col_toggle2, col_toggle3 = st.columns([1, 1, 2])
                
                with col_toggle1:
                    show_valid = st.toggle("✅ Show Valid Addresses", value=True, key="show_valid")
                
                with col_toggle2:
                    show_invalid = st.toggle("❌ Show Invalid Addresses", value=True, key="show_invalid")
                
                with col_toggle3:
                    st.metric(
                        "📊 Data Quality Score", 
                        f"{file_analysis['quality_score']:.1%}",
                        help="Percentage of addresses that pass pre-validation"
                    )
                
                # Display pre-validation results
                self._display_pre_validation_results(file_analysis, show_valid, show_invalid)
                
                # Professional processing button
                if file_analysis['processable_count'] > 0:
                    st.markdown("#### 🚀 USPS Validation")
                    
                    col_process1, col_process2, col_process3 = st.columns([1, 2, 1])
                    with col_process2:
                        if st.button(
                            f"🔥 Process {file_analysis['processable_count']} Addresses with USPS",
                            type="primary",
                            use_container_width=True,
                            key="professional_process"
                        ):
                            self._process_csv_with_usps(file_analysis)
                else:
                    st.warning("⚠️ No valid addresses found for USPS processing")
            
            else:
                st.error("❌ No valid CSV files found for processing")
    
    def _analyze_uploaded_files(self, uploaded_files):
        """Analyze uploaded files and perform pre-validation"""
        analysis = {
            'valid_files': [],
            'total_records': 0,
            'valid_addresses': [],
            'invalid_addresses': [],
            'processable_count': 0,
            'quality_score': 0.0,
            'file_details': []
        }
        
        for file in uploaded_files:
            try:
                file.seek(0)
                df = pd.read_csv(file)
                
                if df.empty:
                    continue
                
                # Auto-detect address columns
                standardized_addresses = self.service.address_validator.standardize_csv_to_address_format(df)
                
                if not standardized_addresses:
                    analysis['file_details'].append({
                        'filename': file.name,
                        'status': 'failed',
                        'reason': 'No address columns detected'
                    })
                    continue
                
                # Pre-validate each address
                file_valid = []
                file_invalid = []
                
                for i, addr in enumerate(standardized_addresses):
                    validation_result = self._pre_validate_address(addr, i + 1, file.name)
                    
                    if validation_result['is_valid']:
                        file_valid.append(validation_result)
                    else:
                        file_invalid.append(validation_result)
                
                analysis['valid_addresses'].extend(file_valid)
                analysis['invalid_addresses'].extend(file_invalid)
                analysis['total_records'] += len(standardized_addresses)
                analysis['processable_count'] += len(file_valid)
                
                analysis['file_details'].append({
                    'filename': file.name,
                    'status': 'analyzed',
                    'total_rows': len(df),
                    'detected_addresses': len(standardized_addresses),
                    'valid_addresses': len(file_valid),
                    'invalid_addresses': len(file_invalid),
                    'quality_score': len(file_valid) / len(standardized_addresses) if standardized_addresses else 0
                })
                
                analysis['valid_files'].append(file.name)
                
            except Exception as e:
                analysis['file_details'].append({
                    'filename': file.name,
                    'status': 'error',
                    'reason': str(e)
                })
        
        # Calculate overall quality score
        if analysis['total_records'] > 0:
            analysis['quality_score'] = analysis['processable_count'] / analysis['total_records']
        
        return analysis
    
    def _pre_validate_address(self, address_data, row_num, filename):
        """Pre-validate address before USPS processing"""
        result = {
            'row_number': row_num,
            'source_file': filename,
            'is_valid': True,
            'issues': [],
            'line1': address_data.get('line1', ''),
            'line2': address_data.get('line2', ''),
            'city': address_data.get('city', ''),
            'state': address_data.get('stateCd', ''),
            'zip': address_data.get('zipCd', ''),
            'complete_address': '',
            'validation_level': 'pre_check'
        }
        
        # Check required fields
        if not result['line1'] or not result['line1'].strip():
            result['is_valid'] = False
            result['issues'].append("Missing street address")
        
        if not result['city'] or not result['city'].strip():
            result['is_valid'] = False
            result['issues'].append("Missing city")
        
        if not result['state'] or not result['state'].strip():
            result['is_valid'] = False
            result['issues'].append("Missing state")
        elif len(result['state']) != 2:
            result['is_valid'] = False
            result['issues'].append("Invalid state format (must be 2 letters)")
        
        if not result['zip'] or not result['zip'].strip():
            result['is_valid'] = False
            result['issues'].append("Missing ZIP code")
        elif not re.match(r'^\d{5}(-\d{4})?$', result['zip'].strip()):
            result['is_valid'] = False
            result['issues'].append("Invalid ZIP format")
        
        # Create complete address string
        address_parts = [result['line1']]
        if result['line2']:
            address_parts.append(result['line2'])
        address_parts.append(f"{result['city']}, {result['state']} {result['zip']}")
        result['complete_address'] = ' | '.join(address_parts)
        
        return result
    
    def _display_pre_validation_results(self, analysis, show_valid, show_invalid):
        """Display pre-validation results with professional styling"""
        
        # Summary metrics
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        
        with col_metric1:
            st.metric("📄 Total Files", len(analysis['valid_files']))
        
        with col_metric2:
            st.metric("📊 Total Records", analysis['total_records'])
        
        with col_metric3:
            st.metric("✅ Valid Addresses", analysis['processable_count'])
        
        with col_metric4:
            st.metric("❌ Invalid Addresses", len(analysis['invalid_addresses']))
        
        # File-by-file breakdown
        with st.expander("📋 File Analysis Breakdown"):
            for detail in analysis['file_details']:
                if detail['status'] == 'analyzed':
                    st.write(
                        f"📄 **{detail['filename']}**: "
                        f"{detail['valid_addresses']}/{detail['detected_addresses']} valid "
                        f"({detail['quality_score']:.1%} quality)"
                    )
                else:
                    st.write(f"❌ **{detail['filename']}**: {detail.get('reason', 'Failed')}")
        
        # Toggle-based display
        if show_valid and analysis['valid_addresses']:
            st.markdown("### ✅ Valid Addresses (Ready for USPS)")
            valid_df = pd.DataFrame(analysis['valid_addresses'])
            
            # Professional styling for valid addresses
            st.markdown("""
            <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #10b981;">
            """, unsafe_allow_html=True)
            
            st.dataframe(
                valid_df[['source_file', 'row_number', 'complete_address']],
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if show_invalid and analysis['invalid_addresses']:
            st.markdown("### ❌ Invalid Addresses (Need Review)")
            invalid_df = pd.DataFrame(analysis['invalid_addresses'])
            
            # Professional styling for invalid addresses
            st.markdown("""
            <div style="background: #fef2f2; padding: 1rem; border-radius: 8px; border-left: 4px solid #ef4444;">
            """, unsafe_allow_html=True)
            
            # Add issues column for display
            invalid_display = invalid_df.copy()
            invalid_display['issues_text'] = invalid_display['issues'].apply(lambda x: '; '.join(x))
            
            st.dataframe(
                invalid_display[['source_file', 'row_number', 'complete_address', 'issues_text']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'issues_text': st.column_config.TextColumn('Issues', width='medium')
                }
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _process_csv_with_usps(self, analysis):
        """Process valid addresses with USPS API"""
        
        # Professional progress tracking
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_container = st.container()
        
        try:
            status_text.info("🚀 **Initializing USPS validation pipeline...**")
            progress_bar.progress(10)
            
            # Process valid addresses
            all_results = []
            successful = 0
            failed = 0
            
            total_valid = len(analysis['valid_addresses'])
            
            for i, valid_addr in enumerate(analysis['valid_addresses']):
                status_text.info(f"🔄 **Processing {i+1}/{total_valid}**: {valid_addr['source_file']}")
                progress_bar.progress(10 + int(80 * (i+1) / total_valid))
                
                # Convert to USPS format and validate
                address_record = {
                    'guid': f"{valid_addr['source_file']}_{valid_addr['row_number']}",
                    'line1': valid_addr['line1'],
                    'line2': valid_addr['line2'] or None,
                    'city': valid_addr['city'],
                    'stateCd': valid_addr['state'],
                    'zipCd': valid_addr['zip'],
                    'countryCd': 'US'
                }
                
                try:
                    usps_result = self.service.validate_single_address(address_record)
                    
                    # Enhance result with source tracking
                    enhanced_result = {
                        'source_file': valid_addr['source_file'],
                        'row_number': valid_addr['row_number'],
                        'input_address': valid_addr['complete_address'],
                        'usps_valid': usps_result.get('mailabilityScore') == '1',
                        'standardized_address': f"{usps_result.get('deliveryAddressLine1', '')} | {usps_result.get('city', '')}, {usps_result.get('stateCd', '')} {usps_result.get('zipCdComplete', '')}",
                        'county': usps_result.get('countyName', ''),
                        'carrier_route': usps_result.get('carrierRoute', ''),
                        'result_percentage': usps_result.get('ResultPercentage', '0'),
                        'error_message': usps_result.get('errorMsg', ''),
                        'full_usps_result': usps_result
                    }
                    
                    all_results.append(enhanced_result)
                    
                    if enhanced_result['usps_valid']:
                        successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    # Handle individual address errors
                    error_result = {
                        'source_file': valid_addr['source_file'],
                        'row_number': valid_addr['row_number'],
                        'input_address': valid_addr['complete_address'],
                        'usps_valid': False,
                        'error_message': str(e),
                        'standardized_address': 'Processing Error'
                    }
                    all_results.append(error_result)
                    failed += 1
            
            progress_bar.progress(100)
            status_text.success("✅ **USPS validation completed!**")
            
            # Professional results display
            self._display_professional_results(all_results, successful, failed, total_valid)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ **Processing failed**: {str(e)}")
    
    def _display_professional_results(self, results, successful, failed, total):
        """Display professional USPS validation results"""
        
        st.markdown("## 🎉 USPS Validation Results")
        
        # Professional metrics display
        col_result1, col_result2, col_result3, col_result4 = st.columns(4)
        
        with col_result1:
            st.metric("📊 Total Processed", total)
        
        with col_result2:
            st.metric("✅ USPS Valid", successful, delta=f"{successful/total:.1%}" if total > 0 else "0%")
        
        with col_result3:
            st.metric("❌ USPS Invalid", failed, delta=f"-{failed/total:.1%}" if total > 0 else "0%")
        
        with col_result4:
            st.metric("🎯 Success Rate", f"{successful/total:.1%}" if total > 0 else "0%")
        
        # Results table with professional formatting
        if results:
            results_df = pd.DataFrame(results)
            
            # Create display columns
            display_df = results_df[[
                'source_file', 'row_number', 'input_address', 
                'usps_valid', 'standardized_address', 'county', 'error_message'
            ]].copy()
            
            st.markdown("### 📊 Detailed Results")
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'usps_valid': st.column_config.CheckboxColumn('USPS Valid'),
                    'source_file': st.column_config.TextColumn('File', width='small'),
                    'row_number': st.column_config.NumberColumn('Row', width='small'),
                    'input_address': st.column_config.TextColumn('Input Address', width='large'),
                    'standardized_address': st.column_config.TextColumn('USPS Standardized', width='large'),
                    'county': st.column_config.TextColumn('County', width='medium'),
                    'error_message': st.column_config.TextColumn('Notes', width='medium')
                }
            )
            
            # Professional download options
            st.markdown("### 📥 Download Results")
            col_download1, col_download2, col_download3 = st.columns(3)
            
            with col_download1:
                full_csv = results_df.to_csv(index=False)
                st.download_button(
                    "📄 Download All Results",
                    full_csv,
                    f"usps_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col_download2:
                valid_results = results_df[results_df['usps_valid'] == True]
                if not valid_results.empty:
                    valid_csv = valid_results.to_csv(index=False)
                    st.download_button(
                        "✅ Download Valid Only",
                        valid_csv,
                        f"valid_addresses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with col_download3:
                invalid_results = results_df[results_df['usps_valid'] == False]
                if not invalid_results.empty:
                    invalid_csv = invalid_results.to_csv(index=False)
                    st.download_button(
                        "❌ Download Invalid Only",
                        invalid_csv,
                        f"invalid_addresses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
    
    def _process_single_address(self, line1, line2, city, state_cd, zip_cd):
        """Process single address validation"""
        if not all([line1, city, state_cd, zip_cd]):
            st.error("❌ Please fill in all required fields (marked with *)")
            return
        
        with st.spinner("🔄 Validating with USPS..."):
            address_record = {
                'guid': '1',
                'line1': line1,
                'line2': line2 if line2 else None,
                'city': city,
                'stateCd': state_cd.upper(),
                'zipCd': zip_cd,
                'countryCd': 'US'
            }
            
            result = self.service.validate_single_address(address_record)
            self._display_single_address_result(result)
    
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
            addr_status = "✅ USPS Ready" if status['address_validation_available'] else "❌ Unavailable"
            st.metric("Address Service", addr_status)
        
        with col3:
            dict_status = "✅ Loaded" if status['dictionary_status'] else "❌ Not Available"
            st.metric("Dictionaries", dict_status)
        
        with col4:
            st.metric("API Version", f"v{status['api_version']}")
        
        # Enhanced processing stats
        name_stats = st.session_state.processing_stats
        address_stats = self._get_address_stats()
        
        # Name validation stats
        st.markdown("### Name Validation Statistics")
        col5, col6, col7, col8, col9 = st.columns(5)
        
        with col5:
            st.metric("Names Processed", name_stats['total_processed'])
        
        with col6:
            st.metric("Successful", name_stats['successful'])
        
        with col7:
            st.metric("Dictionary", name_stats['deterministic'])
        
        with col8:
            st.metric("Hybrid", name_stats['hybrid'])
        
        with col9:
            st.metric("AI Fallback", name_stats['ai_fallback'])
        
        # Address validation stats
        st.markdown("### Address Validation Statistics")
        col10, col11, col12 = st.columns(3)
        
        with col10:
            st.metric("Addresses Validated", address_stats['total_validated'])
        
        with col11:
            st.metric("Valid/Deliverable", address_stats['successful'])
        
        with col12:
            st.metric("Failed/Invalid", address_stats['failed'])
        
        # Dictionary information
        if status['dictionary_status'] and 'dictionary_statistics' in status:
            st.markdown("### Dictionary Information")
            dict_stats = status['dictionary_statistics']
            
            col13, col14, col15 = st.columns(3)
            
            with col13:
                st.metric("First Names", f"{dict_stats.get('first_names_count', 0):,}")
                st.metric("Surnames", f"{dict_stats.get('surnames_count', 0):,}")
            
            with col14:
                st.metric("Gender Mappings", f"{dict_stats.get('gender_mappings_count', 0):,}")
                st.metric("Nickname Mappings", f"{dict_stats.get('nickname_mappings_count', 0):,}")
            
            with col15:
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
            st.session_state.address_stats = {
                'total_validated': 0,
                'successful': 0,
                'failed': 0
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
    
    def _display_single_address_result(self, result: dict):
        """Display single address validation result"""
        
        is_valid = result.get('errorMsg') is None and result.get('mailabilityScore') == '1'
        
        if is_valid:
            st.success("✅ Address is valid and deliverable!")
            
            # Display validated address
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📮 Input Address:**")
                st.write(f"{result.get('inLine1', '')}")
                if result.get('inLine2'):
                    st.write(f"{result.get('inLine2', '')}")
                st.write(f"{result.get('inLine6', '')}, {result.get('inLine7', '')} {result.get('inLine8', '')}")
            
            with col2:
                st.markdown("**✅ USPS Standardized:**")
                st.write(f"{result.get('deliveryAddressLine1', '')}")
                if result.get('deliveryAddressLine2'):
                    st.write(f"{result.get('deliveryAddressLine2', '')}")
                st.write(f"{result.get('city', '')}, {result.get('stateCd', '')} {result.get('zipCdComplete', '')}")
            
            # Additional details
            with st.expander("📊 Additional Details"):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    if result.get('countyName'):
                        st.write(f"**County:** {result['countyName']}")
                    if result.get('carrierRoute'):
                        st.write(f"**Carrier Route:** {result['carrierRoute']}")
                    if result.get('congressionalDistrict'):
                        st.write(f"**Congressional District:** {result['congressionalDistrict']}")
                
                with detail_col2:
                    if result.get('zipCd4'):
                        st.write(f"**ZIP+4:** {result['zipCd4']}")
                    is_residential = result.get('residentialDeliveryIndicator') == 'Y'
                    st.write(f"**Address Type:** {'Residential' if is_residential else 'Business'}")
                    st.write(f"**Result Percentage:** {result.get('ResultPercentage', '0')}%")
        
        else:
            # Address validation failed
            st.error("❌ Address validation failed")
            
            if result.get('errorMsg'):
                st.write(f"**Error:** {result['errorMsg']}")
            
            # Show what was attempted
            with st.expander("📋 Input Details"):
                st.write(f"**Address:** {result.get('inLine1', '')}")
                if result.get('inLine2'):
                    st.write(f"**Line 2:** {result.get('inLine2', '')}")
                st.write(f"**City:** {result.get('inLine6', '')}")
                st.write(f"**State:** {result.get('inLine7', '')}")
                st.write(f"**ZIP:** {result.get('inLine8', '')}")
                
                st.info("💡 **Tips for better results:**\n- Check spelling of street name and city\n- Ensure state code is correct (2 letters)\n- Verify ZIP code is valid for the area")
        
        # Update session stats
        self._update_address_stats(is_valid)
    
    def _update_address_stats(self, is_valid: bool):
        """Update address validation statistics"""
        if 'address_stats' not in st.session_state:
            st.session_state.address_stats = {
                'total_validated': 0,
                'successful': 0,
                'failed': 0
            }
        
        st.session_state.address_stats['total_validated'] += 1
        if is_valid:
            st.session_state.address_stats['successful'] += 1
        else:
            st.session_state.address_stats['failed'] += 1
    
    def _get_address_stats(self):
        """Get address validation statistics"""
        if 'address_stats' not in st.session_state:
            return {'total_validated': 0, 'successful': 0, 'failed': 0}
        return st.session_state.address_stats
    
    def run(self):
        """Main application entry point"""
        # Configure page
        st.set_page_config(
            page_title="Enhanced Name & Address Validator",
            page_icon="🚀",
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
            "🏠 Professional Address Validation", 
            "📊 System Analytics"
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