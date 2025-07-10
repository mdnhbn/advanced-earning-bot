// advanced_earning_bot/mini_app/js/api_client.js

/**
 * এই ফাইলটি ব্যাকএন্ড API-এর সাথে যোগাযোগের জন্য একটি ক্লায়েন্ট হিসেবে কাজ করে।
 * সকল নেটওয়ার্ক অনুরোধ এখান থেকে পাঠানো হবে।
 */

// আপনার Replit প্রজেক্ট চালু করার পর যে URL পাবেন, সেটি এখানে বসাতে হবে।
// ফরম্যাট: https://your-repl-name.replit.dev
const API_BASE_URL = window.location.origin;

// --- Helper Functions ---

function showLoading() {
    document.getElementById('loading-spinner').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-spinner').style.display = 'none';
}

function showNotification(message, duration = 3000) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, duration);
}

// --- API কল করার মূল ফাংশন ---

async function postRequest(endpoint, data) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            // সার্ভার থেকে আসা এরর মেসেজ দেখানোর চেষ্টা করুন
            const errorData = await response.json().catch(() => ({ message: 'An unknown error occurred' }));
            throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();

    } catch (error) {
        console.error(`Error making request to ${endpoint}:`, error);
        showNotification(`Error: ${error.message}`);
        // একটি স্ট্যান্ডার্ড এরর অবজেক্ট রিটার্ন করুন
        return { success: false, message: error.message };
    } finally {
        hideLoading();
    }
}


// --- নির্দিষ্ট API এন্ডপয়েন্টের জন্য ফাংশন ---

/**
 * ব্যবহারকারীর ডেটা নিয়ে আসে।
 * @param {string} userId - টেলিগ্রাম ব্যবহারকারীর আইডি।
 * @returns {Promise<object>} - ব্যবহারকারীর ডেটা বা এরর অবজেক্ট।
 */
async function fetchUserData(userId) {
    return await postRequest('/get_user_data', { user_id: userId });
}

/**
 * দৈনিক বোনাস দাবি করে।
 * @param {string} userId - টেলিগ্রাম ব্যবহারকারীর আইডি।
 * @returns {Promise<object>} - সফল বা ব্যর্থতার বার্তা।
 */
async function claimDailyBonus(userId) {
    return await postRequest('/claim_daily_bonus', { user_id: userId });
}

/**
 * দেখার জন্য একটি বিজ্ঞাপন নিয়ে আসে।
 * @param {string} userId - টেলিগ্রাম ব্যবহারকারীর আইডি।
 * @returns {Promise<object>} - বিজ্ঞাপনের ডেটা বা এরর অবজেক্ট।
 */
async function fetchAdForView(userId) {
    return await postRequest('/get_ad_for_view', { user_id: userId });
}

/**
 * বিজ্ঞাপন দেখার পর তা রেকর্ড করে।
 * @param {string} userId - টেলিগ্রাম ব্যবহারকারীর আইডি।
 * @param {number} adId - বিজ্ঞাপনের আইডি।
 * @param {number} reward - পুরস্কারের পরিমাণ।
 * @returns {Promise<object>} - সফল বা ব্যর্থতার বার্তা।
 */
async function recordAdView(userId, adId, reward) {
    return await postRequest('/record_ad_view', { 
        user_id: userId, 
        ad_id: adId, 
        reward: reward 
    });
}
