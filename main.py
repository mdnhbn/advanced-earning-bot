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

from config import BOT_TOKEN
from database import initialize_database
from modules.bot_settings import initialize_bot_settings
from api.routes import app as fastapi_app
from handlers import start_handler, admin_panel_handler

# main ফাংশনটিকে async হিসেবে ঘোষণা করতে হবে
async def main() -> None:
    print("ডাটাবেস ইনিশিয়ালাইজ করা হচ্ছে...")
    initialize_database()
    print("বটের ডিফল্ট সেটিংস লোড করা হচ্ছে...")
    initialize_bot_settings()
    print("প্রাথমিক সেটআপ সম্পন্ন।")
    
    print("টেলিগ্রাম অ্যাপ্লিকেশন তৈরি করা হচ্ছে...")
    application = Application.builder().token(BOT_TOKEN).build()

    # --- ConversationHandler সেটআপ (আপনার কোড অপরিবর্তিত) ---
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_panel_handler.user_manage_start, pattern='^admin_user_manage_start$'),
            CallbackQueryHandler(admin_panel_handler.user_manage_actions, pattern='^user_(add|deduct)_balance_'),
            CallbackQueryHandler(admin_panel_handler.edit_setting_start, pattern='^edit_setting_'),
            CallbackQueryHandler(admin_panel_handler.add_new_ad_start, pattern='^admin_ad_add_new$'),
            CallbackQueryHandler(admin_panel_handler.add_ad_type_selected, pattern='^add_ad_type_')
        ],
        states={
            admin_panel_handler.USER_ID_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.user_id_input_received)],
            admin_panel_handler.BALANCE_CHANGE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.balance_change_input_received)],
            admin_panel_handler.SETTING_VALUE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.setting_value_input_received)],
            admin_panel_handler.ADD_AD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.add_ad_content_received)],
            admin_panel_handler.ADD_AD_TARGET_VIEWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.add_ad_target_views_received)],
            admin_panel_handler.ADD_AD_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel_handler.add_ad_duration_received)],
        },
        fallbacks=[
            CommandHandler('cancel', admin_panel_handler.cancel_conversation),
            CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_main_menu$')
        ],
        map_to_parent={ConversationHandler.END: 0},
        per_message=False,
        allow_reentry=True
    )

    # --- হ্যান্ডলার রেজিস্ট্রেশন (আপনার কোড অপরিবর্তিত) ---
    application.add_handler(CommandHandler("start", start_handler.start), group=0)
    application.add_handler(CommandHandler("admin", admin_panel_handler.admin_panel), group=0)
    application.add_handler(conv_handler, group=1)
    
    application.add_handler(CallbackQueryHandler(start_handler.verify_membership_callback, pattern='^verify_membership$'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_(stats|global_settings|feature_control|close|main_menu|ad_manage_menu|ad_pending_list)$'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.toggle_feature_status, pattern='^toggle_'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.ad_review_action, pattern='^ad_(approve|reject)_'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.user_manage_actions, pattern='^user_toggle_ban_'), group=0)

    print("সকল হ্যান্ডলার সফলভাবে রেজিস্টার করা হয়েছে।")

    # --- সঠিক পদ্ধতিতে বট এবং সার্ভার চালানো ---
    config = uvicorn.Config(app=fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # `async with` ব্যবহার করলে application.initialize() এবং application.shutdown() নিজে থেকেই সঠিকভাবে কল হবে
    async with application:
        print("বট এবং API সার্ভার চালু করা হচ্ছে...")
        await application.start()  # বটকে ব্যাকগ্রাউন্ডে পোলিং শুরু করার জন্য প্রস্তুত করে
        await application.updater.start_polling() # পোলিং চালু করে

        try:
            await server.serve() # API সার্ভার চালু করে এবং প্রোগ্রামটিকে এখানে ধরে রাখে
        except (KeyboardInterrupt, SystemExit):
            print("সার্ভার বন্ধের অনুরোধ পাওয়া গেছে...")
        finally:
            print("বটের পোলিং বন্ধ করা হচ্ছে...")
            await application.updater.stop() # পোলিং বন্ধ করে
            await application.stop()       # অ্যাপ্লিকেশন ক্লিনার বন্ধ করে
            print("বট সফলভাবে বন্ধ হয়েছে।")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("প্রোগ্রাম বন্ধ করা হলো।")
