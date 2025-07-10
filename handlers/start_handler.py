# advanced_earning_bot/handlers/start_handler.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import json

# আমাদের মডিউলগুলো ইম্পোর্ট করুন
from modules import user_manager, bot_settings

"""
এই ফাইলটি /start কমান্ড এবং নতুন ব্যবহারকারীর অনবোর্ডিং প্রক্রিয়া পরিচালনা করে।
চ্যানেল জয়েন ভেরিফিকেশন এবং মিনি অ্যাপ লঞ্চার বাটন দেখানো এর প্রধান কাজ।
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start কমান্ড হ্যান্ডেল করে।"""
    user = update.effective_user
    user_id = user.id
    
    # রেফারেল আইডি চেক করুন (যদি থাকে)
    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id == user_id: # নিজেকে রেফার করা যাবে না
                referrer_id = None
        except (ValueError, IndexError):
            referrer_id = None

    # ব্যবহারকারীকে ডাটাবেসে যোগ বা খুঁজে বের করুন
    user_data = user_manager.add_or_get_user(user_id, user.username, referrer_id)

    if not user_data:
        await update.message.reply_text("দুঃখিত, আপনার প্রোফাইল তৈরি করতে একটি সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।")
        return

    # চ্যানেল ভেরিফিকেশন চেক করুন
    is_verified = await check_channel_membership(update, context)
    
    if is_verified:
        # যদি ভেরিফাইড হয়, সরাসরি অ্যাপ লঞ্চার বাটন দেখান
        await send_welcome_and_launch_button(update)
    else:
        # যদি ভেরিফাইড না হয়, চ্যানেল জয়েন করার জন্য অনুরোধ করুন
        await send_join_channel_message(update)


async def send_join_channel_message(update: Update) -> None:
    """চ্যানেলে জয়েন করার জন্য মেসেজ এবং বাটন পাঠায়।"""
    required_channels_str, _ = bot_settings.get_setting('required_channels')
    
    try:
        channels = json.loads(required_channels_str)
    except json.JSONDecodeError:
        channels = []

    if not channels:
        # যদি কোনো চ্যানেল সেট করা না থাকে, সরাসরি ওয়েলকাম মেসেজ দেখান
        await send_welcome_and_launch_button(update)
        return

    buttons = []
    for i, channel in enumerate(channels, 1):
        buttons.append([InlineKeyboardButton(f"📢 চ্যানেল {i} এ যোগ দিন", url=f"https://t.me/{channel.lstrip('@')}")])
    
    buttons.append([InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="verify_membership")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    welcome_msg, _ = bot_settings.get_setting('welcome_message')
    
    text = (
        f"{welcome_msg}\n\n"
        "বটটি ব্যবহার করার জন্য, অনুগ্রহ করে আমাদের পার্টনার চ্যানেলগুলোতে যোগ দিন এবং তারপর 'ভেরিফাই করুন' বাটনে ক্লিক করুন।"
    )
    
    await update.message.reply_photo(
        photo='https://i.imgur.com/your-image-url.jpg', # আপনার ওয়েলকাম ইমেজ URL এখানে দিন
        caption=text,
        reply_markup=keyboard
    )


async def send_welcome_and_launch_button(update: Update) -> None:
    """ভেরিফিকেশন সফল হলে ওয়েলকাম মেসেজ এবং অ্যাপ লঞ্চার বাটন পাঠায়।"""
    # এখানে মিনি অ্যাপের URL সেট করতে হবে। Replit-এ রান করার পর URLটি পাওয়া যাবে।
    # আপাতত একটি প্লেসহোল্ডার URL ব্যবহার করা হচ্ছে।
    MINI_APP_URL = "https://your-repl-name.replit.dev/mini_app/index.html"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 অ্যাপে প্রবেশ করুন", web_app=WebAppInfo(url=MINI_APP_URL))]
    ])
    
    await update.message.reply_text(
        "আপনাকে স্বাগতম! নিচের বাটনে ক্লিক করে অ্যাপে প্রবেশ করুন এবং আয় শুরু করুন।",
        reply_markup=keyboard
    )
    # ব্যবহারকারীর ভেরিফিকেশন স্ট্যাটাস ডাটাবেসে আপডেট করুন
    user_manager.set_user_verified(update.effective_user.id, status=True)


async def verify_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'ভেরিফাই করুন' বাটনের ক্লিক হ্যান্ডেল করে।"""
    query = update.callback_query
    await query.answer("আপনার মেম্বারশিপ চেক করা হচ্ছে...")

    is_verified = await check_channel_membership(update, context)

    if is_verified:
        await query.message.delete() # চ্যানেল জয়েন মেসেজটি ডিলিট করে দিন
        await send_welcome_and_launch_button(query)
    else:
        await query.answer("আপনি এখনও সব প্রয়োজনীয় চ্যানেলে যোগ দেননি।", show_alert=True)


async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ব্যবহারকারী সব প্রয়োজনীয় চ্যানেলে যোগ দিয়েছে কিনা তা চেক করে।"""
    user_id = update.effective_user.id
    required_channels_str, _ = bot_settings.get_setting('required_channels')
    
    try:
        channels = json.loads(required_channels_str)
    except json.JSONDecodeError:
        channels = []

    if not channels:
        return True # কোনো চ্যানেল সেট করা না থাকলে সবসময় ভেরিফাইড

    for channel_username in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=f"@{channel_username.lstrip('@')}", user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False # যদি কোনো একটি চ্যানেলেও মেম্বার না থাকে
        except Exception as e:
            print(f"চ্যানেল @{channel_username} চেক করতে সমস্যা: {e}")
            # যদি বট চ্যানেলের এডমিন না থাকে বা চ্যানেলটি প্রাইভেট হয়, তাহলে ত্রুটি হতে পারে।
            # এক্ষেত্রে, আমরা ধরে নিচ্ছি ব্যবহারকারী জয়েন করেনি।
            return False
            
    return True
