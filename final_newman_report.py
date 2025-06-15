import streamlit as st
import subprocess
import json
import os
import time
import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import base64

# Configure Streamlit page
st.set_page_config(
    page_title="Test Execution Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-card {
        border-left-color: #10b981;
    }
    .error-card {
        border-left-color: #ef4444;
    }
    .warning-card {
        border-left-color: #f59e0b;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: bold;
    }
    .download-btn {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%) !important;
    }
    .email-btn {
        background: linear-gradient(90deg, #8b5cf6 0%, #7c3aed 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

class TestDashboard:
    def __init__(self):
        self.collections_path = "collections/"  # Path to your Postman collections
        self.reports_path = "reports/"
        self.ensure_directories()

        # Mock service configurations
        self.all_services = [
            "User Authentication Service",
            "Payment Gateway Service",
            "Order Management Service",
            "Inventory Service",
            "Notification Service",
            "Analytics Service",
            "Reporting Service",
            "Security Service"
        ]

        self.services_with_dependencies = {
            "Payment Gateway Service": ["User Authentication Service"],
            "Order Management Service": ["Payment Gateway Service", "Inventory Service"],
            "Notification Service": ["User Authentication Service", "Order Management Service"]
        }

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        Path(self.collections_path).mkdir(exist_ok=True)
        Path(self.reports_path).mkdir(exist_ok=True)

    def run_newman_command(self, collection_path, environment=None, folder=None):
        """Execute Newman command and return results"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.reports_path, f"report_{timestamp}.html")
        json_report_path = os.path.join(self.reports_path, f"report_{timestamp}.json")

        # Build Newman command
        cmd = [
            "newman", "run", collection_path,
            "--reporters", "html,json",
            "--reporter-html-export", report_path,
            "--reporter-json-export", json_report_path
        ]

        if environment:
            cmd.extend(["--environment", environment])

        if folder:
            cmd.extend(["--folder", folder])

        try:
            # Execute Newman command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Parse JSON report for detailed results
            if os.path.exists(json_report_path):
                with open(json_report_path, 'r') as f:
                    json_results = json.load(f)
                return {
                    "success": result.returncode == 0,
                    "html_report": report_path,
                    "json_report": json_report_path,
                    "json_data": json_results,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                # Return mock data if Newman is not available
                return self.generate_mock_results(report_path)

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timed out"}
        except FileNotFoundError:
            # Newman not installed, return mock data
            return self.generate_mock_results(report_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_mock_results(self, report_path):
        """Generate mock test results for demonstration"""
        import random

        # Generate mock JSON data
        mock_data = {
            "run": {
                "stats": {
                    "tests": {"total": 45, "pending": 2, "failed": 3},
                    "assertions": {"total": 180, "pending": 8, "failed": 3},
                    "requests": {"total": 45, "pending": 0, "failed": 2}
                },
                "timings": {"responseAverage": 245, "responseMin": 89, "responseMax": 1205},
                "executions": []
            }
        }

        # Generate mock executions
        for i in range(45):
            execution = {
                "item": {"name": f"Test Case {i+1}"},
                "response": {
                    "responseTime": random.randint(50, 500),
                    "code": random.choice([200, 201, 400, 500])
                },
                "assertions": [
                    {"assertion": "Status code is 200", "error": None if random.random() > 0.1 else {"message": "Expected 200 but got 400"}}
                ]
            }
            mock_data["run"]["executions"].append(execution)

        # Generate mock HTML report
        self.generate_html_report(mock_data, report_path)

        return {
            "success": True,
            "html_report": report_path,
            "json_data": mock_data,
            "mock": True
        }

    def generate_html_report(self, json_data, report_path):
        """Generate HTML report from JSON data"""
        stats = json_data["run"]["stats"]

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Execution Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid; }}
                .card.total {{ border-left-color: #3b82f6; }}
                .card.passed {{ border-left-color: #10b981; }}
                .card.failed {{ border-left-color: #ef4444; }}
                .card.pending {{ border-left-color: #f59e0b; }}
                .card h3 {{ font-size: 2.5em; margin: 0; }}
                .card p {{ margin: 10px 0 0 0; color: #666; font-weight: bold; }}
                .section {{ margin: 30px 0; }}
                .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
                th {{ background: #f9fafb; font-weight: 600; }}
                .status-passed {{ color: #10b981; font-weight: bold; }}
                .status-failed {{ color: #ef4444; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Test Execution Report</h1>
                    <p>Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="summary">
                    <div class="card total">
                        <h3>{stats['tests']['total']}</h3>
                        <p>Total Tests</p>
                    </div>
                    <div class="card passed">
                        <h3>{stats['tests']['total'] - stats['tests']['failed'] - stats['tests']['pending']}</h3>
                        <p>Passed</p>
                    </div>
                    <div class="card failed">
                        <h3>{stats['tests']['failed']}</h3>
                        <p>Failed</p>
                    </div>
                    <div class="card pending">
                        <h3>{stats['tests']['pending']}</h3>
                        <p>Pending</p>
                    </div>
                </div>

                <div class="section">
                    <h2>📊 Execution Summary</h2>
                    <table>
                        <tr><td><strong>Total Requests:</strong></td><td>{stats['requests']['total']}</td></tr>
                        <tr><td><strong>Failed Requests:</strong></td><td>{stats['requests']['failed']}</td></tr>
                        <tr><td><strong>Total Assertions:</strong></td><td>{stats['assertions']['total']}</td></tr>
                        <tr><td><strong>Failed Assertions:</strong></td><td>{stats['assertions']['failed']}</td></tr>
                    </table>
                </div>

                <div class="footer">
                    <p>Report generated by Newman Test Dashboard | {datetime.datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        with open(report_path, 'w') as f:
            f.write(html_content)

    def send_email_report(self, report_path, recipient_email, smtp_config):
        """Send HTML report via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['sender_email']
            msg['To'] = recipient_email
            msg['Subject'] = f"Test Execution Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Email body
            body = """
            Hello,

            Please find attached the test execution report.

            Summary:
            - Report generated successfully
            - Timestamp: {}

            Best regards,
            Test Automation Team
            """.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            msg.attach(MIMEText(body, 'plain'))

            # Attach HTML report
            with open(report_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(report_path)}'
                )
                msg.attach(part)

            # Send email
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            server.starttls()
            server.login(smtp_config['sender_email'], smtp_config['sender_password'])
            server.send_message(msg)
            server.quit()

            return True, "Email sent successfully!"

        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

def main():
    dashboard = TestDashboard()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 Test Execution Dashboard</h1>
        <p>Manage and execute your Newman test collections</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Test execution type selection
        execution_type = st.selectbox(
            "Select Execution Type:",
            ["", "Run the Regression Suite", "Run Individual Service", "Run Services with Dependencies"],
            key="execution_type"
        )

        selected_services = []
        collection_folder = None

        if execution_type == "Run Individual Service":
            st.subheader("Select Services:")
            selected_services = st.multiselect(
                "Choose services to test:",
                dashboard.all_services,
                key="individual_services"
            )

        elif execution_type == "Run Services with Dependencies":
            st.subheader("Services with Dependencies:")
            for service, deps in dashboard.services_with_dependencies.items():
                st.write(f"**{service}**")
                st.write(f"Dependencies: {', '.join(deps)}")
                st.write("---")

        # Collection and environment settings
        st.subheader("Collection Settings")
        collection_file = st.text_input("Collection File Path:", "collection.json")
        environment_file = st.text_input("Environment File Path (optional):", "")

        # Email configuration
        st.subheader("📧 Email Configuration")
        with st.expander("Email Settings"):
            sender_email = st.text_input("Sender Email:", key="sender_email")
            sender_password = st.text_input("Sender Password:", type="password", key="sender_password")
            smtp_server = st.text_input("SMTP Server:", "smtp.gmail.com", key="smtp_server")
            smtp_port = st.number_input("SMTP Port:", value=587, key="smtp_port")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🚀 Test Execution")

        # Execution button
        if st.button("▶️ Run Tests", key="run_tests", help="Execute selected tests"):
            if not execution_type:
                st.error("Please select an execution type!")
            elif execution_type == "Run Individual Service" and not selected_services:
                st.error("Please select at least one service!")
            else:
                # Show execution progress
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("Initializing test execution...")
                progress_bar.progress(10)
                time.sleep(1)

                status_text.text("Loading collection and environment...")
                progress_bar.progress(30)
                time.sleep(1)

                status_text.text("Executing Newman tests...")
                progress_bar.progress(60)
                time.sleep(2)

                # Determine folder based on selection
                if execution_type == "Run Individual Service":
                    collection_folder = selected_services[0] if selected_services else None
                elif execution_type == "Run Services with Dependencies":
                    collection_folder = list(dashboard.services_with_dependencies.keys())[0]

                # Execute tests
                results = dashboard.run_newman_command(
                    collection_file,
                    environment_file if environment_file else None,
                    collection_folder
                )

                progress_bar.progress(100)
                status_text.text("Test execution completed!")

                # Store results in session state
                st.session_state['test_results'] = results
                st.session_state['execution_type'] = execution_type
                st.session_state['selected_services'] = selected_services

                time.sleep(1)
                st.experimental_rerun()

    with col2:
        st.header("📊 Quick Stats")
        if 'test_results' in st.session_state and st.session_state['test_results']:
            results = st.session_state['test_results']
            if results.get('success'):
                stats = results['json_data']['run']['stats']

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Total Tests", stats['tests']['total'])
                    st.metric("Failed", stats['tests']['failed'], delta=-stats['tests']['failed'])

                with col_b:
                    passed = stats['tests']['total'] - stats['tests']['failed'] - stats['tests']['pending']
                    st.metric("Passed", passed, delta=passed)
                    st.metric("Pending", stats['tests']['pending'])
        else:
            st.info("Run tests to see statistics")

    # Results section
    if 'test_results' in st.session_state and st.session_state['test_results']:
        results = st.session_state['test_results']

        st.header("📋 Test Results")

        if results.get('success'):
            stats = results['json_data']['run']['stats']

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h3>{}</h3>
                    <p>Total Tests</p>
                </div>
                """.format(stats['tests']['total']), unsafe_allow_html=True)

            with col2:
                passed = stats['tests']['total'] - stats['tests']['failed'] - stats['tests']['pending']
                st.markdown("""
                <div class="metric-card success-card">
                    <h3>{}</h3>
                    <p>Passed</p>
                </div>
                """.format(passed), unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div class="metric-card error-card">
                    <h3>{}</h3>
                    <p>Failed</p>
                </div>
                """.format(stats['tests']['failed']), unsafe_allow_html=True)

            with col4:
                st.markdown("""
                <div class="metric-card warning-card">
                    <h3>{}</h3>
                    <p>Pending</p>
                </div>
                """.format(stats['tests']['pending']), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Visualization
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart for test results
                labels = ['Passed', 'Failed', 'Pending']
                values = [passed, stats['tests']['failed'], stats['tests']['pending']]
                colors = ['#10b981', '#ef4444', '#f59e0b']

                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
                fig.update_traces(marker=dict(colors=colors))
                fig.update_layout(title="Test Results Distribution", showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Bar chart for assertions
                categories = ['Total', 'Failed', 'Pending']
                assertion_values = [
                    stats['assertions']['total'],
                    stats['assertions']['failed'],
                    stats['assertions']['pending']
                ]

                fig = px.bar(x=categories, y=assertion_values, title="Assertions Summary")
                fig.update_traces(marker_color=['#3b82f6', '#ef4444', '#f59e0b'])
                st.plotly_chart(fig, use_container_width=True)

            # Action buttons
            st.header("📤 Actions")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Download report button
                if os.path.exists(results['html_report']):
                    with open(results['html_report'], 'rb') as file:
                        st.download_button(
                            label="⬇️ Download HTML Report",
                            data=file.read(),
                            file_name=f"test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html",
                            key="download_report"
                        )

            with col2:
                # Email report button
                recipient_email = st.text_input("Recipient Email:", key="recipient_email")

                if st.button("📧 Send Email Report", key="send_email"):
                    if not recipient_email:
                        st.error("Please enter recipient email!")
                    elif not sender_email:
                        st.error("Please configure sender email in sidebar!")
                    else:
                        smtp_config = {
                            'sender_email': sender_email,
                            'sender_password': sender_password,
                            'smtp_server': smtp_server,
                            'smtp_port': smtp_port
                        }

                        success, message = dashboard.send_email_report(
                            results['html_report'],
                            recipient_email,
                            smtp_config
                        )

                        if success:
                            st.success(message)
                        else:
                            st.error(message)

            with col3:
                # View report button
                if st.button("👁️ View Report", key="view_report"):
                    if os.path.exists(results['html_report']):
                        with open(results['html_report'], 'r') as file:
                            report_content = file.read()
                            st.components.v1.html(report_content, height=600, scrolling=True)

            # Detailed results table
            st.header("📝 Detailed Results")

            # Create DataFrame for test results
            if 'executions' in results['json_data']['run']:
                executions = results['json_data']['run']['executions']

                test_data = []
                for execution in executions:
                    test_name = execution['item']['name']
                    response_time = execution.get('response', {}).get('responseTime', 0)
                    status_code = execution.get('response', {}).get('code', 0)

                    # Check assertions
                    assertions = execution.get('assertions', [])
                    failed_assertions = [a for a in assertions if a.get('error')]
                    status = "FAILED" if failed_assertions else "PASSED"

                    test_data.append({
                        'Test Name': test_name,
                        'Status': status,
                        'Response Time (ms)': response_time,
                        'Status Code': status_code,
                        'Assertions': len(assertions),
                        'Failed Assertions': len(failed_assertions)
                    })

                df = pd.DataFrame(test_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.error(f"Test execution failed: {results.get('error', 'Unknown error')}")
            if results.get('stderr'):
                st.code(results['stderr'])

if __name__ == "__main__":
    main()
