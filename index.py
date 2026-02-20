#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TeleNum Backend Server
A complete Flask backend for Telegram number marketplace
"""

import os
import json
import hashlib
import asyncio
import re
import time
import secrets
from datetime import datetime
from functools import wraps
from threading import Thread

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests

# Telethon imports
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError,
    PhoneNumberInvalidError
)

# ==================== CONFIGURATION ====================

app = Flask(__name__)
CORS(app)

# Telegram API Credentials
API_ID = 27241932
API_HASH = "218edeae0f4cf9053d7dcbf3b1485048"

# Firebase Configuration
FIREBASE_URL = "https://lolaminig-afea4-default-rtdb.firebaseio.com"

# BSCScan Configuration
BSCSCAN_API_KEY = "8BHURRRGKXD35BPGQZ8E94CVEVAUNMD9UF"
DEPOSIT_WALLET = "0x8E00A980274Cfb22798290586d97F7D185E3092D"
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"

# Temporary storage for verification codes
pending_verifications = {}
admin_pending_verifications = {}

# ==================== COUNTRIES DATABASE ====================

COUNTRIES = {
    "sa": {"name": "السعودية", "code": "sa", "phone": "+966", "buyPrice": 8.00, "sellPrice": 5.00, "featured": True, "enabled": True},
    "ae": {"name": "الإمارات", "code": "ae", "phone": "+971", "buyPrice": 8.00, "sellPrice": 5.00, "featured": True, "enabled": True},
    "kw": {"name": "الكويت", "code": "kw", "phone": "+965", "buyPrice": 7.50, "sellPrice": 4.50, "featured": True, "enabled": True},
    "qa": {"name": "قطر", "code": "qa", "phone": "+974", "buyPrice": 7.50, "sellPrice": 4.50, "featured": True, "enabled": True},
    "bh": {"name": "البحرين", "code": "bh", "phone": "+973", "buyPrice": 7.00, "sellPrice": 4.00, "featured": True, "enabled": True},
    "om": {"name": "عمان", "code": "om", "phone": "+968", "buyPrice": 7.00, "sellPrice": 4.00, "featured": True, "enabled": True},
    "eg": {"name": "مصر", "code": "eg", "phone": "+20", "buyPrice": 3.00, "sellPrice": 1.50, "featured": True, "enabled": True},
    "jo": {"name": "الأردن", "code": "jo", "phone": "+962", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "lb": {"name": "لبنان", "code": "lb", "phone": "+961", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "sy": {"name": "سوريا", "code": "sy", "phone": "+963", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "iq": {"name": "العراق", "code": "iq", "phone": "+964", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "ps": {"name": "فلسطين", "code": "ps", "phone": "+970", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "ye": {"name": "اليمن", "code": "ye", "phone": "+967", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "ly": {"name": "ليبيا", "code": "ly", "phone": "+218", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "sd": {"name": "السودان", "code": "sd", "phone": "+249", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "tn": {"name": "تونس", "code": "tn", "phone": "+216", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "dz": {"name": "الجزائر", "code": "dz", "phone": "+213", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "ma": {"name": "المغرب", "code": "ma", "phone": "+212", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "us": {"name": "أمريكا", "code": "us", "phone": "+1", "buyPrice": 6.00, "sellPrice": 3.50, "featured": True, "enabled": True},
    "gb": {"name": "بريطانيا", "code": "gb", "phone": "+44", "buyPrice": 5.50, "sellPrice": 3.00, "featured": True, "enabled": True},
    "de": {"name": "ألمانيا", "code": "de", "phone": "+49", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "fr": {"name": "فرنسا", "code": "fr", "phone": "+33", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "it": {"name": "إيطاليا", "code": "it", "phone": "+39", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "es": {"name": "إسبانيا", "code": "es", "phone": "+34", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "nl": {"name": "هولندا", "code": "nl", "phone": "+31", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "be": {"name": "بلجيكا", "code": "be", "phone": "+32", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "ch": {"name": "سويسرا", "code": "ch", "phone": "+41", "buyPrice": 6.00, "sellPrice": 3.50, "featured": False, "enabled": True},
    "at": {"name": "النمسا", "code": "at", "phone": "+43", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "se": {"name": "السويد", "code": "se", "phone": "+46", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "no": {"name": "النرويج", "code": "no", "phone": "+47", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "dk": {"name": "الدنمارك", "code": "dk", "phone": "+45", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "fi": {"name": "فنلندا", "code": "fi", "phone": "+358", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "pl": {"name": "بولندا", "code": "pl", "phone": "+48", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "cz": {"name": "التشيك", "code": "cz", "phone": "+420", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "hu": {"name": "المجر", "code": "hu", "phone": "+36", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "ro": {"name": "رومانيا", "code": "ro", "phone": "+40", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "bg": {"name": "بلغاريا", "code": "bg", "phone": "+359", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "gr": {"name": "اليونان", "code": "gr", "phone": "+30", "buyPrice": 4.50, "sellPrice": 2.25, "featured": False, "enabled": True},
    "pt": {"name": "البرتغال", "code": "pt", "phone": "+351", "buyPrice": 4.50, "sellPrice": 2.25, "featured": False, "enabled": True},
    "ie": {"name": "أيرلندا", "code": "ie", "phone": "+353", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "ru": {"name": "روسيا", "code": "ru", "phone": "+7", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "ua": {"name": "أوكرانيا", "code": "ua", "phone": "+380", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "tr": {"name": "تركيا", "code": "tr", "phone": "+90", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "in": {"name": "الهند", "code": "in", "phone": "+91", "buyPrice": 2.00, "sellPrice": 1.00, "featured": False, "enabled": True},
    "pk": {"name": "باكستان", "code": "pk", "phone": "+92", "buyPrice": 2.00, "sellPrice": 1.00, "featured": False, "enabled": True},
    "bd": {"name": "بنغلاديش", "code": "bd", "phone": "+880", "buyPrice": 2.00, "sellPrice": 1.00, "featured": False, "enabled": True},
    "id": {"name": "إندونيسيا", "code": "id", "phone": "+62", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "my": {"name": "ماليزيا", "code": "my", "phone": "+60", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "th": {"name": "تايلاند", "code": "th", "phone": "+66", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "vn": {"name": "فيتنام", "code": "vn", "phone": "+84", "buyPrice": 2.00, "sellPrice": 1.00, "featured": False, "enabled": True},
    "ph": {"name": "الفلبين", "code": "ph", "phone": "+63", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "sg": {"name": "سنغافورة", "code": "sg", "phone": "+65", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "jp": {"name": "اليابان", "code": "jp", "phone": "+81", "buyPrice": 6.00, "sellPrice": 3.50, "featured": False, "enabled": True},
    "kr": {"name": "كوريا الجنوبية", "code": "kr", "phone": "+82", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "cn": {"name": "الصين", "code": "cn", "phone": "+86", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "hk": {"name": "هونغ كونغ", "code": "hk", "phone": "+852", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "tw": {"name": "تايوان", "code": "tw", "phone": "+886", "buyPrice": 4.50, "sellPrice": 2.25, "featured": False, "enabled": True},
    "au": {"name": "أستراليا", "code": "au", "phone": "+61", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "nz": {"name": "نيوزيلندا", "code": "nz", "phone": "+64", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "ca": {"name": "كندا", "code": "ca", "phone": "+1", "buyPrice": 5.50, "sellPrice": 3.00, "featured": False, "enabled": True},
    "mx": {"name": "المكسيك", "code": "mx", "phone": "+52", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "br": {"name": "البرازيل", "code": "br", "phone": "+55", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "ar": {"name": "الأرجنتين", "code": "ar", "phone": "+54", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "cl": {"name": "تشيلي", "code": "cl", "phone": "+56", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "co": {"name": "كولومبيا", "code": "co", "phone": "+57", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "pe": {"name": "بيرو", "code": "pe", "phone": "+51", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "ve": {"name": "فنزويلا", "code": "ve", "phone": "+58", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "za": {"name": "جنوب أفريقيا", "code": "za", "phone": "+27", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "ng": {"name": "نيجيريا", "code": "ng", "phone": "+234", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "ke": {"name": "كينيا", "code": "ke", "phone": "+254", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "gh": {"name": "غانا", "code": "gh", "phone": "+233", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "il": {"name": "إسرائيل", "code": "il", "phone": "+972", "buyPrice": 5.00, "sellPrice": 2.75, "featured": False, "enabled": True},
    "ir": {"name": "إيران", "code": "ir", "phone": "+98", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "af": {"name": "أفغانستان", "code": "af", "phone": "+93", "buyPrice": 2.00, "sellPrice": 1.00, "featured": False, "enabled": True},
    "kz": {"name": "كازاخستان", "code": "kz", "phone": "+7", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "uz": {"name": "أوزبكستان", "code": "uz", "phone": "+998", "buyPrice": 2.00, "sellPrice": 1.00, "featured": False, "enabled": True},
    "az": {"name": "أذربيجان", "code": "az", "phone": "+994", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "ge": {"name": "جورجيا", "code": "ge", "phone": "+995", "buyPrice": 3.00, "sellPrice": 1.50, "featured": False, "enabled": True},
    "am": {"name": "أرمينيا", "code": "am", "phone": "+374", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "by": {"name": "بيلاروسيا", "code": "by", "phone": "+375", "buyPrice": 2.50, "sellPrice": 1.25, "featured": False, "enabled": True},
    "lt": {"name": "ليتوانيا", "code": "lt", "phone": "+370", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "lv": {"name": "لاتفيا", "code": "lv", "phone": "+371", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "ee": {"name": "إستونيا", "code": "ee", "phone": "+372", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "hr": {"name": "كرواتيا", "code": "hr", "phone": "+385", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "rs": {"name": "صربيا", "code": "rs", "phone": "+381", "buyPrice": 3.50, "sellPrice": 1.75, "featured": False, "enabled": True},
    "si": {"name": "سلوفينيا", "code": "si", "phone": "+386", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
    "sk": {"name": "سلوفاكيا", "code": "sk", "phone": "+421", "buyPrice": 4.00, "sellPrice": 2.00, "featured": False, "enabled": True},
}

# ==================== FIREBASE HELPER FUNCTIONS ====================

def fb_get(path):
    """Get data from Firebase"""
    try:
        response = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return response.json()
    except Exception as e:
        print(f"Firebase GET error: {e}")
        return None

def fb_set(path, data):
    """Set data in Firebase"""
    try:
        response = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Firebase SET error: {e}")
        return None

def fb_push(path, data):
    """Push new data to Firebase (creates unique ID)"""
    try:
        response = requests.post(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Firebase PUSH error: {e}")
        return None

def fb_update(path, data):
    """Update data in Firebase"""
    try:
        response = requests.patch(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Firebase UPDATE error: {e}")
        return None

def fb_delete(path):
    """Delete data from Firebase"""
    try:
        response = requests.delete(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return True
    except Exception as e:
        print(f"Firebase DELETE error: {e}")
        return False

# ==================== INITIALIZATION ====================

def init_database():
    """Initialize database with countries if empty"""
    countries = fb_get("countries")
    if not countries:
        print("Initializing countries database...")
        fb_set("countries", COUNTRIES)
        print("Countries database initialized!")

# Run initialization
init_database()

# ==================== HELPER FUNCTIONS ====================

def generate_token():
    """Generate a secure random token"""
    return secrets.token_hex(32)

def generate_referral_code():
    """Generate a unique referral code"""
    return f"TN{secrets.token_hex(4).upper()}"

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_token(token):
    """Get user data by token"""
    users = fb_get("users")
    if users:
        for uid, user in users.items():
            if user.get("token") == token:
                user["uid"] = uid
                return user
    return None

def get_user_by_device(device_id):
    """Get user by device ID"""
    users = fb_get("users")
    if users:
        for uid, user in users.items():
            if user.get("deviceId") == device_id:
                user["uid"] = uid
                return user
    return None

def get_user_by_email(email):
    """Get user by email"""
    users = fb_get("users")
    if users:
        for uid, user in users.items():
            if user.get("email") == email:
                user["uid"] = uid
                return user
    return None

def get_user_by_referral(code):
    """Get user by referral code"""
    users = fb_get("users")
    if users:
        for uid, user in users.items():
            if user.get("referralCode") == code:
                user["uid"] = uid
                return user
    return None

def get_country_stock(country_code):
    """Get available numbers count for a country"""
    numbers = fb_get("numbers")
    if not numbers:
        return 0
    count = 0
    for nid, num in numbers.items():
        if num.get("country") == country_code and num.get("status") == "available":
            count += 1
    return count

def detect_country_from_phone(phone):
    """Detect country code from phone number"""
    phone = phone.replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Sort by phone prefix length (longest first)
    sorted_countries = sorted(COUNTRIES.items(), key=lambda x: len(x[1]["phone"]), reverse=True)
    
    for code, country in sorted_countries:
        if phone.startswith(country["phone"]):
            return code
    return None

# ==================== AUTH DECORATOR ====================

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"success": False, "error": "التوكن مطلوب"}), 401
        
        user = get_user_by_token(token)
        if not user:
            return jsonify({"success": False, "error": "جلسة غير صالحة"}), 401
        
        if user.get("banned"):
            return jsonify({"success": False, "error": "تم حظر حسابك"}), 403
        
        request.user = user
        return f(*args, **kwargs)
    return decorated

# ==================== TELEGRAM FUNCTIONS ====================

async def tg_send_code_async(phone):
    """Send verification code to phone"""
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        result = await client.send_code_request(phone)
        session_string = client.session.save()
        
        # Store temporarily
        pending_verifications[phone] = {
            "session": session_string,
            "phone_code_hash": result.phone_code_hash,
            "timestamp": time.time()
        }
        
        await client.disconnect()
        return {"success": True}
    except PhoneNumberInvalidError:
        return {"success": False, "error": "رقم الهاتف غير صالح"}
    except FloodWaitError as e:
        return {"success": False, "error": f"يرجى الانتظار {e.seconds} ثانية"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def tg_verify_code_async(phone, code, password=None):
    """Verify the code and get session"""
    try:
        if phone not in pending_verifications:
            return {"success": False, "error": "لم يتم إرسال كود لهذا الرقم"}
        
        pending = pending_verifications[phone]
        client = TelegramClient(StringSession(pending["session"]), API_ID, API_HASH)
        await client.connect()
        
        try:
            await client.sign_in(phone, code, phone_code_hash=pending["phone_code_hash"])
        except SessionPasswordNeededError:
            if not password:
                await client.disconnect()
                return {"success": False, "error": "2FA_REQUIRED", "needs_2fa": True}
            await client.sign_in(password=password)
        except PhoneCodeInvalidError:
            await client.disconnect()
            return {"success": False, "error": "الكود غير صحيح"}
        except PhoneCodeExpiredError:
            await client.disconnect()
            return {"success": False, "error": "انتهت صلاحية الكود"}
        
        session_string = client.session.save()
        await client.disconnect()
        
        # Clean up
        del pending_verifications[phone]
        
        return {"success": True, "session": session_string}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def tg_get_messages_async(session_string):
    """Get messages from Telegram account"""
    try:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return {"success": False, "error": "الجلسة غير صالحة"}
        
        messages = []
        codes = []
        
        # Get messages from Telegram official channel (verification codes)
        async for message in client.iter_messages(777000, limit=10):
            if message.text:
                messages.append({
                    "text": message.text,
                    "date": str(message.date)
                })
                # Extract codes using regex
                found_codes = re.findall(r'\b(\d{5,6})\b', message.text)
                codes.extend(found_codes)
        
        await client.disconnect()
        
        return {
            "success": True,
            "messages": messages,
            "codes": list(set(codes))  # Remove duplicates
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ==================== BLOCKCHAIN FUNCTIONS ====================

def verify_bsc_transaction(txid):
    """Verify USDT BEP20 transaction"""
    try:
        # Get transaction details
        url = f"https://api.bscscan.com/api?module=proxy&action=eth_getTransactionByHash&txhash={txid}&apikey={BSCSCAN_API_KEY}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if data.get("result") is None:
            return {"success": False, "error": "المعاملة غير موجودة"}
        
        tx = data["result"]
        
        # Check if it's a USDT contract interaction
        if tx.get("to", "").lower() != USDT_CONTRACT.lower():
            return {"success": False, "error": "ليست معاملة USDT"}
        
        # Decode input data
        input_data = tx.get("input", "")
        if not input_data.startswith("0xa9059cbb"):  # transfer method signature
            return {"success": False, "error": "ليست معاملة تحويل"}
        
        # Extract recipient and amount from input data
        recipient = "0x" + input_data[34:74]
        amount_hex = input_data[74:138]
        amount_wei = int(amount_hex, 16)
        amount = amount_wei / (10 ** 18)  # USDT has 18 decimals on BSC
        
        # Verify recipient
        if recipient.lower() != DEPOSIT_WALLET.lower():
            return {"success": False, "error": "المستلم غير صحيح"}
        
        # Get transaction receipt to verify success
        receipt_url = f"https://api.bscscan.com/api?module=proxy&action=eth_getTransactionReceipt&txhash={txid}&apikey={BSCSCAN_API_KEY}"
        receipt_response = requests.get(receipt_url, timeout=15)
        receipt_data = receipt_response.json()
        
        if receipt_data.get("result") is None:
            return {"success": False, "error": "لم يتم تأكيد المعاملة بعد"}
        
        if receipt_data["result"].get("status") != "0x1":
            return {"success": False, "error": "فشلت المعاملة"}
        
        return {
            "success": True,
            "amount": round(amount, 2),
            "from": tx.get("from"),
            "txid": txid
        }
    except Exception as e:
        print(f"BSC verification error: {e}")
        return {"success": False, "error": "خطأ في التحقق من المعاملة"}

# ==================== API ROUTES ====================

@app.route("/")
def serve_frontend():
    """Serve the frontend HTML file"""
    try:
        return send_file("index.html")
    except:
        return "TeleNum API Server Running", 200

@app.route("/api/stats")
def get_stats():
    """Get general statistics"""
    numbers = fb_get("numbers") or {}
    available = sum(1 for n in numbers.values() if n.get("status") == "available")
    countries = fb_get("countries") or COUNTRIES
    
    return jsonify({
        "success": True,
        "stats": {
            "availableNumbers": available,
            "totalCountries": len(countries),
            "walletAddress": DEPOSIT_WALLET
        }
    })

@app.route("/api/countries")
def get_countries():
    """Get all countries with stock"""
    countries = fb_get("countries") or COUNTRIES
    result = []
    
    for code, country in countries.items():
        stock = get_country_stock(code)
        result.append({
            "code": code,
            "name": country["name"],
            "phone": country["phone"],
            "buyPrice": country["buyPrice"],
            "sellPrice": country["sellPrice"],
            "featured": country.get("featured", False),
            "enabled": country.get("enabled", True),
            "stock": stock
        })
    
    # Sort: featured first, then by name
    result.sort(key=lambda x: (not x["featured"], x["name"]))
    
    return jsonify({"success": True, "countries": result})

# ==================== AUTH ROUTES ====================

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register new user"""
    data = request.json
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    device_id = data.get("deviceId", "")
    fingerprint = data.get("fingerprint", {})
    referral_code = data.get("referralCode", "").strip()
    
    # Validation
    if not username or not email or not password:
        return jsonify({"success": False, "error": "جميع الحقول مطلوبة"})
    
    if len(password) < 6:
        return jsonify({"success": False, "error": "كلمة المرور يجب أن تكون 6 أحرف على الأقل"})
    
    # Check if email exists
    if get_user_by_email(email):
        return jsonify({"success": False, "error": "البريد الإلكتروني مستخدم مسبقاً"})
    
    # Check if device is registered
    existing_device = get_user_by_device(device_id)
    if existing_device:
        return jsonify({"success": False, "error": "هذا الجهاز مسجل بحساب آخر"})
    
    # Create user
    token = generate_token()
    user_referral = generate_referral_code()
    balance = 0.0
    
    # Handle referral
    referred_by = None
    if referral_code:
        referrer = get_user_by_referral(referral_code)
        if referrer:
            referred_by = referrer["uid"]
            balance = 0.05  # Bonus for new user
            # Add bonus to referrer
            new_balance = float(referrer.get("balance", 0)) + 0.05
            referral_count = int(referrer.get("referralCount", 0)) + 1
            fb_update(f"users/{referrer['uid']}", {
                "balance": new_balance,
                "referralCount": referral_count
            })
    
    user_data = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "balance": balance,
        "token": token,
        "deviceId": device_id,
        "fingerprint": fingerprint,
        "referralCode": user_referral,
        "referredBy": referred_by,
        "referralCount": 0,
        "banned": False,
        "createdAt": datetime.now().isoformat()
    }
    
    result = fb_push("users", user_data)
    
    if result and "name" in result:
        user_data["uid"] = result["name"]
        return jsonify({
            "success": True,
            "user": {
                "uid": result["name"],
                "username": username,
                "email": email,
                "balance": balance,
                "referralCode": user_referral,
                "token": token
            }
        })
    
    return jsonify({"success": False, "error": "فشل إنشاء الحساب"})

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login user"""
    data = request.json
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    device_id = data.get("deviceId", "")
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"success": False, "error": "البريد الإلكتروني غير مسجل"})
    
    if user.get("password") != hash_password(password):
        return jsonify({"success": False, "error": "كلمة المرور غير صحيحة"})
    
    if user.get("banned"):
        return jsonify({"success": False, "error": "تم حظر حسابك"})
    
    # Update token and device
    new_token = generate_token()
    fb_update(f"users/{user['uid']}", {
        "token": new_token,
        "deviceId": device_id,
        "lastLogin": datetime.now().isoformat()
    })
    
    return jsonify({
        "success": True,
        "user": {
            "uid": user["uid"],
            "username": user["username"],
            "email": user["email"],
            "balance": float(user.get("balance", 0)),
            "referralCode": user.get("referralCode"),
            "referralCount": int(user.get("referralCount", 0)),
            "token": new_token
        }
    })

@app.route("/api/auth/auto-login", methods=["POST"])
def auto_login():
    """Auto login by device ID"""
    data = request.json
    device_id = data.get("deviceId", "")
    
    if not device_id:
        return jsonify({"success": False, "error": "معرف الجهاز مطلوب"})
    
    user = get_user_by_device(device_id)
    if not user:
        return jsonify({"success": False, "error": "لا يوجد حساب مرتبط بهذا الجهاز"})
    
    if user.get("banned"):
        return jsonify({"success": False, "error": "تم حظر حسابك"})
    
    # Generate new token
    new_token = generate_token()
    fb_update(f"users/{user['uid']}", {
        "token": new_token,
        "lastLogin": datetime.now().isoformat()
    })
    
    return jsonify({
        "success": True,
        "user": {
            "uid": user["uid"],
            "username": user["username"],
            "email": user["email"],
            "balance": float(user.get("balance", 0)),
            "referralCode": user.get("referralCode"),
            "referralCount": int(user.get("referralCount", 0)),
            "token": new_token
        }
    })

@app.route("/api/user")
@require_auth
def get_user():
    """Get current user data"""
    user = request.user
    return jsonify({
        "success": True,
        "user": {
            "uid": user["uid"],
            "username": user["username"],
            "email": user["email"],
            "balance": float(user.get("balance", 0)),
            "referralCode": user.get("referralCode"),
            "referralCount": int(user.get("referralCount", 0))
        }
    })

# ==================== BUY/SELL ROUTES ====================

@app.route("/api/buy", methods=["POST"])
@require_auth
def buy_number():
    """Buy a number"""
    data = request.json
    country_code = data.get("country")
    user = request.user
    
    # Get country info
    countries = fb_get("countries") or COUNTRIES
    country = countries.get(country_code)
    
    if not country:
        return jsonify({"success": False, "error": "الدولة غير موجودة"})
    
    if not country.get("enabled", True):
        return jsonify({"success": False, "error": "هذه الدولة غير متاحة حالياً"})
    
    price = float(country["buyPrice"])
    balance = float(user.get("balance", 0))
    
    if balance < price:
        return jsonify({"success": False, "error": "رصيدك غير كافٍ"})
    
    # Find available number
    numbers = fb_get("numbers") or {}
    available_number = None
    number_id = None
    
    for nid, num in numbers.items():
        if num.get("country") == country_code and num.get("status") == "available":
            available_number = num
            number_id = nid
            break
    
    if not available_number:
        return jsonify({"success": False, "error": "لا توجد أرقام متاحة لهذه الدولة"})
    
    # Deduct balance
    new_balance = balance - price
    fb_update(f"users/{user['uid']}", {"balance": new_balance})
    
    # Update number status
    fb_update(f"numbers/{number_id}", {"status": "sold"})
    
    # Create purchase record
    purchase = {
        "userId": user["uid"],
        "numberId": number_id,
        "phone": available_number["phone"],
        "country": country_code,
        "countryName": country["name"],
        "price": price,
        "status": "active",
        "session": available_number.get("session"),
        "purchasedAt": datetime.now().isoformat()
    }
    
    result = fb_push("purchases", purchase)
    
    return jsonify({
        "success": True,
        "purchase": {
            "id": result["name"],
            "phone": available_number["phone"],
            "country": country["name"],
            "price": price
        },
        "newBalance": new_balance
    })

@app.route("/api/my-numbers")
@require_auth
def get_my_numbers():
    """Get user's purchased numbers"""
    user = request.user
    purchases = fb_get("purchases") or {}
    
    my_numbers = []
    for pid, purchase in purchases.items():
        if purchase.get("userId") == user["uid"]:
            my_numbers.append({
                "id": pid,
                "phone": purchase["phone"],
                "country": purchase.get("countryName", purchase.get("country")),
                "status": purchase.get("status", "active"),
                "purchasedAt": purchase.get("purchasedAt")
            })
    
    # Sort by date, newest first
    my_numbers.sort(key=lambda x: x.get("purchasedAt", ""), reverse=True)
    
    return jsonify({"success": True, "numbers": my_numbers})

