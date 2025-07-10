# advanced_earning_bot/payment_gateways/base_gateway.py

from abc import ABC, abstractmethod

"""
এটি সকল পেমেন্ট গেটওয়ের জন্য একটি অ্যাবস্ট্রাক্ট বেস ক্লাস (টেমপ্লেট)।
ভবিষ্যতে নতুন পেমেন্ট গেটওয়ে যোগ করতে হলে এই ক্লাসটিকে ইনহেরিট করতে হবে।
"""

class BaseGateway(ABC):
    
    def __init__(self, api_key, api_secret=None):
        """
        প্রতিটি গেটওয়ের জন্য প্রয়োজনীয় API কী এবং অন্যান্য তথ্য দিয়ে ইনিশিয়ালাইজ করা হবে।
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = ""

    @abstractmethod
    def create_payout(self, amount, currency, address, memo=None):
        """
        একটি নতুন উইথড্র বা পে-আউট তৈরি করার জন্য এই মেথডটি ইমপ্লিমেন্ট করতে হবে।
        
        Args:
            amount (float): পাঠানোর অর্থের পরিমাণ।
            currency (str): কারেন্সির কোড (যেমন, 'USDT', 'BDT')।
            address (str): প্রাপকের ওয়ালেট বা অ্যাকাউন্ট অ্যাড্রেস।
            memo (str, optional): কিছু ক্রিপ্টোকারেন্সির জন্য প্রয়োজনীয় ট্যাগ বা মেমো।

        Returns:
            dict: একটি ডিকশনারি যাতে লেনদেনের স্ট্যাটাস এবং আইডি থাকবে।
                  {'success': True, 'transaction_id': 'xyz123'} অথবা
                  {'success': False, 'message': 'Error message'}
        """
        pass

    @abstractmethod
    def check_payout_status(self, transaction_id):
        """
        একটি নির্দিষ্ট পে-আউটের স্ট্যাটাস চেক করার জন্য এই মেথডটি ইমপ্লিমেন্ট করতে হবে।
        
        Args:
            transaction_id (str): চেক করার জন্য লেনদেনের আইডি।

        Returns:
            dict: একটি ডিকশনারি যাতে স্ট্যাটাস থাকবে।
                  {'status': 'completed' / 'pending' / 'failed'}
        """
        pass
