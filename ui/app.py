# ui/app.py
"""
Streamlit UI for name and address validation
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
    """Main Streamlit application"""
    
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
        """Apply custom CSS styling"""
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
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render application header"""
        name_available = self.service.is_name_validation_available()
        address_available = self.service.is_address_validation_available()
        
        st.markdown('''
        <div class="header">
            <div class="title">Name & Address Validator</div>
            <div class="subtitle">Professional validation platform with USPS integration</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            status_html = ""
            if name_available:
                status_html += '<span class="status-success">✓ Name Validation Ready</span>'
            else:
                status_html += '<span class="status-warning">⚠ Name Service Unavailable</span>'
            
            if address_available:
                status_html += '<span class="status-success">✓ USPS API Connected</span>'
            else:
                status_html += '<span class="status-warning">⚠ USPS API Not Configured</span>'
            
            st.markdown(f'<div style="text-align: center;">{status_html}</div>', unsafe_allow_html=True)
    
    def render_name_validation(self):
        """Render name validation interface"""
        st.markdown("## 👤 Name Validation")
        
        # Single name validation
        with st.expander("Single Name Validation", expanded=True):
            with st.form("single_name_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    first_name = st.text_input("First Name", placeholder="Enter first name")
                
                with col2:
                    last_name = st.text_input("Last Name", placeholder="Enter last name")
                
                submitted = st.form_submit_button("🔍 Validate Name", type="primary")
                
                if submitted and first_name and last_name:
                    with st.spinner("Validating..."):
                        result = self.service.validate_single_name(first_name, last_name)
                        self._display_name_result(result)
        
        # API Testing
        with st.expander("API Testing"):
            st.markdown("### Test API Payload")
            
            default_payload = {
                "records": [
                    {
                        "uniqueid": "001",
                        "name": "John Michael Smith",
                        "gender": "",
                        "party_type": "I",
                        "parseInd": "Y"
                    },
                    {
                        "uniqueid": "002",
                        "name": "TechCorp Solutions LLC",
                        "gender": "",
                        "party_type": "O",
                        "parseInd": "N"
                    }
                ]
            }
            
            json_input = st.text_area(
                "JSON Payload:",
                value=json.dumps(default_payload, indent=2),
                height=250
            )
            
            if st.button("🚀 Test API", type="primary"):
                try:
                    payload = json.loads(json_input)
                    records = payload.get('records', [])
                    
                    with st.spinner("Processing API request..."):
                        result = self.service.process_api_records(records)
                        st.success("✅ API request processed successfully")
                        st.json(result)
                        
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # CSV Upload
        with st.expander("CSV Upload"):
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.success(f"✅ File uploaded: {len(df)} rows")
                    
                    if st.button("🔄 Process CSV", type="primary"):
                        with st.spinner("Processing CSV..."):
                            result = self.service.process_csv_names(df)
                            
                            if result['success']:
                                st.success(f"✅ Processed {result['processed_records']} names")
                                st.write(f"Success rate: {result['success_rate']:.1%}")
                                
                                if result['results']:
                                    results_df = pd.DataFrame(result['results'])
                                    st.dataframe(results_df)
                            else:
                                st.error(f"❌ {result['error']}")
                                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
    
    def render_address_validation(self):
        """Render address validation interface"""
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
        """Render monitoring dashboard"""
        st.markdown("## 📊 System Monitoring")
        
        # Service status
        status = self.service.get_service_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name_status = "✅ Available" if status['name_validation_available'] else "❌ Unavailable"
            st.metric("Name Service", name_status)
        
        with col2:
            addr_status = "✅ Available" if status['address_validation_available'] else "❌ Unavailable"
            st.metric("Address Service", addr_status)
        
        with col3:
            st.metric("API Version", status['api_version'])
        
        # Processing stats
        stats = st.session_state.processing_stats
        
        st.markdown("### Processing Statistics")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.metric("Total Processed", stats['total_processed'])
        
        with col5:
            st.metric("Successful", stats['successful'])
        
        with col6:
            st.metric("Failed", stats['failed'])
        
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
    
    def _display_name_result(self, result: dict):
        """Display name validation result"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Valid" if result['valid'] else "❌ Invalid"
            st.metric("Status", status)
        
        with col2:
            confidence = result.get('confidence', 0)
            st.metric("Confidence", f"{confidence:.1%}")
        
        with col3:
            processing_time = result.get('processing_time_ms', 0)
            st.metric("Processing Time", f"{processing_time}ms")
        
        # Normalized name
        if 'normalized' in result:
            normalized = result['normalized']
            st.success(f"**Normalized:** {normalized['first_name']} {normalized['last_name']}")
        
        # Errors and warnings
        if result.get('errors'):
            st.error("**Errors:**")
            for error in result['errors']:
                st.write(f"- {error}")
        
        if result.get('warnings'):
            st.warning("**Warnings:**")
            for warning in result['warnings']:
                st.write(f"- {warning}")
        
        # Update stats
        st.session_state.processing_stats['total_processed'] += 1
        if result['valid']:
            st.session_state.processing_stats['successful'] += 1
        else:
            st.session_state.processing_stats['failed'] += 1
    
    def _display_address_result(self, result: dict):
        """Display address validation result"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_status = "✅ Valid" if result['overall_valid'] else "❌ Invalid"
            st.metric("Overall Status", overall_status)
        
        with col2:
            name_result = result.get('name_result', {})
            name_status = "✅ Valid" if name_result.get('valid', False) else "❌ Invalid"
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
            page_title="Name & Address Validator",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply styling
        self.apply_styling()
        
        # Render header
        self.render_header()
        
        # Main tabs
        name_tab, address_tab, monitoring_tab = st.tabs([
            "👤 Name Validation",
            "🏠 Address Validation", 
            "📊 Monitoring"
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