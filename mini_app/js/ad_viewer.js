// advanced_earning_bot/mini_app/js/ad_viewer.js

/**
 * এই ফাইলটি ad_viewer.html পেজের কার্যকারিতা নিয়ন্ত্রণ করে।
 * বিজ্ঞাপন লোড করা, টাইমার চালানো এবং পুরস্কার দাবি করার প্রক্রিয়া পরিচালনা করে।
 */

// --- গ্লোবাল ভেরিয়েবল ---
let tg = window.Telegram.WebApp;
let adData = {};

// --- UI এলিমেন্ট ---
const adFrame = document.getElementById('ad-frame');
const timerText = document.getElementById('timer-text');
const claimButton = document.getElementById('claim-reward-btn');

// --- প্রধান ফাংশন ---

/**
 * পেজ লোড হলে এই ফাংশনটি রান হবে।
 */
function onAdViewerReady() {
    tg.ready();

    // URL থেকে বিজ্ঞাপনের প্যারামিটারগুলো নিন
    const urlParams = new URLSearchParams(window.location.search);
    adData = {
        adId: parseInt(urlParams.get('ad_id')),
        duration: parseInt(urlParams.get('duration')),
        reward: parseInt(urlParams.get('reward')),
        adType: urlParams.get('ad_type'),
        adContent: decodeURIComponent(urlParams.get('ad_content')),
        bloggerBaseUrl: decodeURIComponent(urlParams.get('blogger_base_url'))
    };

    if (!adData.adId) {
        timerText.textContent = "বিজ্ঞাপন লোড করতে সমস্যা হয়েছে।";
        return;
    }

    // বিজ্ঞাপন লোড করুন এবং টাইমার শুরু করুন
    loadAd();
    startTimer();
}

/**
 * বিজ্ঞাপনের ধরন অনুযায়ী iframe-এ কন্টেন্ট লোড করে।
 */
function loadAd() {
    if (adData.adType === 'video_embed') {
        // যদি ব্লগারের মাধ্যমে ভিডিও এম্বেড হয়
        // ব্লগারের URL-এ ভিডিও লিঙ্কটি প্যারামিটার হিসেবে পাঠান
        const finalUrl = `${adData.bloggerBaseUrl}?video_url=${encodeURIComponent(adData.adContent)}`;
        adFrame.src = finalUrl;
    } else if (adData.adType === 'direct_link_ad') {
        // যদি ডিরেক্ট লিঙ্ক হয়
        adFrame.src = adData.adContent;
    }
}

/**
 * কাউন্টডাউন টাইমার শুরু করে।
 */
function startTimer() {
    let timeLeft = adData.duration;
    timerText.textContent = `বিজ্ঞাপনটি ${timeLeft} সেকেন্ড দেখুন`;

    const timerInterval = setInterval(() => {
        timeLeft--;
        timerText.textContent = `বিজ্ঞাপনটি ${timeLeft} সেকেন্ড দেখুন`;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            activateClaimButton();
        }
    }, 1000);
}

/**
 * টাইমার শেষ হলে 'পুরস্কার নিন' বাটনটি সক্রিয় করে।
 */
function activateClaimButton() {
    timerText.textContent = "আপনি এখন পুরস্কার নিতে পারেন!";
    claimButton.disabled = false;
    claimButton.classList.add('active');
    claimButton.textContent = `✅ ${adData.reward} পয়েন্ট নিন`;
}

// --- ইভেন্ট লিসেনার ---

claimButton.addEventListener('click', async () => {
    // বাটনটি নিষ্ক্রিয় করুন যাতে একাধিকবার ক্লিক না করা যায়
    claimButton.disabled = true;
    claimButton.classList.remove('active');
    claimButton.textContent = 'প্রসেসিং...';

    const userId = tg.initDataUnsafe.user.id;
    const response = await recordAdView(userId, adData.adId, adData.reward);

    if (response.success) {
        // সফল হলে একটি বার্তা দেখান এবং অ্যাপটি বন্ধ করুন
        tg.showAlert(`অভিনন্দন! আপনি ${adData.reward} পয়েন্ট পেয়েছেন।`, () => {
            tg.close();
        });
    } else {
        // ব্যর্থ হলে বার্তা দেখান এবং অ্যাপ বন্ধ করুন
        tg.showAlert(`দুঃখিত! ${response.message}`, () => {
            tg.close();
        });
    }
});

// --- অ্যাপ চালু করা ---
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onAdViewerReady);
} else {
    onAdViewerReady();
}
