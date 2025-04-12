# Resume Chatbot with Arli AI

A personalized chatbot that answers questions based on your resume/CV. This application includes a user form to collect visitor information and an attractive, interactive chat interface.

## Features

- User information form for visitor data collection
- CV/Resume-based chatbot that answers questions about your professional experience
- Professional, modern UI with profile photo
- Responsive design that works well on different devices

## Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your profile photo

Place your professional headshot in the following location:
```
images/profile_photo.jpg
```

The app will display a placeholder if no photo is found. The recommended photo size is 400x400 pixels or larger, with a square aspect ratio.

### 3. Add your CV data

Edit the `cv_data.txt` file with your actual resume information. The formatting will be preserved and used to answer questions from users.

### 4. Set up your Arli AI API key

#### For local development:
- Create a `.env` file in the root directory
- Add your Arli AI key: `ARLIAI_API_KEY=your_api_key_here`

#### For Streamlit Share deployment:
The app is configured to use Streamlit's secrets management. In Streamlit Share:

1. Go to your app settings
2. Find the "Secrets" section
3. Add your secrets in TOML format:
```toml
[arli]
api_key = "your_arliai_api_key_here"
```

### 5. Run the application

```bash
streamlit run app_stream.py
```

The application will be available at http://localhost:8501

## Using the Chatbot

1. Visitors will see a welcome page with your profile photo and a form to fill out:
   - Name
   - Email
   - Company/Organization
   - Position
   - Reason for contact

2. After submitting the form, they can chat with the bot that will answer questions about your CV.

3. The visitor's information is displayed in the sidebar for reference.

4. The chat interface has a clean design with message bubbles for easy reading.

## Customization

### Changing the color scheme

You can modify the colors in the CSS section at the top of `app_stream.py`. The current theme uses purple tones, but you can change these to match your personal brand.

### Modifying the system prompt

To change how the chatbot responds, edit the system prompt in the `get_arli_response()` function.

## Technical Details

The app uses:
- Streamlit for the web interface
- Arli AI for generating responses based on your resume
- Direct API integration with Arli AI's chat completions endpoint 