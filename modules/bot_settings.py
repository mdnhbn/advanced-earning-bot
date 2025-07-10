# advanced_earning_bot/modules/bot_settings.py

import sqlite3
import json
from config import DATABASE_NAME

"""
এই মডিউলটি ডাটাবেসের `bot_config` টেবিল থেকে সকল সেটিংস লোড করা এবং
সেখানে নতুন সেটিংস যোগ বা আপডেট করার কাজ করে।
এটি বটের সকল ডাইনামিক নিয়মকানুন পরিচালনা করে।
"""

# ডিফল্ট সেটিংস যা ডাটাবেসে না থাকলে যোগ করা হবে।
# এডমিন প্যানেল থেকে এই মানগুলো পরিবর্তন করা যাবে।
DEFAULT_SETTINGS = {
    'maintenance_mode_global': ('off', True, 'সম্পূর্ণ বট চালু/বন্ধ করার জন্য। "on" অথবা "off"'),
    'feature_ads_view': ('on', True, 'বিজ্ঞাপন দেখার ফিচার চালু/বন্ধ। "on" অথবা "off"'),
    'feature_deposit': ('on', True, 'ডিপোজিট ফিচার চালু/বন্ধ। "on" অথবা "off"'),
    'feature_withdrawal': ('on', True, 'উইথড্র ফিচার চালু/বন্ধ। "on" অথবা "off"'),
    'feature_balance_transfer': ('on', True, 'ব্যালেন্স ট্রান্সফার ফিচার চালু/বন্ধ। "on" অথবা "off"'),
    'withdrawal_mode': ('manual', True, 'উইথড্র মোড। "manual" অথবা "automatic"'),
    'min_auto_withdraw_amount': ('500', True, 'স্বয়ংক্রিয় উইথড্রর সর্বনিম্ন পরিমাণ'),
    'daily_auto_withdraw_limit': ('5000', True, 'প্রতি ইউজারের দৈনিক স্বয়ংক্রিয় উইথড্র লিমিট'),
    'transfer_fee_percent': ('5', True, 'ব্যালেন্স ট্রান্সফারের জন্য শতকরা ফি'),
    'daily_bonus_amount': ('10', True, 'দৈনিক বোনাসের পরিমাণ'),
    'weekly_bonus_amount': ('100', True, 'সাপ্তাহিক বোনাসের পরিমাণ'),
    'monthly_bonus_amount': ('500', True, 'মাসিক বোনাসের পরিমাণ'),
    'blogger_page_url': ('', True, 'বিজ্ঞাপন দেখানোর জন্য ব্লগার পেজের URL'),
    'required_channels': ('[]', True, 'বাধ্যতামূলক চ্যানেলগুলোর তালিকা (JSON format)'),
    'welcome_message': ('স্বাগতম!', True, 'নতুন ব্যবহারকারীদের জন্য ওয়েলকাম মেসেজ')
}

def initialize_bot_settings():
    """
    ডাটাবেসে ডিফল্ট সেটিংসগুলো যোগ করে যদি সেগুলো আগে থেকে না থাকে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        for key, value_tuple in DEFAULT_SETTINGS.items():
            value, is_active, description = value_tuple
            cursor.execute("SELECT * FROM bot_config WHERE setting_name = ?", (key,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO bot_config (setting_name, setting_value, is_active, description) VALUES (?, ?, ?, ?)",
                    (key, value, is_active, description)
                )
        conn.commit()
        print("বটের ডিফল্ট সেটিংস সফলভাবে ইনিশিয়ালাইজ হয়েছে।")
    except sqlite3.Error as e:
        print(f"ডিফল্ট সেটিংস ইনিশিয়ালাইজ করতে ত্রুটি: {e}")
    finally:
        if conn:
            conn.close()


def get_setting(setting_name):
    """
    ডাটাবেস থেকে একটি নির্দিষ্ট সেটিং এর মান এবং স্ট্যাটাস নিয়ে আসে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value, is_active FROM bot_config WHERE setting_name = ?", (setting_name,))
        result = cursor.fetchone()
        if result:
            return result[0], result[1] # (value, is_active)
        return None, False
    except sqlite3.Error as e:
        print(f"সেটিং '{setting_name}' লোড করতে ত্রুটি: {e}")
        return None, False
    finally:
        if conn:
            conn.close()


def get_all_settings():
    """
    ডাটাবেস থেকে সকল সেটিংস একটি ডিকশনারি হিসেবে নিয়ে আসে।
    """
    settings = {}
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_name, setting_value, is_active FROM bot_config")
        all_rows = cursor.fetchall()
        for row in all_rows:
            settings[row[0]] = {'value': row[1], 'is_active': bool(row[2])}
        return settings
    except sqlite3.Error as e:
        print(f"সকল সেটিংস লোড করতে ত্রুটি: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def update_setting(setting_name, new_value=None, new_status=None):
    """
    ডাটাবেসে একটি নির্দিষ্ট সেটিং এর মান বা স্ট্যাটাস আপডেট করে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        if new_value is not None and new_status is not None:
            cursor.execute("UPDATE bot_config SET setting_value = ?, is_active = ? WHERE setting_name = ?", (new_value, new_status, setting_name))
        elif new_value is not None:
            cursor.execute("UPDATE bot_config SET setting_value = ? WHERE setting_name = ?", (new_value, setting_name))
        elif new_status is not None:
            cursor.execute("UPDATE bot_config SET is_active = ? WHERE setting_name = ?", (new_status, setting_name))
        
        conn.commit()
        print(f"সেটিং '{setting_name}' সফলভাবে আপডেট হয়েছে।")
        return True
    except sqlite3.Error as e:
        print(f"সেটিং '{setting_name}' আপডেট করতে ত্রুটি: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ডাটাবেস ইনিশিয়ালাইজেশনের অংশ হিসেবে এই ফাংশনটি কল করা হবে।
if __name__ == '__main__':
    # এটি নিশ্চিত করে যে `bot_config` টেবিলে ডিফল্ট মানগুলো লোড করা আছে।
    # database.py ফাইলটি প্রথমে রান করতে হবে।
    initialize_bot_settings()
    
    # উদাহরণ: একটি সেটিং প্রিন্ট করে দেখা
    channels, status = get_setting('required_channels')
    if channels:
        print(f"Required Channels: {json.loads(channels)}, Status: {status}")
