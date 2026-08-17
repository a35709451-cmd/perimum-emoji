from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging
import re
import json
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable not set!")
    sys.exit(1)

EMOJI_FILE = "emojis.json"

# Default premium emojis
PREMIUM_EMOJIS = {
    "verified": {"id": "6147565374289220368", "fallback": "✅", "added_by": "system", "date": "2024-01-01"},
    "flex": {"id": "6147464060305676048", "fallback": "😎", "added_by": "system", "date": "2024-01-01"},
    "blue_verification": {"id": "6147524086768604985", "fallback": "💎", "added_by": "system", "date": "2024-01-01"},
    "frozen": {"id": "5449449325434266744", "fallback": "❄️", "added_by": "system", "date": "2024-01-01"},
    "crying": {"id": "6273840152980755328", "fallback": "😭", "added_by": "system", "date": "2024-01-01"},
    "smiling": {"id": "6276057176444246654", "fallback": "🙂", "added_by": "system", "date": "2024-01-01"},
    "seeing_up": {"id": "6273997026661241933", "fallback": "😋", "added_by": "system", "date": "2024-01-01"},
    "teeth": {"id": "6273726078649372769", "fallback": "😁", "added_by": "system", "date": "2024-01-01"},
    "done": {"id": "6274007313107915274", "fallback": "👍", "added_by": "system", "date": "2024-01-01"},
    "blue_badge": {"id": "5978776771623914876", "fallback": "🟫", "added_by": "system", "date": "2024-01-01"},
    "black_badge": {"id": "5978686323907628843", "fallback": "🔸", "added_by": "system", "date": "2024-01-01"},
    "busy_tag": {"id": "5852873584912896283", "fallback": "🟧", "added_by": "system", "date": "2024-01-01"},
    "instagram": {"id": "5895297528106061174", "fallback": "🌐", "added_by": "system", "date": "2024-01-01"},
    "telegram": {"id": "5895735846698487922", "fallback": "🌐", "added_by": "system", "date": "2024-01-01"},
    "whatsapp": {"id": "5895343514320899727", "fallback": "🌐", "added_by": "system", "date": "2024-01-01"},
    "india": {"id": "5913754823643107921", "fallback": "🇮🇳", "added_by": "system", "date": "2024-01-01"},
    "dollar": {"id": "5197434882321567830", "fallback": "💵", "added_by": "system", "date": "2024-01-01"},
    "top": {"id": "5463071033256848094", "fallback": "🔝", "added_by": "system", "date": "2024-01-01"},
    "bro": {"id": "5463256910851546817", "fallback": "🤝", "added_by": "system", "date": "2024-01-01"},
    "yes": {"id": "5463423955014529788", "fallback": "👌", "added_by": "system", "date": "2024-01-01"},
    "lock": {"id": "5465443379917629504", "fallback": "🔓", "added_by": "system", "date": "2024-01-01"},
    "good": {"id": "5465465194056525619", "fallback": "👍", "added_by": "system", "date": "2024-01-01"},
    "sigma": {"id": "6235620067942341623", "fallback": "🥃", "added_by": "system", "date": "2024-01-01"},
    "don": {"id": "6235717714023814969", "fallback": "🍂", "added_by": "system", "date": "2024-01-01"},
    "skills": {"id": "6235593671073339928", "fallback": "💀", "added_by": "system", "date": "2024-01-01"},
    "heart": {"id": "6147617184479711380", "fallback": "❤️‍🔥", "added_by": "system", "date": "2024-01-01"},
    "stars": {"id": "6235403472741603087", "fallback": "⭐", "added_by": "system", "date": "2024-01-01"},
    "github": {"id": "5346181118884331907", "fallback": "📱", "added_by": "system", "date": "2024-01-01"},
    "motion": {"id": "5971944878815317190", "fallback": "💠", "added_by": "system", "date": "2024-01-01"},
}

user_data_store = {}

def save_emojis():
    try:
        with open(EMOJI_FILE, 'w', encoding='utf-8') as f:
            json.dump(PREMIUM_EMOJIS, f, ensure_ascii=False, indent=2)
        logger.info("✅ Emojis saved successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving emojis: {e}")
        return False

