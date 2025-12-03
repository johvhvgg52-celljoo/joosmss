import requests
import time
import re
import urllib3
import requests.utils
from datetime import datetime, timedelta, timezone

# لتجاهل تحذيرات SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# 🔑 LOGIN CREDENTIALS - MULTIPLE ACCOUNTS (HARDCODED)
# =========================================================

# 1. IMS SMS Accounts (I)
# يمكنك إضافة أو إزالة أي عدد من حسابات IMS هنا
IMS_ACCOUNTS = [
    {"username": "yousssef", "password": "yousssefjo", "cookies": {}, "last_msgs": set()},
    {"username": "Ambrooo", "password": "Ambrooo", "cookies": {}, "last_msgs": set()}, 
]

# 2. Number Panel Accounts (P)
# يمكنك إضافة أو إزالة أي عدد من حسابات Panel هنا
PANEL_ACCOUNTS = [
    {"username": "Joojoo", "password": "Joojoo", "cookies": {}, "last_msgs": set()},
    # {"username": "panel_user2", "password": "panel_pass2", "cookies": {}, "last_msgs": set()},
]
# =========================================================

# Telegram settings
TELEGRAM_TOKEN = "8312180689:AAG3XLhtrKNt6yfTEEctBzoQUti1re7Z4Kw"
CHAT_ID = "-1003158632585"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# ----------------- وظيفة الإرسال للتليجرام -----------------

def send_to_telegram(text):
    try:
        text = str(text).replace("\x00","")
        payload = {
            "chat_id": CHAT_ID, 
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(TELEGRAM_URL, data=payload, verify=False)
    except Exception as e:
        print("❌ Telegram send error:", e)

# ----------------- Captcha & Cookie Renewal Functions -----------------

def solve_simple_captcha(html_content):
    """يحل عملية الجمع ويستخرج etkk (إن وجد)."""
    captcha_answer = ""
    etkk = ""
    match_placeholder = re.search(r'(\d+)\s*[\+\-]\s*(\d+)', html_content)
    if match_placeholder:
        num1 = int(match_placeholder.group(1))
        num2 = int(match_placeholder.group(2))
        captcha_answer = str(num1 + num2) 
    match_etkk = re.search(r'name=["\']etkk["\']\s+value=["\'](.*?)["\']', html_content)
    if match_etkk:
        etkk = match_etkk.group(1)
    return captcha_answer, etkk


def renew_imssms_cookie(account_data):
    LOGIN_URL = "https://www.imssms.org/signin"
    LOGIN_PAGE_URL = "https://www.imssms.org/login"
    return renew_cookie_base(account_data, LOGIN_URL, LOGIN_PAGE_URL, {"etkk_required": True})

def renew_panel_cookie(account_data):
    LOGIN_URL = "http://51.89.99.105/NumberPanel/signin"
    LOGIN_PAGE_URL = "http://51.89.99.105/NumberPanel/login"
    return renew_cookie_base(account_data, LOGIN_URL, LOGIN_PAGE_URL, {})


def renew_cookie_base(account_data, signin_url, login_page_url, options):
    """وظيفة أساسية لتجديد الكوكي لجميع المنصات باستخدام requests.Session."""
    username = account_data["username"]
    password = account_data["password"]
    short_name = signin_url.split('/')[2].split('.')[0].upper()
    if short_name == '51': short_name = 'PANEL'
    if short_name == 'WWW': short_name = 'IMS'

    login_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': login_page_url,
    }
    
    with requests.Session() as s:
        s.verify = False 
        
        try:
            response_login_page = s.get(login_page_url, headers=login_headers, timeout=10)
            captcha_answer, etkk = solve_simple_captcha(response_login_page.text)
            
            print(f"[{short_name} - {username}]: الكابتشا: {captcha_answer}. etkk: {etkk}")
            
            login_data = {'username': username, 'password': password, 'capt': captcha_answer}
            
            if options.get("etkk_required") and etkk:
                login_data['etkk'] = etkk
            
            response = s.post(signin_url, data=login_data, headers=login_headers, allow_redirects=True, timeout=10)
            
            
            if '/client' in response.url.lower() or 'dashboard' in response.text.lower():
                
                current_cookies_dict = requests.utils.dict_from_cookiejar(s.cookies)

                if current_cookies_dict.get('PHPSESSID'):
                    
                    account_data["cookies"] = current_cookies_dict

                    print(f"✅ {short_name} ({username}): تم تجديد الكوكي بنجاح.")
                    return current_cookies_dict
            
            print(f"❌ {short_name} ({username}): فشل التجديد. لم يتم العثور على PHPSESSID جديد.")
            return None
                
        except Exception as e:
            print(f"❌ {short_name} ({username}): خطأ في عملية تسجيل الدخول: {e}")
            return None

