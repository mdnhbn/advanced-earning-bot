# advanced_earning_bot/modules/user_manager.py

import sqlite3
from datetime import datetime
from config import DATABASE_NAME, DEFAULT_LANGUAGE

"""
এই মডিউলটি ব্যবহারকারী সংক্রান্ত সকল কাজ পরিচালনা করে।
নতুন ব্যবহারকারী তৈরি করা, তথ্য খুঁজে বের করা, ব্যালেন্স আপডেট, ব্যান/আনব্যান ইত্যাদি।
"""

def add_or_get_user(user_id, username, referrer_id=None):
    """
    যদি ব্যবহারকারী ডাটাবেসে না থাকে, তাকে যোগ করে।
    সবসময় ব্যবহারকারীর তথ্য রিটার্ন করে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # ব্যবহারকারী আগে থেকেই আছে কিনা চেক করুন
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()

        if user_data is None:
            # নতুন ব্যবহারকারী, ডাটাবেসে যোগ করুন
            cursor.execute(
                """
                INSERT INTO users (user_id, username, language, referrer_id, join_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, username, DEFAULT_LANGUAGE, referrer_id, datetime.now())
            )
            conn.commit()
            print(f"নতুন ব্যবহারকারী যোগ করা হয়েছে: ID {user_id}, Username: {username}")
            
            # নতুন করে তথ্য নিয়ে আসুন
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()

        # কলামের নাম সহ ডিকশনারি হিসেবে রিটার্ন করুন
        if user_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, user_data))
        
        return None

    except sqlite3.Error as e:
        print(f"ব্যবহারকারী যোগ বা খুঁজে বের করতে ত্রুটি: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_id(user_id):
    """নির্দিষ্ট আইডি দিয়ে ব্যবহারকারীর তথ্য খুঁজে বের করে।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, user_data))
        
        return None
    except sqlite3.Error as e:
        print(f"ID {user_id} এর ব্যবহারকারী খুঁজতে ত্রুটি: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_balance(user_id, amount_change):
    """
    ব্যবহারকারীর ব্যালেন্স পরিবর্তন করে (যোগ বা বিয়োগ)।
    amount_change পজিটিভ হলে যোগ হবে, নেগেটিভ হলে বিয়োগ হবে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount_change, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"ID {user_id} এর ব্যালেন্স আপডেট করতে ত্রুটি: {e}")
        return False
    finally:
        if conn:
            conn.close()

def set_user_verified(user_id, status=True):
    """ব্যবহারকারীর ভেরিফিকেশন স্ট্যাটাস পরিবর্তন করে।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified = ? WHERE user_id = ?", (status, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"ID {user_id} এর ভেরিফিকেশন স্ট্যাটাস পরিবর্তনে ত্রুটি: {e}")
        return False
    finally:
        if conn:
            conn.close()

def set_ban_status(user_id, status=True):
    """ব্যবহারকারীকে ব্যান বা আনব্যান করে।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (status, user_id))
        conn.commit()
        print(f"ব্যবহারকারী ID {user_id} এর ব্যান স্ট্যাটাস '{status}' করা হয়েছে।")
        return True
    except sqlite3.Error as e:
        print(f"ID {user_id} এর ব্যান স্ট্যাটাস পরিবর্তনে ত্রুটি: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_warning_count(user_id, increment=1):
    """ব্যবহারকারীর ওয়ার্নিং সংখ্যা বাড়ায়।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET warning_count = warning_count + ? WHERE user_id = ?", (increment, user_id))
        conn.commit()
        # নতুন ওয়ার্নিং সংখ্যা রিটার্ন করতে পারি
        cursor.execute("SELECT warning_count FROM users WHERE user_id = ?", (user_id,))
        new_count = cursor.fetchone()
        return new_count[0] if new_count else 0
    except sqlite3.Error as e:
        print(f"ID {user_id} এর ওয়ার্নিং সংখ্যা আপডেটে ত্রুটি: {e}")
        return -1
    finally:
        if conn:
            conn.close()


def update_user_language(user_id, lang_code):
    """ব্যবহারকারীর ভাষা পরিবর্তন করে।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang_code, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"ID {user_id} এর ভাষা পরিবর্তনে ত্রুটি: {e}")
        return False
    finally:
        if conn:
            conn.close()

# উদাহরণ
if __name__ == '__main__':
    # এই মডিউলটি সরাসরি রান করার জন্য নয়, তবে টেস্ট করার জন্য ব্যবহার করা যেতে পারে।
    # প্রথমে database.py এবং bot_settings.py রান করতে হবে।
    
    # টেস্ট ইউজার যোগ করা
    test_user = add_or_get_user(12345, 'testuser', referrer_id=98765)
    print("Test User Data:", test_user)

    # ব্যালেন্স আপডেট
    update_balance(12345, 100)
    
    # তথ্য আবার নিয়ে আসা
    updated_user = get_user_by_id(12345)
    print("Updated User Data:", updated_user)
