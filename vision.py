import os
from dotenv import load_dotenv
import streamlit as st
from PIL import Image
import google.generativeai as genai
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

# Load environment variables
load_dotenv()

# Configure the Generative AI API with the key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("API key not found. Please check your .env file.")
    st.stop()

genai.configure(api_key=api_key)

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    st.error("MongoDB URI not found. Please check your .env file.")
    st.stop()

# Ensure dnspython is installed
try:
    import dns.resolver
except ImportError:
    st.error("dnspython is not installed. Please install it using 'pip install dnspython'.")
    st.stop()

try:
    client = MongoClient(mongo_uri)
    db = client['invoice']
    collection = db['invoice details']
except ConfigurationError as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# Function to load the Generative AI model and get response
def get_gemini_response(input_text, image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_text, image, prompt])
    return response.text

# Function to set up input image
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        return Image.open(uploaded_file)
    else:
        raise FileNotFoundError("No file uploaded")

# Function to save response to MongoDB
def save_response_to_mongodb(input_text, response_text):
    document = {
        "input_text": input_text,
        "response_text": response_text
    }
    collection.insert_one(document)

# Initialize Streamlit app
st.set_page_config(page_title="Gemini Image Demo")
st.header("Gemini Application")

# User inputs
input_text = st.text_input("Input Prompt: ", key="input")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

submit = st.button("Tell me about the image")

input_prompt = """
You are an expert in understanding invoices.
You will receive input images as invoices &
you will have to answer questions based on the input image.
"""

# If submit button is clicked
if submit:
    if not uploaded_file:
        st.error("Please upload an image.")
    else:
        image = input_image_setup(uploaded_file)
        response = get_gemini_response(input_text, image, input_prompt)
        st.subheader("The Response is")
        st.write(response)
        
        # Save response to MongoDB
        save_response_to_mongodb(input_text, response)
        st.success("Response saved to MongoDB.")