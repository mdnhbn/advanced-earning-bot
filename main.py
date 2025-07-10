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
    
    # --- ধাপ ১: প্রাথমিক সেটআপ ---
    print("ডাটাবেস ইনিশিয়ালাইজ করা হচ্ছে...")
    initialize_database()
    
    print("বটের ডিফল্ট সেটিংস লোড করা হচ্ছে...")
    initialize_bot_settings()
    print("প্রাথমিক সেটআপ সম্পন্ন।")
    
    
    # --- ধাপ ২: টেলিগ্রাম বট অ্যাপ্লিকেশন তৈরি ---
    print("টেলিগ্রাম অ্যাপ্লিকেশন তৈরি করা হচ্ছে...")
    application = Application.builder().token(BOT_TOKEN).build()


    # --- ধাপ ৩: হ্যান্ডলার রেজিস্টার করা ---
    
    # এডমিন প্যানেলের জন্য ConversationHandler সেটআপ
    # এটি ব্যবহারকারী থেকে ইনপুট নেওয়ার প্রক্রিয়া পরিচালনা করে (যেমন আইডি বা ব্যালেন্স)
    admin_conversation_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_panel_handler.user_manage_start, pattern='^admin_user_manage_start$'),
            CallbackQueryHandler(admin_panel_handler.user_manage_actions, pattern='^user_(add|deduct)_balance_')
        ],
        states={
            admin_panel_handler.USER_ID_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.user_id_input_received)],
            admin_panel_handler.BALANCE_CHANGE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.balance_change_input_received)],
        },
        fallbacks=[
            CommandHandler('cancel', admin_panel_handler.cancel_conversation),
            CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_main_menu$') # মেনুতে ফিরে যাওয়ার অপশন
        ],
        map_to_parent={
            # যদি কনভার্সেশন শেষ হয়, তাহলে মূলCallbackQueryHandler কাজ করবে
            ConversationHandler.END: 0,
        },
        per_message=False,
        allow_reentry=True
    )

    # মূল হ্যান্ডলার গ্রুপ তৈরি করা হচ্ছে
    # গ্রুপ 0 তে প্রধান হ্যান্ডলারগুলো থাকবে
    # গ্রুপ 1 তে কনভার্সেশন হ্যান্ডলার থাকবে
    
    # Start এবং Admin কমান্ড
    application.add_handler(CommandHandler("start", start_handler.start), group=0)
    application.add_handler(CommandHandler("admin", admin_panel_handler.admin_panel), group=0)
    
    # সকল বাটন ক্লিকের জন্য CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(start_handler.verify_membership_callback, pattern='^verify_membership$'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_(stats|global_settings|feature_control|ad_manage|close|main_menu)$'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.toggle_feature_status, pattern='^toggle_'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.ad_review_action, pattern='^ad_(approve|reject)_'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.user_manage_actions, pattern='^user_toggle_ban_'), group=0)

    # কনভার্সেশন হ্যান্ডলারটিকে একটি আলাদা গ্রুপে যোগ করা হচ্ছে
    application.add_handler(admin_conversation_handler, group=1)

    print("সকল হ্যান্ডলার সফলভাবে রেজিস্টার করা হয়েছে।")

    # --- ধাপ ৪: API সার্ভার এবং বট একসাথে চালানো ---
    # uvicorn সার্ভার কনফিগার করুন
    config = uvicorn.Config(app=fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    async def run_concurrently():
        print("বট পোলিং এবং API সার্ভার একসাথে চালু হচ্ছে...")
        
        # বটকে ব্যাকগ্রাউন্ডে চালানোর জন্য একটি টাস্ক তৈরি করুন
        # drop_pending_updates=True দিলে বট রিস্টার্ট হলে পুরোনো মেসেজ ইগনোর করবে
        bot_task = asyncio.create_task(application.run_polling(drop_pending_updates=True))
        
        # API সার্ভারকে মেইন থ্রেডে চালান
        server_task = asyncio.create_task(server.serve())
        
        await asyncio.gather(bot_task, server_task)

    # ইভেন্ট লুপ রান করুন
    try:
        asyncio.run(run_concurrently())
    except (KeyboardInterrupt, SystemExit):
        print("বট এবং সার্ভার বন্ধ করা হচ্ছে।")

if __name__ == "__main__":
    main()