# ----------------- Utility Functions -----------------

def get_date_params():
    now_utc = datetime.now(timezone.utc)
    fdate1 = now_utc.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    next_day = now_utc + timedelta(days=1)
    fdate2 = next_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    return fdate1, fdate2

def extract_country(service_name):
    countries = ["Ecuador","Burundi","Egypt","Senegal","Sudan","Slovenia","Indonesia"]
    service_name = str(service_name).lower()
    for c in countries:
        if c.lower() in service_name:
            return c
    return "Unknown"

def mask_number(number):
    cleaned_number = re.sub(r'\D', '', str(number))
    length = len(cleaned_number)
    
    if length > 6:
        visible_start = cleaned_number[:3]
        visible_end = cleaned_number[-3:]
        masked_part = '*' * (length - 6) 
        return f"{visible_start}{masked_part}{visible_end}"
    
    return cleaned_number

# ----------------- Platform Configuration -----------------
base_params = {
    "fdate1": "","fdate2": "",
    "frange":"","fnum":"","fcli":"","fgdate":"","fgmonth":"","fgrange":"",
    "fgnumber":"","fgcli":"","fg":"0","sEcho":"1","iColumns":"7","sColumns":",,,,,,",
    "iDisplayStart":"0","iDisplayLength":"25","iSortCol_0":"0","sSortDir_0":"desc","iSortingCols":"1"
}

panel_url = "http://51.89.99.105/NumberPanel/client/res/data_smscdr.php"
panel_headers = {"Accept":"application/json, text/javascript, */*; q=0.01","Accept-Language":"en-GB,en;q=0.9",
                 "User-Agent":"Mozilla/5.0","X-Requested-With":"XMLHttpRequest",
                 "Referer":"http://51.89.99.105/NumberPanel/client/SMSCDRStats"}

imssms_url = "https://www.imssms.org/client/res/data_smscdr.php"
imssms_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-GB,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://www.imssms.org/client/SMSCDRStats',
    'sec-ch-ua-platform': '"Windows"' 
}

# ----------------- Core Processing Function -----------------

