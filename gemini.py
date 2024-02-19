import asyncio
import json
import os
import traceback
from dotenv import load_dotenv
import requests
import telebot

# Load environment variables from .env file
load_dotenv()

# Telegram bot token and chat ID
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize 
bot = telebot.TeleBot(BOT_TOKEN)

# Send welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Hello {message.from_user.first_name}!")

# start bot polling
bot.infinity_polling()