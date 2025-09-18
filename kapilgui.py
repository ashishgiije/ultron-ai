import tkinter as tk
from PIL import Image, ImageTk
import pyttsx3
import google.generativeai as genai
import pywhatkit
import random
import vobject
import os
import re
import datetime
import webbrowser
from config import apikey
import time
import textwrap
import numpy as np
import noisereduce as nr
import speech_recognition as sr


chatstr = ""
intro_spoken = False  # Flag to track if the intro message has been spoken

def chat(query):
    global chatstr
    genai.configure(api_key=apikey)
    chatstr += f"User: {query}\n"

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 50,
        "max_output_tokens": 200,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(history=[])

    base_prompt = ("You are Ultron, an AI assistant created by Kapil and his team. "
                   "Your responses should feel human-like. Always be polite, helpful, and clear. "
                   "You are a virtual assistant that can identify actions based on a statement. "
                   "It were a normal conversation and not a command. Now, get ready to assist the user in whatever they need!"
                   "always give the shortest answers but give atleast two line answers."
                   "dont use any emoji in sentance while answering the questions."

                   )

    response = chat_session.send_message(base_prompt + " Statement prompt is: '" + chatstr + "'")
    say(response.text)
    chatstr += f"{response.text}\n"
    print(f"User: {query}\nUltron: {response.text}")
    update_chat_display(f"User: {query}\nUltron: {response.text}")

def ai(prompt):
    genai.configure(api_key=apikey)
    text = f"geminiai response for Prompt: {''.join(prompt.split('AI')[1:]).strip()} \n ***************------*****************------*************\n\n"

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 1000,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(history=[])

    response = chat_session.send_message(''.join(prompt.split('AI')[1:]).strip())

    text += response.text
    if not os.path.exists("geminiai"):
        os.mkdir("geminiai")

    with open(f"geminiai/{''.join(prompt.split('AI')[1:]).strip()}.txt", "w") as f:
        f.write(text)





# Function for Text-to-Speech
def say(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def get_password():
    def submit_password():
        global password
        password = password_entry.get()
        root.destroy()  # Close the window once password is submitted

    root = tk.Tk()
    root.title("Enter Instagram Password")

    tk.Label(root, text="Enter your Instagram password:").pack(pady=10)
    password_entry = tk.Entry(root, show='*')  # Mask password input
    password_entry.pack(pady=10)
    submit_button = tk.Button(root, text="Submit", command=submit_password)
    submit_button.pack(pady=10)

    root.mainloop()


def load_contacts_from_vcf(vcf_file):
    contacts = {}
    try:
        with open(vcf_file, 'r') as file:
            for vcard in vobject.readComponents(file):
                name = vcard.fn.value.lower()
                phone = None
                if hasattr(vcard, 'tel'):
                    phone = vcard.tel.value.replace(" ", "").replace("-", "")
                if name and phone:
                    contacts[name] = phone
        say("Contacts loaded successfully.")
        return contacts
    except Exception as e:
        say("Failed to load contacts from the vCard file.")
        print(f"Error: {e}")
        return {}


# Function to send WhatsApp message
def send_whatsapp_message(contacts, contact_name, message):
    try:
        phone_number = contacts.get(contact_name.lower())
        if not phone_number:
            say(f"Sorry, I couldn't find a contact named {contact_name}.")
            return

        say(f"Sending message to {contact_name}.")
        update_chat_display(f"Ultron: Sending message to {contact_name}: {message}")


        pywhatkit.sendwhatmsg_instantly(phone_number, message)
        say("Message sent successfully.")
        update_chat_display(f"Ultron: Message sent successfully.")
    except Exception as e:
        say("Failed to send the message. Please try again.")
        print(f"Error: {e}")

recognizer = sr.Recognizer()

def takeCommand():
    if listening == True:
        status_label.config(text="Listening...", fg="green")
        root.update()

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)  # Calibrate to current noise level
            audio = recognizer.listen(source)
            status_label.config(text="Recognizing...", fg="yellow")
            root.update()

            try:
                # Save the raw audio data for noise reduction
                raw_audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)

                # Apply noise reduction
                reduced_noise = nr.reduce_noise(y=raw_audio_data, sr=source.SAMPLE_RATE)

                # Convert the reduced noise back into audio data format
                reduced_audio = sr.AudioData(reduced_noise.tobytes(), source.SAMPLE_RATE, audio.sample_width)

                # Recognize speech using Google with Marathi, Hindi, and English support
                query = recognizer.recognize_google(reduced_audio, language="en-IN")
                return query

            except sr.UnknownValueError:
                say("Sorry, I didn't catch that. Please speak clearly.")
                update_chat_display("Ultron: Sorry, I didn't catch that. Please speak clearly.")
                return None
            except sr.RequestError as e:
                say("Could not request results; check your internet connection.")
                update_chat_display("Ultron: Could not request results; check your internet connection.")
                return None