def process_source(short_name, url, headers, account_data, base_params):
    """يعالج البيانات من مصدر واحد (IMS أو Panel) باستخدام بيانات حساب محدد."""
    
    username = account_data["username"]
    current_cookies = account_data["cookies"] 
    last_msgs = account_data["last_msgs"]
    
    fdate1, fdate2 = get_date_params()
    params = base_params.copy()
    params["fdate1"] = fdate1
    params["fdate2"] = fdate2

    attempts = 0
    max_attempts = 2
    
    while attempts < max_attempts:
        attempts += 1
        
        try:
            current_headers = headers.copy() 
            
            response = requests.get(url, headers=current_headers, cookies=current_cookies, params=params, verify=False, timeout=15)
            
            if 'login' in response.text.lower() or response.status_code == 302:
                raise Exception("Cookie Expired/Invalid (Login page detected).")
                
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                raise Exception(f"Response is not JSON. Status: {response.status_code}")

            rows = data.get("aaData", [])
            # فلترة خاصة لـ IMS عند عدم وجود بيانات
            if short_name == "I" and len(rows) == 1 and rows[0][0] == "0,0,0,0":
                return
            
            break 
            
        except Exception as e:
            # محاولة تجديد الكوكي التلقائي
            if attempts == 1:
                print(f"⚠️ {short_name} ({username}): محاولة تجديد الكوكي التلقائي بسبب الفشل... ({e})")
                
                new_cookie = None
                if short_name == "P":
                    new_cookie = renew_panel_cookie(account_data)
                elif short_name == "I":
                    new_cookie = renew_imssms_cookie(account_data)
                    
                if new_cookie:
                    current_cookies = account_data["cookies"]
                    continue
                else:
                    # نستخدم الإدخال اليدوي كحل أخير (مثل السكريبت الأصلي)
                    print("="*60)
                    print(f"🚨🚨 {short_name} ({username}): فشل التجديد التلقائي. يرجى إدخال سلسلة الكوكيز يدوياً. 🚨🚨")
                    manual_cookie_string = input(f"◀️ أدخل سلسلة الكوكيز (PHPSESSID=...) لمنصة {short_name} لليوزر {username}: ").strip()
                    print("="*60)

                    if manual_cookie_string:
                        parsed_cookies = {}
                        try:
                            # تحليل بسيط كحل بديل
                            parsed_cookies['PHPSESSID'] = manual_cookie_string.split(';')[0].split('=')[-1].strip()
                        except Exception:
                            pass
                        
                        if parsed_cookies:
                            account_data["cookies"] = parsed_cookies 
                            current_cookies = parsed_cookies 
                            print(f"✅ {short_name} ({username}): تم حفظ الكوكيز اليدوية. إعادة المحاولة...")
                            continue
                        else:
                            print(f"❌ {short_name} ({username}): لم يتم إدخال كوكي صالح. التوقف عن المحاولة.")
                            time.sleep(30)
                            return
                    else:
                        print(f"❌ {short_name} ({username}): لم يتم إدخال كوكي. التوقف عن المحاولة.")
                        time.sleep(30)
                        return
            else:
                print(f"❌ Error in {short_name} ({username}) on attempt 2: {e}")
                return

    # استمرار معالجة البيانات
    if 'rows' in locals() and rows:
        for row in rows:
            if len(row) < 6:
                continue

            timestamp = str(row[0])
            service = str(row[1])
            number = str(row[2]) 
            message = str(row[4]).replace('\u200f', '').replace('\u200e', '')
            
            # 🛑 فلترة المحتوى الفارغ
            if message.strip() in ["0","0,0,0,1"]:
                continue

            unique = f"{timestamp}-{number}-{message}-{username}-{short_name}" 

            # 🛑 مؤقتاً: تجاهل فلترة التكرار للتشخيص
            # if unique in last_msgs:
            #     continue 
            
            # last_msgs.add(unique) 

            # Code Extraction Logic 
            code = "" 
            spaced_codes = re.findall(r'(\d{3,4}[\s\-\:]\d{2,4})', message) 
            if spaced_codes:
                code_with_separator = spaced_codes[-1]
                code = re.sub(r'[\s\-\:]', '', code_with_separator)
            else:
                continuous_codes = re.findall(r'\d{4,8}', message)
                if continuous_codes:
                    code = continuous_codes[-1]
                else:
                    all_digits = re.findall(r'\d{3}', message)
                    code = all_digits[-1] if all_digits else ""
            
            country = extract_country(service)
            masked_num = mask_number(number)
            
            # Building Telegram message
            app_name = "SMS" 
            if "telegram" in service.lower() or "telegram" in message.lower():
                app_name = "Telegram"
            elif "whatsapp" in service.lower() or "whatsapp" in message.lower():
                app_name = "WhatsApp"

            if app_name != "SMS":
                telegram_text = f"""
🔒 <b>New {app_name} Code</b> from <b>{short_name} - {username}</b>

🌍 Country: {country}
📱 Number: {masked_num} 
🔐 Code: {code}
🕒 Time: {timestamp}
"""
            else:
                telegram_text = f"""
📩 <b>New SMS</b> from <b>{short_name} - {username}</b>

🌍 Country: {country}
📱 Number: {masked_num} 
🔐 Code: {code}
🕒 Time: {timestamp}

📨 Full Message:
{message}
"""
            
            # طباعة الرسالة في الكونسول
            print("------------------------------------------------")
            print(f"🌐 Platform: {short_name} | User: {username}")
            print(f"📅 Time: {timestamp}")
            print(f"📱 Number: {masked_num}")
            print(f"🔐 Code: {code}")
            print(f"📨 Message:\n{message}")
            print("------------------------------------------------\n")
            
            # إرسال الرسالة إلى تليجرام
            send_to_telegram(telegram_text)

# ----------------- Monitoring Loop -----------------

print("🚀 Starting monitoring on all hardcoded platforms and accounts...")
print(f"🕒 Current UTC Date Range: {get_date_params()[0]} to {get_date_params()[1]}\n")

# ⚠️ تجديد الكوكيز لجميع الحسابات عند البدء
print("--- Initializing IMS SMS Accounts ---")
for acc in IMS_ACCOUNTS:
    renew_imssms_cookie(acc)

print("\n--- Initializing Number Panel Accounts ---")
for acc in PANEL_ACCOUNTS:
    renew_panel_cookie(acc)

print("\n--- Starting Monitoring Loop ---\n")

while True:
    # 1. معالجة جميع حسابات Number Panel
    for acc in PANEL_ACCOUNTS:
        process_source(
            "P", 
            panel_url, 
            panel_headers, 
            acc, 
            base_params
        )

    # 2. معالجة جميع حسابات IMS SMS
    for acc in IMS_ACCOUNTS:
        process_source(
            "I", 
            imssms_url, 
            imssms_headers, 
            acc, 
            base_params
        )
        
    # الانتظار لمدة 3 ثوانٍ قبل التكرار التالي
    time.sleep(3)
