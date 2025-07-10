// advanced_earning_bot/mini_app/js/main.js

/**
 * এই ফাইলটি মিনি অ্যাপের মূল কার্যকারিতা নিয়ন্ত্রণ করে।
 * ব্যবহারকারীর ইন্টারঅ্যাকশন, ডেটা লোডিং এবং UI আপডেট এখানে পরিচালনা করা হয়।
 */

// --- গ্লোবাল ভেরিয়েবল ---
let tg = window.Telegram.WebApp; // টেলিগ্রাম ওয়েব অ্যাপ অবজেক্ট
let userData = null; // ব্যবহারকারীর ডেটা সংরক্ষণের জন্য

// --- UI এলিমেন্টগুলো সিলেক্ট করা ---
const usernameDisplay = document.getElementById('username-display');
const balanceDisplay = document.getElementById('balance-display');
const watchAdBtn = document.getElementById('watch-ad-btn');
const dailyBonusBtn = document.getElementById('daily-bonus-btn');

// --- প্রধান ফাংশন ---

/**
 * অ্যাপটি প্রথমবার লোড হলে এই ফাংশনটি রান হবে।
 */
async function onDocumentReady() {
    tg.ready(); // টেলিগ্রামকে জানানো যে অ্যাপটি প্রস্তুত
    tg.expand(); // অ্যাপটিকে পূর্ণ স্ক্রিনে বিস্তৃত করা

    // টেলিগ্রাম থেকে ব্যবহারকারীর প্রাথমিক তথ্য নিন
    const initData = tg.initDataUnsafe;
    if (!initData || !initData.user) {
        showNotification("Error: Could not retrieve user data from Telegram.", 5000);
        return;
    }
    
    const userId = initData.user.id;

    // ব্যাকএন্ড থেকে ব্যবহারকারীর বিস্তারিত ডেটা লোড করুন
    const response = await fetchUserData(userId);

    if (response.success) {
        userData = response.user;
        updateUI();
    } else {
        showNotification(response.message, 5000);
    }

    // বাটনগুলোতে ইভেন্ট লিসেনার যোগ করুন
    addEventListeners();
}

/**
 * UI-তে ব্যবহারকারীর ডেটা আপডেট করে।
 */
function updateUI() {
    if (userData) {
        usernameDisplay.textContent = userData.username || 'User';
        balanceDisplay.textContent = userData.balance.toLocaleString(); // সংখ্যা ফরম্যাট করার জন্য
    }
}

/**
 * সকল বাটনের জন্য ইভেন্ট লিসেনার সেট করে।
 */
function addEventListeners() {
    // দৈনিক বোনাস বাটন
    dailyBonusBtn.addEventListener('click', async () => {
        if (!userData) return;
        
        const response = await claimDailyBonus(tg.initDataUnsafe.user.id);
        showNotification(response.message, 3000);
        
        if (response.success) {
            // সফল হলে ব্যালেন্স রিফ্রেশ করুন
            const updatedData = await fetchUserData(tg.initDataUnsafe.user.id);
            if(updatedData.success) {
                userData = updatedData.user;
                updateUI();
            }
        }
    });

    // বিজ্ঞাপন দেখা বাটন
    watchAdBtn.addEventListener('click', async () => {
        if (!userData) return;

        const response = await fetchAdForView(tg.initDataUnsafe.user.id);

        if (response.success) {
            const ad = response.ad;
            // ad_viewer.html পেজটি বিজ্ঞাপনর ডেটা সহ খুলুন
            const url = `ad_viewer.html?ad_id=${ad.ad_id}&duration=${ad.duration}&reward=${ad.reward}&ad_type=${ad.ad_type}&ad_content=${encodeURIComponent(ad.ad_content)}&blogger_base_url=${encodeURIComponent(ad.blogger_base_url)}`;
            
            // মিনি অ্যাপের মধ্যে নতুন পেজ খোলার জন্য
            tg.openLink(url, {try_instant_view: true});

        } else {
            showNotification(response.message, 3000);
        }
    });

    // TODO: অন্যান্য বাটনের জন্য ইভেন্ট লিসেনার যোগ করতে হবে
    // document.getElementById('post-ad-btn').addEventListener(...)
    // document.getElementById('referral-btn').addEventListener(...)
    // document.getElementById('wallet-btn').addEventListener(...)
}


// --- অ্যাপ চালু করা ---

// ডকুমেন্ট সম্পূর্ণরূপে লোড হওয়ার পর onDocumentReady() ফাংশনটি চালান
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onDocumentReady);
} else {
    onDocumentReady();
}
