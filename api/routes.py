# advanced_earning_bot/api/routes.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json

# আমাদের মডিউলগুলো ইম্পোর্ট করুন
from modules import user_manager, ad_manager, bonus_manager, wallet_manager, bot_settings

"""
এই ফাইলটি মিনি অ্যাপ (ফ্রন্টএন্ড) এবং বট (ব্যাকএন্ড) এর মধ্যে যোগাযোগের জন্য
API এন্ডপয়েন্ট (রাউট) তৈরি করে।
"""

# FastAPI অ্যাপ তৈরি করুন
app = FastAPI()

# CORS (Cross-Origin Resource Sharing) মিডলওয়্যার যোগ করুন
# এটি মিনি অ্যাপকে ব্যাকএন্ডের সাথে নিরাপদে যোগাযোগ করতে দেবে।
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # নিরাপত্তার জন্য এখানে নির্দিষ্ট ডোমেইন দেওয়া উচিত, তবে Replit-এর জন্য "*" কাজ করবে।
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/get_user_data")
async def get_user_data(request: Request):
    """
    মিনি অ্যাপ চালু হলে ব্যবহারকারীর প্রাথমিক তথ্য পাঠানোর জন্য এই এন্ডপয়েন্ট ব্যবহৃত হয়।
    """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        user_data = user_manager.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        # সংবেদনশীল তথ্য বাদ দিন, শুধুমাত্র প্রয়োজনীয় তথ্য পাঠান
        safe_user_data = {
            'username': user_data.get('username'),
            'balance': user_data.get('balance'),
            'language': user_data.get('language'),
            'timezone': user_data.get('timezone'),
        }
        return JSONResponse(content={'success': True, 'user': safe_user_data})

    except Exception as e:
        return JSONResponse(status_code=500, content={'success': False, 'message': str(e)})


@app.post("/claim_daily_bonus")
async def claim_daily_bonus_route(request: Request):
    """দৈনিক বোনাস দাবি করার অনুরোধ প্রক্রিয়া করে।"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
            
        result = bonus_manager.claim_daily_bonus(user_id)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={'success': False, 'message': str(e)})


@app.post("/get_ad_for_view")
async def get_ad_for_view_route(request: Request):
    """ব্যবহারকারীর জন্য একটি বিজ্ঞাপন খুঁজে বের করে।"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID is required")
        
        ad = ad_manager.get_ad_for_user(user_id)
        if ad:
            # ব্লগার পেজের URL সেটিংস থেকে নিন
            blogger_url, _ = bot_settings.get_setting('blogger_page_url')
            
            # মিনি অ্যাপকে দেখানোর জন্য ডেটা প্রস্তুত করুন
            response_data = {
                'ad_id': ad['ad_id'],
                'duration': ad['view_duration_seconds'],
                'reward': 10, # উদাহরণ, এটি ডাইনামিক করা যেতে পারে
                'ad_type': ad['ad_type'],
                'ad_content': ad['ad_content'],
                'blogger_base_url': blogger_url # ব্লগার পেজের URL
            }
            return JSONResponse(content={'success': True, 'ad': response_data})
        else:
            return JSONResponse(content={'success': False, 'message': 'আপনার জন্য এখন কোনো নতুন বিজ্ঞাপন নেই।'})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={'success': False, 'message': str(e)})

@app.post("/record_ad_view")
async def record_ad_view_route(request: Request):
    """বিজ্ঞাপন দেখা সফল হলে তা রেকর্ড করে।"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        ad_id = data.get('ad_id')
        reward = data.get('reward')
        
        if not all([user_id, ad_id, reward]):
            raise HTTPException(status_code=400, detail="User ID, Ad ID, and Reward are required")
        
        result = ad_manager.record_ad_view(user_id, ad_id, reward)
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(status_code=500, content={'success': False, 'message': str(e)})


# এখানে অন্যান্য এন্ডপয়েন্ট যোগ করা হবে (যেমন, ব্যালেন্স ট্রান্সফার, উইথড্র ইত্যাদি)
# @app.post("/transfer_balance")
# ...

# এই ফাইলটি সরাসরি রান করা হবে না। `main.py` থেকে এটি ইম্পোর্ট করে চালানো হবে।
# উদাহরণ
if __name__ == '__main__':
    import uvicorn
    print("API সার্ভার টেস্ট করার জন্য, main.py ফাইলটি রান করুন।")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