def load_emojis():
    global PREMIUM_EMOJIS
    try:
        if os.path.exists(EMOJI_FILE):
            with open(EMOJI_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge loaded emojis with defaults
                for key, value in loaded.items():
                    PREMIUM_EMOJIS[key] = value
                logger.info(f"✅ Loaded {len(loaded)} emojis from file")
                return True
        else:
            # Create default emojis file
            save_emojis()
            logger.info("✅ Created default emojis file")
            return True
    except Exception as e:
        logger.error(f"❌ Error loading emojis: {e}")
        return False

def get_emoji_html(name):
    if name in PREMIUM_EMOJIS:
        data = PREMIUM_EMOJIS[name]
        return f'<tg-emoji emoji-id="{data["id"]}">{data["fallback"]}</tg-emoji>'
    return ""

def format_with_emojis(text):
    return process_text_with_emojis(text)

async def is_admin_in_channel(context, user_id, channel_username):
    try:
        chat = await context.bot.get_chat(chat_id=channel_username)
        chat_member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user_id)
        return chat_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verified = get_emoji_html("verified")
    stars = get_emoji_html("stars")
    
    message = f"{verified} Premium Emoji Broadcast Bot {stars}\n\n" + format_with_emojis(
        "'top' How to use 'done':\n"
        "1. Use /ads to see all emojis\n"
        "2. Use /myemojis to see your added emojis\n"
        "3. Use /broadcast to broadcast (Admin only)\n"
        "4. Use /addemoji to add new emoji\n"
        "5. Use /help for more info\n\n"
        "Example text: welcome to premium emoji bot 'verified'\n"
        "Replace 'verified' with any emoji name from /ads"
    )
    await update.message.reply_text(message, parse_mode="HTML")

async def ads_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji_list = []
    for name, data in PREMIUM_EMOJIS.items():
        emoji_html = get_emoji_html(name)
        added_by = data.get("added_by", "system")
        emoji_list.append(f"{emoji_html} {name} (by {added_by})")
    
    top = get_emoji_html("top")
    stars = get_emoji_html("stars")
    
    message = f"{top} Available Premium Emojis ({len(PREMIUM_EMOJIS)}) {stars}\n\n" + \
              "\n".join(emoji_list) + \
              format_with_emojis(
                  "\n\n'good' Usage: Type emoji names in single quotes like 'emoji_name'\n\n"
                  "Example: Hello 'verified' 'stars' 'dollar'\n\n"
                  "Use /myemojis to see emojis you added"
              )
    await update.message.reply_text(message, parse_mode="HTML")

