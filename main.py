# advanced_earning_bot/main.py

import asyncio
import uvicorn
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# আমাদের মডিউল এবং হ্যান্ডলারগুলো ইম্পোর্ট করুন
from config import BOT_TOKEN
from database import initialize_database
from modules.bot_settings import initialize_bot_settings
from api.routes import app as fastapi_app
from handlers import start_handler, admin_panel_handler

"""
এটি প্রজেক্টের মূল চালিকাশক্তি।
এই ফাইলটি টেলিগ্রাম বট এবং API সার্ভার উভয়ই একসাথে চালু করে।
"""

def main() -> None:
    """মূল ফাংশন যা বট সেটআপ এবং চালু করে।"""
    
    print("ডাটাবেস ইনিশিয়ালাইজ করা হচ্ছে...")
    initialize_database()
    
    print("বটের ডিফল্ট সেটিংস লোড করা হচ্ছে...")
    initialize_bot_settings()
    print("প্রাথমিক সেটআপ সম্পন্ন।")
    
    print("টেলিগ্রাম অ্যাপ্লিকেশন তৈরি করা হচ্ছে...")
    application = Application.builder().token(BOT_TOKEN).build()

    # --- এডমিন প্যানেলের জন্য ConversationHandler সেটআপ ---
    user_management_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_panel_handler.user_manage_start, pattern='^admin_user_manage_start$')],
        states={
            admin_panel_handler.USER_ID_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.user_id_input_received)],
            admin_panel_handler.BALANCE_CHANGE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.balance_change_input_received)],
        },
        fallbacks=[CommandHandler('cancel', admin_panel_handler.cancel_conversation)],
        per_message=False,
        allow_reentry=True
    )
    
    # --- সকল হ্যান্ডলার যোগ করুন ---
    application.add_handler(CommandHandler("start", start_handler.start))
    application.add_handler(CommandHandler("admin", admin_panel_handler.admin_panel))
    
    # এডমিন কনভার্সেশন হ্যান্ডলার
    application.add_handler(user_management_conv)
    
    # প্রধান এডমিন বাটন ক্লিকের জন্য
    application.add_handler(CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_(stats|global_settings|feature_control|ad_manage|close|main_menu)$'))
    # ফিচার স্ট্যাটাস টগল করার জন্য
    application.add_handler(CallbackQueryHandler(admin_panel_handler.toggle_feature_status, pattern='^toggle_'))
    # বিজ্ঞাপন রিভিউ বাটনের জন্য
    application.add_handler(CallbackQueryHandler(admin_panel_handler.ad_review_action, pattern='^ad_(approve|reject)_'))
    # ব্যবহারকারী ম্যানেজমেন্ট অ্যাকশন বাটনের জন্য
    application.add_handler(CallbackQueryHandler(admin_panel_handler.user_manage_actions, pattern='^user_'))

    # চ্যানেল ভেরিফিকেশন বাটনের জন্য
    application.add_handler(CallbackQueryHandler(start_handler.verify_membership_callback, pattern='^verify_membership$'))
    
    print("সকল হ্যান্ডলার সফলভাবে রেজিস্টার করা হয়েছে।")

    # --- API সার্ভার এবং বট একসাথে চালানো ---
    config = uvicorn.Config(app=fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    async def run_concurrently():
        print("বট পোলিং এবং API সার্ভার একসাথে চালু হচ্ছে...")
        bot_task = asyncio.create_task(application.run_polling(drop_pending_updates=True))
        server_task = asyncio.create_task(server.serve())
        await asyncio.gather(bot_task, server_task)

    try:
        asyncio.run(run_concurrently())
    except (KeyboardInterrupt, SystemExit):
        print("বট এবং সার্ভার বন্ধ করা হচ্ছে।")

if __name__ == "__main__":
    main()
