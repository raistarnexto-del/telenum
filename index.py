from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import hashlib
import secrets
import requests
import asyncio
import re
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# ============== Configuration ==============
TELEGRAM_API_ID = 27241932
TELEGRAM_API_HASH = "218edeae0f4cf9053d7dcbf3b1485048"
DEPOSIT_WALLET = "0x8E00A980274Cfb22798290586d97F7D185E3092D"
BSCSCAN_API_KEY = "8BHURRRGKXD35BPGQZ8E94CVEVAUNMD9UF"
USDT_CONTRACT_BSC = "0x55d398326f99059fF775485246999027B3197955"
FIREBASE_URL = "https://lolaminig-afea4-default-rtdb.firebaseio.com"

phone_sessions = {}

# ============== 90 Countries ==============
DEFAULT_COUNTRIES = {
    'KW': {'sell': 3.00, 'buy': 4.00, 'name': 'الكويت', 'flag': 'kw', 'code': '+965', 'enabled': True},
    'QA': {'sell': 2.50, 'buy': 3.50, 'name': 'قطر', 'flag': 'qa', 'code': '+974', 'enabled': True},
    'AE': {'sell': 2.00, 'buy': 2.80, 'name': 'الإمارات', 'flag': 'ae', 'code': '+971', 'enabled': True},
    'BH': {'sell': 2.00, 'buy': 2.80, 'name': 'البحرين', 'flag': 'bh', 'code': '+973', 'enabled': True},
    'OM': {'sell': 1.80, 'buy': 2.50, 'name': 'عُمان', 'flag': 'om', 'code': '+968', 'enabled': True},
    'SA': {'sell': 1.50, 'buy': 2.00, 'name': 'السعودية', 'flag': 'sa', 'code': '+966', 'enabled': True},
    'EG': {'sell': 0.40, 'buy': 0.60, 'name': 'مصر', 'flag': 'eg', 'code': '+20', 'enabled': True},
    'IQ': {'sell': 0.50, 'buy': 0.75, 'name': 'العراق', 'flag': 'iq', 'code': '+964', 'enabled': True},
    'JO': {'sell': 0.80, 'buy': 1.20, 'name': 'الأردن', 'flag': 'jo', 'code': '+962', 'enabled': True},
    'LB': {'sell': 0.70, 'buy': 1.00, 'name': 'لبنان', 'flag': 'lb', 'code': '+961', 'enabled': True},
    'SY': {'sell': 0.60, 'buy': 0.90, 'name': 'سوريا', 'flag': 'sy', 'code': '+963', 'enabled': True},
    'PS': {'sell': 0.80, 'buy': 1.20, 'name': 'فلسطين', 'flag': 'ps', 'code': '+970', 'enabled': True},
    'YE': {'sell': 0.50, 'buy': 0.80, 'name': 'اليمن', 'flag': 'ye', 'code': '+967', 'enabled': True},
    'LY': {'sell': 0.70, 'buy': 1.00, 'name': 'ليبيا', 'flag': 'ly', 'code': '+218', 'enabled': True},
    'SD': {'sell': 0.50, 'buy': 0.75, 'name': 'السودان', 'flag': 'sd', 'code': '+249', 'enabled': True},
    'MA': {'sell': 0.55, 'buy': 0.85, 'name': 'المغرب', 'flag': 'ma', 'code': '+212', 'enabled': True},
    'DZ': {'sell': 0.50, 'buy': 0.80, 'name': 'الجزائر', 'flag': 'dz', 'code': '+213', 'enabled': True},
    'TN': {'sell': 0.55, 'buy': 0.85, 'name': 'تونس', 'flag': 'tn', 'code': '+216', 'enabled': True},
    'MR': {'sell': 0.60, 'buy': 0.90, 'name': 'موريتانيا', 'flag': 'mr', 'code': '+222', 'enabled': True},
    'MM': {'sell': 0.20, 'buy': 0.35, 'name': 'ميانمار', 'flag': 'mm', 'code': '+95', 'enabled': True},
    'VN': {'sell': 0.22, 'buy': 0.38, 'name': 'فيتنام', 'flag': 'vn', 'code': '+84', 'enabled': True},
    'LA': {'sell': 0.25, 'buy': 0.40, 'name': 'لاوس', 'flag': 'la', 'code': '+856', 'enabled': True},
    'ID': {'sell': 0.28, 'buy': 0.45, 'name': 'إندونيسيا', 'flag': 'id', 'code': '+62', 'enabled': True},
    'KH': {'sell': 0.30, 'buy': 0.48, 'name': 'كمبوديا', 'flag': 'kh', 'code': '+855', 'enabled': True},
    'PH': {'sell': 0.32, 'buy': 0.50, 'name': 'الفلبين', 'flag': 'ph', 'code': '+63', 'enabled': True},
    'TH': {'sell': 0.45, 'buy': 0.70, 'name': 'تايلاند', 'flag': 'th', 'code': '+66', 'enabled': True},
    'MY': {'sell': 0.50, 'buy': 0.80, 'name': 'ماليزيا', 'flag': 'my', 'code': '+60', 'enabled': True},
    'IN': {'sell': 0.30, 'buy': 0.50, 'name': 'الهند', 'flag': 'in', 'code': '+91', 'enabled': True},
    'PK': {'sell': 0.35, 'buy': 0.55, 'name': 'باكستان', 'flag': 'pk', 'code': '+92', 'enabled': True},
    'BD': {'sell': 0.35, 'buy': 0.55, 'name': 'بنغلاديش', 'flag': 'bd', 'code': '+880', 'enabled': True},
    'LK': {'sell': 0.40, 'buy': 0.65, 'name': 'سريلانكا', 'flag': 'lk', 'code': '+94', 'enabled': True},
    'NP': {'sell': 0.40, 'buy': 0.65, 'name': 'نيبال', 'flag': 'np', 'code': '+977', 'enabled': True},
    'CN': {'sell': 0.80, 'buy': 1.30, 'name': 'الصين', 'flag': 'cn', 'code': '+86', 'enabled': True},
    'JP': {'sell': 2.00, 'buy': 3.00, 'name': 'اليابان', 'flag': 'jp', 'code': '+81', 'enabled': True},
    'KR': {'sell': 1.80, 'buy': 2.80, 'name': 'كوريا الجنوبية', 'flag': 'kr', 'code': '+82', 'enabled': True},
    'HK': {'sell': 1.50, 'buy': 2.30, 'name': 'هونغ كونغ', 'flag': 'hk', 'code': '+852', 'enabled': True},
    'TW': {'sell': 1.60, 'buy': 2.50, 'name': 'تايوان', 'flag': 'tw', 'code': '+886', 'enabled': True},
    'SG': {'sell': 1.80, 'buy': 2.80, 'name': 'سنغافورة', 'flag': 'sg', 'code': '+65', 'enabled': True},
    'RU': {'sell': 0.35, 'buy': 0.55, 'name': 'روسيا', 'flag': 'ru', 'code': '+7', 'enabled': True},
    'KZ': {'sell': 0.38, 'buy': 0.60, 'name': 'كازاخستان', 'flag': 'kz', 'code': '+7', 'enabled': True},
    'UZ': {'sell': 0.35, 'buy': 0.55, 'name': 'أوزبكستان', 'flag': 'uz', 'code': '+998', 'enabled': True},
    'KG': {'sell': 0.35, 'buy': 0.55, 'name': 'قيرغيزستان', 'flag': 'kg', 'code': '+996', 'enabled': True},
    'TJ': {'sell': 0.35, 'buy': 0.55, 'name': 'طاجيكستان', 'flag': 'tj', 'code': '+992', 'enabled': True},
    'TM': {'sell': 0.40, 'buy': 0.65, 'name': 'تركمانستان', 'flag': 'tm', 'code': '+993', 'enabled': True},
    'AZ': {'sell': 0.45, 'buy': 0.70, 'name': 'أذربيجان', 'flag': 'az', 'code': '+994', 'enabled': True},
    'GE': {'sell': 0.50, 'buy': 0.80, 'name': 'جورجيا', 'flag': 'ge', 'code': '+995', 'enabled': True},
    'AM': {'sell': 0.45, 'buy': 0.70, 'name': 'أرمينيا', 'flag': 'am', 'code': '+374', 'enabled': True},
    'UA': {'sell': 0.40, 'buy': 0.65, 'name': 'أوكرانيا', 'flag': 'ua', 'code': '+380', 'enabled': True},
    'PL': {'sell': 0.50, 'buy': 0.80, 'name': 'بولندا', 'flag': 'pl', 'code': '+48', 'enabled': True},
    'RO': {'sell': 0.45, 'buy': 0.70, 'name': 'رومانيا', 'flag': 'ro', 'code': '+40', 'enabled': True},
    'CZ': {'sell': 0.55, 'buy': 0.85, 'name': 'التشيك', 'flag': 'cz', 'code': '+420', 'enabled': True},
    'HU': {'sell': 0.50, 'buy': 0.80, 'name': 'المجر', 'flag': 'hu', 'code': '+36', 'enabled': True},
    'BG': {'sell': 0.45, 'buy': 0.70, 'name': 'بلغاريا', 'flag': 'bg', 'code': '+359', 'enabled': True},
    'RS': {'sell': 0.50, 'buy': 0.80, 'name': 'صربيا', 'flag': 'rs', 'code': '+381', 'enabled': True},
    'HR': {'sell': 0.55, 'buy': 0.85, 'name': 'كرواتيا', 'flag': 'hr', 'code': '+385', 'enabled': True},
    'SK': {'sell': 0.55, 'buy': 0.85, 'name': 'سلوفاكيا', 'flag': 'sk', 'code': '+421', 'enabled': True},
    'SI': {'sell': 0.60, 'buy': 0.95, 'name': 'سلوفينيا', 'flag': 'si', 'code': '+386', 'enabled': True},
    'LT': {'sell': 0.60, 'buy': 0.95, 'name': 'ليتوانيا', 'flag': 'lt', 'code': '+370', 'enabled': True},
    'LV': {'sell': 0.55, 'buy': 0.85, 'name': 'لاتفيا', 'flag': 'lv', 'code': '+371', 'enabled': True},
    'EE': {'sell': 0.60, 'buy': 0.95, 'name': 'إستونيا', 'flag': 'ee', 'code': '+372', 'enabled': True},
    'BY': {'sell': 0.40, 'buy': 0.65, 'name': 'بيلاروسيا', 'flag': 'by', 'code': '+375', 'enabled': True},
    'MD': {'sell': 0.40, 'buy': 0.65, 'name': 'مولدوفا', 'flag': 'md', 'code': '+373', 'enabled': True},
    'AL': {'sell': 0.50, 'buy': 0.80, 'name': 'ألبانيا', 'flag': 'al', 'code': '+355', 'enabled': True},
    'MK': {'sell': 0.50, 'buy': 0.80, 'name': 'مقدونيا', 'flag': 'mk', 'code': '+389', 'enabled': True},
    'BA': {'sell': 0.55, 'buy': 0.85, 'name': 'البوسنة', 'flag': 'ba', 'code': '+387', 'enabled': True},
    'ME': {'sell': 0.60, 'buy': 0.95, 'name': 'الجبل الأسود', 'flag': 'me', 'code': '+382', 'enabled': True},
    'GB': {'sell': 0.70, 'buy': 1.10, 'name': 'بريطانيا', 'flag': 'gb', 'code': '+44', 'enabled': True},
    'DE': {'sell': 1.00, 'buy': 1.60, 'name': 'ألمانيا', 'flag': 'de', 'code': '+49', 'enabled': True},
    'FR': {'sell': 0.90, 'buy': 1.40, 'name': 'فرنسا', 'flag': 'fr', 'code': '+33', 'enabled': True},
    'IT': {'sell': 0.85, 'buy': 1.30, 'name': 'إيطاليا', 'flag': 'it', 'code': '+39', 'enabled': True},
    'ES': {'sell': 0.80, 'buy': 1.25, 'name': 'إسبانيا', 'flag': 'es', 'code': '+34', 'enabled': True},
    'PT': {'sell': 0.75, 'buy': 1.15, 'name': 'البرتغال', 'flag': 'pt', 'code': '+351', 'enabled': True},
    'NL': {'sell': 1.20, 'buy': 1.90, 'name': 'هولندا', 'flag': 'nl', 'code': '+31', 'enabled': True},
    'BE': {'sell': 1.10, 'buy': 1.70, 'name': 'بلجيكا', 'flag': 'be', 'code': '+32', 'enabled': True},
    'AT': {'sell': 1.00, 'buy': 1.60, 'name': 'النمسا', 'flag': 'at', 'code': '+43', 'enabled': True},
    'CH': {'sell': 1.80, 'buy': 2.80, 'name': 'سويسرا', 'flag': 'ch', 'code': '+41', 'enabled': True},
    'SE': {'sell': 1.30, 'buy': 2.00, 'name': 'السويد', 'flag': 'se', 'code': '+46', 'enabled': True},
    'NO': {'sell': 1.40, 'buy': 2.20, 'name': 'النرويج', 'flag': 'no', 'code': '+47', 'enabled': True},
    'DK': {'sell': 1.30, 'buy': 2.00, 'name': 'الدنمارك', 'flag': 'dk', 'code': '+45', 'enabled': True},
    'FI': {'sell': 1.20, 'buy': 1.90, 'name': 'فنلندا', 'flag': 'fi', 'code': '+358', 'enabled': True},
    'IE': {'sell': 1.00, 'buy': 1.60, 'name': 'أيرلندا', 'flag': 'ie', 'code': '+353', 'enabled': True},
    'GR': {'sell': 0.70, 'buy': 1.10, 'name': 'اليونان', 'flag': 'gr', 'code': '+30', 'enabled': True},
    'CY': {'sell': 0.80, 'buy': 1.25, 'name': 'قبرص', 'flag': 'cy', 'code': '+357', 'enabled': True},
    'TR': {'sell': 0.50, 'buy': 0.80, 'name': 'تركيا', 'flag': 'tr', 'code': '+90', 'enabled': True},
    'IR': {'sell': 0.60, 'buy': 0.95, 'name': 'إيران', 'flag': 'ir', 'code': '+98', 'enabled': True},
    'NG': {'sell': 0.35, 'buy': 0.55, 'name': 'نيجيريا', 'flag': 'ng', 'code': '+234', 'enabled': True},
    'ZA': {'sell': 0.45, 'buy': 0.70, 'name': 'جنوب أفريقيا', 'flag': 'za', 'code': '+27', 'enabled': True},
    'KE': {'sell': 0.40, 'buy': 0.65, 'name': 'كينيا', 'flag': 'ke', 'code': '+254', 'enabled': True},
    'GH': {'sell': 0.40, 'buy': 0.65, 'name': 'غانا', 'flag': 'gh', 'code': '+233', 'enabled': True},
    'US': {'sell': 0.50, 'buy': 0.80, 'name': 'أمريكا', 'flag': 'us', 'code': '+1', 'enabled': True},
    'CA': {'sell': 0.60, 'buy': 0.95, 'name': 'كندا', 'flag': 'ca', 'code': '+1', 'enabled': True},
    'MX': {'sell': 0.50, 'buy': 0.80, 'name': 'المكسيك', 'flag': 'mx', 'code': '+52', 'enabled': True},
    'BR': {'sell': 0.40, 'buy': 0.65, 'name': 'البرازيل', 'flag': 'br', 'code': '+55', 'enabled': True},
    'AR': {'sell': 0.45, 'buy': 0.70, 'name': 'الأرجنتين', 'flag': 'ar', 'code': '+54', 'enabled': True},
    'CO': {'sell': 0.40, 'buy': 0.65, 'name': 'كولومبيا', 'flag': 'co', 'code': '+57', 'enabled': True},
    'AU': {'sell': 1.20, 'buy': 1.90, 'name': 'أستراليا', 'flag': 'au', 'code': '+61', 'enabled': True},
    'NZ': {'sell': 1.30, 'buy': 2.00, 'name': 'نيوزيلندا', 'flag': 'nz', 'code': '+64', 'enabled': True},
}

