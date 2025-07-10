# advanced_earning_bot/database.py

import sqlite3
import json
from config import DATABASE_NAME

"""
এই ফাইলটি ডাটাবেস সংযোগ স্থাপন এবং প্রয়োজনীয় সকল টেবিল তৈরি করার জন্য দায়ী।
বট প্রথমবার চালু হলে এই ফাইলটি রান করানো হবে।
"""

def create_connection():
    """ডাটাবেসের সাথে একটি সংযোগ তৈরি করে এবং সংযোগ অবজেক্টটি রিটার্ন করে।"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        print(f"SQLite DB '{DATABASE_NAME}' এর সাথে সফলভাবে সংযুক্ত।")
    except sqlite3.Error as e:
        print(f"ডাটাবেস সংযোগে ত্রুটি: {e}")
    return conn

def create_tables(conn):
    """প্রয়োজনীয় সকল টেবিল তৈরি করে।"""
    cursor = conn.cursor()

    try:
        # --- users টেবিল ---
        # ব্যবহারকারীদের সকল তথ্য এখানে সংরক্ষিত থাকবে।
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            is_verified BOOLEAN DEFAULT FALSE,
            is_banned BOOLEAN DEFAULT FALSE,
            warning_count INTEGER DEFAULT 0,
            language TEXT DEFAULT 'bn',
            timezone TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            referrer_id INTEGER,
            last_daily_bonus DATE,
            last_weekly_bonus DATE,
            last_monthly_bonus DATE
        );
        """)
        print("`users` টেবিল সফলভাবে তৈরি/লোড হয়েছে।")

        # --- ads টেবিল ---
        # সকল বিজ্ঞাপন (এডমিন এবং ব্যবহারকারীর) এখানে সংরক্ষিত থাকবে।
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id INTEGER,
            ad_source TEXT NOT NULL, -- 'user_submitted', 'admin_direct_link', 'admin_blogger_embed'
            ad_type TEXT NOT NULL,   -- 'video_embed', 'direct_link_ad'
            ad_content TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'active', 'paused', 'completed'
            target_views INTEGER DEFAULT 0,
            current_views INTEGER DEFAULT 0,
            view_duration_seconds INTEGER DEFAULT 30,
            viewed_by_users TEXT -- JSON list of user_ids
        );
        """)
        print("`ads` টেবিল সফলভাবে তৈরি/লোড হয়েছে।")

        # --- transactions টেবিল ---
        # সকল আর্থিক লেনদেন এখানে রেকর্ড করা হবে।
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'deposit', 'withdrawal', 'transfer_sent', 'transfer_received', 'ad_reward', 'bonus'
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'completed', -- 'pending', 'completed', 'failed', 'rejected'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT -- JSON format for extra data like receiver_id, payment_gateway_id
        );
        """)
        print("`transactions` টেবিল সফলভাবে তৈরি/লোড হয়েছে।")

        # --- bot_config টেবিল ---
        # এডমিন প্যানেল থেকে নিয়ন্ত্রিত সকল সেটিংস এখানে থাকবে।
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_config (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            description TEXT
        );
        """)
        print("`bot_config` টেবিল সফলভাবে তৈরি/লোড হয়েছে।")

        # --- dynamic_buttons টেবিল ---
        # এডমিন প্যানেলের মেনু বিল্ডার দ্বারা তৈরি বাটনগুলো এখানে থাকবে।
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_buttons (
            button_id INTEGER PRIMARY KEY AUTOINCREMENT,
            button_text TEXT NOT NULL,
            parent_id INTEGER,
            action_type TEXT NOT NULL, -- 'show_message', 'open_submenu', 'execute_function'
            action_value TEXT,
            position INTEGER DEFAULT 0
        );
        """)
        print("`dynamic_buttons` টেবিল সফলভাবে তৈরি/লোড হয়েছে।")

        conn.commit()

    except sqlite3.Error as e:
        print(f"টেবিল তৈরিতে ত্রুটি: {e}")
    finally:
        if cursor:
            cursor.close()

def initialize_database():
    """ডাটাবেস এবং টেবিল তৈরির মূল ফাংশন।"""
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("ডাটাবেস সংযোগ স্থাপন করা সম্ভব হয়নি।")

# এই ফাইলটি সরাসরি রান করা হলে ডাটাবেস ইনিশিয়ালাইজ হবে।
if __name__ == '__main__':
    initialize_database()
