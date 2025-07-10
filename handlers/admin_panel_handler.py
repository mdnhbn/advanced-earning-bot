# advanced_earning_bot/handlers/admin_panel_handler.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS
from modules import user_manager, bot_settings

"""
এই ফাইলটি এডমিন প্যানেলের সমস্ত কার্যকারিতা পরিচালনা করে।
শুধুমাত্র ADMIN_IDS-এ থাকা ব্যবহারকারীরা এটি ব্যবহার করতে পারবে।
"""

# ConversationHandler এর জন্য স্টেট
SETTING_VALUE, USER_ID_INPUT = range(2)


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
        [InlineKeyboardButton("👤 ব্যবহারকারী ম্যানেজমেন্ট", callback_data="admin_user_manage")],
        [InlineKeyboardButton("📢 বিজ্ঞাপন ম্যানেজমেন্ট", callback_data="admin_ad_manage")],
        [InlineKeyboardButton("❌ প্যানেল বন্ধ করুন", callback_data="admin_close")]
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
    
    # query.data থেকে বোঝা যাবে কোন বাটনে ক্লিক করা হয়েছে
    data = query.data

    if data == "admin_main_menu":
        await query.edit_message_text("👋 এডমিন প্যানেলে স্বাগতম!", reply_markup=build_admin_menu())
    
    elif data == "admin_stats":
        # TODO: পরিসংখ্যান দেখানোর কোড এখানে লেখা হবে।
        await query.edit_message_text("📊 পরিসংখ্যান (শীঘ্রই আসছে...)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]]))
    
    elif data == "admin_global_settings":
        await show_global_settings(query)

    elif data == "admin_feature_control":
        await show_feature_control(query)
        
    elif data == "admin_user_manage":
        text = "👤 ব্যবহারকারী ম্যানেজমেন্ট\n\nঅনুগ্রহ করে ব্যবহারকারীর আইডি দিন:"
        await query.edit_message_text(text)
        return USER_ID_INPUT # ConversationHandler এর পরবর্তী ধাপে যান

    elif data == "admin_ad_manage":
        # TODO: বিজ্ঞাপন ম্যানেজমেন্টের কোড এখানে লেখা হবে।
        await query.edit_message_text("📢 বিজ্ঞাপন ম্যানেজমেন্ট (শীঘ্রই আসছে...)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]]))

    elif data == "admin_close":
        await query.edit_message_text("প্যানেল বন্ধ করা হয়েছে।")
        await query.message.delete()


async def show_global_settings(query):
    """গ্লোবাল সেটিংস মেনু দেখায়।"""
    text = "⚙️ গ্লোবাল সেটিংস\n\nএখান থেকে আপনি বটের মূল নিয়মাবলী পরিবর্তন করতে পারবেন।"
    # TODO: সেটিংস পরিবর্তনের জন্য বাটন তৈরি করতে হবে।
    keyboard = [
        [InlineKeyboardButton("🚨 গ্লোবাল মেইনটেন্যান্স", callback_data="toggle_maintenance_global")],
        # ... অন্যান্য সেটিংস ...
        [InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_feature_control(query):
    """ফিচার কন্ট্রোল মেনু দেখায়।"""
    text = "🔧 ফিচার কন্ট্রোল\n\nএখান থেকে নির্দিষ্ট ফিচার চালু বা বন্ধ করতে পারবেন।"
    
    # ডাটাবেস থেকে বর্তমান স্ট্যাটাস নিয়ে বাটন তৈরি করুন
    settings_to_show = {
        'feature_ads_view': '👁️ বিজ্ঞাপন দেখা',
        'feature_deposit': '💰 ডিপোজিট',
        'feature_withdrawal': '💸 উইথড্র',
        'feature_balance_transfer': '🔁 ব্যালেন্স ট্রান্সফার'
    }
    
    buttons = []
    for setting_name, button_text in settings_to_show.items():
        _, is_active = bot_settings.get_setting(setting_name)
        status_icon = "✅" if is_active else "❌"
        buttons.append([InlineKeyboardButton(f"{button_text} {status_icon}", callback_data=f"toggle_{setting_name}")])
    
    buttons.append([InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def toggle_feature_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """যেকোনো ফিচারের স্ট্যাটাস পরিবর্তন করে (on/off)।"""
    query = update.callback_query
    await query.answer()
    
    # 'toggle_feature_ads_view' থেকে 'feature_ads_view' বের করা
    setting_name = query.data.replace("toggle_", "")
    
    _, current_status = bot_settings.get_setting(setting_name)
    new_status = not current_status
    
    bot_settings.update_setting(setting_name, new_status=new_status)
    
    # মেনুটি আবার দেখান, যাতে আপডেট হওয়া স্ট্যাটাস দেখা যায়
    await show_feature_control(query)


# --- Conversation Handlers for input ---
async def user_id_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ব্যবহারকারীর আইডি ইনপুট নেয় এবং তার প্রোফাইল দেখায়।"""
    try:
        user_id = int(update.message.text)
        user_data = user_manager.get_user_by_id(user_id)
        if not user_data:
            await update.message.reply_text("এই আইডির কোনো ব্যবহারকারী খুঁজে পাওয়া যায়নি।")
            return ConversationHandler.END

        # TODO: ব্যবহারকারীর তথ্য এবং ম্যানেজ করার বাটন (ব্যান, ব্যালেন্স পরিবর্তন) দেখানোর কোড।
        await update.message.reply_text(f"ব্যবহারকারীর তথ্য: \n{user_data}")
        # ...

    except ValueError:
        await update.message.reply_text("অনুগ্রহ করে একটি সঠিক নিউমেরিক আইডি দিন।")
    
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """যেকোনো কনভার্সেশন বাতিল করে।"""
    await update.message.reply_text("অপারেশন বাতিল করা হয়েছে।")
    return ConversationHandler.END