async def myemojis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.username or update.effective_user.first_name
    
    user_emojis = []
    for name, data in PREMIUM_EMOJIS.items():
        if data.get("added_by", "").lower() == str(user_id).lower() or data.get("added_by", "") == user_name:
            emoji_html = get_emoji_html(name)
            date = data.get("date", "Unknown")
            user_emojis.append(f"{emoji_html} {name} (added: {date})")
    
    if user_emojis:
        top = get_emoji_html("top")
        stars = get_emoji_html("stars")
        
        message = f"{top} Your Added Emojis ({len(user_emojis)}) {stars}\n\n" + \
                  "\n".join(user_emojis) + \
                  format_with_emojis(
                      "\n\n'good' Use /addemoji to add more emojis"
                  )
    else:
        message = format_with_emojis(
            "❌ You haven't added any emojis yet!\n\n"
            "'good' Use /addemoji to add your first emoji\n"
            "Everyone will be able to use your added emojis!"
        )
    
    await update.message.reply_text(message, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verified = get_emoji_html("verified")
    stars = get_emoji_html("stars")
    
    message = f"{verified} Help Guide\n\n" + format_with_emojis(
        "'stars' Commands 'top':\n"
        "• /start - Start the bot\n"
        "• /ads - Show ALL available emojis\n"
        "• /myemojis - Show emojis YOU added\n"
        "• /broadcast - Broadcast (Admin only)\n"
        "• /addemoji - Add new custom emoji\n"
        "• /help - Show this help\n\n"
        "'lock' Admin Requirement 'verified':\n"
        "• Must be admin in target channel\n"
        "• Bot must be admin in channel\n"
        "• Only admins can broadcast\n\n"
        "'good' Emoji Sharing 'heart':\n"
        "• Anyone can add emojis\n"
        "• Everyone can use added emojis\n"
        "• Check /myemojis for your contributions"
    )
    await update.message.reply_text(message, parse_mode="HTML")

async def addemoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {"step": "waiting_emoji_name", "user_name": update.effective_user.username or update.effective_user.first_name}
    
    plus = get_emoji_html("done")
    await update.message.reply_text(
        f"{plus} Adding New Emoji\n\n" + format_with_emojis(
            "Step 1️⃣: Send the emoji name (no spaces, use underscore)\n"
            "Example: fire_emoji or cool_badge\n\n"
            "'stars' Everyone will see and use your emoji!"
        ),
        parse_mode="HTML"
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    broadcast_emoji = get_emoji_html("telegram")
    await update.message.reply_text(
        f"{broadcast_emoji} Broadcast Setup (Admin Only)\n\n" + format_with_emojis(
            "⚠️ You must be admin in target channel\n"
            "Step 1️⃣: Send the text you want to broadcast\n"
            "Include emoji names in single quotes like 'emoji_name'\n\n"
            "'top' Example 'done':\n"
            "Welcome to our premium channel 'verified' Get offers 'dollar' 'stars'"
        ),
        parse_mode="HTML"
    )
    
    user_data_store[user_id] = {"step": "waiting_text"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data_store:
        return
    
    step = user_data_store[user_id].get("step")
    
    if step == "waiting_emoji_name":
        emoji_name = update.message.text.strip().lower()
        
        if ' ' in emoji_name:
            error_emoji = get_emoji_html("crying")
            await update.message.reply_text(
                f"{error_emoji} Emoji name cannot contain spaces. Use underscore (_) instead.\n"
                "Example: fire_emoji\n\n"
                "Send emoji name again:",
                parse_mode="HTML"
            )
            return
        
        if emoji_name in PREMIUM_EMOJIS:
            existing_emoji = get_emoji_html(emoji_name)
            await update.message.reply_text(
                f"❌ Emoji name '{emoji_name}' already exists! {existing_emoji}\n"
                f"Choose a different name:",
                parse_mode="HTML"
            )
            return
        
        user_data_store[user_id]["emoji_name"] = emoji_name
        user_data_store[user_id]["step"] = "waiting_emoji_data"
        
        done_emoji = get_emoji_html("done")
        await update.message.reply_text(
            f"{done_emoji} Emoji name: {emoji_name}\n\n"
            "Step 2️⃣: Now forward a message with emoji in this format:\n"
            "📝 Text/Caption\n[emoji]\n\n🔎 Entities\n• Custom Emoji ID: 1234567890\n\n"
            "Or send the emoji ID directly:\n\n"
            "⭐ Everyone will be able to use this emoji!",
            parse_mode="HTML"
        )
    
    elif step == "waiting_emoji_data":
        emoji_name = user_data_store[user_id]["emoji_name"]
        message_text = update.message.text or ""
        
        emoji_id = None
        fallback_text = None
        
        if update.message.forward_from_message_id:
            lines = message_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if "📝 Text/Caption" in line and i + 1 < len(lines):
                    fallback_text = lines[i + 1].strip()
                
                if "Custom Emoji ID:" in line:
                    parts = line.split("Custom Emoji ID:")
                    if len(parts) > 1:
                        emoji_id = parts[1].strip()
                        break
        
        if not emoji_id:
            if message_text.isdigit():
                emoji_id = message_text
                fallback_text = "❓"
            else:
                match = re.search(r'(\d{10,})', message_text)
                if match:
                    emoji_id = match.group(1)
                    fallback_text = "❓"
        
        if emoji_id:
            if not fallback_text or fallback_text == "❓":
                await update.message.reply_text(
                    f"✅ Emoji ID: {emoji_id}\n\n"
                    "Please send the fallback emoji character:\n"
                    "Example: 🔥 or ⭐"
                )
                user_data_store[user_id]["emoji_id"] = emoji_id
                user_data_store[user_id]["step"] = "waiting_fallback"
                return
            
            user_name = user_data_store[user_id].get("user_name", str(user_id))
            
            PREMIUM_EMOJIS[emoji_name] = {
                "id": emoji_id,
                "fallback": fallback_text,
                "added_by": user_name,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            save_emojis()
            
            del user_data_store[user_id]
            
            new_emoji = f'<tg-emoji emoji-id="{emoji_id}">{fallback_text}</tg-emoji>'
            await update.message.reply_text(
                f"{new_emoji} Emoji added successfully!\n\n" +
                format_with_emojis(
                    f"✅ Added to global emoji list!\n"
                    f"Name: {emoji_name}\n"
                    f"Added by: {user_name}\n"
                    f"Use in text like: example text '{emoji_name}'\n\n"
                    f"'stars' Everyone can now use '{emoji_name}' emoji!\n"
                    f"Check /ads to see all emojis\n"
                    f"Check /myemojis to see your emojis"
                ),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ Could not extract emoji ID!\n"
                "Please send in correct format or send emoji ID directly.\n"
                "Example format:\n"
                "📝 Text/Caption\n💠\n\n🔎 Entities\n• Custom Emoji ID: 5971944878815317190"
            )
    
    elif step == "waiting_fallback":
        fallback_text = update.message.text.strip()
        emoji_name = user_data_store[user_id]["emoji_name"]
        emoji_id = user_data_store[user_id]["emoji_id"]
        user_name = user_data_store[user_id].get("user_name", str(user_id))
        
        PREMIUM_EMOJIS[emoji_name] = {
            "id": emoji_id,
            "fallback": fallback_text,
            "added_by": user_name,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        save_emojis()
        
        del user_data_store[user_id]
        
        new_emoji = f'<tg-emoji emoji-id="{emoji_id}">{fallback_text}</tg-emoji>'
        await update.message.reply_text(
            f"{new_emoji} Emoji added successfully!\n\n" +
            format_with_emojis(
                f"✅ Added to global emoji list!\n"
                f"Name: {emoji_name}\n"
                f"Added by: {user_name}\n"
                f"Use in text like: example text '{emoji_name}'\n\n"
                f"'stars' Everyone can now use '{emoji_name}' emoji!\n"
                f"Check /ads to see all emojis\n"
                f"Check /myemojis to see your emojis"
            ),
            parse_mode="HTML"
        )
    
    elif step == "waiting_text":
        text = update.message.text
        user_data_store[user_id]["text"] = text
        user_data_store[user_id]["step"] = "waiting_channel"
        
        preview_text = format_with_emojis(text)
        
        try:
            preview_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=preview_text,
                parse_mode="HTML"
            )
            
            user_data_store[user_id]["preview_msg_id"] = preview_msg.message_id
            
            done_emoji = get_emoji_html("done")
            await update.message.reply_text(
                f"{done_emoji} Text received!\n\n"
                "Above is how it will look with premium emojis ↑\n\n"
                f"Step 2️⃣: Now send the channel username (with @)\n"
                f"Example: @yourchannel\n\n"
                "⚠️ You must be admin in that channel",
                parse_mode="HTML"
            )
            
        except Exception as e:
            error_emoji = get_emoji_html("crying")
            await update.message.reply_text(
                f"{error_emoji} Error: {str(e)}\n\n"
                "Make sure emoji names are correct. Use /ads to check emoji names."
            )
            del user_data_store[user_id]
    
    elif step == "waiting_channel":
        channel = update.message.text.strip()
        
        if not channel.startswith("@"):
            error_emoji = get_emoji_html("crying")
            await update.message.reply_text(
                f"{error_emoji} Please send channel username starting with @\n"
                "Example: @yourchannel",
                parse_mode="HTML"
            )
            return
        
        is_admin = await is_admin_in_channel(context, user_id, channel)
        
        if not is_admin:
            error_emoji = get_emoji_html("crying")
            await update.message.reply_text(
                f"{error_emoji} Access Denied!\n\n"
                f"You are not an admin in {channel}\n"
                "Only channel admins can broadcast messages.\n\n"
                "Make sure:\n"
                "1. You are admin in the channel\n"
                "2. Bot is admin in the channel\n"
                "3. Channel username is correct",
                parse_mode="HTML"
            )
            del user_data_store[user_id]
            return
        
        user_data_store[user_id]["channel"] = channel
        user_data_store[user_id]["step"] = "confirm"
        
        verified = get_emoji_html("verified")
        await update.message.reply_text(
            f"{verified} Admin Verified!\n\n"
            f"📢 Channel: {channel}\n"
            f"👑 Your Status: Admin ✓\n\n"
            f"✅ Send CONFIRM to forward the message\n"
            f"❌ Send CANCEL to abort",
            parse_mode="HTML"
        )
    
    elif step == "confirm":
        response = update.message.text.upper()
        
        if response == "CONFIRM":
            try:
                channel = user_data_store[user_id]["channel"]
                preview_msg_id = user_data_store[user_id].get("preview_msg_id")
                chat_id = update.effective_chat.id
                
                is_admin = await is_admin_in_channel(context, user_id, channel)
                
                if not is_admin:
                    error_emoji = get_emoji_html("crying")
                    await update.message.reply_text(
                        f"{error_emoji} Access Revoked!\n\n"
                        f"You are no longer admin in {channel}\n"
                        "Broadcast cancelled.",
                        parse_mode="HTML"
                    )
                    del user_data_store[user_id]
                    return
                
                await context.bot.forward_message(
                    chat_id=channel,
                    from_chat_id=chat_id,
                    message_id=preview_msg_id,
                    disable_notification=True
                )
                
                success_emoji = get_emoji_html("verified")
                await update.message.reply_text(
                    f"{success_emoji} Broadcast successful!\n\n"
                    f"📢 Sent to: {channel}\n"
                    f"👑 Broadcast by: Admin\n\n"
                    f"Use /broadcast for another message",
                    parse_mode="HTML"
                )
                
            except Exception as e:
                error_emoji = get_emoji_html("crying")
                await update.message.reply_text(
                    f"{error_emoji} Error: {str(e)}\n\n"
                    f"Make sure:\n"
                    f"1. Bot is admin in {channel}\n"
                    f"2. Bot can send messages in channel\n"
                    f"3. Try again with /broadcast"
                )
            
            del user_data_store[user_id]
        
        elif response == "CANCEL":
            del user_data_store[user_id]
            cancel_emoji = get_emoji_html("crying")
            await update.message.reply_text(f"{cancel_emoji} Broadcast cancelled", parse_mode="HTML")
        
        else:
            await update.message.reply_text(
                "Please send CONFIRM or CANCEL"
            )

def process_text_with_emojis(text):
    def replace_emoji(match):
        emoji_name = match.group(1).strip().lower()
        
        if emoji_name in PREMIUM_EMOJIS:
            data = PREMIUM_EMOJIS[emoji_name]
            emoji_id = data.get("id")
            fallback = data.get("fallback", "❓")
            return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
        
        return match.group(0)
    
    pattern = r"'([^']+)'"
    result = re.sub(pattern, replace_emoji, text)
    
    return result

def main():
    logger.info("🚀 Starting Telegram Premium Emoji Bot...")
    
    # Load emojis
    if not load_emojis():
        logger.error("❌ Failed to load emojis. Exiting...")
        sys.exit(1)
    
    logger.info("✅ Emojis loaded successfully")
    
    # Create application
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("✅ Application built successfully")
    except Exception as e:
        logger.error(f"❌ Failed to build application: {e}")
        sys.exit(1)
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ads", ads_command))
    application.add_handler(CommandHandler("myemojis", myemojis_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("addemoji", addemoji_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ All handlers registered")
    logger.info("🤖 Bot is ready and polling for updates...")
    
    # Start polling
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Bot polling error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
