# advanced_earning_bot/handlers/admin_panel_handler.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import ADMIN_IDS
from modules import user_manager, bot_settings

"""
এই ফাইলটি এডমিন প্যানেলের সমস্ত কার্যকারিতা পরিচালনা করে।
শুধুমাত্র ADMIN_IDS-এ থাকা ব্যবহারকারীরা এটি ব্যবহার করতে পারবে।
"""

# ConversationHandler এর জন্য স্টেট
USER_ID_INPUT, BALANCE_CHANGE_INPUT = range(2)


# --- Helper Functions ---
async def is_admin(user_id: int) -> bool:
    """ব্যবহারকারী এডমিন কিনা তা চেক করে।"""
    return user_id in ADMIN_IDS

def build_admin_menu():
    """মূল এডমিন প্যানেলের মেনু বাটন তৈরি করে।"""
    keyboard = [
        [InlineKeyboardButton("📊 পরিসংখ্যান", callback_data="admin_stats")],
        [InlineKeyboardButton("⚙️ গ্লোবাল সেটিংস", callback_data="admin_global_settings")],
        [InlineKeyboardButton("🔧 ফিচার কন্ট্রোল", callback_data="admin_feature_control")],
        [InlineKeyboardButton("👤 ব্যবহারকারী ম্যানেজমেন্ট", callback_data="admin_user_manage_start")],
        [InlineKeyboardButton("📢 বিজ্ঞাপন ম্যানেজমেন্ট", callback_data="admin_ad_manage")],
        [InlineKeyboardButton("❌ প্যানেল বন্ধ করুন", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_user_manage_menu(user_id, is_banned=False):
    """একজন নির্দিষ্ট ব্যবহারকারীকে ম্যানেজ করার জন্য বাটন তৈরি করে।"""
    ban_text = "✅ আনব্যান করুন" if is_banned else "🚫 ব্যান করুন"
    keyboard = [
        [
            InlineKeyboardButton("💰 ব্যালেন্স যোগ করুন", callback_data=f"user_add_balance_{user_id}"),
            InlineKeyboardButton("💸 ব্যালেন্স কাটুন", callback_data=f"user_deduct_balance_{user_id}")
        ],
        [
            InlineKeyboardButton(ban_text, callback_data=f"user_toggle_ban_{user_id}")
        ],
        [InlineKeyboardButton("⬅️ এডমিন মেনুতে ফিরে যান", callback_data="admin_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Main Command Handler ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/admin কমান্ড হ্যান্ডেল করে এবং মূল এডমিন প্যানেল দেখায়।"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("দুঃখিত, এই কমান্ডটি শুধুমাত্র এডমিনদের জন্য।")
        return

    text = "👋 এডমিন প্যানেলে স্বাগতম! অনুগ্রহ করে একটি অপশন বেছে নিন:"
    await update.message.reply_text(text, reply_markup=build_admin_menu())


# --- Callback Query Handlers ---
async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """এডমিন প্যানেলের সকল বাটন ক্লিক হ্যান্ডেল করে।"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not await is_admin(user_id):
        await query.edit_message_text("দুঃখিত, আপনি এডমিন নন।")
        return
    
    data = query.data

    if data == "admin_main_menu":
        await query.edit_message_text("👋 এডমিন প্যানেলে স্বাগতম!", reply_markup=build_admin_menu())
    
    elif data == "admin_stats":
        stats_result = user_manager.get_bot_statistics()
        if stats_result['success']:
            stats = stats_result['data']
            text = (
                f"📊 **বটের বর্তমান পরিসংখ্যান**\n\n"
                f"👤 মোট ব্যবহারকারী: `{stats['total_users']}`\n"
                f"✅ ভেরিফাইড ব্যবহারকারী: `{stats['verified_users']}`\n"
                f"🚫 ব্যানড ব্যবহারকারী: `{stats['banned_users']}`\n\n"
                f"_(এই তথ্য রিয়েল-টাইমে আপডেট হয়।)_"
            )
        else:
            text = f"দুঃখিত, পরিসংখ্যান লোড করতে একটি সমস্যা হয়েছে:\n`{stats_result['message']}`"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    elif data == "admin_global_settings":
        await show_global_settings(query)

    elif data == "admin_feature_control":
        await show_feature_control(query)
    
    elif data == "admin_ad_manage":
        await query.edit_message_text("📢 বিজ্ঞাপন ম্যানেজমেন্ট (শীঘ্রই আসছে...)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]]))

    elif data == "admin_close":
        await query.edit_message_text("প্যানেল বন্ধ করা হয়েছে।")


async def show_global_settings(query):
    text = "⚙️ গ্লোবাল সেটিংস\n\nএখান থেকে আপনি বটের মূল নিয়মাবলী পরিবর্তন করতে পারবেন।"
    keyboard = [[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_feature_control(query):
    text = "🔧 ফিচার কন্ট্রোল\n\nএখান থেকে নির্দিষ্ট ফিচার চালু বা বন্ধ করতে পারবেন।"
    settings_to_show = {'feature_ads_view': '👁️ বিজ্ঞাপন দেখা', 'feature_deposit': '💰 ডিপোজিট', 'feature_withdrawal': '💸 উইথড্র', 'feature_balance_transfer': '🔁 ব্যালেন্স ট্রান্সফার'}
    buttons = []
    for setting_name, button_text in settings_to_show.items():
        _, is_active = bot_settings.get_setting(setting_name)
        status_icon = "✅" if is_active else "❌"
        buttons.append([InlineKeyboardButton(f"{button_text} {status_icon}", callback_data=f"toggle_{setting_name}")])
    buttons.append([InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def toggle_feature_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    setting_name = query.data.replace("toggle_", "")
    _, current_status = bot_settings.get_setting(setting_name)
    new_status = not current_status
    bot_settings.update_setting(setting_name, new_status=new_status)
    await show_feature_control(query)


# --- User Management Conversation ---
async def user_manage_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "👤 **ব্যবহারকারী ম্যানেজমেন্ট**\n\nঅনুগ্রহ করে যে ব্যবহারকারীকে ম্যানেজ করতে চান তার টেলিগ্রাম আইডি দিন:"
    await query.edit_message_text(text)
    return USER_ID_INPUT

async def user_id_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        target_user_id = int(update.message.text)
        user_data = user_manager.get_user_by_id(target_user_id)
        if not user_data:
            await update.message.reply_text("এই আইডির কোনো ব্যবহারকারী খুঁজে পাওয়া যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন বা /cancel দিন।")
            return USER_ID_INPUT
        
        context.user_data['target_user_id'] = target_user_id
        await show_user_profile(update.message, user_data)
        
    except ValueError:
        await update.message.reply_text("এটি একটি সঠিক নিউমেরিক আইডি নয়। অনুগ্রহ করে আবার চেষ্টা করুন বা /cancel দিন।")
        return USER_ID_INPUT

    return ConversationHandler.END


async def show_user_profile(message, user_data):
    user_id = user_data['user_id']
    text = (
        f"👤 **ব্যবহারকারীর প্রোফাইল**\n\n"
        f"**ID:** `{user_id}`\n"
        f"**Username:** @{user_data['username']}\n"
        f"**ব্যালেন্স:** `{user_data['balance']}` পয়েন্ট\n"
        f"**ভেরিফাইড:** `{'হ্যাঁ' if user_data['is_verified'] else 'না'}`\n"
        f"**ব্যানড:** `{'হ্যাঁ' if user_data['is_banned'] else 'না'}`\n"
        f"**ওয়ার্নিং:** `{user_data['warning_count']}`\n"
    )
    keyboard = build_user_manage_menu(user_id, user_data['is_banned'])
    await message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')


async def user_manage_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[1]
    target_user_id = int(data[-1])

    if action == "toggle" and data[2] == "ban":
        user_data = user_manager.get_user_by_id(target_user_id)
        new_ban_status = not user_data['is_banned']
        user_manager.set_ban_status(target_user_id, new_ban_status)
        await query.answer(f"ব্যবহারকারীকে {'ব্যান' if new_ban_status else 'আনব্যান'} করা হয়েছে।", show_alert=True)
        
        # প্রোফাইল রিফ্রেশ করুন
        updated_user_data = user_manager.get_user_by_id(target_user_id)
        await show_user_profile(query.message, updated_user_data)
        
    elif action in ["add", "deduct"]:
        context.user_data['target_user_id'] = target_user_id
        context.user_data['balance_action'] = action
        action_text = "যোগ" if action == "add" else "কাটতে"
        await query.edit_message_text(f"আপনি কত পয়েন্ট {action_text} চান? অনুগ্রহ করে পরিমাণটি লিখুন:")
        return BALANCE_CHANGE_INPUT

    return ConversationHandler.END


async def balance_change_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = int(update.message.text)
        if amount <= 0:
            await update.message.reply_text("পরিমাণটি অবশ্যই একটি পজিটিভ সংখ্যা হতে হবে।")
            return ConversationHandler.END

        target_user_id = context.user_data['target_user_id']
        action = context.user_data['balance_action']
        
        amount_to_change = amount if action == "add" else -amount
        
        user_manager.update_balance(target_user_id, amount_to_change)
        
        await update.message.reply_text(f"সফলভাবে {amount} পয়েন্ট {'যোগ' if action == 'add' else 'কাটা'} হয়েছে।")
        
        # প্রোফাইল আবার দেখান
        user_data = user_manager.get_user_by_id(target_user_id)
        await show_user_profile(update.message, user_data)

    except (ValueError, KeyError):
        await update.message.reply_text("একটি সমস্যা হয়েছে বা সঠিক পরিমাণ দেওয়া হয়নি।")

    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """যেকোনো কনভার্সেশন বাতিল করে।"""
    if 'target_user_id' in context.user_data:
        del context.user_data['target_user_id']
    if 'balance_action' in context.user_data:
        del context.user_data['balance_action']
        
    await update.message.reply_text("অপারেশন বাতিল করা হয়েছে।")
    return ConversationHandler.END
