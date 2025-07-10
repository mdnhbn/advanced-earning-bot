# advanced_earning_bot/modules/wallet_manager.py

import sqlite3
import json
from datetime import datetime
from config import DATABASE_NAME
from modules.user_manager import update_balance, get_user_by_id
from modules.bot_settings import get_setting

"""
এই মডিউলটি ওয়ালেট এবং আর্থিক লেনদেন সংক্রান্ত সকল কাজ পরিচালনা করে।
ডিপোজিট, উইথড্র, ট্রান্সফার এবং লেনদেনের ইতিহাস।
"""

def record_transaction(user_id, trans_type, amount, status='completed', details=None):
    """
    `transactions` টেবিলে একটি নতুন লেনদেন রেকর্ড করে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # details যদি ডিকশনারি হয়, তাকে JSON স্ট্রিং-এ রূপান্তর করুন
        details_json = json.dumps(details) if details else None
        
        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, status, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, trans_type, amount, status, datetime.now(), details_json)
        )
        conn.commit()
        return cursor.lastrowid # নতুন ট্রানজেকশন আইডি রিটার্ন করে
    except sqlite3.Error as e:
        print(f"লেনদেন রেকর্ড করতে ত্রুটি: {e}")
        return None
    finally:
        if conn:
            conn.close()

def transfer_balance(sender_id, receiver_id, amount):
    """
    একজন ব্যবহারকারী থেকে অন্য ব্যবহারকারীকে ব্যালেন্স ট্রান্সফার করে।
    """
    if sender_id == receiver_id:
        return {'success': False, 'message': 'আপনি নিজেকে পয়েন্ট পাঠাতে পারবেন না।'}

    # ট্রান্সফার ফি কত শতাংশ তা সেটিংস থেকে নিন
    fee_percent_str, _ = get_setting('transfer_fee_percent')
    fee_percent = int(fee_percent_str) if fee_percent_str.isdigit() else 5

    fee = (amount * fee_percent) // 100
    total_deduction = amount + fee

    sender = get_user_by_id(sender_id)
    receiver = get_user_by_id(receiver_id)

    if not sender:
        return {'success': False, 'message': 'প্রেরকের অ্যাকাউন্ট খুঁজে পাওয়া যায়নি।'}
    if not receiver:
        return {'success': False, 'message': 'প্রাপকের অ্যাকাউন্ট খুঁজে পাওয়া যায়নি।'}
    if sender['balance'] < total_deduction:
        return {'success': False, 'message': f'আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই। মোট প্রয়োজন: {total_deduction} পয়েন্ট।'}

    # লেনদেন শুরু করুন
    try:
        # প্রেরকের ব্যালেন্স কমান
        if not update_balance(sender_id, -total_deduction):
            raise Exception("প্রেরকের ব্যালেন্স আপডেট ব্যর্থ হয়েছে।")

        # প্রাপকের ব্যালেন্স বাড়ান
        if not update_balance(receiver_id, amount):
            # যদি প্রাপকের ব্যালেন্স আপডেট ব্যর্থ হয়, প্রেরকের টাকা ফেরত দিন
            update_balance(sender_id, total_deduction)
            raise Exception("প্রাপকের ব্যালেন্স আপডেট ব্যর্থ হয়েছে।")

        # লেনদেন রেকর্ড করুন
        record_transaction(sender_id, 'transfer_sent', -total_deduction, details={'receiver_id': receiver_id, 'amount': amount, 'fee': fee})
        record_transaction(receiver_id, 'transfer_received', amount, details={'sender_id': sender_id})
        
        return {'success': True, 'message': f'{amount} পয়েন্ট সফলভাবে পাঠানো হয়েছে। ফি: {fee} পয়েন্ট।'}
    except Exception as e:
        print(f"ট্রান্সফারে ত্রুটি: {e}")
        return {'success': False, 'message': 'লেনদেন প্রক্রিয়া করার সময় একটি সমস্যা হয়েছে।'}

def create_withdrawal_request(user_id, amount, method, address):
    """
    একটি উইথড্র অনুরোধ তৈরি করে এবং এটিকে 'pending' স্ট্যাটাসে রাখে।
    """
    user = get_user_by_id(user_id)
    if not user:
        return {'success': False, 'message': 'আপনার অ্যাকাউন্ট খুঁজে পাওয়া যায়নি।'}
    if user['balance'] < amount:
        return {'success': False, 'message': 'আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।'}

    # ব্যবহারকারীর ব্যালেন্স থেকে টাকা হোল্ড করুন (কেটে নিন)
    if not update_balance(user_id, -amount):
         return {'success': False, 'message': 'ব্যালেন্স আপডেট করতে সমস্যা হয়েছে।'}

    # পেন্ডিং ট্রানজেকশন রেকর্ড করুন
    details = {'method': method, 'address': address}
    trans_id = record_transaction(user_id, 'withdrawal', -amount, status='pending', details=details)

    if trans_id:
        return {'success': True, 'message': 'আপনার উইথড্র অনুরোধটি প্রক্রিয়া করা হচ্ছে।', 'transaction_id': trans_id}
    else:
        # যদি ট্রানজেকশন রেকর্ড ব্যর্থ হয়, টাকা ফেরত দিন
        update_balance(user_id, amount)
        return {'success': False, 'message': 'উইথড্র অনুরোধ তৈরি করতে সমস্যা হয়েছে।'}

def process_auto_withdrawal(transaction_id):
    """
    স্বয়ংক্রিয় উইথড্র প্রক্রিয়া পরিচালনা করে (ভবিষ্যতের জন্য)।
    এখানে পেমেন্ট গেটওয়ের API কল করা হবে।
    """
    # ধাপ ১: ট্রানজেকশনের তথ্য ডাটাবেস থেকে নিন।
    # ধাপ ২: পেমেন্ট গেটওয়ের সাথে সংযোগ স্থাপন করুন।
    # ধাপ ৩: টাকা পাঠান।
    # ধাপ ৪: সফল হলে, ট্রানজেকশনের স্ট্যাটাস 'completed' করুন।
    # ধাপ ৫: ব্যর্থ হলে, স্ট্যাটাস 'failed' করুন এবং এডমিনকে নোটিফাই করুন।
    
    print(f"ট্রানজেকশন আইডি {transaction_id} স্বয়ংক্রিয়ভাবে প্রক্রিয়া করা হচ্ছে (এখনও ইমপ্লিমেন্ট করা হয়নি)।")
    # আপাতত, আমরা এটিকে ম্যানুয়ালি সম্পন্ন করব।
    pass

def get_user_transactions(user_id, limit=20):
    """
    একজন ব্যবহারকারীর সাম্প্রতিক লেনদেনের তালিকা নিয়ে আসে।
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT type, amount, status, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"ID {user_id} এর লেনদেন খুঁজতে ত্রুটি: {e}")
        return []
    finally:
        if conn:
            conn.close()

# উদাহরণ
if __name__ == '__main__':
    # এই মডিউলটি সরাসরি রান করার জন্য নয়।
    # টেস্ট করার জন্য দুটি ইউজার তৈরি করতে হবে।
    # from user_manager import add_or_get_user
    # user1 = add_or_get_user(111, 'sender')
    # user2 = add_or_get_user(222, 'receiver')
    # update_balance(111, 1000) # প্রেরকের অ্যাকাউন্টে টাকা যোগ করা
    
    # result = transfer_balance(111, 222, 500)
    # print(result)
    pass
