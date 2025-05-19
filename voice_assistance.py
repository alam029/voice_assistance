import speech_recognition as sr
import pyttsx3
import pyaudio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import threading
import requests
from openai import OpenAI
import dateparser
import os

os.environ["PYTHONWARNINGS"] = "ignore"

# Creating a list for storing the reminder tasks
reminders = []

# Enter your weather API key
weather_api_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Enter your OpenAI API key
client = OpenAI(api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

# Initialize recognizer
recognizer = sr.Recognizer()
        
# Initialize text-to-speech engine
engine = pyttsx3.init('espeak')
engine.setProperty('rate', 120)
engine.setProperty('volume', 1.0)

# Function for giving answer by speaking
def speak(text):
    """Convert text to speech"""
    engine.say(text)
    engine.runAndWait()

# Function for listening to voice
def listen():
    """Listen to user's voice input"""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
            try:
                text = recognizer.recognize_whisper(audio)
                print(f"User said: {text}")
                return text.lower()
            except sr.UnknownValueError:
                print("Could not understand audio")
                return ""
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return ""
    except Exception as e:
        print(f"Error with microphone: {e}")
        return ""

# Function for sending email
def send_email(to_email, subject, body):
    """Send email using Gmail SMTP"""
    try:
        # Email configuration
        from_email = "example@gmail.com"  # Replace with your email
        password = "xxxx xxxx xxxx xxxx"  # Replace with your app password
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
            
        # Add body
        msg.attach(MIMEText(body, 'plain'))
            
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Function for checking reminders
def check_reminder():
    while True:
        now = datetime.now()
        for reminder in reminders[:]:  # Create a copy of the list
            if now >= reminder['time']:
                message = f"Reminder: {reminder['text']}"
                speak(message)
                reminders.remove(reminder)
        time.sleep(10)

# Function for setting reminder
def set_reminder(reminder_text, reminder_time):
    """Set a reminder for a specific time"""
    try:
        # Try parsing natural language time with dateparser
        parsed_time = dateparser.parse(reminder_time)

        if not parsed_time:
            return "Sorry, I couldn't understand the reminder time. Please try again."

        reminders.append({
            'text': reminder_text,
            'time': parsed_time
        })
        print(f"Reminder set for {parsed_time.strftime('%Y-%m-%d %H:%M')}")
        return "Reminder added successfully"
    except Exception as e:
        return f"Failed to set reminder: {str(e)}"
    
# Function for getting weather information
def get_weather(city):
    try:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': weather_api_key,
            'units': 'metric'
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
           
        if data['cod'] == 200:
            weather = data['weather'][0]['description']
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            return f"The weather in {city} is {weather} with a temperature of {temp}°C and humidity of {humidity}%"
        else:
            return "Sorry, I couldn't fetch the weather information."
    except Exception as e:
        return f"Error getting weather: {str(e)}"

# Function for giving general answers to questions
def get_gpt_response(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I couldn't get a response: {str(e)}"
    
# Function for processing all commands
def process_command(text):
    """Process user commands"""
    if not text:
        return True
        
    if 'send email' in text:
        speak("Please provide the recipient's email address")
        to_email = listen()
        speak("What should be the subject?")
        subject = listen()
        speak("What should be the message?")
        body = listen()
        response = send_email(to_email, subject, body)
        speak(response)
        
    elif 'set reminder' in text:
        speak("What should I remind you about?")
        reminder_text = listen()
        speak("When should I remind you?")
        reminder_time = listen()
        response = set_reminder(reminder_text, reminder_time)
        speak(response)
        
    elif 'weather' in text:
        city = text.replace('weather', '').strip()
        if not city:
            speak("Which city's weather would you like to know?")
            city = listen()
        response = get_weather(city)
        speak(response)
        
    elif 'exit' in text or 'quit' in text:
        speak("Goodbye!")
        return False
        
    else:
        response = get_gpt_response(text)
        speak(response)
        
    return True

# Start reminder thread
reminder_thread = threading.Thread(target=check_reminder, daemon=True)
reminder_thread.start()

# Main loop
print("Wellcome")
speak("Hello! I'm your voice assistant. How can I help you today?")
engine.runAndWait()

while True:
    print("Listening...")
    text = listen()
    if not process_command(text):
        break 