DEFAULT_SETTINGS = {
    'minDeposit': 0.1,
    'minWithdrawal': 3.0,
    'referralBonus': 0.05,
    'referralBonusNewUser': 0.05,
}

# ============== Firebase ==============
def fb_get(path):
    try:
        r = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fb_set(path, data):
    try:
        r = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def fb_push(path, data):
    try:
        r = requests.post(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return r.json().get('name') if r.status_code == 200 else None
    except:
        return None

def fb_update(path, data):
    try:
        r = requests.patch(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def fb_delete(path):
    try:
        r = requests.delete(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return r.status_code == 200
    except:
        return False

# ============== Helpers ==============
def get_countries():
    c = fb_get('countries')
    if not c:
        fb_set('countries', DEFAULT_COUNTRIES)
        return DEFAULT_COUNTRIES
    return c

def get_settings():
    s = fb_get('settings')
    if not s:
        fb_set('settings', DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    return {**DEFAULT_SETTINGS, **s}

def generate_token():
    return secrets.token_hex(32)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def generate_referral_code():
    return secrets.token_urlsafe(6).upper()

def detect_country(phone):
    phone = phone.replace(' ', '').replace('-', '')
    countries = get_countries()
    matched = None
    for code, info in countries.items():
        if phone.startswith(info['code']):
            if not matched or len(info['code']) > len(countries[matched]['code']):
                matched = code
    return matched

def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
        if not token:
            return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
        users = fb_get('users') or {}
        for uid, u in users.items():
            if u and u.get('token') == token:
                if u.get('banned'):
                    return jsonify({'success': False, 'error': 'حسابك محظور'}), 403
                request.user_id = uid
                request.user = u
                return f(*args, **kwargs)
        return jsonify({'success': False, 'error': 'جلسة غير صالحة'}), 401
    return decorated

# ============== Telegram ==============
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def tg_send_code(phone):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import FloodWaitError
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    try:
        await client.connect()
        result = await client.send_code_request(phone)
        session = client.session.save()
        phone_sessions[phone] = {'session': session, 'hash': result.phone_code_hash}
        return True, "تم إرسال الكود"
    except FloodWaitError as e:
        return False, f"انتظر {e.seconds} ثانية"
    except Exception as e:
        return False, str(e)
    finally:
        await client.disconnect()

async def tg_verify(phone, code, password=None):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError
    if phone not in phone_sessions:
        return False, "أعد إرسال الكود", None
    data = phone_sessions[phone]
    client = TelegramClient(StringSession(data['session']), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    try:
        await client.connect()
        await client.sign_in(phone=phone, code=code, phone_code_hash=data['hash'])
        session = client.session.save()
        del phone_sessions[phone]
        return True, "تم", session
    except SessionPasswordNeededError:
        if password:
            try:
                await client.sign_in(password=password)
                session = client.session.save()
                del phone_sessions[phone]
                return True, "تم", session
            except:
                return False, "كلمة مرور 2FA خاطئة", None
        return False, "2FA_REQUIRED", None
    except PhoneCodeInvalidError:
        return False, "الكود غير صحيح", None
    except Exception as e:
        return False, str(e), None
    finally:
        await client.disconnect()

async def tg_get_messages(session_str):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(session_str), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    messages = []
    try:
        await client.connect()
        if await client.is_user_authorized():
            async for msg in client.iter_messages(777000, limit=10):
                if msg.message:
                    codes = re.findall(r'\b\d{5,6}\b', msg.message)
                    if codes:
                        messages.append({'code': codes[0], 'timestamp': msg.date.isoformat()})
    except:
        pass
    finally:
        await client.disconnect()
    return messages

# ============== BSC ==============
def verify_bsc_tx(txid):
    try:
        r = requests.get("https://api.bscscan.com/api", params={
            'module': 'proxy', 'action': 'eth_getTransactionByHash',
            'txhash': txid, 'apikey': BSCSCAN_API_KEY
        }, timeout=15)
        data = r.json()
        if not data.get('result'):
            return False, 0, "لم يتم العثور على المعاملة"
        tx = data['result']
        to = tx.get('to', '').lower()
        if to == USDT_CONTRACT_BSC.lower():
            inp = tx.get('input', '')
            if inp.startswith('0xa9059cbb'):
                recipient = '0x' + inp[34:74]
                if recipient.lower() == DEPOSIT_WALLET.lower():
                    amount = int(inp[74:138], 16) / 1e18
                    if amount < 0.1:
                        return False, 0, "الحد الأدنى 0.1$"
                    return True, amount, "تم التحقق"
        return False, 0, "معاملة غير صالحة"
    except Exception as e:
        return False, 0, str(e)

# ============== HTML ==============
def get_index_html():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "<h1>Error loading page</h1>"

# ============== Routes ==============
@app.route('/')
def index():
    return Response(get_index_html(), mimetype='text/html')

@app.route('/api/stats')
def stats():
    numbers = fb_get('numbers') or {}
    countries = get_countries()
    available = sum(1 for n in numbers.values() if n and n.get('status') == 'available')
    return jsonify({
        'availableNumbers': available,
        'totalCountries': len([c for c in countries.values() if c and c.get('enabled', True)]),
        'depositWallet': DEPOSIT_WALLET
    })

@app.route('/api/countries')
def countries_api():
    numbers = fb_get('numbers') or {}
    countries = get_countries()
    result = []
    for code, info in countries.items():
        if info and info.get('enabled', True):
            count = sum(1 for n in numbers.values() if n and n.get('status') == 'available' and n.get('country') == code)
            result.append({
                'code': code, 'name': info['name'], 'flag': info['flag'],
                'phoneCode': info['code'], 'buyPrice': info['buy'],
                'sellPrice': info['sell'], 'stock': count
            })
    result.sort(key=lambda x: (-x['stock'], x['buyPrice']))
    return jsonify({'success': True, 'countries': result})

# Auth
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    ref_code = data.get('referralCode', '').strip()
    device_id = data.get('deviceId')
    fingerprint = data.get('fingerprint', {})
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'جميع الحقول مطلوبة'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'كلمة المرور قصيرة'})
    
    users = fb_get('users') or {}
    
    # Check device
    for u in users.values():
        if u and u.get('deviceId') == device_id:
            return jsonify({'success': False, 'error': 'هذا الجهاز مرتبط بحساب آخر'})
    
    # Check email
    for u in users.values():
        if u and u.get('email') == email:
            return jsonify({'success': False, 'error': 'البريد مستخدم'})
    
    token = generate_token()
    my_ref = generate_referral_code()
    
    new_user = {
        'username': username, 'email': email, 'password': hash_password(password),
        'balance': 0.0, 'token': token, 'referralCode': my_ref,
        'referredBy': None, 'referralCount': 0, 'referralEarnings': 0.0,
        'banned': False, 'deviceId': device_id, 'fingerprint': fingerprint,
        'createdAt': datetime.now().isoformat()
    }
    
    uid = fb_push('users', new_user)
    
    if uid and ref_code:
        for ref_uid, ref_user in users.items():
            if ref_user and ref_user.get('referralCode') == ref_code:
                if ref_user.get('deviceId') == device_id:
                    fb_update(f'users/{uid}', {'banned': True, 'banReason': 'إحالة ذاتية'})
                    return jsonify({'success': False, 'error': 'لا يمكنك إحالة نفسك'})
                
                settings = get_settings()
                bonus = settings.get('referralBonus', 0.05)
                fb_update(f'users/{ref_uid}', {
                    'balance': ref_user.get('balance', 0) + bonus,
                    'referralCount': ref_user.get('referralCount', 0) + 1,
                    'referralEarnings': ref_user.get('referralEarnings', 0) + bonus
                })
                fb_update(f'users/{uid}', {'balance': bonus, 'referredBy': ref_uid})
                break
    
    if uid:
        return jsonify({'success': True, 'user': {
            'id': uid, 'username': username, 'email': email, 'balance': 0.0,
            'token': token, 'referralCode': my_ref, 'referralCount': 0, 'referralEarnings': 0.0
        }})
    return jsonify({'success': False, 'error': 'حدث خطأ'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    device_id = data.get('deviceId')
    fingerprint = data.get('fingerprint', {})
    
    users = fb_get('users') or {}
    for uid, u in users.items():
        if u and u.get('email') == email and u.get('password') == hash_password(password):
            if u.get('banned'):
                return jsonify({'success': False, 'error': f"محظور: {u.get('banReason', '')}"})
            token = generate_token()
            fb_update(f'users/{uid}', {
                'token': token, 'deviceId': device_id, 'fingerprint': fingerprint,
                'lastLogin': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'user': {
                'id': uid, 'username': u.get('username'), 'email': email,
                'balance': u.get('balance', 0), 'token': token,
                'referralCode': u.get('referralCode'),
                'referralCount': u.get('referralCount', 0),
                'referralEarnings': u.get('referralEarnings', 0)
            }})
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'})

@app.route('/api/auth/auto-login', methods=['POST'])
def auto_login():
    data = request.json or {}
    device_id = data.get('deviceId')
    if not device_id:
        return jsonify({'success': False})
    users = fb_get('users') or {}
    for uid, u in users.items():
        if u and u.get('deviceId') == device_id:
            if u.get('banned'):
                return jsonify({'success': False, 'error': 'محظور'})
            token = generate_token()
            fb_update(f'users/{uid}', {'token': token, 'lastLogin': datetime.now().isoformat()})
            return jsonify({'success': True, 'user': {
                'id': uid, 'username': u.get('username'), 'email': u.get('email'),
                'balance': u.get('balance', 0), 'token': token,
                'referralCode': u.get('referralCode'),
                'referralCount': u.get('referralCount', 0),
                'referralEarnings': u.get('referralEarnings', 0)
            }})
    return jsonify({'success': False})

@app.route('/api/auth/me')
@verify_token
def me():
    return jsonify({'success': True, 'user': {
        'id': request.user_id, 'username': request.user.get('username'),
        'email': request.user.get('email'), 'balance': request.user.get('balance', 0),
        'referralCode': request.user.get('referralCode'),
        'referralCount': request.user.get('referralCount', 0),
        'referralEarnings': request.user.get('referralEarnings', 0)
    }})

# Buy
@app.route('/api/buy', methods=['POST'])
@verify_token
def buy():
    data = request.json or {}
    country = data.get('country')
    countries = get_countries()
    if country not in countries:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    info = countries[country]
    price = info['buy']
    balance = request.user.get('balance', 0)
    
    if balance < price:
        return jsonify({'success': False, 'error': f'رصيدك غير كافٍ'})
    
    numbers = fb_get('numbers') or {}
    target = None
    target_id = None
    for nid, n in numbers.items():
        if n and n.get('status') == 'available' and n.get('country') == country:
            target = n
            target_id = nid
            break
    
    if not target:
        return jsonify({'success': False, 'error': 'لا توجد أرقام متاحة'})
    
    new_balance = balance - price
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    
    purchase_id = fb_push('purchases', {
        'userId': request.user_id, 'numberId': target_id, 'phone': target['phone'],
        'country': country, 'price': price, 'session': target.get('session'),
        'status': 'active', 'createdAt': datetime.now().isoformat()
    })
    
    fb_update(f'numbers/{target_id}', {'status': 'sold', 'soldTo': request.user_id})
    
    return jsonify({'success': True, 'purchaseId': purchase_id, 'phone': target['phone'], 'newBalance': new_balance})

@app.route('/api/messages/<purchase_id>')
@verify_token
def messages(purchase_id):
    purchase = fb_get(f'purchases/{purchase_id}')
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'غير موجود'})
    session = purchase.get('session')
    if not session:
        return jsonify({'success': True, 'messages': []})
    try:
        msgs = run_async(tg_get_messages(session))
        return jsonify({'success': True, 'messages': msgs})
    except:
        return jsonify({'success': True, 'messages': []})

@app.route('/api/complete', methods=['POST'])
@verify_token
def complete():
    data = request.json or {}
    purchase_id = data.get('purchaseId')
    purchase = fb_get(f'purchases/{purchase_id}')
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'غير موجود'})
    fb_update(f'purchases/{purchase_id}', {'status': 'completed', 'completedAt': datetime.now().isoformat()})
    return jsonify({'success': True})

@app.route('/api/my-numbers')
@verify_token
def my_numbers():
    purchases = fb_get('purchases') or {}
    result = [{'id': pid, 'phone': p.get('phone'), 'country': p.get('country'), 'status': p.get('status'), 'createdAt': p.get('createdAt')}
              for pid, p in purchases.items() if p and p.get('userId') == request.user_id]
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'numbers': result})

