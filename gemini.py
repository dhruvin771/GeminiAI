import json
import os
import re
import requests
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

def load_data(file_name):
    try:
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                return json.load(file)
        return {}
    except Exception as e:
        print(f"Error loading data from {file_name}: {e}")
        return {}

def save_data(file_name, data):
    try:
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error saving data to {file_name}: {e}")

def update_json(user_id, role, text):
    file_name = f"{user_id}.json"
    data = load_data(file_name)

    if 'contents' not in data:
        data['contents'] = []

    while len(data['contents']) >= 30:
        data['contents'].pop(0)

    data['contents'].append({
        "role": role,
        "parts": [{"text": text}]
    })

    save_data(file_name, data)

    return data

def generate_content(payload):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_TOKEN}"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error generating content: {e}")
        return {}

def send_generated_content(user_id, content):
    formatted_content = ""
    for part in content.get('parts', []):
        cleaned_text = part.get('text', '')
        cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_text)
        cleaned_text = re.sub(r'```(.*?)```', r'<i>\1</i>', cleaned_text)
        formatted_content += cleaned_text + "\n"
    try:
        bot.send_message(user_id, formatted_content, parse_mode="HTML")
    except telebot.apihelper.ApiException as e:
        print(f"Error sending message to {user_id}: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, f"Hello {message.from_user.first_name}!")
    except telebot.apihelper.ApiException as e:
        print(f"Error sending welcome message: {e}")

@bot.message_handler(func=lambda message: message.content_type == 'text' and not message.text.startswith('/'))
def process_message(message):
    user_id = str(message.from_user.id)
    user_input = message.text
    data = update_json(user_id, "user", user_input)

    payload = {"contents": data.get('contents', [])}
    generated_content = generate_content(payload)

    for candidate in generated_content.get('candidates', []):
        content = candidate.get('content', {})
        if content.get('role') == 'model':
            text = content.get('parts', [{}])[0].get('text', '')
            update_json(user_id, "model", text)
            send_generated_content(user_id, content)

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = str(message.from_user.id)
    file_name = f"{user_id}.json"
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
            bot.reply_to(message, "History cleared successfully.")
        else:
            bot.reply_to(message, "No history found.")
    except Exception as e:
        print(f"Error clearing history for {user_id}: {e}")
        bot.reply_to(message, "An error occurred while clearing history.")

try:
    bot.infinity_polling()
except Exception as e:
    print(f"Error with bot polling: {e}")
