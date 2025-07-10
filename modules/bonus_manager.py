# advanced_earning_bot/modules/bonus_manager.py

import sqlite3
from datetime import date, timedelta
from config import DATABASE_NAME
from modules.bot_settings import get_setting
from modules.wallet_manager import record_transaction
from modules.user_manager import update_balance, get_user_by_id

"""
এই মডিউলটি সকল প্রকার বোনাস সিস্টেম পরিচালনা করে।
দৈনিক, সাপ্তাহিক, মাসিক এবং ডিপোজিট বোনাস।
"""

def claim_daily_bonus(user_id):
    """দৈনিক বোনাস দাবি করার প্রক্রিয়া পরিচালনা করে।"""
    user = get_user_by_id(user_id)
    if not user:
        return {'success': False, 'message': 'ব্যবহারকারী খুঁজে পাওয়া যায়নি।'}

    last_bonus_str = user.get('last_daily_bonus')
    today = date.today()

    if last_bonus_str:
        last_bonus_date = date.fromisoformat(last_bonus_str)
        if last_bonus_date >= today:
            return {'success': False, 'message': 'আপনি আজকের দৈনিক বোনাস ইতিমধ্যে নিয়ে নিয়েছেন।'}

    # সেটিংস থেকে বোনাসের পরিমাণ নিন
    bonus_amount_str, _ = get_setting('daily_bonus_amount')
    bonus_amount = int(bonus_amount_str) if bonus_amount_str.isdigit() else 10

    # বোনাস প্রদান করুন
    if update_balance(user_id, bonus_amount):
        # লেনদেন রেকর্ড করুন
        record_transaction(user_id, 'bonus', bonus_amount, details={'bonus_type': 'daily'})
        
        # ডাটাবেসে শেষ বোনাসের তারিখ আপডেট করুন
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_daily_bonus = ? WHERE user_id = ?", (today.isoformat(), user_id))
            conn.commit()
            return {'success': True, 'message': f'দৈনিক বোনাস হিসেবে আপনি {bonus_amount} পয়েন্ট পেয়েছেন!'}
        except sqlite3.Error as e:
            print(f"দৈনিক বোনাসের তারিখ আপডেটে ত্রুটি: {e}")
            # যদি তারিখ আপডেট ব্যর্থ হয়, বোনাস ফেরত নিন (নিরাপত্তার জন্য)
            update_balance(user_id, -bonus_amount)
            return {'success': False, 'message': 'একটি সমস্যা হয়েছে, অনুগ্রহ করে আবার চেষ্টা করুন।'}
        finally:
            if conn:
                conn.close()
    
    return {'success': False, 'message': 'বোনাস প্রদান করতে একটি সমস্যা হয়েছে।'}


# সাপ্তাহিক এবং মাসিক বোনাসের জন্য ফাংশনগুলোও একই রকম হবে
# এখানে শুধুমাত্র ফাংশনের কাঠামো দেওয়া হলো। আপনি একই লজিকে এগুলো পূর্ণ করতে পারবেন।

def claim_weekly_bonus(user_id):
    """সাপ্তাহিক বোনাস দাবি করার প্রক্রিয়া পরিচালনা করে।"""
    # কাজ: চেক করুন ব্যবহারকারী এই সপ্তাহে বোনাস নিয়েছে কিনা।
    # সপ্তাহের শুরু (যেমন সোমবার) থেকে গণনা করা যেতে পারে।
    # যদি না নিয়ে থাকে, তাহলে বোনাস দিন এবং ডাটাবেস আপডেট করুন।
    # এই ফাংশনটি এখন একটি প্লেসহোল্ডার।
    return {'success': False, 'message': 'সাপ্তাহিক বোনাস সিস্টেমটি এখনও সক্রিয় করা হয়নি।'}

def claim_monthly_bonus(user_id):
    """মাসিক বোনাস দাবি করার প্রক্রিয়া পরিচালনা করে।"""
    # কাজ: চেক করুন ব্যবহারকারী এই মাসে বোনাস নিয়েছে কিনা।
    # যদি না নিয়ে থাকে, তাহলে বোনাস দিন এবং ডাটাবেস আপডেট করুন।
    # এই ফাংশনটি এখন একটি প্লেসহোল্ডার।
    return {'success': False, 'message': 'মাসিক বোনাস সিস্টেমটি এখনও সক্রিয় করা হয়নি।'}


def apply_deposit_bonus(user_id, deposit_amount):
    """
    ডিপোজিটের পরিমাণের উপর ভিত্তি করে স্বয়ংক্রিয়ভাবে বোনাস প্রয়োগ করে।
    """
    # এই ফিচারটি এখনও ইমপ্লিমেন্ট করা হয়নি।
    # ভবিষ্যতে এখানে `bot_config` থেকে বোনাসের নিয়ম (`deposit_bonus_rules`)
    # নিয়ে আসা হবে এবং সেই অনুযায়ী বোনাস দেওয়া হবে।
    print(f"ID {user_id} এর {deposit_amount} ডিপোজিটের জন্য বোনাস চেক করা হচ্ছে (এখনও ইমপ্লিমেন্ট করা হয়নি)।")
    return {'success': True, 'bonus_added': 0}


# উদাহরণ
if __name__ == '__main__':
    # এই মডিউলটি সরাসরি রান করার জন্য নয়।
    # টেস্ট করার জন্য, database.py, bot_settings.py এবং user_manager.py প্রথমে সেটআপ করতে হবে।
    # from user_manager import add_or_get_user
    # test_user_id = 777
    # add_or_get_user(test_user_id, 'bonustaker')
    
    # result = claim_daily_bonus(test_user_id)
    # print(result)
    
    # দ্বিতীয়বার চেষ্টা করলে
    # result_again = claim_daily_bonus(test_user_id)
    # print(result_again)
    pass