def clean_search_terms(query, site_name):
    search_keywords = ["search", "for", "on", "about", "find", "look up", "open", site_name]
    search_query = query.lower()

    for keyword in search_keywords:
        search_query = re.sub(r'\b' + keyword + r'\b', '', search_query).strip()

    return search_query

def open_site_or_search(query):
    sites = {
        "youtube": "https://www.youtube.com",
        "wikipedia": "https://www.wikipedia.org",
        "google": "https://www.google.com"
    }

    for site_name, base_url in sites.items():
        if site_name in query.lower():
            search_query = clean_search_terms(query, site_name)

            if search_query:
                if site_name == "google":
                    search_url = f"{base_url}/search?q={search_query.replace(' ', '+')}"
                elif site_name == "youtube":
                    search_url = f"{base_url}/results?search_query={search_query.replace(' ', '+')}"
                elif site_name == "wikipedia":
                    search_url = f"{base_url}/wiki/{search_query.replace(' ', '_')}"

                say(f"Searching for {search_query} on {site_name}...")
                update_chat_display(f"Ultron: Searching for {search_query} on {site_name}...")
                webbrowser.open(search_url)
            else:
                say(f"Opening {site_name}...")
                webbrowser.open(base_url)

            return True
    return False


def openWebsite(website_name):
    # Construct the URL based on the website name
    url = f"https://www.{website_name}.com"
    print(f"Opening {url}...")
    webbrowser.open(url)


def update_chat_display(message):
    if listening == True:

        # Clear previous content
        canvas.delete("all")

        # Redraw the image
        canvas.create_image(500, 50, anchor=tk.NW, image=photo)

        # Define maximum width for text wrapping
        max_width = 700

        # Separate the message into lines and split based on who said it (User/Ultron)
        lines = message.split('\n')
        y_position = 500  # Starting y position for text

        # Loop through each line to display it individually
        for line in lines:
            if line.strip():  # Only process non-empty lines
                # Wrapping text to avoid overflow
                wrapped_text = textwrap.fill(line, width=70)

                # Display the text
                canvas.create_text(
                    root.winfo_width() // 2, y_position,  # Center horizontally
                    anchor="center",
                    text=wrapped_text,
                    fill="white",
                    font=("Arial", 15)
                )

                # Calculate vertical spacing based on the number of lines
                y_position += (wrapped_text.count('\n') + 1) * 100  # Adjust vertical spacing if lines wrap


import threading

def speak_intro():
    # Play the intro audio
    say("Welcome to Ultron AI Assistant.")

def show_intro_message():
    # Update the chat display with the intro message
    update_chat_display("Ultron: Welcome to Ultron AI Assistant. How can I help you today?")

def start_intro():
    # Start speaking intro in a separate thread
    threading.Thread(target=speak_intro).start()
    # Schedule the message update in the main thread
    root.after(0, show_intro_message)


def start_listening():
    if listening == True:
        threading.Thread(target=listen_for_commands, daemon=True).start()


listening = True  # Variable to track listening state

def pause_listening():
    global listening
    listening = False
    status_label.config(text="Listening Paused", fg="red")




def resume_listening():
    global listening
    listening = True
    root.after(100, start_listening)


