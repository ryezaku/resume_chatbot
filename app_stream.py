import streamlit as st
import os
import requests
import json
import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables for local development
load_dotenv()

# Page config with wider layout
st.set_page_config(
    page_title="Mohammad Haziq - AI Engineer",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    body {
        color: #333333;
    }
    .main-header {
        font-size: 2.8rem;
        color: #3949AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        background: linear-gradient(90deg, #304FFE, #5E35B1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 10px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.8rem;
        color: #512DA8;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .profile-container {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        color: #333333;
    }
    .stButton button {
        background-color: #3949AB;
        color: white;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #5E35B1;
    }
    /* Ensure all text is dark and easily readable */
    p, span, label, div {
        color: #333333;
    }
    /* Style for chat messages */
    .user-message {
        background-color: #f0f2f6; 
        padding: 10px; 
        border-radius: 10px; 
        margin-bottom: 10px;
        color: #333333;
    }
    .bot-message {
        background-color: #e8eaf6; 
        padding: 10px; 
        border-radius: 10px; 
        margin-bottom: 10px;
        color: #333333;
    }
    /* Header tag with special styling */
    .specialty-tag {
        display: inline-block;
        background-color: #3949AB;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    /* Section headers */
    .section-title {
        color: #5E35B1;
        font-weight: 600;
        font-size: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #e8eaf6;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Arli AI API key from Streamlit secrets or environment variables
if "arli" in st.secrets:
    arli_api_key = st.secrets["arli"]["api_key"]
else:
    arli_api_key = os.getenv("ARLIAI_API_KEY")

# Google Sheets configuration - using only secrets
google_creds_dict = None
if "google_sheets" in st.secrets:
    google_creds_dict = st.secrets["google_sheets"]

# Define default model 
DEFAULT_MODEL = "Mistral-Nemo-12B-SauerkrautLM"

# Profile photo path
PROFILE_PHOTO = "images/profile_photo.png"

# Session state initialization
if "user_info" not in st.session_state:
    st.session_state.user_info = None
    
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_id" not in st.session_state:
    # Generate a unique session ID for tracking conversations
    st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Function to connect to Google Sheets
def connect_to_google_sheets():
    try:
        # Define the scope
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Use credentials from secrets
        if "google_sheets" in st.secrets:
            # Create credentials dictionary from Streamlit secrets
            credentials_dict = st.secrets["google_sheets"]
            # Silently log for debugging purposes but don't display in UI
            #st.sidebar.info(f"Found Google Sheets credentials in secrets")
            
            # Debug: Print the keys that are in the credentials dict (without exposing sensitive data)
            required_keys = ["type", "project_id", "private_key_id", "private_key", "client_email"]
            missing_keys = [key for key in required_keys if key not in credentials_dict]
            if missing_keys:
                # Only show an error if there's an issue
                st.sidebar.error(f"Missing required Google credentials keys: {', '.join(missing_keys)}")
            
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        else:
            # No credentials available - show minimal error
            st.sidebar.error("Google Sheets not configured. Chat history won't be saved.")
            return None
        
        # Authorize the client
        client = gspread.authorize(credentials)
        #st.sidebar.info("Successfully authorized with Google Sheets")
        
        # Get user's personal email from secrets
        personal_email = None
        folder_name = "Resume Chatbot Data"
        spreadsheet_name = "Resume_Chatbot_Data"
        
        if "google_sheets" in st.secrets and "personal_email" in st.secrets["google_sheets"]:
            personal_email = st.secrets["google_sheets"]["personal_email"]
        
        # Check if the spreadsheet already exists
        try:
            # Try to open the spreadsheet by name
            spreadsheet = client.open(spreadsheet_name)
            #st.sidebar.info(f"Found existing spreadsheet: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            # Create a new spreadsheet in a folder
            #st.sidebar.info(f"Creating new spreadsheet: {spreadsheet_name}")
            
            # Create a new spreadsheet in root first
            spreadsheet = client.create(spreadsheet_name)
            
            # Share with the service account
            if "google_sheets" in st.secrets and "client_email" in st.secrets["google_sheets"]:
                service_email = st.secrets["google_sheets"]["client_email"]
                spreadsheet.share(service_email, perm_type='user', role='writer')
            
            # Share with the user's personal email
            if personal_email:
                # Only show this info once when creating a new spreadsheet
                st.sidebar.info(f"New data spreadsheet created and shared with: {personal_email}")
                # Share with editor access to ensure they can move it to a folder
                spreadsheet.share(personal_email, perm_type='user', role='owner')
            else:
                st.sidebar.warning("No personal email found in secrets. Chat history may not be accessible.")
                # Simplify the manual share UI
                with st.sidebar.expander("Share spreadsheet"):
                    user_email = st.text_input("Your email address:")
                    if st.button("Share with me") and user_email:
                        try:
                            spreadsheet.share(user_email, perm_type='user', role='owner')
                            st.success(f"Spreadsheet shared with {user_email}")
                        except Exception as e:
                            st.error(f"Failed to share: {str(e)}")
        
        # Remove the spreadsheet link from the sidebar completely
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        
        # Check for and create worksheets if they don't exist
        try:
            recruiter_sheet = spreadsheet.worksheet("Recruiters")
        except gspread.WorksheetNotFound:
            recruiter_sheet = spreadsheet.add_worksheet(title="Recruiters", rows=1000, cols=20)
            # Add headers
            recruiter_sheet.append_row([
                "Session ID", "Timestamp", "Name", "Email", "Company", 
                "Position", "Reason", "Form Submitted At"
            ])
        
        try:
            chat_sheet = spreadsheet.worksheet("Chat History")
        except gspread.WorksheetNotFound:
            chat_sheet = spreadsheet.add_worksheet(title="Chat History", rows=1000, cols=20)
            # Add headers
            chat_sheet.append_row([
                "Session ID", "Timestamp", "Sender", "Message"
            ])
        
        #st.sidebar.success("Google Sheets connection successful")
        return {
            "spreadsheet": spreadsheet,
            "recruiter_sheet": recruiter_sheet,
            "chat_sheet": chat_sheet
        }
    except Exception as e:
        # Only show a concise error, not the full details
        st.sidebar.error(f"Unable to connect to Google Sheets: {str(e).split('.')[:1]}")
        return None

# Function to save recruiter info to Google Sheets
def save_recruiter_info(user_info):
    try:
        sheets = connect_to_google_sheets()
        if not sheets:
            return False
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare the row data
        row_data = [
            st.session_state.session_id,
            timestamp,
            user_info["name"],
            user_info["email"],
            user_info["company"],
            user_info["position"],
            user_info["reason"],
            timestamp
        ]
        
        # Append to the recruiter sheet
        sheets["recruiter_sheet"].append_row(row_data)
        return True
    except Exception as e:
        st.sidebar.error(f"Error saving recruiter info: {str(e)}")
        return False

# Function to save chat message to Google Sheets
def save_chat_message(sender, message):
    try:
        sheets = connect_to_google_sheets()
        if not sheets:
            return False
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare the row data
        row_data = [
            st.session_state.session_id,
            timestamp,
            sender,
            message
        ]
        
        # Append to the chat history sheet
        sheets["chat_sheet"].append_row(row_data)
        return True
    except Exception as e:
        st.sidebar.error(f"Error saving chat message: {str(e)}")
        return False

# Function to read CV data
def get_cv_text():
    with open("cv_data.txt", "r") as file:
        text = file.read()
    return text

# Function to get response from Arli AI
def get_arli_response(prompt, system_message=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {arli_api_key}"
    }
    
    # Create messages with system prompt containing CV information
    cv_text = get_cv_text()
    
    if system_message:
        system_content = system_message
    else:
        system_content = f"""You are a resume chatbot that answers questions about the following resume. 
        Respond as if you are the person described in this resume:
        
        {cv_text}
        
        Always be professional, honest, and provide relevant information from the resume.
        If asked about something not in the resume, you can politely mention that information is not available.
        """
    
    messages = [
        {"role": "system", "content": system_content},
    ]
    
    # Add chat history for context
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            messages.append({"role": "user", "content": message})
        else:
            messages.append({"role": "assistant", "content": message})
    
    # Add the current prompt
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    
    try:
        response = requests.post(
            "https://api.arliai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            return f"Error: {response.text}"
            
        response_json = response.json()
        return response_json["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# Function to display profile photo with fallback
def display_profile_photo(width=150):
    if os.path.exists(PROFILE_PHOTO):
        st.image(PROFILE_PHOTO, width=width)
    else:
        # Display a placeholder avatar if no profile photo exists
        st.markdown(
            f"""
            <div style="background-color: #3949AB; width: {width}px; height: {width}px; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: white; font-size: {width//3}px; font-weight: bold;">
                MH
            </div>
            """,
            unsafe_allow_html=True
        )

# Function to display specialty tags
def display_specialty_tags():
    specialties = ["AI Engineer", "Machine Learning", "Computer Vision", "LLMs", "MLOps"]
    tags_html = ""
    for specialty in specialties:
        tags_html += f'<span class="specialty-tag">{specialty}</span>'
    st.markdown(f'<div style="text-align: center; margin-bottom: 1.5rem;">{tags_html}</div>', unsafe_allow_html=True)

# User info form
def display_user_form():
    # Profile picture at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="profile-container">', unsafe_allow_html=True)
        display_profile_photo(width=200)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-header">Mohammad Haziq</h1>', unsafe_allow_html=True)
        display_specialty_tags()
        st.markdown('<p style="text-align: center; font-size: 1.2rem; margin-bottom: 2rem; color: #333333;">Please fill out this form to chat with my AI assistant.</p>', unsafe_allow_html=True)
    
    form_col1, form_col2, form_col3 = st.columns([1, 2, 1])
    with form_col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Contact Information</h3>', unsafe_allow_html=True)
        with st.form("user_info_form"):
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            company = st.text_input("Your Company/Organization")
            position = st.text_input("Your Position")
            
            reason = st.selectbox(
                "Reason for contact",
                [
                    "Job Opportunity",
                    "Project Collaboration",
                    "Networking",
                    "Information Request",
                    "Other"
                ]
            )
            
            if reason == "Other":
                other_reason = st.text_input("Please specify")
            else:
                other_reason = ""
            
            submitted = st.form_submit_button("Start Chatting")
            
            if submitted:
                user_info = {
                    "name": name,
                    "email": email,
                    "company": company,
                    "position": position,
                    "reason": other_reason if reason == "Other" else reason
                }
                
                # Validate form
                if not name or not email:
                    st.error("Please fill in your name and email to continue.")
                    return None
                
                # Save to Google Sheets
                save_success = save_recruiter_info(user_info)
                if not save_success:
                    st.warning("Your information was saved locally but couldn't be saved to Google Sheets.")
                
                return user_info
        st.markdown('</div>', unsafe_allow_html=True)
    
    return None

# Chat interface
def display_chat_interface():
    # Top section with profile picture and header
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="profile-container">', unsafe_allow_html=True)
        display_profile_photo(width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">Mohammad Haziq</h1>', unsafe_allow_html=True)
    display_specialty_tags()
    
    # Display user info in a sidebar card
    st.sidebar.markdown('<h2 class="sub-header">Your Information</h2>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="card">', unsafe_allow_html=True)
    st.sidebar.write(f"**Name:** {st.session_state.user_info['name']}")
    st.sidebar.write(f"**Email:** {st.session_state.user_info['email']}")
    st.sidebar.write(f"**Company:** {st.session_state.user_info['company']}")
    st.sidebar.write(f"**Position:** {st.session_state.user_info['position']}")
    st.sidebar.write(f"**Reason:** {st.session_state.user_info['reason']}")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Reset button
    if st.sidebar.button("Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Chat container
    st.markdown('<h2 class="section-title">Chat With My AI Assistant</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #333333;">Ask me anything about my skills, experience, projects or qualifications!</p>', unsafe_allow_html=True)
    
    chat_container = st.container()
    
    # Display chat history in a stylized way
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.markdown(
                    f"""
                    <div class="user-message">
                        <strong>You:</strong> {message}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="bot-message">
                        <strong>Mohammad:</strong> {message}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
    
    # Input for new messages
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area("Your question:", key="user_input", height=100, 
                                  placeholder="Example: Tell me about your experience with AI projects...")
        col1, col2, col3 = st.columns([3, 1, 3])
        with col2:
            submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            with st.spinner("Thinking..."):
                # Save user message to Google Sheets
                save_chat_message("User", user_input)
                
                # Get response from Arli AI
                response = get_arli_response(user_input)
                
                # Save bot response to Google Sheets
                save_chat_message("Bot", response)
                
                # Update chat history
                st.session_state.chat_history.append(user_input)
                st.session_state.chat_history.append(response)
            
            st.rerun()

# Main application
def main():
    # Check for API key
    if not arli_api_key:
        st.error("Arli AI API key not found. Please set the ARLIAI_API_KEY environment variable or configure it in Streamlit secrets.")
        st.info("For local development, you can create a .env file with ARLIAI_API_KEY=your_api_key")
        st.info("For Streamlit Share, add your API key to the secrets.toml file under [arli]")
        return
    
    # Test Google Sheets connection silently
    sheets_connection = connect_to_google_sheets()
    # Don't show warning in main page, only in sidebar if needed
    
    # Check if profile photo exists, if not display a message in the sidebar
    if not os.path.exists(PROFILE_PHOTO):
        st.sidebar.warning(f"Profile photo not found. Please add a photo at '{PROFILE_PHOTO}'")
    
    # Display form if user info not collected yet
    if not st.session_state.user_info:
        user_info = display_user_form()
        if user_info:
            st.session_state.user_info = user_info
            st.rerun()
    else:
        # Display chat interface
        display_chat_interface()

if __name__ == "__main__":
    main()
