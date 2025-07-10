# advanced_earning_bot/handlers/admin_panel_handler.py

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS
from modules import user_manager, bot_settings, ad_manager

# ConversationHandler এর জন্য স্টেট
USER_ID_INPUT, BALANCE_CHANGE_INPUT, SETTING_VALUE_INPUT, ADD_AD_CONTENT, ADD_AD_TARGET_VIEWS, ADD_AD_DURATION = range(6)


# --- Helper Functions ---
async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def build_admin_menu():
    pending_ads_count = len(ad_manager.get_pending_ads())
    ad_manage_text = f"📢 বিজ্ঞাপন ম্যানেজমেন্ট ({pending_ads_count})" if pending_ads_count > 0 else "📢 বিজ্ঞাপন ম্যানেজমেন্ট"
    keyboard = [
        [InlineKeyboardButton("📊 পরিসংখ্যান", callback_data="admin_stats")],
        [InlineKeyboardButton("⚙️ গ্লোবাল সেটিংস", callback_data="admin_global_settings")],
        [InlineKeyboardButton("🔧 ফিচার কন্ট্রোল", callback_data="admin_feature_control")],
        [InlineKeyboardButton("👤 ব্যবহারকারী ম্যানেজমেন্ট", callback_data="admin_user_manage_start")],
        [InlineKeyboardButton(ad_manage_text, callback_data="admin_ad_manage_menu")],
        [InlineKeyboardButton("❌ প্যানেল বন্ধ করুন", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_user_manage_menu(user_id, is_banned=False):
    ban_text = "✅ আনব্যান করুন" if is_banned else "🚫 ব্যান করুন"
    keyboard = [
        [InlineKeyboardButton("💰 ব্যালেন্স যোগ", callback_data=f"user_add_balance_{user_id}"),
         InlineKeyboardButton("💸 ব্যালেন্স কাটুন", callback_data=f"user_deduct_balance_{user_id}")],
        [InlineKeyboardButton(ban_text, callback_data=f"user_toggle_ban_{user_id}")],
        [InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_ad_manage_menu():
    keyboard = [
        [InlineKeyboardButton("👀 পেন্ডিং বিজ্ঞাপন দেখুন", callback_data="admin_ad_pending_list")],
        [InlineKeyboardButton("➕ নতুন বিজ্ঞাপন যোগ করুন", callback_data="admin_ad_add_new")],
        [InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Main Command & Callback Handlers ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("দুঃখিত, এই কমান্ডটি শুধুমাত্র এডমিনদের জন্য।")
        return
    text = "👋 এডমিন প্যানেলে স্বাগতম! অনুগ্রহ করে একটি অপশন বেছে নিন:"
    reply_markup = build_admin_menu()
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not await is_admin(user_id):
        await query.edit_message_text("দুঃখিত, আপনি এডমিন নন।")
        return
    
    data = query.data
    if data == "admin_main_menu":
        await admin_panel(update, context)
    elif data == "admin_stats":
        await show_stats(query)
    elif data == "admin_global_settings":
        await show_global_settings(query)
    elif data == "admin_feature_control":
        await show_feature_control(query)
    elif data == "admin_ad_manage_menu":
        await show_ad_manage_menu(query)
    elif data == "admin_ad_pending_list":
        await show_pending_ads(query)
    elif data == "admin_close":
        await query.edit_message_text("প্যানেল বন্ধ করা হয়েছে।")

async def show_stats(query):
    stats_result = user_manager.get_bot_statistics()
    if stats_result['success']:
        stats = stats_result['data']
        text = (f"📊 **বটের বর্তমান পরিসংখ্যান**\n\n"
                f"👤 মোট ব্যবহারকারী: `{stats['total_users']}`\n"
                f"✅ ভেরিফাইড ব্যবহারকারী: `{stats['verified_users']}`\n"
                f"🚫 ব্যানড ব্যবহারকারী: `{stats['banned_users']}`\n\n"
                f"_(এই তথ্য রিয়েল-টাইমে আপডেট হয়।)_")
    else:
        text = f"দুঃখিত, পরিসংখ্যান লোড করতে একটি সমস্যা হয়েছে:\n`{stats_result['message']}`"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")]])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_global_settings(query: Update):
    settings_to_display = {
        'daily_bonus_amount': '💰 দৈনিক বোনাস',
        'transfer_fee_percent': '💸 ট্রান্সফার ফি (%)',
        'blogger_page_url': '🌐 ব্লগার URL',
        'withdrawal_mode': '🤖 উইথড্র মোড',
        'min_auto_withdraw_amount': '➖ সর্বনিম্ন উইথড্র'
    }
    text = "⚙️ **গ্লোবাল সেটিংস**\n\n"
    buttons = []
    for key, name in settings_to_display.items():
        value, _ = bot_settings.get_setting(key)
        text += f"**{name}:** `{value if value else 'সেট করা হয়নি'}`\n"
        buttons.append([InlineKeyboardButton(f"✏️ {name} পরিবর্তন", callback_data=f"edit_setting_{key}")])
    buttons.append([InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='Markdown')

async def edit_setting_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    setting_key = query.data.replace("edit_setting_", "")
    context.user_data['setting_to_edit'] = setting_key
    current_value, _ = bot_settings.get_setting(setting_key)
    text = f"আপনি `{setting_key}` পরিবর্তন করছেন।\nবর্তমান মান: `{current_value}`\n\nঅনুগ্রহ করে নতুন মান দিন:"
    context.user_data['last_admin_message'] = await query.edit_message_text(text, parse_mode='Markdown')
    return SETTING_VALUE_INPUT

async def setting_value_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_value = update.message.text
    await update.message.delete()
    setting_key = context.user_data.get('setting_to_edit')
    if not setting_key: return ConversationHandler.END
    bot_settings.update_setting(setting_key, new_value=new_value)
    del context.user_data['setting_to_edit']
    await context.user_data['last_admin_message'].edit_text(f"`{setting_key}`-এর মান সফলভাবে পরিবর্তন করা হয়েছে।")
    await asyncio.sleep(2)
    await show_global_settings(context.user_data['last_admin_message'])
    return ConversationHandler.END

async def show_feature_control(query):
    text = "🔧 ফিচার কন্ট্রোল"
    settings_to_show = {'feature_ads_view': '👁️ বিজ্ঞাপন দেখা', 'feature_deposit': '💰 ডিপোজিট', 'feature_withdrawal': '💸 উইথড্র', 'feature_balance_transfer': '🔁 ব্যালেন্স ট্রান্সফার'}
    buttons = []
    for setting_name, button_text in settings_to_show.items():
        _, is_active = bot_settings.get_setting(setting_name)
        status_icon = "✅" if is_active else "❌"
        buttons.append([InlineKeyboardButton(f"{button_text} {status_icon}", callback_data=f"toggle_{setting_name}")])
    buttons.append([InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_main_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def toggle_feature_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    setting_name = query.data.replace("toggle_", "")
    _, current_status = bot_settings.get_setting(setting_name)
    bot_settings.update_setting(setting_name, new_status=not current_status)
    await show_feature_control(query)

async def show_ad_manage_menu(query: Update):
    text = "📢 **বিজ্ঞাপন ম্যানেজমেন্ট**"
    await query.edit_message_text(text, reply_markup=build_ad_manage_menu())

async def show_pending_ads(query: Update):
    pending_ads = ad_manager.get_pending_ads()
    if not pending_ads:
        text = " পর্যালোচনার জন্য কোনো নতুন বিজ্ঞাপন নেই।"
        keyboard = [[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_ad_manage_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    ad_data = pending_ads[0]
    columns = ['ad_id', 'owner_user_id', 'ad_source', 'ad_type', 'ad_content', 'status', 'target_views', 'current_views', 'view_duration_seconds', 'viewed_by_users']
    ad_dict = dict(zip(columns, ad_data))
    text = (f"**📢 নতুন বিজ্ঞাপন রিভিউ**\n\nAd ID: `{ad_dict['ad_id']}`\nজমা দিয়েছে: `{ad_dict['owner_user_id']}`\n"
            f"কন্টেন্ট: `{ad_dict['ad_content']}`\nটার্গেট ভিউ: `{ad_dict['target_views']}`")
    keyboard = [[InlineKeyboardButton("✅ অনুমোদন", callback_data=f"ad_approve_{ad_dict['ad_id']}"),
                 InlineKeyboardButton("❌ প্রত্যাখ্যান", callback_data=f"ad_reject_{ad_dict['ad_id']}")],
                [InlineKeyboardButton("➡️ পরবর্তী", callback_data="admin_ad_pending_list")],
                [InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_ad_manage_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def ad_review_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    action, ad_id = data[1], int(data[2])
    if action == "approve":
        ad_manager.update_ad_status(ad_id, "approved")
        await query.answer("বিজ্ঞাপনটি অনুমোদন করা হয়েছে!", show_alert=True)
    elif action == "reject":
        ad_manager.update_ad_status(ad_id, "rejected")
        await query.answer("বিজ্ঞাপনটি প্রত্যাখ্যান করা হয়েছে।", show_alert=True)
    await show_pending_ads(query)

async def add_new_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("ভিডিও (ব্লগার)", callback_data="add_ad_type_video_embed")],
                [InlineKeyboardButton("ডিরেক্ট লিঙ্ক", callback_data="add_ad_type_direct_link_ad")],
                [InlineKeyboardButton("⬅️ ফিরে যান", callback_data="admin_ad_manage_menu")]]
    text = "➕ **নতুন বিজ্ঞাপন যোগ করুন**\n\nআপনি কোন ধরনের বিজ্ঞাপন যোগ করতে চান?"
    context.user_data['last_admin_message'] = await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_AD_CONTENT

async def add_ad_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ad_type = query.data.replace("add_ad_type_", "")
    context.user_data['new_ad_type'] = ad_type
    await query.edit_message_text(f"আপনি `{ad_type}` নির্বাচন করেছেন।\n\nঅনুগ্রহ করে বিজ্ঞাপনের কন্টেন্ট (URL) দিন:")
    return ADD_AD_CONTENT

async def add_ad_content_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_ad_content'] = update.message.text
    await update.message.delete()
    await context.user_data['last_admin_message'].edit_text("টার্গেট ভিউ সংখ্যা দিন (যেমন: 1000):")
    return ADD_AD_TARGET_VIEWS

async def add_ad_target_views_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['new_ad_target_views'] = int(update.message.text)
        await update.message.delete()
        await context.user_data['last_admin_message'].edit_text("বিজ্ঞাপনটি কত সেকেন্ড দেখাতে চান (যেমন: 30):")
        return ADD_AD_DURATION
    except ValueError:
        await context.user_data['last_admin_message'].edit_text("সঠিক সংখ্যা দিন। আবার চেষ্টা করুন:")
        return ADD_AD_TARGET_VIEWS

async def add_ad_duration_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['new_ad_duration'] = int(update.message.text)
        await update.message.delete()
        
        ad_id = ad_manager.submit_ad_by_user(
            user_id=update.effective_user.id,
            ad_source='admin_added',
            ad_type=context.user_data['new_ad_type'],
            ad_content=context.user_data['new_ad_content'],
            target_views=context.user_data['new_ad_target_views'],
            duration=context.user_data['new_ad_duration']
        )
        if ad_id:
            ad_manager.update_ad_status(ad_id, 'approved')
            await context.user_data['last_admin_message'].edit_text("✅ বিজ্ঞাপনটি সফলভাবে যোগ এবং সক্রিয় করা হয়েছে।")
        else:
            await context.user_data['last_admin_message'].edit_text("❌ বিজ্ঞাপন যোগ করতে সমস্যা হয়েছে।")
            
        context.user_data.clear()
        await asyncio.sleep(2)
        await admin_panel(update, context)
        return ConversationHandler.END
    except ValueError:
        await context.user_data['last_admin_message'].edit_text("সঠিক সংখ্যা দিন। আবার চেষ্টা করুন:")
        return ADD_AD_DURATION

async def user_manage_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "👤 **ব্যবহারকারী ম্যানেজমেন্ট**\n\nঅনুগ্রহ করে যে ব্যবহারকারীকে ম্যানেজ করতে চান তার টেলিগ্রাম আইডি দিন:"
    context.user_data['last_admin_message'] = await query.edit_message_text(text)
    return USER_ID_INPUT

async def user_id_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        target_user_id = int(update.message.text)
        await update.message.delete()
        user_data = user_manager.get_user_by_id(target_user_id)
        if not user_data:
            await context.user_data['last_admin_message'].edit_text("এই আইডির কোনো ব্যবহারকারী খুঁজে পাওয়া যায়নি।")
            return USER_ID_INPUT
        context.user_data['target_user_id'] = target_user_id
        await show_user_profile(context.user_data['last_admin_message'], user_data)
    except (ValueError, KeyError):
        return USER_ID_INPUT
    return ConversationHandler.END

async def show_user_profile(message, user_data):
    user_id = user_data['user_id']
    text = (f"👤 **ব্যবহারকারীর প্রোফাইল**\n\nID: `{user_id}`\nUsername: @{user_data.get('username', 'N/A')}\n"
            f"ব্যালেন্স: `{user_data['balance']}`\nভেরিফাইড: `{'হ্যাঁ' if user_data['is_verified'] else 'না'}`\n"
            f"ব্যানড: `{'হ্যাঁ' if user_data['is_banned'] else 'না'}`\nওয়ার্নিং: `{user_data['warning_count']}`")
    keyboard = build_user_manage_menu(user_id, user_data['is_banned'])
    await message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def user_manage_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action, target_user_id = data[1], int(data[-1])
    if action == "toggle" and data[2] == "ban":
        user_data = user_manager.get_user_by_id(target_user_id)
        new_ban_status = not user_data['is_banned']
        user_manager.set_ban_status(target_user_id, new_ban_status)
        await query.answer(f"ব্যবহারকারীকে {'ব্যান' if new_ban_status else 'আনব্যান'} করা হয়েছে।", show_alert=True)
        updated_user_data = user_manager.get_user_by_id(target_user_id)
        await show_user_profile(query.message, updated_user_data)
    elif action in ["add", "deduct"]:
        context.user_data['target_user_id'] = target_user_id
        context.user_data['balance_action'] = action
        action_text = "যোগ" if action == "add" else "কাটতে"
        context.user_data['last_admin_message'] = await query.edit_message_text(f"আপনি কত পয়েন্ট {action_text} চান?")
        return BALANCE_CHANGE_INPUT
    return ConversationHandler.END

async def balance_change_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = int(update.message.text)
        await update.message.delete()
        if amount <= 0: return ConversationHandler.END
        target_user_id = context.user_data['target_user_id']
        action = context.user_data['balance_action']
        amount_to_change = amount if action == "add" else -amount
        user_manager.update_balance(target_user_id, amount_to_change)
        user_data = user_manager.get_user_by_id(target_user_id)
        await show_user_profile(context.user_data['last_admin_message'], user_data)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"সফলভাবে {amount} পয়েন্ট {'যোগ' if action == 'add' else 'কাটা'} হয়েছে।")
    except (ValueError, KeyError): pass
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("অপারেশন বাতিল করা হয়েছে।")
    await admin_panel(update, context)
    return ConversationHandler.END