@app.route("/api/messages/<purchase_id>")
@require_auth
def get_messages(purchase_id):
    """Get messages for a purchased number"""
    user = request.user
    
    # Get purchase
    purchase = fb_get(f"purchases/{purchase_id}")
    if not purchase:
        return jsonify({"success": False, "error": "عملية الشراء غير موجودة"})
    
    if purchase.get("userId") != user["uid"]:
        return jsonify({"success": False, "error": "غير مصرح"})
    
    if purchase.get("status") == "completed":
        return jsonify({"success": False, "error": "تم إنهاء هذا الرقم"})
    
    session = purchase.get("session")
    if not session:
        return jsonify({"success": False, "error": "لا توجد جلسة لهذا الرقم"})
    
    # Get messages from Telegram
    result = run_async(tg_get_messages_async(session))
    
    return jsonify(result)

@app.route("/api/complete", methods=["POST"])
@require_auth
def complete_number():
    """Complete/end a number usage"""
    data = request.json
    purchase_id = data.get("purchaseId")
    user = request.user
    
    purchase = fb_get(f"purchases/{purchase_id}")
    if not purchase:
        return jsonify({"success": False, "error": "عملية الشراء غير موجودة"})
    
    if purchase.get("userId") != user["uid"]:
        return jsonify({"success": False, "error": "غير مصرح"})
    
    fb_update(f"purchases/{purchase_id}", {
        "status": "completed",
        "completedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True})

# ==================== SELL ROUTES ====================

@app.route("/api/sell/send-code", methods=["POST"])
@require_auth
def sell_send_code():
    """Send verification code for selling a number"""
    data = request.json
    phone = data.get("phone", "").strip()
    
    if not phone:
        return jsonify({"success": False, "error": "رقم الهاتف مطلوب"})
    
    # Normalize phone
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Check if country is supported
    country_code = detect_country_from_phone(phone)
    if not country_code:
        return jsonify({"success": False, "error": "الدولة غير مدعومة"})
    
    result = run_async(tg_send_code_async(phone))
    return jsonify(result)

@app.route("/api/sell/verify", methods=["POST"])
@require_auth
def sell_verify():
    """Verify code and create sell request"""
    data = request.json
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()
    password = data.get("password")
    user = request.user
    
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Verify code
    result = run_async(tg_verify_code_async(phone, code, password))
    
    if not result["success"]:
        return jsonify(result)
    
    # Get country info
    country_code = detect_country_from_phone(phone)
    countries = fb_get("countries") or COUNTRIES
    country = countries.get(country_code, {})
    sell_price = country.get("sellPrice", 1.0)
    
    # Create sell request
    sell_request = {
        "userId": user["uid"],
        "phone": phone,
        "country": country_code,
        "countryName": country.get("name", "غير معروف"),
        "session": result["session"],
        "price": sell_price,
        "status": "pending",
        "createdAt": datetime.now().isoformat()
    }
    
    fb_push("sell_requests", sell_request)
    
    return jsonify({
        "success": True,
        "message": "تم إرسال طلب البيع بنجاح. سيتم مراجعته خلال 24 ساعة.",
        "price": sell_price
    })

# ==================== FINANCIAL ROUTES ====================

@app.route("/api/deposit", methods=["POST"])
@require_auth
def deposit():
    """Process deposit"""
    data = request.json
    txid = data.get("txid", "").strip()
    user = request.user
    
    if not txid:
        return jsonify({"success": False, "error": "معرف المعاملة مطلوب"})
    
    # Check if TXID already used
    deposits = fb_get("deposits") or {}
    for dep in deposits.values():
        if dep.get("txid") == txid:
            return jsonify({"success": False, "error": "هذه المعاملة مستخدمة مسبقاً"})
    
    pending = fb_get("pending_deposits") or {}
    for dep in pending.values():
        if dep.get("txid") == txid:
            return jsonify({"success": False, "error": "هذه المعاملة قيد المراجعة"})
    
    # Verify transaction
    result = verify_bsc_transaction(txid)
    
    if result["success"]:
        # Auto-approved deposit
        amount = result["amount"]
        new_balance = float(user.get("balance", 0)) + amount
        
        fb_update(f"users/{user['uid']}", {"balance": new_balance})
        
        fb_push("deposits", {
            "userId": user["uid"],
            "txid": txid,
            "amount": amount,
            "status": "approved",
            "auto": True,
            "createdAt": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "message": f"تم إضافة ${amount} لرصيدك بنجاح!",
            "amount": amount,
            "newBalance": new_balance
        })
    else:
        # Add to pending for manual review
        fb_push("pending_deposits", {
            "userId": user["uid"],
            "username": user["username"],
            "txid": txid,
            "error": result.get("error"),
            "status": "pending",
            "createdAt": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "message": "تم إرسال طلب الإيداع للمراجعة. سيتم التحقق خلال 24 ساعة.",
            "pending": True
        })

@app.route("/api/withdraw", methods=["POST"])
@require_auth
def withdraw():
    """Request withdrawal"""
    data = request.json
    amount = float(data.get("amount", 0))
    address = data.get("address", "").strip()
    user = request.user
    
    if amount < 1:
        return jsonify({"success": False, "error": "الحد الأدنى للسحب هو $1"})
    
    if not address or len(address) != 42 or not address.startswith("0x"):
        return jsonify({"success": False, "error": "عنوان المحفظة غير صالح"})
    
    balance = float(user.get("balance", 0))
    if balance < amount:
        return jsonify({"success": False, "error": "رصيدك غير كافٍ"})
    
    # Deduct balance
    new_balance = balance - amount
    fb_update(f"users/{user['uid']}", {"balance": new_balance})
    
    # Create withdrawal request
    fb_push("withdrawals", {
        "userId": user["uid"],
        "username": user["username"],
        "amount": amount,
        "address": address,
        "status": "pending",
        "createdAt": datetime.now().isoformat()
    })
    
    return jsonify({
        "success": True,
        "message": "تم إرسال طلب السحب بنجاح",
        "newBalance": new_balance
    })

# ==================== ADMIN ROUTES ====================

@app.route("/api/admin/dashboard")
@require_auth
def admin_dashboard():
    """Get admin dashboard stats"""
    users = fb_get("users") or {}
    numbers = fb_get("numbers") or {}
    sell_requests = fb_get("sell_requests") or {}
    withdrawals = fb_get("withdrawals") or {}
    pending_deposits = fb_get("pending_deposits") or {}
    
    available_numbers = sum(1 for n in numbers.values() if n.get("status") == "available")
    pending_sells = sum(1 for s in sell_requests.values() if s.get("status") == "pending")
    pending_withdrawals = sum(1 for w in withdrawals.values() if w.get("status") == "pending")
    pending_deps = sum(1 for d in pending_deposits.values() if d.get("status") == "pending")
    
    return jsonify({
        "success": True,
        "stats": {
            "totalUsers": len(users),
            "availableNumbers": available_numbers,
            "pendingSells": pending_sells,
            "pendingWithdrawals": pending_withdrawals,
            "pendingDeposits": pending_deps
        }
    })

@app.route("/api/admin/users")
@require_auth
def admin_users():
    """Get all users"""
    users = fb_get("users") or {}
    result = []
    
    for uid, user in users.items():
        result.append({
            "uid": uid,
            "username": user.get("username"),
            "email": user.get("email"),
            "balance": float(user.get("balance", 0)),
            "banned": user.get("banned", False),
            "referralCount": int(user.get("referralCount", 0)),
            "createdAt": user.get("createdAt")
        })
    
    return jsonify({"success": True, "users": result})

@app.route("/api/admin/user/<uid>/ban", methods=["POST"])
@require_auth
def admin_ban_user(uid):
    """Ban/unban user"""
    data = request.json
    banned = data.get("banned", True)
    
    fb_update(f"users/{uid}", {"banned": banned})
    
    return jsonify({"success": True})

@app.route("/api/admin/user/<uid>/add-balance", methods=["POST"])
@require_auth
def admin_add_balance(uid):
    """Add balance to user"""
    data = request.json
    amount = float(data.get("amount", 0))
    
    user = fb_get(f"users/{uid}")
    if not user:
        return jsonify({"success": False, "error": "المستخدم غير موجود"})
    
    new_balance = float(user.get("balance", 0)) + amount
    fb_update(f"users/{uid}", {"balance": new_balance})
    
    return jsonify({"success": True, "newBalance": new_balance})

@app.route("/api/admin/sells")
@require_auth
def admin_sells():
    """Get pending sell requests"""
    sell_requests = fb_get("sell_requests") or {}
    result = []
    
    for sid, req in sell_requests.items():
        if req.get("status") == "pending":
            result.append({
                "id": sid,
                "phone": req.get("phone"),
                "country": req.get("countryName"),
                "price": req.get("price"),
                "userId": req.get("userId"),
                "createdAt": req.get("createdAt")
            })
    
    return jsonify({"success": True, "requests": result})

@app.route("/api/admin/approve-sell", methods=["POST"])
@require_auth
def admin_approve_sell():
    """Approve sell request"""
    data = request.json
    sell_id = data.get("id")
    
    sell_req = fb_get(f"sell_requests/{sell_id}")
    if not sell_req:
        return jsonify({"success": False, "error": "الطلب غير موجود"})
    
    # Add number to inventory
    fb_push("numbers", {
        "phone": sell_req["phone"],
        "country": sell_req.get("country"),
        "session": sell_req.get("session"),
        "status": "available",
        "addedAt": datetime.now().isoformat()
    })
    
    # Add balance to seller
    user = fb_get(f"users/{sell_req['userId']}")
    if user:
        new_balance = float(user.get("balance", 0)) + float(sell_req.get("price", 0))
        fb_update(f"users/{sell_req['userId']}", {"balance": new_balance})
    
    # Update request status
    fb_update(f"sell_requests/{sell_id}", {
        "status": "approved",
        "approvedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True})

@app.route("/api/admin/reject-sell", methods=["POST"])
@require_auth
def admin_reject_sell():
    """Reject sell request"""
    data = request.json
    sell_id = data.get("id")
    
    fb_update(f"sell_requests/{sell_id}", {
        "status": "rejected",
        "rejectedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True})

@app.route("/api/admin/withdrawals")
@require_auth
def admin_withdrawals():
    """Get pending withdrawals"""
    withdrawals = fb_get("withdrawals") or {}
    result = []
    
    for wid, w in withdrawals.items():
        if w.get("status") == "pending":
            result.append({
                "id": wid,
                "username": w.get("username"),
                "amount": w.get("amount"),
                "address": w.get("address"),
                "userId": w.get("userId"),
                "createdAt": w.get("createdAt")
            })
    
    return jsonify({"success": True, "withdrawals": result})

@app.route("/api/admin/approve-withdrawal", methods=["POST"])
@require_auth
def admin_approve_withdrawal():
    """Approve withdrawal"""
    data = request.json
    wid = data.get("id")
    txid = data.get("txid", "")
    
    fb_update(f"withdrawals/{wid}", {
        "status": "approved",
        "txid": txid,
        "approvedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True})

@app.route("/api/admin/reject-withdrawal", methods=["POST"])
@require_auth
def admin_reject_withdrawal():
    """Reject withdrawal and refund"""
    data = request.json
    wid = data.get("id")
    
    withdrawal = fb_get(f"withdrawals/{wid}")
    if withdrawal:
        # Refund user
        user = fb_get(f"users/{withdrawal['userId']}")
        if user:
            new_balance = float(user.get("balance", 0)) + float(withdrawal.get("amount", 0))
            fb_update(f"users/{withdrawal['userId']}", {"balance": new_balance})
    
    fb_update(f"withdrawals/{wid}", {
        "status": "rejected",
        "rejectedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True})

@app.route("/api/admin/pending-deposits")
@require_auth
def admin_pending_deposits():
    """Get pending deposits"""
    pending = fb_get("pending_deposits") or {}
    result = []
    
    for did, d in pending.items():
        if d.get("status") == "pending":
            result.append({
                "id": did,
                "username": d.get("username"),
                "txid": d.get("txid"),
                "error": d.get("error"),
                "userId": d.get("userId"),
                "createdAt": d.get("createdAt")
            })
    
    return jsonify({"success": True, "deposits": result})

@app.route("/api/admin/approve-deposit", methods=["POST"])
@require_auth
def admin_approve_deposit():
    """Manually approve deposit"""
    data = request.json
    did = data.get("id")
    amount = float(data.get("amount", 0))
    
    deposit = fb_get(f"pending_deposits/{did}")
    if not deposit:
        return jsonify({"success": False, "error": "الإيداع غير موجود"})
    
    # Add balance
    user = fb_get(f"users/{deposit['userId']}")
    if user:
        new_balance = float(user.get("balance", 0)) + amount
        fb_update(f"users/{deposit['userId']}", {"balance": new_balance})
    
    # Move to deposits
    fb_push("deposits", {
        "userId": deposit["userId"],
        "txid": deposit["txid"],
        "amount": amount,
        "status": "approved",
        "auto": False,
        "createdAt": datetime.now().isoformat()
    })
    
    # Remove from pending
    fb_delete(f"pending_deposits/{did}")
    
    return jsonify({"success": True})

@app.route("/api/admin/reject-deposit", methods=["POST"])
@require_auth
def admin_reject_deposit():
    """Reject deposit"""
    data = request.json
    did = data.get("id")
    
    fb_delete(f"pending_deposits/{did}")
    
    return jsonify({"success": True})

@app.route("/api/admin/numbers")
@require_auth
def admin_numbers():
    """Get all numbers"""
    numbers = fb_get("numbers") or {}
    result = []
    
    for nid, num in numbers.items():
        if num.get("status") == "available":
            result.append({
                "id": nid,
                "phone": num.get("phone"),
                "country": num.get("country"),
                "addedAt": num.get("addedAt")
            })
    
    return jsonify({"success": True, "numbers": result})

@app.route("/api/admin/add-send-code", methods=["POST"])
@require_auth
def admin_add_send_code():
    """Send code for adding new number (admin)"""
    data = request.json
    phone = data.get("phone", "").strip()
    
    if not phone.startswith("+"):
        phone = "+" + phone
    
    result = run_async(tg_send_code_async(phone))
    
    if result["success"]:
        admin_pending_verifications[phone] = True
    
    return jsonify(result)

@app.route("/api/admin/add-verify", methods=["POST"])
@require_auth
def admin_add_verify():
    """Verify code and add number to inventory"""
    data = request.json
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()
    password = data.get("password")
    
    if not phone.startswith("+"):
        phone = "+" + phone
    
    result = run_async(tg_verify_code_async(phone, code, password))
    
    if not result["success"]:
        return jsonify(result)
    
    # Detect country
    country_code = detect_country_from_phone(phone)
    
    # Add number
    fb_push("numbers", {
        "phone": phone,
        "country": country_code,
        "session": result["session"],
        "status": "available",
        "addedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True, "message": "تم إضافة الرقم بنجاح"})

@app.route("/api/admin/add-session", methods=["POST"])
@require_auth
def admin_add_session():
    """Add number directly via session string"""
    data = request.json
    phone = data.get("phone", "").strip()
    session = data.get("session", "").strip()
    
    if not phone or not session:
        return jsonify({"success": False, "error": "الرقم والجلسة مطلوبان"})
    
    if not phone.startswith("+"):
        phone = "+" + phone
    
    country_code = detect_country_from_phone(phone)
    
    fb_push("numbers", {
        "phone": phone,
        "country": country_code,
        "session": session,
        "status": "available",
        "addedAt": datetime.now().isoformat()
    })
    
    return jsonify({"success": True})

@app.route("/api/admin/delete-number", methods=["POST"])
@require_auth
def admin_delete_number():
    """Delete a number"""
    data = request.json
    nid = data.get("id")
    
    fb_delete(f"numbers/{nid}")
    
    return jsonify({"success": True})

@app.route("/api/admin/delete-all", methods=["POST"])
@require_auth
def admin_delete_all():
    """Delete all data (dangerous!)"""
    data = request.json
    confirm = data.get("confirm")
    
    if confirm != "DELETE":
        return jsonify({"success": False, "error": "التأكيد غير صحيح"})
    
    # Delete all collections
    fb_delete("users")
    fb_delete("numbers")
    fb_delete("purchases")
    fb_delete("sell_requests")
    fb_delete("deposits")
    fb_delete("pending_deposits")
    fb_delete("withdrawals")
    
    # Re-initialize countries
    fb_set("countries", COUNTRIES)
    
    return jsonify({"success": True, "message": "تم حذف جميع البيانات"})

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "المسار غير موجود"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "خطأ في السيرفر"}), 500

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    print("=" * 50)
    print("TeleNum Backend Server")
    print("=" * 50)
    print(f"Firebase URL: {FIREBASE_URL}")
    print(f"Deposit Wallet: {DEPOSIT_WALLET}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