def listen_for_commands():
    global intro_spoken

    if not intro_spoken:
        start_intro()
        intro_spoken = True  # Set the flag to True after starting the intro

    while listening==True:

        if not listening:  # Check if listening is paused
            time.sleep(1)
            continue


        query = takeCommand()


        if query is None or query.strip() == "":
            time.sleep(1)
            continue

        if open_site_or_search(query):
            continue

        if "play music" in query or "play songs" in query or "play song" in query:
            music_dir = 'C:\Playlists'
            songs = os.listdir(music_dir)

            say("Playing Music ")
            update_chat_display(f"User: {query}\nUltron: Playing music")


            if songs:
                random_song = random.choice(songs)
                os.startfile(os.path.join(music_dir, random_song))

        elif "the time" in query or "current time" in query :
            hour = datetime.datetime.now().strftime("%H")
            minute = datetime.datetime.now().strftime("%M")
            say(f"Sir, the time is {hour} hours and {minute} minutes")
            root.after(0, lambda: update_chat_display(f"Sir, the time is {hour} hours and {minute} minutes"))

        elif "open camera" in query.lower() or "camera" in query.lower():
            os.system("start microsoft.windows.camera:")
            say("Opening Camera ")
            update_chat_display(f"User: {query}\nUltron: Opening Camera")

        elif "open notepad" in query.lower() or "notepad" in query:
            os.system("start notepad")
            say("Opening notepad ")
            update_chat_display(f"User: {query}\nUltron: Opening notepad ")
        elif "open calculator" in query.lower():
            os.system("C:\\Windows\\System32\\calc.exe")
            say("Opening calculator ")
            update_chat_display(f"User: {query}\nUltron: Opening Calculator")


        elif "Using AI ".lower() in query.lower():
            print("PATH--C:-Users-ashish-PycharmProjects-ULTRON-geminiai")
            update_chat_display(f"User: {query}\nUltron: The file is saved in the Geminiai folder. File location -> PATH--C:-Users-ashish-PycharmProjects-ULTRON-geminiai")
            say("The file is saved in the Geminiai folder. File location given bellow")
            ai(prompt=query)

        elif "send message " in query.lower() or "send message on whatsapp to" in query.lower() or "send a message" in query.lower() or "message" in query.lower() or "whatsapp message" in query.lower():
            vcf_file_path = "C:\\vcard.vcf"  # Replace with the path to your vCard file
            update_chat_display(f"User: {query}")

            # Load contacts from vCard file
            if not os.path.exists(vcf_file_path):
                say("vCard file not found. Please check the file path.")
                print("vCard file not found.")
                exit()

            contacts = load_contacts_from_vcf(vcf_file_path)

            if not contacts:
                say("No contacts found in the vCard file.")
                print("No contacts found in the vCard file.")
                exit()

            while True:   # Take the contact name as input
                say("Who should I send the message to?")
                update_chat_display(f"Ultron: Who should I send the message to?")
                contact_name = takeCommand()
                if not contact_name:
                    continue

                # Check for multi-word names
                contact_name = contact_name.strip().lower()

                # Take the message as input
                say(f"What is the message for {contact_name}?")
                update_chat_display(f"Ultron: What is the message for {contact_name}?")

                message = takeCommand()
                if not message:
                    continue

                # Send the WhatsApp message
                send_whatsapp_message(contacts, contact_name, message)

                # Ask if the user wants to send another message

                break

            # OPENING ANY WEBSITE
        elif "open" in query and "website" in query:
            # Extract the website name by removing "open" from the command
            website_name = query.replace("open", "").replace("website", "").strip()
            say("opening sir...")
            update_chat_display(f"User: {query}\nUltron:opening {website_name} sir...  ")
            openWebsite(website_name)  # OPENWEBSITE FUNCTION MENSTION ABOVE

        elif "reset chat" in query.lower():
            global chatstr
            chatstr = ""
            root.after(0, lambda: update_chat_display(""))

        elif "ultron exit" in query.lower() or "exit" in query.lower():
            say("okay! have a nice day sir")
            root.quit()
            exit()

        else:
            chat(query)

if __name__ == '__main__':
    print('Welcome to Ultron A.I')
    # chat("can you tell me the address of mgm college of cs and it nanded")
    

    # Initialize the GUI
    root = tk.Tk()
    root.title("Ultron AI Assistant")
    root.geometry("1400x800")
    root.configure(bg='black')

    canvas = tk.Canvas(root, bg='black', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Load and display the main image
    try:
        image = Image.open("ultron.jpeg")
        image = image.resize((400, 400), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        canvas.create_image(500, 50, anchor=tk.NW, image=photo)
    except Exception as e:
        print(f"Error loading main image: {e}")

    # Status label
    status_label = tk.Label(root, text="", bg='black', fg='white', font=("Arial", 24))
    status_label.pack(side=tk.BOTTOM, pady=30)
    pause_button = tk.Button(root, text="Pause Listening", command=pause_listening, font=("Arial", 12), bg="red",
                             fg="white")
    pause_button.pack(side=tk.LEFT, padx=20, pady=10)

    start_button = tk.Button(root, text="Start", command=resume_listening, font=("Arial", 12), bg="green",
                             fg="white")
    start_button.pack(side=tk.RIGHT, padx=20, pady=10)

    # Start listening for commands after the GUI initializes
    # root.after(100, start_listening)

    # Start the GUI event loop
    root.mainloop()