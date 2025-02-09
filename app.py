import requests
import logging
import time
import threading
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = ''  # Replace with your actual token
bot = Bot(token=TELEGRAM_TOKEN)

previous_task_ids = set()
Chat_id = 'Chat Id mu'
DEFAULT_PROVIDER_NAME = "Nama User Mu" 


def fetch_tasks():
    url = "https://api-testnet.prover.xyz/api/v1/task?status=1&pageSize=1" 
    response = requests.get(url)
    
    if response.status_code == 200:
        tasks_data = response.json()
        task_list = tasks_data.get('data', {}).get('list', [])
        
        for task in task_list:
            task_id_minus_10 = task.get('ID')
            task_id = task_id_minus_10 - 30 #await untuk submited proof
            print(f"Task ID (minus 10): {task_id_minus_10}")
        
        return task_list  
    else:
        logger.error(f"Failed to fetch tasks: {response.status_code}")
        return None
    url = "https://api-testnet.prover.xyz/api/v1/task?status=1&pageSize=1" 
    response = requests.get(url)
    
    if response.status_code == 200:
        tasks_data = response.json()
        task_list = tasks_data.get('data', {}).get('list', [])
        
        for task in task_list:
            task_id = task.get('ID')
            print(f"Task ID: {task_id}")
        
        return task_list  
    else:
        logger.error(f"Failed to fetch tasks: {response.status_code}")
        return None

# Function to fetch task details from the API
def fetch_task_details(task_id):
    url = f"https://api-testnet.prover.xyz/api/v1/task/{task_id}"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,id;q=0.8",
        "origin": "https://testnet.cysic.xyz",
        "referer": "https://testnet.cysic.xyz/",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Linux\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-cysic-address": "get your address conected on web",  
        "x-cysic-sign": "get you your signed key from cysic web", 
        "x-dav-tsi": "1",
        "access-control-allow-credentials": "true",
        "access-control-allow-origin": "*",
        "access-control-expose-headers": "Content-Length",
        "content-type": "application/json; charset=utf-8"
    }
    time.sleep(5)
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        task_details = response.json()
        return task_details
    else:
        logger.error(f"Failed to fetch task details for ID {task_id}: {response.status_code}")
        return None

def check_rewards_for_user(username, task_id):
    rewarded_users = []
    tasks = fetch_tasks()
    
    if tasks:
        for task in tasks:
            task_id = task.get('ID')  
            task_details = fetch_task_details(task_id)
            print(task_details)
            
            if task_details:
                provider_list = task_details.get('data', {}).get('provider_list', [])
                
                if isinstance(provider_list, list):
                    rewarded_providers = [
                        provider for provider in provider_list if provider.get('has_reward') == 1
                    ]
                    rewarded_providers.sort(key=lambda p: p['name'])
                    
                    for rank, provider in enumerate(rewarded_providers, start=1):
                        provider_name = provider.get('name')
                        
                        if provider_name == username:
                            rewarded_users.append((provider_name, rank, task_id))  # Append task_id
                else:
                    logger.warning(f"Provider list for task ID {task_id} is not a valid list.")
    else:
        logger.warning("No tasks found.")

    return rewarded_users


async def send_telegram_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent successfully to chat ID {chat_id}: {text}")
    except Exception as e:
        logger.error(f"Failed to send message to chat ID {chat_id}. Error: {e}")

async def fetch_tasks_periodically(application):
    global previous_task_ids  

    while True:
        tasks = fetch_tasks()  
        
        if tasks:
            current_task_ids = {task.get('ID') for task in tasks}
            
            new_task_ids = current_task_ids - previous_task_ids
            
            if new_task_ids:
                for task_id in new_task_ids:
                    await send_telegram_message(chat_id={Chat_id}, text=f"New Task ID found: {task_id}")
                    logger.info(f"New Task ID found: {task_id}")
                    
                    rewarded_users = check_rewards_for_user(DEFAULT_PROVIDER_NAME, task_id)
                    
                    if rewarded_users:
                        response = "\n".join([f"Task ID: {task_id} - {provider_name} has received rewards with rank: {rank}" 
                                              for provider_name, rank, task_id in rewarded_users])
                        await send_telegram_message(chat_id={Chat_id}, text=response)
                        logger.info(f"Rewards found for Task ID {task_id}: {rewarded_users}")
                    else:
                        await send_telegram_message(chat_id={Chat_id}, text=f"Task ID: {task_id} - No rewards found for {DEFAULT_PROVIDER_NAME}")
                        logger.info(f"No rewards found for Task ID {task_id}.")
                    
                    task_details = fetch_task_details(task_id)
                    print (task_details)
                    if task_details:
                        task_info = task_details.get('data', {}).get('task_info', "No additional details available.")
                        await send_telegram_message(chat_id={Chat_id}, text=f"Details for Task ID {task_id}: {task_info}")
                        logger.info(f"Task details sent for Task ID {task_id}: {task_info}")
                        previous_task_ids = current_task_ids
        
        await asyncio.sleep(5) 

# Start button handler
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Start Fetching Tasks", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome! Click the button below to start the task fetching process:', reply_markup=reply_markup)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Fetching tasks... Please wait.")
    await fetch_tasks_periodically(context.application)

def start_task_fetching_thread(application):
    task_fetch_thread = threading.Thread(target=fetch_tasks_periodically, args=(application,), daemon=True)
    task_fetch_thread.start()

def main():
    from telegram.ext import Application

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    start_task_fetching_thread(application)

    application.run_polling()

if __name__ == "__main__":
    main()
