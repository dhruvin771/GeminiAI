import json
import os
import re
import requests
from dotenv import load_dotenv
import telebot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    return {}

def save_data(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

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
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

def send_generated_content(user_id, content):
    formatted_content = ""
    for part in content['parts']:
        cleaned_text = part['text']
        cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_text)
        cleaned_text = re.sub(r'```(.*?)```', r'<i>\1</i>', cleaned_text)
        formatted_content += cleaned_text + "\n"
    bot.send_message(user_id, formatted_content, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Hello {message.from_user.first_name}!")

@bot.message_handler(func=lambda message: message.content_type == 'text' and not message.text.startswith('/'))
def process_message(message):
    user_id = str(message.from_user.id)
    user_input = f'{message.text}'
    data = update_json(user_id, "user", user_input)

    payload = {"contents": data['contents']}

    generated_content = generate_content(payload)

    for content in generated_content['candidates']:
        if content['content']['role'] == 'model':
            update_json(user_id, "model", content['content']['parts'][0]['text'])
            send_generated_content(user_id, content['content'])

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = str(message.from_user.id)
    file_name = f"{user_id}.json"
    if os.path.exists(file_name):
        os.remove(file_name)
        bot.reply_to(message, "History cleared successfully.")
    else:
        bot.reply_to(message, "No history found.")

bot.infinity_polling()
