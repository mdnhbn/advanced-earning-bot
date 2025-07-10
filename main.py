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

def main() -> None:
    print("ডাটাবেস ইনিশিয়ালাইজ করা হচ্ছে...")
    initialize_database()
    print("বটের ডিফল্ট সেটিংস লোড করা হচ্ছে...")
    initialize_bot_settings()
    print("প্রাথমিক সেটআপ সম্পন্ন।")
    
    print("টেলিগ্রাম অ্যাপ্লিকেশন তৈরি করা হচ্ছে...")
    application = Application.builder().token(BOT_TOKEN).build()

    # --- ConversationHandler সেটআপ ---
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

    # --- হ্যান্ডলার রেজিস্ট্রেশন ---
    application.add_handler(CommandHandler("start", start_handler.start), group=0)
    application.add_handler(CommandHandler("admin", admin_panel_handler.admin_panel), group=0)
    application.add_handler(conv_handler, group=1)
    
    application.add_handler(CallbackQueryHandler(start_handler.verify_membership_callback, pattern='^verify_membership$'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.admin_panel_callback, pattern='^admin_(stats|global_settings|feature_control|close|main_menu|ad_manage_menu|ad_pending_list)$'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.toggle_feature_status, pattern='^toggle_'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.ad_review_action, pattern='^ad_(approve|reject)_'), group=0)
    application.add_handler(CallbackQueryHandler(admin_panel_handler.user_manage_actions, pattern='^user_toggle_ban_'), group=0)

    print("সকল হ্যান্ডলার সফলভাবে রেজিস্টার করা হয়েছে।")

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
