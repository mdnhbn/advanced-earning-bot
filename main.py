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
    # ডাটাবেস এবং টেবিল তৈরি করা (যদি না থাকে)
    print("ডাটাবেস ইনিশিয়ালাইজ করা হচ্ছে...")
    initialize_database()
    
    # বটের ডিফল্ট সেটিংস ডাটাবেসে যোগ করা (যদি না থাকে)
    print("বটের ডিফল্ট সেটিংস লোড করা হচ্ছে...")
    initialize_bot_settings()
    print("প্রাথমিক সেটআপ সম্পন্ন।")
    
    
    # --- ধাপ ২: টেলিগ্রাম বট অ্যাপ্লিকেশন তৈরি ---
    print("টেলিগ্রাম অ্যাপ্লিকেশন তৈরি করা হচ্ছে...")
    application = Application.builder().token(BOT_TOKEN).build()


    # --- ধাপ ৩: হ্যান্ডলার রেজিস্টার করা ---
    # এডমিন প্যানেলের জন্য ConversationHandler তৈরি
    admin_conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_user_manage$')],
        states={
            admin_panel_handler.USER_ID_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.user_id_input_received)],
        },
        fallbacks=[CommandHandler('cancel', admin_panel_handler.cancel_conversation)],
        per_message=False
    )
    
    # সকল হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start_handler.start))
    application.add_handler(CommandHandler("admin", admin_panel_handler.admin_panel))
    
    # এডমিন প্যানেলের মূল বাটন ক্লিকের জন্য
    application.add_handler(CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_'))
    # ফিচার স্ট্যাটাস টগল করার জন্য
    application.add_handler(CallbackQueryHandler(admin_panel_handler.toggle_feature_status, pattern='^toggle_'))
    # চ্যানেল ভেরিফিকেশন বাটনের জন্য
    application.add_handler(CallbackQueryHandler(start_handler.verify_membership_callback, pattern='^verify_membership$'))
    
    # এডমিন কনভার্সেশন হ্যান্ডলার যোগ করুন
    application.add_handler(admin_conversation_handler)

    print("সকল হ্যান্ডলার সফলভাবে রেজিস্টার করা হয়েছে।")

    # --- ধাপ ৪: API সার্ভার এবং বট একসাথে চালানো ---
    # এটি একটি অ্যাডভান্সড কৌশল যা uvicorn এবং python-telegram-bot কে একসাথে চালায়।
    
    # uvicorn সার্ভার কনফিগার করুন
    config = uvicorn.Config(app=fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    # asyncio ব্যবহার করে উভয়কে একসাথে চালান
    # nest_asyncio.apply() # Google Colab বা Jupyter Notebook-এর জন্য প্রয়োজন হতে পারে
    
    async def run_concurrently():
        print("বট পোলিং এবং API সার্ভার একসাথে চালু হচ্ছে...")
        
        # বটকে ব্যাকগ্রাউন্ডে চালানোর জন্য একটি টাস্ক তৈরি করুন
        bot_task = asyncio.create_task(application.run_polling())
        
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
