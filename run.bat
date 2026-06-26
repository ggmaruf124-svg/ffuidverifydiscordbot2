@echo off
title Discord FF Verification Bot — Autobot
cls

echo =======================================================
echo    🔧 [Autobot] প্রয়োজনীয় লাইব্রেরি চেক করা হচ্ছে...
echo =======================================================
echo.

:: requirements.txt ফাইল থেকে লাইব্রেরি অটো ইনস্টল বা আপডেট করবে
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ কোনো লাইব্রেরি ইনস্টল করতে সমস্যা হয়েছে! 
    echo 🔗 আপনার ইন্টারনেট কানেকশন চেক করুন অথবা ম্যানুয়ালি 'pip install telethon main.py aiohttp' লিখুন।
    pause
    exit
)

echo.
echo =======================================================
echo    ✅ সমস্ত লাইব্রেরি প্রস্তুত! বট চালু করা হচ্ছে...
echo =======================================================
echo.

:: এরপর আপনার মূল পাইথন ফাইলটি রান করবে
python main.py

echo.
echo ⚠️ বটটি কোনো কারণে বন্ধ হয়ে গেছে।
pause