# Sell
@app.route('/api/sell/send-code', methods=['POST'])
@verify_token
def sell_send():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    if not phone.startswith('+'):
        return jsonify({'success': False, 'error': 'الرقم يجب أن يبدأ بـ +'})
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    try:
        success, msg = run_async(tg_send_code(phone))
        if success:
            countries = get_countries()
            return jsonify({'success': True, 'country': country, 'countryName': countries[country]['name'], 'price': countries[country]['sell']})
        return jsonify({'success': False, 'error': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sell/verify', methods=['POST'])
@verify_token
def sell_verify():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    password = data.get('password')
    if not phone or not code:
        return jsonify({'success': False, 'error': 'بيانات ناقصة'})
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    try:
        success, msg, session = run_async(tg_verify(phone, code, password))
        if not success:
            if msg == "2FA_REQUIRED":
                return jsonify({'success': False, 'error': '2FA_REQUIRED'})
            return jsonify({'success': False, 'error': msg})
        countries = get_countries()
        fb_push('sell_requests', {
            'userId': request.user_id, 'username': request.user.get('username'),
            'phone': phone, 'country': country, 'price': countries[country]['sell'],
            'session': session, 'status': 'pending', 'createdAt': datetime.now().isoformat()
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Deposit
@app.route('/api/deposit', methods=['POST'])
@verify_token
def deposit():
    data = request.json or {}
    txid = data.get('txid', '').strip()
    if not txid.startswith('0x') or len(txid) < 60:
        return jsonify({'success': False, 'error': 'TXID غير صحيح'})
    
    deposits = fb_get('deposits') or {}
    for d in deposits.values():
        if d and d.get('txid') == txid:
            return jsonify({'success': False, 'error': 'المعاملة مستخدمة'})
    
    valid, amount, msg = verify_bsc_tx(txid)
    if valid:
        fb_push('deposits', {'userId': request.user_id, 'txid': txid, 'amount': amount, 'status': 'approved', 'createdAt': datetime.now().isoformat()})
        new_balance = request.user.get('balance', 0) + amount
        fb_update(f'users/{request.user_id}', {'balance': new_balance})
        return jsonify({'success': True, 'amount': amount, 'newBalance': new_balance})
    else:
        fb_push('pending_deposits', {'userId': request.user_id, 'username': request.user.get('username'), 'txid': txid, 'status': 'pending', 'error': msg, 'createdAt': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': 'manual_review'})

# Withdraw
@app.route('/api/withdraw', methods=['POST'])
@verify_token
def withdraw():
    data = request.json or {}
    amount = float(data.get('amount', 0))
    address = data.get('address', '').strip()
    if amount < 3:
        return jsonify({'success': False, 'error': 'الحد الأدنى $3'})
    if not address.startswith('0x') or len(address) != 42:
        return jsonify({'success': False, 'error': 'عنوان غير صحيح'})
    balance = request.user.get('balance', 0)
    if balance < amount:
        return jsonify({'success': False, 'error': 'رصيد غير كافٍ'})
    new_balance = balance - amount
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    fb_push('withdrawals', {'userId': request.user_id, 'username': request.user.get('username'), 'amount': amount, 'address': address, 'status': 'pending', 'createdAt': datetime.now().isoformat()})
    return jsonify({'success': True, 'newBalance': new_balance})

# Admin
@app.route('/api/admin/dashboard')
def admin_dashboard():
    users = fb_get('users') or {}
    numbers = fb_get('numbers') or {}
    sells = fb_get('sell_requests') or {}
    wths = fb_get('withdrawals') or {}
    pending_deps = fb_get('pending_deposits') or {}
    return jsonify({'success': True, 'stats': {
        'totalUsers': len([u for u in users.values() if u]),
        'availableNumbers': sum(1 for n in numbers.values() if n and n.get('status') == 'available'),
        'pendingSells': sum(1 for s in sells.values() if s and s.get('status') == 'pending'),
        'pendingWithdrawals': sum(1 for w in wths.values() if w and w.get('status') == 'pending'),
        'pendingDeposits': sum(1 for d in pending_deps.values() if d and d.get('status') == 'pending')
    }})

@app.route('/api/admin/users')
def admin_users():
    users = fb_get('users') or {}
    return jsonify({'success': True, 'users': [{'id': uid, 'username': u.get('username'), 'email': u.get('email'), 'balance': u.get('balance', 0), 'banned': u.get('banned', False)} for uid, u in users.items() if u]})

@app.route('/api/admin/user/<uid>/ban', methods=['POST'])
def admin_ban(uid):
    data = request.json or {}
    fb_update(f'users/{uid}', {'banned': True, 'banReason': data.get('reason', '')})
    return jsonify({'success': True})

@app.route('/api/admin/user/<uid>/unban', methods=['POST'])
def admin_unban(uid):
    fb_update(f'users/{uid}', {'banned': False, 'banReason': None})
    return jsonify({'success': True})

@app.route('/api/admin/user/<uid>/add-balance', methods=['POST'])
def admin_add_balance(uid):
    data = request.json or {}
    amount = float(data.get('amount', 0))
    user = fb_get(f'users/{uid}')
    if user:
        fb_update(f'users/{uid}', {'balance': user.get('balance', 0) + amount})
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/admin/sells')
def admin_sells():
    sells = fb_get('sell_requests') or {}
    return jsonify({'success': True, 'items': [{'id': k, **v} for k, v in sells.items() if v and v.get('status') == 'pending']})

@app.route('/api/admin/approve-sell', methods=['POST'])
def admin_approve_sell():
    data = request.json or {}
    sell_id = data.get('id')
    sell = fb_get(f'sell_requests/{sell_id}')
    if not sell:
        return jsonify({'success': False})
    countries = get_countries()
    country = sell.get('country')
    fb_push('numbers', {'phone': sell['phone'], 'country': country, 'price': countries.get(country, {}).get('buy', 1.0), 'session': sell.get('session'), 'status': 'available', 'createdAt': datetime.now().isoformat()})
    fb_update(f'sell_requests/{sell_id}', {'status': 'approved'})
    user = fb_get(f"users/{sell['userId']}")
    if user:
        fb_update(f"users/{sell['userId']}", {'balance': user.get('balance', 0) + sell['price']})
    return jsonify({'success': True})

@app.route('/api/admin/reject-sell', methods=['POST'])
def admin_reject_sell():
    data = request.json or {}
    fb_update(f"sell_requests/{data.get('id')}", {'status': 'rejected'})
    return jsonify({'success': True})

@app.route('/api/admin/withdrawals')
def admin_withdrawals():
    wths = fb_get('withdrawals') or {}
    return jsonify({'success': True, 'items': [{'id': k, **v} for k, v in wths.items() if v]})

@app.route('/api/admin/approve-withdrawal', methods=['POST'])
def admin_approve_wth():
    data = request.json or {}
    fb_update(f"withdrawals/{data.get('id')}", {'status': 'approved', 'txid': data.get('txid', ''), 'approvedAt': datetime.now().isoformat()})
    return jsonify({'success': True})

@app.route('/api/admin/reject-withdrawal', methods=['POST'])
def admin_reject_wth():
    data = request.json or {}
    wid = data.get('id')
    wth = fb_get(f'withdrawals/{wid}')
    if wth:
        user = fb_get(f"users/{wth['userId']}")
        if user:
            fb_update(f"users/{wth['userId']}", {'balance': user.get('balance', 0) + wth.get('amount', 0)})
    fb_update(f"withdrawals/{wid}", {'status': 'rejected'})
    return jsonify({'success': True})

@app.route('/api/admin/pending-deposits')
def admin_pending_deposits():
    deps = fb_get('pending_deposits') or {}
    return jsonify({'success': True, 'items': [{'id': k, **v} for k, v in deps.items() if v and v.get('status') == 'pending']})

@app.route('/api/admin/approve-deposit', methods=['POST'])
def admin_approve_deposit():
    data = request.json or {}
    dep_id = data.get('id')
    amount = float(data.get('amount', 0))
    dep = fb_get(f'pending_deposits/{dep_id}')
    if not dep:
        return jsonify({'success': False})
    fb_push('deposits', {'userId': dep['userId'], 'txid': dep['txid'], 'amount': amount, 'status': 'approved', 'approvedAt': datetime.now().isoformat()})
    user = fb_get(f"users/{dep['userId']}")
    if user:
        fb_update(f"users/{dep['userId']}", {'balance': user.get('balance', 0) + amount})
    fb_update(f'pending_deposits/{dep_id}', {'status': 'approved', 'amount': amount})
    return jsonify({'success': True})

@app.route('/api/admin/reject-deposit', methods=['POST'])
def admin_reject_deposit():
    data = request.json or {}
    fb_update(f"pending_deposits/{data.get('id')}", {'status': 'rejected'})
    return jsonify({'success': True})

@app.route('/api/admin/numbers')
def admin_numbers():
    numbers = fb_get('numbers') or {}
    return jsonify({'success': True, 'items': [{'id': k, **v} for k, v in numbers.items() if v]})

@app.route('/api/admin/delete-number', methods=['POST'])
def admin_del_number():
    data = request.json or {}
    fb_delete(f"numbers/{data.get('id')}")
    return jsonify({'success': True})

@app.route('/api/admin/add-send-code', methods=['POST'])
def admin_send_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    try:
        success, msg = run_async(tg_send_code(phone))
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/add-verify', methods=['POST'])
def admin_verify_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    password = data.get('password')
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    try:
        success, msg, session = run_async(tg_verify(phone, code, password))
        if not success:
            if msg == "2FA_REQUIRED":
                return jsonify({'success': False, 'error': '2FA_REQUIRED'})
            return jsonify({'success': False, 'error': msg})
        countries = get_countries()
        fb_push('numbers', {'phone': phone, 'country': country, 'price': countries[country]['buy'], 'session': session, 'status': 'available', 'createdAt': datetime.now().isoformat()})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/delete-all', methods=['POST'])
def admin_delete_all():
    data = request.json or {}
    if data.get('confirm') != 'DELETE_ALL_DATA':
        return jsonify({'success': False, 'error': 'تأكيد غير صحيح'})
    for path in ['users', 'numbers', 'purchases', 'sell_requests', 'deposits', 'pending_deposits', 'withdrawals']:
        fb_delete(path)
    return jsonify({'success': True})

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
