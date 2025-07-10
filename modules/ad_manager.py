# advanced_earning_bot/modules/ad_manager.py

import sqlite3
import json
from config import DATABASE_NAME
from modules.wallet_manager import record_transaction
from modules.user_manager import update_balance

"""
এই মডিউলটি বিজ্ঞাপন সংক্রান্ত সকল কাজ পরিচালনা করে।
বিজ্ঞাপন খুঁজে বের করা, ভিউ ট্র্যাক করা, বিজ্ঞাপন যোগ করা এবং অনুমোদন করা।
"""

def get_ad_for_user(user_id):
    """
    একজন ব্যবহারকারীর জন্য দেখানোর মতো একটি উপযুক্ত বিজ্ঞাপন খুঁজে বের করে।
    - বিজ্ঞাপনটি 'active' হতে হবে।
    - ব্যবহারকারী বিজ্ঞাপনটি আগে দেখে থাকলে সেটি দেখানো হবে না।
    - ব্যবহারকারী তার নিজের বিজ্ঞাপন দেখতে পাবে না।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # সকল সক্রিয় বিজ্ঞাপন নিয়ে আসুন
        cursor.execute("SELECT * FROM ads WHERE status = 'active' AND owner_user_id != ?", (user_id,))
        active_ads = cursor.fetchall()

        if not active_ads:
            return None # দেখানোর মতো কোনো বিজ্ঞাপন নেই

        columns = [description[0] for description in cursor.description]

        # উপযুক্ত বিজ্ঞাপন খুঁজে বের করুন
        for ad_data in active_ads:
            ad_dict = dict(zip(columns, ad_data))
            viewed_by = json.loads(ad_dict['viewed_by_users']) if ad_dict['viewed_by_users'] else []
            
            if user_id not in viewed_by:
                return ad_dict # উপযুক্ত বিজ্ঞাপন পাওয়া গেছে

        return None # ব্যবহারকারী সব বিজ্ঞাপন দেখে ফেলেছে
    except sqlite3.Error as e:
        print(f"বিজ্ঞাপন খুঁজতে ত্রুটি: {e}")
        return None
    finally:
        if conn:
            conn.close()

def record_ad_view(user_id, ad_id, reward_amount):
    """
    একজন ব্যবহারকারীর বিজ্ঞাপন দেখা সফলভাবে রেকর্ড করে।
    - `ads` টেবিলে `current_views` এবং `viewed_by_users` আপডেট করে।
    - ব্যবহারকারীর ব্যালেন্সে পুরস্কার যোগ করে।
    - একটি ট্রানজেকশন রেকর্ড করে।
    - যদি টার্গেট ভিউ পূর্ণ হয়, বিজ্ঞাপনের স্ট্যাটাস 'completed' করে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # বিজ্ঞাপনের বর্তমান তথ্য নিন
        cursor.execute("SELECT viewed_by_users, target_views, current_views FROM ads WHERE ad_id = ?", (ad_id,))
        result = cursor.fetchone()
        if not result:
            return {'success': False, 'message': 'বিজ্ঞাপন খুঁজে পাওয়া যায়নি।'}

        viewed_by_str, target_views, current_views = result
        viewed_by_list = json.loads(viewed_by_str) if viewed_by_str else []

        # ব্যবহারকারী ইতিমধ্যে দেখেছে কিনা আবার চেক করুন (নিরাপত্তার জন্য)
        if user_id in viewed_by_list:
            return {'success': False, 'message': 'আপনি এই বিজ্ঞাপনটি ইতিমধ্যে দেখেছেন।'}

        # তালিকা আপডেট করুন
        viewed_by_list.append(user_id)
        new_viewed_by_str = json.dumps(viewed_by_list)
        new_current_views = current_views + 1
        
        # বিজ্ঞাপনের স্ট্যাটাস নির্ধারণ করুন
        new_status = 'active'
        if new_current_views >= target_views:
            new_status = 'completed'

        # ডাটাবেস আপডেট করুন
        cursor.execute(
            "UPDATE ads SET current_views = ?, viewed_by_users = ?, status = ? WHERE ad_id = ?",
            (new_current_views, new_viewed_by_str, new_status, ad_id)
        )

        # ব্যবহারকারীর ব্যালেন্সে পুরস্কার যোগ করুন
        update_balance(user_id, reward_amount)
        record_transaction(user_id, 'ad_reward', reward_amount, details={'ad_id': ad_id})
        
        conn.commit()
        return {'success': True, 'message': f'পুরস্কার হিসেবে {reward_amount} পয়েন্ট যোগ করা হয়েছে।'}
    except sqlite3.Error as e:
        print(f"বিজ্ঞাপন ভিউ রেকর্ড করতে ত্রুটি: {e}")
        return {'success': False, 'message': 'ভিউ রেকর্ড করতে একটি সমস্যা হয়েছে।'}
    finally:
        if conn:
            conn.close()

def submit_ad_by_user(user_id, ad_source, ad_type, ad_content, target_views, duration):
    """
    ব্যবহারকারীর জমা দেওয়া বিজ্ঞাপন 'pending' স্ট্যাটাসে ডাটাবেসে যোগ করে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ads (owner_user_id, ad_source, ad_type, ad_content, target_views, view_duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """,
            (user_id, ad_source, ad_type, ad_content, target_views, duration)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"ব্যবহারকারীর বিজ্ঞাপন জমা দিতে ত্রুটি: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_pending_ads():
    """এডমিনের পর্যালোচনার জন্য সকল পেন্ডিং বিজ্ঞাপন নিয়ে আসে।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ads WHERE status = 'pending'")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"পেন্ডিং বিজ্ঞাপন খুঁজতে ত্রুটি: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_ad_status(ad_id, new_status):
    """বিজ্ঞাপনের স্ট্যাটাস পরিবর্তন করে (approved, rejected, paused ইত্যাদি)।"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        # 'approved' হলে স্ট্যাটাস 'active' করা হয়
        status_to_set = 'active' if new_status == 'approved' else new_status
        cursor.execute("UPDATE ads SET status = ? WHERE ad_id = ?", (status_to_set, ad_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"বিজ্ঞাপনের স্ট্যাটাস আপডেট করতে ত্রুটি: {e}")
        return False
    finally:
        if conn:
            conn.close()
