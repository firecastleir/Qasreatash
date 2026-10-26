import os, asyncio, json, random, re, shutil, subprocess, sys, tempfile, datetime, html
from pathlib import Path

import requests
import edge_tts

# ======================= تنظیمات سایت =======================
SITE = os.environ.get("WP_SITE", "https://firecastle.ir").rstrip("/")
WP_USER = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "")
# draft = پیش‌نویس (برای بازبینی) | publish = انتشار مستقیم
POST_STATUS = os.environ.get("POST_STATUS", "draft")

BRAND = "شومینه قصر آتش"
SITE_SHORT = "firecastle.ir"
PHONE = "02144278518"
MOBILE = "09031413301"
WORKSHOP = "تهران، پل ساوه، خیابان غفاری ۳، پلاک ۴"
OFFICE = "تهران، ستارخان، خیابان اسدی، خیابان قدیانی، پلاک ۴۳، واحد ۸"

BUSINESS = (
    "شومینه قصر آتش در تهران شومینه بیواتانول، گازی و هیزمی و همچنین باربیکیو را طراحی و تولید می‌کند "
    "(کارگاه تولید در تهران، سفارش‌های سفارشی و اجرا)."
)

CAT_BIO = "شومینه بیواتانول"
CAT_GAS = "شومینه گازی"
CAT_WOOD = "شومینه هیزمی"
CAT_BBQ = "باربیکیو"
CAT_GUIDE = "راهنمای شومینه"


def T(title, cat, kw, kw2=None):
    return {"title": title, "cat": cat, "kw": kw, "kw2": kw2 or []}


# ترتیب: اول کلمه‌های تجاری (سفارش و خرید)، بعد آموزشی. حجم جستجو را من نمی‌دانم؛
# بعد از چند هفته در Google Search Console ببینید کدام عبارت‌ها بازدید می‌گیرند.
TOPICS = [
    T("ساخت شومینه سفارشی در تهران: مراحل، هزینه و نکات", CAT_GUIDE, "ساخت شومینه در تهران", ["ساخت شومینه سفارشی", "شومینه سفارشی", "طراحی شومینه"]),
    T("شومینه بیواتانول در تهران: راهنمای خرید و سفارش", CAT_BIO, "شومینه بیواتانول", ["خرید شومینه بیواتانول", "شومینه بیواتانول سفارشی", "قیمت شومینه بیواتانول"]),
    T("شومینه گازی در تهران: نصب، دودکش و هزینه", CAT_GAS, "شومینه گازی", ["نصب شومینه گازی", "قیمت شومینه گازی", "شومینه گازی توکار"]),
    T("شومینه هیزمی در تهران: طراحی، ساخت و دودکش", CAT_WOOD, "شومینه هیزمی", ["ساخت شومینه هیزمی", "قیمت شومینه هیزمی", "شومینه هیزمی ویلا"]),
    T("ساخت باربیکیو سفارشی: انواع، طراحی و نکات", CAT_BBQ, "ساخت باربیکیو", ["باربیکیو سفارشی", "باربیکیو فلزی", "باربیکیو حیاط"]),
    T("مزایا و معایب شومینه بیواتانول در آپارتمان", CAT_BIO, "شومینه بیواتانول آپارتمانی", ["شومینه بیواتانول مناسب آپارتمان"]),
    T("شومینه بیواتانول چیست و چگونه کار می‌کند", CAT_BIO, "شومینه بیواتانول چیست", ["طرز کار شومینه بیواتانول"]),
    T("نکات ایمنی استفاده از شومینه بیواتانول", CAT_BIO, "ایمنی شومینه بیواتانول", ["خطرات شومینه بیواتانول"]),
    T("سوخت بیواتانول چیست و چطور نگهداری می‌شود", CAT_BIO, "سوخت بیواتانول", ["نگهداری بیواتانول", "مصرف سوخت بیواتانول"]),
    T("انواع شومینه بیواتانول: دیواری، رومیزی، توکار و ایستاده", CAT_BIO, "انواع شومینه بیواتانول", ["شومینه بیواتانول دیواری", "شومینه بیواتانول توکار"]),
    T("آیا شومینه بیواتانول دودکش لازم دارد؟", CAT_BIO, "شومینه بیواتانول دودکش", ["شومینه بدون دودکش"]),
    T("شومینه بیواتانول سفارشی برای دکوراسیون مدرن", CAT_BIO, "شومینه بیواتانول سفارشی", ["شومینه بیواتانول مدرن"]),
    T("راهنمای خرید شومینه بیواتانول", CAT_BIO, "خرید شومینه بیواتانول", ["انتخاب شومینه بیواتانول"]),
    T("تفاوت شومینه بیواتانول و شومینه گازی", CAT_BIO, "تفاوت شومینه بیواتانول و گازی", ["بیواتانول یا گازی"]),
    T("شومینه بیواتانول برای بالکن و فضای باز", CAT_BIO, "شومینه بیواتانول بالکن", ["شومینه بیواتانول فضای باز"]),
    T("شومینه گازی چیست و چه مزایایی دارد", CAT_GAS, "شومینه گازی چیست", ["مزایای شومینه گازی"]),
    T("نکات ایمنی نصب شومینه گازی", CAT_GAS, "نصب شومینه گازی", ["ایمنی شومینه گازی"]),
    T("دودکش شومینه گازی: انواع و اصول اجرا", CAT_GAS, "دودکش شومینه گازی", ["اجرای دودکش گازی"]),
    T("مصرف گاز شومینه گازی چقدر است؟", CAT_GAS, "مصرف گاز شومینه گازی", ["هزینه گاز شومینه"]),
    T("شومینه گازی توکار یا ایستاده؟ کدام بهتر است", CAT_GAS, "شومینه گازی توکار", ["شومینه گازی ایستاده"]),
    T("نگهداری و سرویس دوره‌ای شومینه گازی", CAT_GAS, "سرویس شومینه گازی", ["تعمیر شومینه گازی"]),
    T("شومینه گازی شیشه‌ای و مزایای آن", CAT_GAS, "شومینه گازی شیشه ای", ["شومینه گازی شیشه نسوز"]),
    T("شومینه هیزمی چیست و چگونه کار می‌کند", CAT_WOOD, "شومینه هیزمی چیست", ["طرز کار شومینه هیزمی"]),
    T("اصول طراحی دودکش شومینه هیزمی", CAT_WOOD, "دودکش شومینه هیزمی", ["اجرای دودکش شومینه"]),
    T("بهترین هیزم برای شومینه کدام است", CAT_WOOD, "هیزم شومینه", ["بهترین هیزم", "هیزم خشک"]),
    T("شومینه هیزمی فلزی یا سنگی؟", CAT_WOOD, "شومینه هیزمی فلزی", ["شومینه هیزمی سنگی"]),
    T("شومینه هیزمی در ویلا: نکات طراحی و اجرا", CAT_WOOD, "شومینه هیزمی ویلا", ["شومینه ویلا"]),
    T("روش تمیز کردن و نگهداری شومینه هیزمی", CAT_WOOD, "نگهداری شومینه هیزمی", ["تمیز کردن شومینه"]),
    T("شومینه هیزمی با شیشه نسوز: مزایا و نکات", CAT_WOOD, "شومینه هیزمی شیشه نسوز", ["شیشه نسوز شومینه"]),
    T("قیمت شومینه هیزمی به چه عواملی بستگی دارد", CAT_WOOD, "قیمت شومینه هیزمی", ["هزینه ساخت شومینه هیزمی"]),
    T("باربیکیو چیست و چه انواعی دارد", CAT_BBQ, "باربیکیو", ["انواع باربیکیو"]),
    T("باربیکیو ذغالی یا گازی؟ راهنمای انتخاب", CAT_BBQ, "باربیکیو ذغالی", ["باربیکیو گازی"]),
    T("باربیکیو ساختمانی برای حیاط و ویلا", CAT_BBQ, "باربیکیو ساختمانی", ["ساخت باربیکیو حیاط"]),
    T("باربیکیو فلزی سفارشی و ویژگی‌های آن", CAT_BBQ, "باربیکیو فلزی", ["باربیکیو فلزی سفارشی"]),
    T("نکات ایمنی کباب‌پزی با باربیکیو", CAT_BBQ, "ایمنی باربیکیو", ["مسمومیت با دود ذغال"]),
    T("طراحی آلاچیق و باربیکیو در حیاط", CAT_BBQ, "آلاچیق و باربیکیو", ["طراحی آلاچیق"]),
    T("نگهداری از باربیکیو و جلوگیری از زنگ‌زدگی", CAT_BBQ, "نگهداری باربیکیو", ["زنگ زدگی باربیکیو"]),
    T("باربیکیو نصب شده در تراس و بالکن: نکات مهم", CAT_BBQ, "باربیکیو تراس", ["باربیکیو بالکن"]),
    T("شومینه چه تاثیری در دکوراسیون خانه دارد", CAT_GUIDE, "دکوراسیون شومینه", ["شومینه و دکوراسیون"]),
    T("راهنمای انتخاب شومینه مناسب برای خانه شما", CAT_GUIDE, "انتخاب شومینه", ["بهترین شومینه", "نوع شومینه"]),
    T("قاب و نمای شومینه: سنگ، گچ، کابینت و فلز", CAT_GUIDE, "نمای شومینه", ["سنگ شومینه", "قاب شومینه"]),
    T("شومینه دیواری مدرن و ایده‌های طراحی", CAT_GUIDE, "شومینه دیواری", ["شومینه دیواری مدرن"]),
    T("شومینه در آپارتمان: چه نوعی مجاز و ایمن است", CAT_GUIDE, "شومینه آپارتمانی", ["شومینه برای آپارتمان"]),
    T("اشتباهات رایج هنگام خرید و نصب شومینه", CAT_GUIDE, "خرید شومینه", ["اشتباه در خرید شومینه"]),
]

# ============================================================

AUTH = (WP_USER, WP_APP_PASSWORD)
API = f"{SITE}/wp-json/wp/v2"
HERE = Path(__file__).parent
STATE_FILE = HERE / "state.json"

# رنگ‌های ویدیو (BGR برای زیرنویس) و پس‌زمینه (RGB)
ACCENT_ASS = "&H005AA2E8"      # مس روشن
ACCENT_BAR = "&H005AA2E8"
BG_TOP = (34, 18, 10)          # بالای پس‌زمینه
BG_BOTTOM = (112, 60, 24)      # پایین پس‌زمینه


# ---------------------------------------------------------------- helpers
def load_state():
    if not STATE_FILE.exists():
        return {"done": [], "used_images": []}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        raise RuntimeError("command failed: " + " ".join(map(str, cmd[:3])))
    return r.stdout


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", str(path)]).strip())


_MODELS = None
_ALL = None


def list_models():
    global _ALL
    if _ALL is None:
        _ALL = []
        try:
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                             params={"key": GEMINI_API_KEY, "pageSize": 200}, timeout=60)
            r.raise_for_status()
            for m in r.json().get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    _ALL.append(m["name"].split("/")[-1])
        except Exception as e:
            print("model list failed:", type(e).__name__)
    return _ALL


def candidate_models():
    """مدل‌های فعال را از خود گوگل می‌پرسد تا به اسم مدل وابسته نباشیم."""
    global _MODELS
    if _MODELS is not None:
        return _MODELS
    names = [n for n in list_models() if "flash" in n and not any(
        x in n for x in ("image", "tts", "live", "audio", "thinking", "robotics", "computer", "embed", "native"))]

    def ver(n):
        m = re.search(r"(\d+(?:\.\d+)?)", n)
        return (float(m.group(1)) if m else 0, "lite" not in n, "preview" not in n)

    names.sort(key=ver, reverse=True)
    pref = [GEMINI_MODEL] if os.environ.get("GEMINI_MODEL") else []
    _MODELS = pref + [n for n in names if n not in pref] + (["gemini-flash-latest"] if "gemini-flash-latest" not in names else [])
    print("models to try:", _MODELS[:6])
    return _MODELS


def gemini(prompt, retries=2):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 30000, "responseMimeType": "application/json"}}
    for model in candidate_models()[:6]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for i in range(retries):
            try:
                r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=240)
                if r.status_code in (404, 400):
                    print("model unavailable:", model, r.status_code)
                    break
                if r.status_code == 429:
                    print("quota/rate limit on", model, "- waiting")
                    time.sleep(30)
                    continue
                r.raise_for_status()
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
                print("using model:", model)
                return json.loads(text)
            except Exception as e:
                print("gemini retry", model, i, str(e)[:200])
                time.sleep(8)
    raise RuntimeError("Gemini failed with all models")


import time


# ---------------------------------------------------------------- topic
def pick_topic(state):
    topics = list(TOPICS) + state.get("extra_topics", [])
    left = [t for t in topics if t["title"] not in state["done"]]
    if not left:
        print("topic list exhausted -> asking Gemini for new topics")
        cats = [CAT_BIO, CAT_GAS, CAT_WOOD, CAT_BBQ, CAT_GUIDE]
        new = gemini(f"""برای وبلاگ فنی سایت «{BRAND}» ({BUSINESS})
۱۰ موضوع جدید مقاله فنی و سئو شده بنویس که با این عناوین تکراری نباشد:
{json.dumps(state['done'][-80:], ensure_ascii=False)}
فقط JSON: لیستی از اشیاء با کلیدهای title, cat (یکی از: {', '.join(cats)}), kw (کلمه کلیدی اصلی فارسی), kw2 (لیست ۲ تا ۳ کلمه کلیدی فرعی)""")
        state.setdefault("extra_topics", []).extend(new)
        left = new
    return left[0]


# ---------------------------------------------------------------- article
def recent_posts():
    try:
        r = requests.get(f"{API}/posts", params={"per_page": 20, "status": "publish", "_fields": "title,link"}, timeout=60)
        return [{"title": p["title"]["rendered"], "url": p["link"]} for p in r.json()]
    except Exception:
        return []


def write_article(topic):
    internal = recent_posts()
    prompt = f"""تو سردبیر فنی و متخصص سئوی فارسی هستی و برای سایت «{BRAND}» ({SITE}) مقاله می‌نویسی.
درباره کسب‌وکار: {BUSINESS}
موضوع مقاله: «{topic['title']}»
کلمه کلیدی اصلی: «{topic['kw']}»
کلمات کلیدی فرعی (فقط طبیعی و بدون تکرار زیاد در متن، یکی دو بار در تیترها): {', '.join(topic.get('kw2', []))}

هدف: مقاله‌ای جامع، فنی، کاربردی و روان که از رقبای صفحه اول گوگل کامل‌تر و مفیدتر باشد، برای کاربر ایرانی (صاحبخانه، مشتری ویلا و آپارتمان، معمار و طراح دکوراسیون).

قوانین محتوا:
- فارسی روان و استاندارد ایران، لحن حرفه‌ای، دقیق و قابل فهم. حدود ۲۰۰۰ تا ۲۶۰۰ کلمه.
- دقت فنی در اولویت است. هیچ عدد، قیمت، مشخصات، استاندارد، گواهی یا ادعای ساختگی ننویس. اگر از عددی مطمئن نیستی، توصیف کلی بنویس. درباره محصولات {BRAND} ادعای خاص (مدل، ضمانت، قیمت) نکن.
- ساختار پیشنهادی: مقدمه کوتاه با کلمه کلیدی، پاسخ سریع به سوال اصلی، توضیح فنی اصول کار، انواع و مقایسه (حتماً حداقل یک جدول HTML با table)، مزایا و معایب، مراحل یا نکات اجرا و نصب، نکات ایمنی، نگهداری، اشتباهات رایج، عوامل موثر بر هزینه (بدون قیمت دقیق)، نتیجه‌گیری.
- از h2 و h3، لیست‌های ul و ol، جدول، و در صورت نیاز تگ strong استفاده کن. تگ h1 نگذار.
- ایمنی را شفاف و محتاطانه بنویس: تهویه، فاصله از مواد قابل اشتعال، سوخت بیواتانول (نگهداری و سوخت‌گیری فقط وقتی شعله کاملاً خاموش و سرد است)، گاز و دودکش، دود و مونوکسیدکربن در باربیکیو. نصب گازی و دودکش را به متخصص مجاز ارجاع بده.
- کلمه کلیدی در عنوان، پاراگراف اول، حداقل دو تیتر h2 و نتیجه‌گیری بیاید (طبیعی، بدون پرکردن).
- ادعای تجربه یا آمار جعلی نیاور (مثلاً «ما ۲۰ سال سابقه داریم»)، فقط از «تیم فنی {BRAND}» به صورت کلی استفاده کن.
- در انتها دعوت به مشاوره با {BRAND} بیاور (بدون شماره تلفن؛ شماره را سیستم اضافه می‌کند).
- ۳ تا ۵ لینک داخلی طبیعی (با متن لنگر توصیفی) فقط از این فهرست و فقط مقاله‌های مرتبط، با تگ a. اگر فهرست خالی است هیچ لینکی نساز و هیچ آدرسی از خودت نساز: {json.dumps(internal, ensure_ascii=False)}
- متن روایت ویدیو (narration): ۱۳۰ تا ۱۶۰ کلمه، حداکثر ۷ جمله، گفتاری، طبیعی و فنی ولی ساده برای گوینده، هر جمله حداکثر ۲۰ کلمه و با نقطه تمام‌شونده. برای خوانده‌شدن درست توسط موتور تبدیل متن به گفتار: همه عددها را با حروف بنویس، هیچ کلمه انگلیسی، مخفف، علامت و ایموجی نیاور، از کلمه‌های ساده و رایج فارسی معیار و املای استاندارد با نیم‌فاصله درست استفاده کن. بدون آدرس سایت و شماره. شروع جذاب و پایان با دعوت به مشاوره با {BRAND}.
- slides: به تعداد جمله‌های narration (به ترتیب)، برای هر جمله یک شیء با کلیدهای title (عنوان کوتاه فارسی حداکثر ۵ کلمه) و points (۲ تا ۳ نکته بسیار کوتاه فارسی، هرکدام حداکثر ۷ کلمه، دقیقاً مطابق همان جمله). این‌ها روی صفحه ویدیو نمایش داده می‌شوند، پس باید دقیق، فنی و بدون غلط باشند.
- video_title: عنوان جذاب ویدیو برای آپارات و یوتیوب (حداکثر ۷۰ کاراکتر، شامل کلمه کلیدی). video_description: توضیح ۴ تا ۶ خطی فارسی برای زیر ویدیو، با کلمه کلیدی و دعوت به تماس با {BRAND} (بدون لینک و بدون شماره). hashtags: ۶ تا ۸ هشتگ فارسی بدون علامت #.
- summary_points: فهرست ۴ تا ۵ جمله‌ی خیلی کوتاه فارسی که مهم‌ترین نکات مقاله را خلاصه می‌کنند (برای کادر «خلاصه مقاله» بالای مقاله).

فقط JSON با این کلیدها:
title (حداکثر ۶۰ کاراکتر، شامل کلمه کلیدی), slug (انگلیسی کوچک با خط تیره), meta_description (۱۲۰ تا ۱۵۵ کاراکتر شامل کلمه کلیدی),
tags (۳ تا ۵ برچسب فارسی), article_html, faq (لیست ۶ شیء با q و a، پاسخ‌های دقیق و کامل در ۲ تا ۴ جمله), summary_points, narration, slides, video_title, video_description, hashtags, image_alt (متن جایگزین فارسی عکس شاخص)"""
    art = gemini(prompt)
    return review_article(art, topic)


def review_article(art, topic):
    """یک دور بازبینی فنی: اشتباهات، اعداد مشکوک و توصیه‌های ناایمن را اصلاح می‌کند."""
    if os.environ.get("REVIEW_PASS", "1") == "0":
        return art
    old = art.get("article_html", "")
    prompt = f"""تو بازبین فنی ارشد شومینه، سوخت‌های گرمایشی و باربیکیو هستی. مقاله HTML زیر درباره «{topic['title']}» است.
آن را با دقت بخوان و هر ادعای فنی نادرست یا مشکوک، عدد یا استاندارد بی‌پشتوانه، توصیه ناایمن (به‌ویژه گاز، بیواتانول و آتش) و اغراق را اصلاح یا حذف کن.
جزئیات مفید را کم نکن. ساختار HTML، تیترها و جدول‌ها را حفظ کن و طول را کم‌تر از ۹۰ درصد نکن.
فقط JSON با کلیدهای article_html (متن اصلاح‌شده کامل) و changes (فهرست کوتاه تغییرات).

{old}"""
    try:
        r = gemini(prompt, retries=1)
        new = r.get("article_html", "")
        if len(new) >= 0.7 * len(old):
            art["article_html"] = new
            print("review changes:", r.get("changes", [])[:8])
    except Exception as e:
        print("review pass skipped:", str(e)[:200])
    return art


# ---------------------------------------------------------------- library
def download(url, path):
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    Path(path).write_bytes(r.content)


def strip_tags(t):
    t = re.sub(r"<[^>]+>", " ", html.unescape(str(t or "")))
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()


def fetch_library():
    """عکس‌ها و فیلم‌های کتابخانه سایت که صاحب سایت برایشان توضیح نوشته است."""
    items = []
    for mt in ("image", "video"):
        for page in range(1, 4):
            try:
                r = requests.get(f"{API}/media", params={
                    "per_page": 100, "page": page, "media_type": mt,
                    "_fields": "id,source_url,alt_text,title,caption,description,media_details"}, auth=AUTH, timeout=60)
                if r.status_code != 200:
                    break
                data = r.json()
            except Exception as e:
                print("media list failed:", type(e).__name__)
                break
            if not data:
                break
            for m in data:
                url = m.get("source_url", "")
                fn = url.rsplit("/", 1)[-1].lower()
                if re.match(r"(cover|vertical|horizontal|featured|card|story|slide|logo|poster)[-_.\d]", fn):
                    continue
                if strip_tags((m.get("description") or {}).get("rendered")) == "AUTO":
                    continue
                alt = strip_tags(m.get("alt_text"))
                cap = strip_tags((m.get("caption") or {}).get("rendered"))
                desc = strip_tags((m.get("description") or {}).get("rendered"))
                ttl = strip_tags((m.get("title") or {}).get("rendered"))
                if not (alt or cap or desc):
                    continue
                label = " | ".join(dict.fromkeys(x for x in (desc, cap, alt, ttl) if x))[:200]
                d = m.get("media_details") or {}
                large = ((d.get("sizes") or {}).get("large") or {}).get("source_url")
                items.append({"id": m["id"], "type": mt, "url": url, "large": large or url,
                              "label": label, "alt": alt or desc or cap or ttl})
            if len(data) < 100:
                break
    print("library items with descriptions:", len(items))
    return items


def match_library(topic, sentences, heads, library):
    """هوش مصنوعی مناسب‌ترین مورد کتابخانه را برای هر صحنه و هر بخش مقاله پیدا می‌کند (یا هیچ‌کدام)."""
    empty = {"video_scenes": [], "section_media": [], "story_media": [], "featured": None, "section_points": []}
    lib = [{"id": i["id"], "type": i["type"], "label": i["label"]} for i in library[:300]]
    prompt = f"""موضوع مقاله: «{topic['title']}»
جمله‌های روایت ویدیو (به ترتیب): {json.dumps(sentences, ensure_ascii=False)}
تیترهای مقاله (به ترتیب): {json.dumps(heads, ensure_ascii=False)}
کتابخانه رسانه سایت (id، type و label که توضیح خود صاحب سایت است): {json.dumps(lib, ensure_ascii=False)}

وظیفه: برای هر جمله ویدیو، هر تیتر مقاله و هر صفحه وب‌استوری (به تعداد جمله‌ها) دقیق‌ترین مورد کتابخانه را پیدا کن.
قوانین: فقط اگر label واقعاً همان محصول، موضوع یا کار را توصیف می‌کند انتخاب کن. اگر شک داری یا مرتبط نیست null بگذار. حدس نزن و مورد بی‌ربط انتخاب نکن (مثلاً برای شومینه گازی، عکس شومینه هیزمی یا باربیکیو ممنوع است). هر id را در هر فهرست فقط یک بار استفاده کن. مورد type=video فقط در video_scenes مجاز است.
برای هر تیتر مقاله ۳ نکته خیلی کوتاه و دقیق فارسی (هرکدام حداکثر ۷ کلمه) هم بنویس (برای کارت گرافیکی).
فقط JSON: {{"video_scenes": [{len(sentences)} عدد id یا null], "section_media": [{len(heads)} عدد id یا null], "story_media": [{len(sentences)} عدد id یا null], "featured": id یا null, "section_points": [{len(heads)} فهرست ۳ تایی]}}"""
    try:
        r = gemini(prompt, retries=1)
    except Exception as e:
        print("library match skipped:", str(e)[:200])
        return empty
    by_id = {i["id"]: i for i in library}

    def clean(lst, n, allow_video):
        out, used = [], set()
        for k in range(n):
            v = lst[k] if isinstance(lst, list) and k < len(lst) else None
            try:
                v = int(v) if v is not None else None
            except (TypeError, ValueError):
                v = None
            it = by_id.get(v)
            if it and v not in used and (allow_video or it["type"] == "image"):
                used.add(v)
                out.append(v)
            else:
                out.append(None)
        return out

    feat = r.get("featured")
    try:
        feat = int(feat) if feat is not None else None
    except (TypeError, ValueError):
        feat = None
    if feat not in by_id or by_id[feat]["type"] != "image":
        feat = None
    pts = r.get("section_points") if isinstance(r.get("section_points"), list) else []
    return {"video_scenes": clean(r.get("video_scenes"), len(sentences), True),
            "section_media": clean(r.get("section_media"), len(heads), False),
            "story_media": clean(r.get("story_media"), len(sentences), False),
            "featured": feat, "section_points": pts}


# ---------------------------------------------------------------- video
def split_sentences(text, max_parts=7):
    parts = [p.strip() for p in re.split(r"(?<=[.!؟?…])\s+", text.strip()) if p.strip()]
    merged = []
    for p in parts:
        if merged and len(merged[-1]) < 40:
            merged[-1] += " " + p
        else:
            merged.append(p)
    while len(merged) > max_parts:
        i = min(range(len(merged) - 1), key=lambda k: len(merged[k]) + len(merged[k + 1]))
        merged[i:i + 2] = [merged[i] + " " + merged[i + 1]]
    return merged


EDGE_VOICE = os.environ.get("EDGE_VOICE", "fa-IR-DilaraNeural")  # صدای زن
EDGE_RATE = os.environ.get("EDGE_RATE", "-8%")
GEMINI_TTS_VOICE = os.environ.get("GEMINI_TTS_VOICE", "Aoede")  # صدای زن طبیعی‌تر


async def tts(text, path):
    await edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE).save(str(path))


def gemini_tts(text, pcm_path, wav_path):
    """صدای طبیعی‌تر با Gemini TTS. اگر خطا داد، برنامه خودش به edge-tts برمی‌گردد."""
    import base64
    models = [n for n in list_models() if "tts" in n]
    if not models:
        raise RuntimeError("no gemini tts model available")
    prompt = ("Language: Persian (Farsi, fa-IR), standard Tehran accent. You are a professional Iranian female "
              "narrator recording an explainer video. Read the text below exactly as written, fluently and naturally, "
              "with correct Persian pronunciation, a warm calm tone, a steady medium pace and short natural pauses "
              "between sentences. Do not add or skip any words and do not read these instructions.\n\nText:\n" + text)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEMINI_TTS_VOICE}}}}}
    last = None
    for model in models[:3]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(3):
            try:
                r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=300)
                if r.status_code == 429:
                    print("tts rate limit, waiting")
                    time.sleep(45)
                    continue
                r.raise_for_status()
                part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
                rate = 24000
                m = re.search(r"rate=(\d+)", part.get("mimeType", ""))
                if m:
                    rate = int(m.group(1))
                Path(pcm_path).write_bytes(base64.b64decode(part["data"]))
                run(["ffmpeg", "-y", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", str(pcm_path),
                     "-ar", "44100", "-ac", "1", "-af", "apad=pad_dur=0.5", str(wav_path)])
                return
            except Exception as e:
                last = e
                print("gemini tts retry", model, attempt, str(e)[:200])
                time.sleep(6)
    raise RuntimeError(f"gemini tts failed: {last}")


def find_pauses(path):
    r = subprocess.run(["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-32dB:d=0.18", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return [(a + b) / 2 for a, b in zip(starts, ends)]


def segment_durations(sentences, wav_path, total):
    """زمان هر جمله را از روی طول متن حدس می‌زند و به نزدیک‌ترین مکث واقعی صدا می‌چسباند."""
    if len(sentences) == 1:
        return [total]
    weights = [max(len(x), 1) for x in sentences]
    pauses = find_pauses(wav_path)
    avg = total / len(sentences)
    bounds, cum = [0.0], 0
    for w in weights[:-1]:
        cum += w
        target = total * cum / sum(weights)
        cands = [p for p in pauses if abs(p - target) <= 0.35 * avg and p > bounds[-1] + 0.8]
        b = min(cands, key=lambda p: abs(p - target)) if cands else max(target, bounds[-1] + 0.8)
        bounds.append(min(b, total - 0.5))
    bounds.append(total)
    return [max(bounds[i + 1] - bounds[i], 0.5) for i in range(len(sentences))]


def synth_all(sentences, work):
    """کل متن را یک‌جا می‌خواند (صدا و لحن یکدست) و زمان جمله‌ها را برای زیرنویس حساب می‌کند."""
    text = " ".join(sentences)
    wav = work / "audio.wav"
    ok = False
    if os.environ.get("USE_GEMINI_TTS", "1") != "0":
        try:
            gemini_tts(text, work / "full.pcm", wav)
            ok = True
            print("voice: gemini tts", GEMINI_TTS_VOICE)
        except Exception as e:
            print("gemini tts failed, falling back to edge-tts:", str(e)[:300])
    if not ok:
        mp3 = work / "full.mp3"
        asyncio.run(tts(text, mp3))
        run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", "-af", "apad=pad_dur=0.5", str(wav)])
        print("voice: edge-tts", EDGE_VOICE)
    total = duration(wav)
    durs = segment_durations(sentences, wav, total)
    return [(sent, "", d) for sent, d in zip(sentences, durs)]


def ass_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def fa(n):
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def esc(t):
    """متن را برای زیرنویس تمیز می‌کند و جهت راست‌به‌چپ را مشخص می‌کند."""
    t = re.sub(r"[{}\\]", "", str(t or "")).replace("\n", " ").strip()
    return ("\u200f" + t + "\u200f") if t else t


def make_bg(work, W, H, name):
    (r0, g0, b0), (r1, g1, b1) = BG_TOP, BG_BOTTOM
    vf = (f"format=gbrp,geq=r='{r0}+({r1}-{r0})*Y/{H}':g='{g0}+({g1}-{g0})*Y/{H}':b='{b0}+({b1}-{b0})*Y/{H}',"
          f"format=rgb24")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d=1", "-vf", vf, "-frames:v", "1",
         f"bg_{name}.png"], cwd=work)
    return f"bg_{name}.png"


def make_explainer_ass(segments, slides, W, H, path, title, intro, outro):
    vertical = H > W
    head_sz = 90 if vertical else 68
    body_sz = 60 if vertical else 46
    sub_sz = 48 if vertical else 38
    sub_mv = 250 if vertical else 60
    cx = W // 2
    head_y = 330 if vertical else 140
    body_y0 = 610 if vertical else 320
    gap = 200 if vertical else 110
    narr = sum(d for _, _, d in segments)
    total = intro + narr + outro
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Head,Vazirmatn,{head_sz},{ACCENT_ASS},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,8,90,90,40,1
Style: Body,Vazirmatn,{body_sz},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,100,100,40,1
Style: Sub,Vazirmatn,{sub_sz},&H00FFFFFF,&H00FFFFFF,&H78000000,&H96000000,1,0,0,0,100,100,0,0,3,3,0,2,90,90,{sub_mv},1
Style: Mark,Vazirmatn,{int(body_sz*0.6)},{ACCENT_ASS},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,40,40,{60 if vertical else 30},1
Style: Card,Vazirmatn,{head_sz},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,5,100,100,40,1
Style: Step,Vazirmatn,{int(body_sz*0.7)},{ACCENT_ASS},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,9,40,40,40,1
Style: Bar,Vazirmatn,20,{ACCENT_BAR},&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,9,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    ev = []
    # برند بالای صفحه در تمام مدت
    ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(total)},Mark,,0,0,0,,{{\\an8\\pos({cx},{60 if vertical else 28})}}{esc(BRAND)}  |  {SITE_SHORT}")
    # کارت عنوان (ابتدا)
    ev.append(f"Dialogue: 2,{ass_time(0.2)},{ass_time(intro)},Card,,0,0,0,,{{\\fad(450,350)}}{esc(title)}")
    # نوار پیشرفت
    bar_h = 14
    ev.append(f"Dialogue: 1,{ass_time(intro)},{ass_time(intro + narr)},Bar,,0,0,0,,"
              f"{{\\an9\\pos({W},0)\\p1\\fscx1\\t(0,{int(narr * 1000)},\\fscx100)}}m 0 0 l {W} 0 l {W} {bar_h} l 0 {bar_h}{{\\p0}}")
    t = intro
    n = len(segments)
    for i, (text, _, d) in enumerate(segments):
        end = t + d
        sl = slides[i] if i < len(slides) else {}
        ttl = esc(sl.get("title") or " ".join(text.split()[:5]))
        ev.append(f"Dialogue: 2,{ass_time(t)},{ass_time(end)},Head,,0,0,0,,{{\\an8\\pos({cx},{head_y})\\fad(250,150)}}{ttl}")
        for k, p in enumerate((sl.get("points") or [])[:3]):
            bs = min(t + 0.7 + 0.9 * k, end - 0.4)
            ev.append(f"Dialogue: 2,{ass_time(bs)},{ass_time(end)},Body,,0,0,0,,"
                      f"{{\\an8\\pos({cx},{body_y0 + k * gap})\\fad(300,100)}}\u200f• {esc(p)}")
        ev.append(f"Dialogue: 2,{ass_time(t)},{ass_time(end)},Step,,0,0,0,,{{\\pos({W - 50},{110 if vertical else 80})}}گام {fa(i + 1)} از {fa(n)}")
        ev.append(f"Dialogue: 3,{ass_time(t)},{ass_time(end)},Sub,,0,0,0,,{esc(text)}")
        t = end
    # کارت پایانی
    ev.append(f"Dialogue: 2,{ass_time(intro + narr)},{ass_time(total)},Card,,0,0,0,,"
              f"{{\\fad(400,0)}}{esc(BRAND)}\\Nتماس: {PHONE}\\N{MOBILE}\\N{SITE_SHORT}")
    Path(path).write_text(head + "\n".join(ev), encoding="utf-8")


def build_explainer(work, segments, slides, scenes, W, H, name, title, intro=3.2, outro=4.5):
    bg = make_bg(work, W, H, name)
    narr = sum(d for _, _, d in segments)
    total = intro + narr + outro
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", "30", "-pix_fmt", "yuv420p"]
    dark = "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.5:t=fill"

    def graphic(d, tag):
        out = f"g_{name}_{tag}.mp4"
        frames = int(round(d * 30)) + 2
        vf = f"zoompan=z='min(1+0.0004*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30"
        run(["ffmpeg", "-y", "-i", bg, "-vf", vf, "-t", f"{d:.3f}"] + enc + [out], cwd=work)
        return out

    clips = [graphic(intro, "intro")]
    for i, (text, _, d) in enumerate(segments):
        sc = scenes[i] if i < len(scenes) else None
        out = f"s_{name}_{i}.mp4"
        try:
            if sc and sc[0] == "vid":
                vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,{dark}"
                run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", sc[1], "-t", f"{d:.3f}", "-vf", vf, "-an"] + enc + [out], cwd=work)
            elif sc and sc[0] == "img":
                frames = int(round(d * 30)) + 2
                sw, sh = int(W * 1.5) // 2 * 2, int(H * 1.5) // 2 * 2
                z = "min(zoom+0.0007,1.12)" if i % 2 == 0 else "if(eq(on,1),1.12,max(zoom-0.0007,1.0))"
                vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},"
                      f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,{dark}")
                run(["ffmpeg", "-y", "-i", sc[1], "-vf", vf, "-t", f"{d:.3f}"] + enc + [out], cwd=work)
            else:
                out = graphic(d, f"seg{i}")
        except Exception as e:
            print("scene failed, using graphic:", i, str(e)[:100])
            out = graphic(d, f"seg{i}")
        clips.append(out)
    clips.append(graphic(outro, "outro"))
    (work / f"list_{name}.txt").write_text("".join(f"file '{c}'\n" for c in clips))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"list_{name}.txt", "-c", "copy", f"base_{name}.mp4"], cwd=work)
    make_explainer_ass(segments, slides, W, H, work / f"sub_{name}.ass", title, intro, outro)
    ms = int(intro * 1000)
    fc = (f"[1:a]adelay={ms}:all=1,apad=whole_dur={total:.2f}[a];[0:v]ass=sub_{name}.ass,format=yuv420p[v]")
    out = f"{name}.mp4"
    run(["ffmpeg", "-y", "-i", f"base_{name}.mp4", "-i", "audio.wav", "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], cwd=work)
    return work / out


def make_videos(art, sentences, scene_ids, lib_by_id, work):
    segments = synth_all(sentences, work)
    segments = [(t, w, max(round(d * 30) / 30, 0.5)) for t, w, d in segments]
    slides = art.get("slides") or []
    scenes = []
    for i in range(len(segments)):
        sid = scene_ids[i] if i < len(scene_ids) else None
        item = lib_by_id.get(sid) if sid else None
        sc = None
        if item:
            try:
                name = f"lib_{item['id']}" + (".mp4" if item["type"] == "video" else ".jpg")
                download(item["url"], work / name)
                sc = ("vid" if item["type"] == "video" else "img", name)
            except Exception as e:
                print("library download failed:", str(e)[:100])
        scenes.append(sc)
    print("video scenes:", [sc[0] if sc else "graphic" for sc in scenes])
    vv = build_explainer(work, segments, slides, scenes, 1080, 1920, "vertical", art["title"])
    vh = build_explainer(work, segments, slides, scenes, 1920, 1080, "horizontal", art["title"])
    return vv, vh


def still_ass(W, H, title, points, step):
    vertical = H > W
    square = abs(W - H) < 50
    head_sz = 90 if vertical else (46 if square else 62)
    body_sz = 60 if vertical else (30 if square else 42)
    cx = W // 2
    head_y = 420 if vertical else (90 if square else 110)
    body_y0 = 760 if vertical else (230 if square else 270)
    gap = 210 if vertical else (80 if square else 105)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Head,Vazirmatn,{head_sz},{ACCENT_ASS},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,8,60,60,40,1
Style: Body,Vazirmatn,{body_sz},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,70,70,40,1
Style: Mark,Vazirmatn,{int(body_sz*0.6)},{ACCENT_ASS},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,40,40,{60 if vertical else 24},1
Style: Step,Vazirmatn,{int(body_sz*0.7)},{ACCENT_ASS},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,9,40,40,40,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    ev = [f"Dialogue: 1,{ass_time(0)},{ass_time(9)},Mark,,0,0,0,,{{\\an8\\pos({cx},{60 if vertical else 24})}}{esc(BRAND)}  |  {SITE_SHORT}",
          f"Dialogue: 2,{ass_time(0)},{ass_time(9)},Head,,0,0,0,,{{\\an8\\pos({cx},{head_y})}}{esc(title)}"]
    for k, p in enumerate((points or [])[:3]):
        ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(9)},Body,,0,0,0,,{{\\an8\\pos({cx},{body_y0 + k * gap})}}\u200f• {esc(p)}")
    if step:
        ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(9)},Step,,0,0,0,,{{\\pos({W - 50},{110 if vertical else 60})}}{esc(step)}")
    return head + "\n".join(ev)


def render_still(work, W, H, photo, title, points, out, step=None):
    """یک تصویر ثابت (کارت گرافیکی یا عکس کتابخانه با نوشته) می‌سازد."""
    Path(work / f"{out}.ass").write_text(still_ass(W, H, title, points, step), encoding="utf-8")
    bg = photo or make_bg(work, W, H, f"still{W}x{H}")
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if photo:
        vf += ",drawbox=x=0:y=0:w=iw:h=ih:color=black@0.5:t=fill"
    vf += f",ass={out}.ass"
    run(["ffmpeg", "-y", "-i", bg, "-vf", vf, "-frames:v", "1", "-q:v", "2", out], cwd=work)
    return work / out


# ---------------------------------------------------------------- wordpress
def upload(path, mime, title, alt=""):
    path = Path(path)
    r = requests.post(f"{API}/media", auth=AUTH, timeout=900,
                      headers={"Content-Disposition": f'attachment; filename="{path.name}"', "Content-Type": mime},
                      data=path.read_bytes())
    r.raise_for_status()
    j = r.json()
    requests.post(f"{API}/media/{j['id']}", auth=AUTH, json={"title": title, "alt_text": alt, "caption": alt, "description": "AUTO"}, timeout=60)
    return j["id"], j["source_url"]


def term(kind, name):
    r = requests.get(f"{API}/{kind}", params={"search": name, "per_page": 50}, auth=AUTH, timeout=60).json()
    for t in r:
        if t["name"] == name:
            return t["id"]
    r = requests.post(f"{API}/{kind}", json={"name": name}, auth=AUTH, timeout=60)
    return r.json()["id"] if r.ok else None


def sanitize_html(h):
    """متن مقاله را تمیز و برای موبایل مناسب می‌کند."""
    h = (h or "").strip()
    h = re.sub(r"^```(?:html)?\s*|\s*```$", "", h, flags=re.I).strip()
    if h.count("&lt;") > 5 and "<h2" not in h:
        h = html.unescape(h)
    h = re.sub(r"(?is)<(script|style|iframe)\b.*?</\1>", "", h)
    h = re.sub(r"(?is)<!doctype[^>]*>", "", h)
    h = re.sub(r"(?is)</?(html|head|body|h1)\b[^>]*>", "", h)
    h = re.sub(r"(?is)<table\b[^>]*>", '<table style="width:100%;border-collapse:collapse;font-size:15px">', h)
    h = re.sub(r"(?is)<th\b[^>]*>", '<th style="border:1px solid #d0b79a;background:#f0e0cc;color:#3a2410;padding:8px;text-align:right">', h)
    h = re.sub(r"(?is)<td\b[^>]*>", '<td style="border:1px solid #d0b79a;background:#ffffff;color:#2a1a0e;padding:8px;text-align:right;vertical-align:top">', h)
    h = re.sub(r"(?is)(<table\b.*?</table>)",
               r'<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;margin:16px 0">\1</div>', h)
    return h


PLACEHOLDER = (
    '<!-- wp:html -->\n<div style="border:2px dashed #e0a800;padding:16px;margin:0 0 22px;text-align:center;'
    'background:#fff8e1;color:#5c4400;font-weight:bold">📹 جای ویدیوهای آپارات و یوتیوب. بعد از آپلود، مرحله attach-video را در GitHub اجرا کنید تا این کادر خودکار با ویدیوها پر شود.</div>\n<!-- /wp:html -->\n')


def figure_html(url, alt, caption, dims=""):
    return (f'<figure style="margin:18px 0;text-align:center"><img src="{url}" alt="{html.escape(alt)}"{dims} loading="lazy" '
            f'style="max-width:100%;height:auto;border-radius:10px">'
            f'<figcaption style="font-size:14px;opacity:.85">{html.escape(caption)}</figcaption></figure>')


def insert_section_images(h, figs):
    parts = re.split(r"(?i)(?=<h2\b)", h)
    out = [parts[0]]
    for idx, part in enumerate(parts[1:]):
        if idx in figs:
            m = re.search(r"(?is)</h2>.*?</p>", part)
            if m:
                part = part[:m.end()] + figs[idx] + part[m.end():]
            else:
                part = re.sub(r"(?is)</h2>", "</h2>" + figs[idx], part, count=1)
        out.append(part)
    return "".join(out)


def add_toc(h):
    """به هر تیتر h2 شناسه می‌دهد و فهرست سرفصل‌ها را می‌سازد."""
    items = []

    def rep(m):
        items.append(strip_tags(m.group(2)))
        return f'<h2 id="sec-{len(items)}"{m.group(1)}>{m.group(2)}</h2>'

    h = re.sub(r"(?is)<h2\b([^>]*)>(.*?)</h2>", rep, h)
    return h, items


def build_content(art, figs, with_placeholder, banner_url="", related=None):
    body, items = add_toc(insert_section_images(art["article_html"], figs))
    h = PLACEHOLDER if with_placeholder else ""
    h += '<div dir="rtl">\n'
    if banner_url:
        h += figure_html(banner_url, art["title"], "", ' width="1600" height="500"').replace("border-radius:10px", "border-radius:12px;width:100%")
    pts = [p for p in (art.get("summary_points") or []) if str(p).strip()][:5]
    if pts:
        h += ('<div style="border:2px solid #b87333;border-radius:12px;padding:16px;margin:18px 0;background:#fff4e8;color:#2a1a0e">'
              '<h2 style="margin-top:0;color:#6b3a12;font-size:20px">خلاصه مقاله</h2><ul style="color:#2a1a0e;margin:0;padding-right:20px">'
              + "".join(f"<li>{html.escape(str(p))}</li>" for p in pts) + "</ul></div>\n")
    toc_items = items + (["سوالات متداول"] if art.get("faq") else [])
    if len(toc_items) >= 3:
        h += ('<nav style="border:1px solid #d0b79a;border-radius:12px;padding:16px;margin:18px 0;background:#ffffff;color:#2a1a0e">'
              '<strong style="color:#6b3a12">سرفصل‌های مقاله</strong><ol style="color:#2a1a0e;margin:8px 0 0;padding-right:22px">'
              + "".join(f'<li><a href="#{"faq" if (art.get("faq") and k == len(toc_items) - 1) else "sec-" + str(k + 1)}" style="color:#8a4b14">{html.escape(t)}</a></li>'
                        for k, t in enumerate(toc_items)) + "</ol></nav>\n")
    h += body
    if art.get("faq"):
        h += '\n<h2 id="faq">سوالات متداول</h2>\n'
        for f in art["faq"]:
            h += f"<h3>{html.escape(f['q'])}</h3>\n<p>{html.escape(f['a'])}</p>\n"
    if related:
        h += ('<div style="border:1px solid #d0b79a;border-radius:12px;padding:16px;margin:24px 0;background:#ffffff;color:#2a1a0e">'
              '<strong style="color:#6b3a12">مطالب مرتبط</strong><ul style="color:#2a1a0e;margin:8px 0 0;padding-right:20px">'
              + "".join(f'<li><a href="{r["url"]}" style="color:#8a4b14">{html.escape(strip_tags(r["title"]))}</a></li>' for r in related[:4])
              + "</ul></div>\n")
    h += f"""
<div style="border:2px solid #b87333;border-radius:12px;padding:18px;margin-top:30px;background:#fff8f2;color:#2a1a0e">
<h3 style="color:#6b3a12;margin-top:0">مشاوره و سفارش از {BRAND}</h3>
<p style="color:#2a1a0e">تلفن: <a href="tel:{PHONE}" style="color:#8a4b14">{PHONE}</a> | موبایل: <a href="tel:{MOBILE}" style="color:#8a4b14">{MOBILE}</a></p>
<p style="color:#2a1a0e">آدرس کارگاه: {WORKSHOP}</p>
<p style="color:#2a1a0e">آدرس دفتر: {OFFICE}</p>
</div>
</div>"""
    return h


def set_rank_math(post_id, topic, art, image_url):
    secondary = [t for t in (topic.get("kw2", []) + art.get("tags", []))[:4] if t and t != topic["kw"]]
    meta = {"rank_math_title": f"%title% %sep% {BRAND}",
            "rank_math_description": art["meta_description"],
            "rank_math_focus_keyword": ",".join([topic["kw"]] + secondary),
            "rank_math_facebook_title": art["title"],
            "rank_math_facebook_description": art["meta_description"],
            "rank_math_twitter_use_facebook": "on"}
    if image_url:
        meta["rank_math_facebook_image"] = image_url
    try:
        rm = requests.post(f"{SITE}/wp-json/rankmath/v1/updateMeta", auth=AUTH, timeout=60,
                           json={"objectID": post_id, "objectType": "post", "meta": meta})
        print("rankmath:", rm.status_code, rm.text[:120])
    except Exception as e:
        print("rankmath update failed:", type(e).__name__)


# ---------------------------------------------------------------- telegram
def tg_call(method, data, files=None):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/{method}", data=data, files=files, timeout=900)
        if not r.ok:
            print("telegram error:", r.status_code, r.text[:200])
        return r.ok
    except Exception as e:
        print("telegram failed:", type(e).__name__)
        return False


def fit_for_telegram(path):
    path = Path(path)
    if path.stat().st_size <= 48 * 1024 * 1024:
        return path
    out = path.with_name(path.stem + "_small.mp4")
    run(["ffmpeg", "-y", "-i", str(path), "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
         "-c:a", "aac", "-b:a", "96k", str(out)])
    return out


def tg_pick_chat():
    """اگر شناسه چت اشتباه بود، آخرین گفتگوی خصوصی شما با ربات را پیدا می‌کند."""
    try:
        r = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", timeout=60)
        for u in reversed(r.json().get("result", [])):
            msg = u.get("message") or u.get("edited_message") or {}
            ch = msg.get("chat") or {}
            if ch.get("type") == "private" and not (msg.get("from") or {}).get("is_bot"):
                return str(ch["id"])
    except Exception as e:
        print("telegram getUpdates failed:", type(e).__name__)
    return ""


def send_to_telegram(art, article_url, vv, vh, post_id=0):
    if not (TG_TOKEN and TG_CHAT):
        print("telegram not configured: videos saved only as backup artifact")
        return False
    tags = " ".join("#" + re.sub(r"\s+", "_", str(t).strip().lstrip("#")) for t in (art.get("hashtags") or [])[:8])
    msg = (f"📹 ویدیوی امروز {BRAND}\n\nعنوان ویدیو:\n{art.get('video_title') or art['title']}\n\n"
           f"توضیحات ویدیو:\n{art.get('video_description', '')}\n\n{tags}\n\nلینک مقاله برای گذاشتن زیر ویدیو: {article_url}\nشناسه مقاله (برای مرحله آخر): {post_id}")
    chat = TG_CHAT
    if not tg_call("sendMessage", {"chat_id": chat, "text": msg[:4000]}):
        alt = tg_pick_chat()
        if not alt:
            print("telegram: شناسه چت اشتباه است. در تلگرام به ربات خودتان یک پیام بدهید و دوباره اجرا کنید.")
            return False
        print(f"telegram: شناسه چت اشتباه بود. شناسه درست شما این عدد است: {alt} (آن را در TELEGRAM_CHAT_ID بگذارید)")
        chat = alt
        if not tg_call("sendMessage", {"chat_id": chat, "text": msg[:4000]}):
            return False
    ok = True
    for label, p in (("ویدیوی افقی: برای آپارات و داخل مقاله", vh), ("ویدیوی عمودی: برای یوتیوب Shorts", vv)):
        try:
            p = fit_for_telegram(p)
            with open(p, "rb") as f:
                ok = tg_call("sendVideo", {"chat_id": chat, "caption": label, "supports_streaming": "true"},
                             {"video": f}) and ok
        except Exception as e:
            print("telegram video failed:", type(e).__name__)
            ok = False
    return ok


# ---------------------------------------------------------------- web story
def story_html(title, poster_url, logo_url, pages, article_url):
    t = html.escape(title, quote=True)
    out = (f'<amp-story standalone title="{t}" publisher="{html.escape(BRAND, quote=True)}" '
           f'publisher-logo-src="{logo_url}" poster-portrait-src="{poster_url}">')
    for i, (img, alt) in enumerate(pages):
        last = i == len(pages) - 1
        out += (f'<amp-story-page id="page-{i + 1}" auto-advance-after="6s"><amp-story-grid-layer template="fill">'
                f'<amp-img src="{img}" width="1080" height="1920" layout="fill" alt="{html.escape(alt, quote=True)}"></amp-img>'
                f'</amp-story-grid-layer>')
        if last and article_url:
            out += f'<amp-story-page-outlink layout="nodisplay"><a href="{article_url}">مشاهده مقاله کامل</a></amp-story-page-outlink>'
        out += '</amp-story-page>'
    return out + '</amp-story>'


def _uid():
    import uuid
    return str(uuid.uuid4())


def story_data_json(pages):
    """ساختار داده‌ی ویرایشگر Web Stories (افزونه هر دو را با هم می‌خواهد)."""
    white = {"color": {"r": 255, "g": 255, "b": 255}}
    out = []
    for url, alt, mid in pages:
        out.append({"id": _uid(), "type": "page", "backgroundColor": white, "elements": [
            {"id": _uid(), "type": "shape", "x": 1, "y": 1, "width": 1, "height": 1, "scale": 100, "focalX": 50, "focalY": 50,
             "mask": {"type": "rectangle"}, "flip": {"vertical": False, "horizontal": False},
             "isBackground": True, "isDefaultBackground": True, "backgroundColor": white},
            {"id": _uid(), "type": "image", "x": 0, "y": 0, "width": 412, "height": 732, "rotationAngle": 0,
             "scale": 100, "focalX": 50, "focalY": 50, "mask": {"type": "rectangle"},
             "flip": {"vertical": False, "horizontal": False},
             "resource": {"type": "image", "mimeType": "image/jpeg", "id": mid, "src": url, "width": 1080,
                          "height": 1920, "alt": alt, "isPlaceholder": False, "sizes": {}}}]})
    return {"version": 50, "pages": out, "autoAdvance": True, "defaultPageDuration": 6,
            "currentStoryStyles": {"colors": [], "textStyles": []}}


def create_web_story(work, art, slides, story_ids, lib_by_id, article_url, base="article"):
    """وب‌استوری را به صورت پیش‌نویس می‌سازد (نیاز به افزونه Web Stories)."""
    pages, n = [], min(len(slides), 6)
    for i in range(n):
        sl = slides[i]
        photo = None
        item = lib_by_id.get(story_ids[i]) if i < len(story_ids) and story_ids[i] else None
        if item and item["type"] == "image":
            try:
                photo = f"storybg_{i}.jpg"
                download(item["large"], work / photo)
            except Exception:
                photo = None
        name = f"{base}-story-{i + 1}.jpg"
        render_still(work, 1080, 1920, photo, sl.get("title", ""), sl.get("points", []), name, step=f"{fa(i + 1)} / {fa(n)}")
        mid, url = upload(work / name, "image/jpeg", f"{art['title']} - {i + 1}", sl.get("title", art["title"]))
        pages.append((url, sl.get("title", art["title"]), mid))
    render_still(work, 1080, 1920, None, BRAND, [f"تلفن: {PHONE}", f"موبایل: {MOBILE}", SITE_SHORT], f"{base}-story-contact.jpg")
    mid, url = upload(work / f"{base}-story-contact.jpg", "image/jpeg", f"{art['title']} - تماس", BRAND)
    pages.append((url, f"تماس با {BRAND}", mid))
    render_still(work, 960, 1280, None, art["title"], [], f"{base}-story-poster.jpg")
    pid, poster_url = upload(work / f"{base}-story-poster.jpg", "image/jpeg", art["title"], art["title"])
    logo_url = ""
    try:
        logo_url = requests.get(f"{SITE}/wp-json/", timeout=30).json().get("site_icon_url") or ""
    except Exception:
        pass
    if not logo_url:
        render_still(work, 512, 512, None, BRAND, [], f"{base}-logo.jpg")
        _, logo_url = upload(work / f"{base}-logo.jpg", "image/jpeg", BRAND, BRAND)
    content = story_html(art["title"], poster_url, logo_url, [(u, a) for u, a, _ in pages], article_url)
    payload = {"title": art["title"], "status": "draft", "content": content,
               "story_data": story_data_json(pages), "featured_media": pid}
    for ep in (f"{SITE}/wp-json/web-stories/v1/web-story", f"{API}/web-story"):
        r = requests.post(ep, auth=AUTH, json=payload, timeout=120)
        print("web story:", ep.split("/wp-json/")[1], r.status_code, "ok" if r.ok else r.text[:200])
        if r.ok:
            return True
    return False


# ---------------------------------------------------------------- main
def related_posts():
    try:
        r = requests.get(f"{API}/posts", params={"per_page": 6, "status": "publish", "_fields": "title,link"}, timeout=60)
        return [{"title": p["title"]["rendered"], "url": p["link"]} for p in r.json()]
    except Exception:
        return []


def main():
    state = load_state()
    topic = pick_topic(state)
    print("topic:", topic["title"], "| keyword:", topic["kw"])
    art = write_article(topic)
    art["article_html"] = sanitize_html(art["article_html"])
    print("article:", art["title"])

    slug = re.sub(r"[^a-z0-9-]+", "-", str(art.get("slug", "")).lower()).strip("-")[:60] or "article"
    work = Path(tempfile.mkdtemp())
    sentences = split_sentences(art["narration"])
    heads_all = [strip_tags(x) for x in re.findall(r"(?is)<h2\b[^>]*>(.*?)</h2>", art["article_html"])]
    cand = [i for i, hd in enumerate(heads_all) if not re.search(r"سوالات متداول|نتیجه", hd)][:6]
    library = fetch_library()
    lib_by_id = {i["id"]: i for i in library}
    m = match_library(topic, sentences, [heads_all[i] for i in cand], library)

    vv = vh = None
    try:
        vv, vh = make_videos(art, sentences, m["video_scenes"], lib_by_id, work)
        outdir = HERE / "out"
        outdir.mkdir(exist_ok=True)
        shutil.copy(vv, outdir / "vertical.mp4")
        shutil.copy(vh, outdir / "horizontal.mp4")
    except Exception as e:
        print("video creation failed, continuing with article only:", str(e)[:200])

    # تصویر شاخص: عکس مرتبط کتابخانه، وگرنه کارت گرافیکی
    featured_id, featured_url = None, ""
    if m["featured"] and m["featured"] in lib_by_id:
        featured_id, featured_url = m["featured"], lib_by_id[m["featured"]]["url"]
    else:
        try:
            cover = render_still(work, 1280, 720, None, art["title"], [], f"{slug}-cover.jpg")
            featured_id, featured_url = upload(cover, "image/jpeg", art["title"], art.get("image_alt", art["title"]))
        except Exception as e:
            print("cover failed:", str(e)[:150])

    # بنر بالای مقاله
    banner_url = ""
    try:
        bn = render_still(work, 1600, 500, None, art["title"], [], f"{slug}-banner.jpg")
        _, banner_url = upload(bn, "image/jpeg", art["title"], f"بنر {art['title']}")
    except Exception as e:
        print("banner failed:", str(e)[:150])

    # عکس هر بخش مقاله
    figs, cards = {}, 0
    for pos, i in enumerate(cand):
        try:
            sid = m["section_media"][pos] if pos < len(m["section_media"]) else None
            item = lib_by_id.get(sid) if sid else None
            if item:
                figs[i] = figure_html(item["large"], item["alt"], item["label"][:120])
            elif cards < 4 and pos < len(m["section_points"]) and m["section_points"][pos]:
                jpg = render_still(work, 1280, 720, None, heads_all[i], m["section_points"][pos], f"{slug}-section-{pos + 1}.jpg")
                _, url = upload(jpg, "image/jpeg", heads_all[i], f"{heads_all[i]} - {art['title']}")
                figs[i] = figure_html(url, f"{heads_all[i]} - {art['title']}", heads_all[i], ' width="1280" height="720"')
                cards += 1
        except Exception as e:
            print("section image failed:", str(e)[:150])

    content = build_content(art, figs, with_placeholder=bool(vh and TG_TOKEN and TG_CHAT),
                            banner_url=banner_url, related=related_posts())
    cats = [c for c in [term("categories", topic["cat"])] if c]
    tags = [t for t in (term("tags", x) for x in art.get("tags", [])[:5]) if t]
    payload = {"title": art["title"], "content": content, "excerpt": art["meta_description"],
               "status": POST_STATUS, "categories": cats, "tags": tags, "slug": slug}
    if featured_id:
        payload["featured_media"] = featured_id
    r = requests.post(f"{API}/posts", auth=AUTH, timeout=120, json=payload)
    r.raise_for_status()
    post = r.json()
    article_url = f"{SITE}/?p={post['id']}"
    print("created:", article_url, POST_STATUS)
    set_rank_math(post["id"], topic, art, featured_url)

    if vv and vh:
        send_to_telegram(art, article_url, vv, vh, post["id"])
    try:
        create_web_story(work, art, art.get("slides") or [], m["story_media"], lib_by_id, article_url, slug)
    except Exception as e:
        print("web story failed:", str(e)[:200])

    state["done"].append(topic["title"])
    save_state(state)


# ---------------------------------------------------------------- attach (after you upload to Aparat / YouTube)
def youtube_id(url):
    m = re.search(r"(?:youtu\.be/|v=|/shorts/|/embed/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else ""


def attach():
    pid = os.environ.get("POST_ID", "").strip()
    aparat = os.environ.get("APARAT_URL", "").strip()
    embed = os.environ.get("APARAT_EMBED", "").strip()
    yt = os.environ.get("YOUTUBE_URL", "").strip()
    shorts = os.environ.get("SHORTS_URL", "").strip()
    publish = os.environ.get("PUBLISH", "no").strip().lower() == "yes"
    if not pid:
        raise SystemExit("POST_ID is empty")
    r = requests.get(f"{API}/posts/{pid}", params={"context": "edit"}, auth=AUTH, timeout=60)
    r.raise_for_status()
    raw = r.json()["content"]["raw"]
    block = ""
    if embed:
        block += f'<div style="max-width:100%;margin:0 0 18px">{embed}</div>'
    ytid = youtube_id(yt)
    if ytid:
        block += (f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:0 0 18px">'
                  f'<iframe src="https://www.youtube.com/embed/{ytid}" title="ویدیو" loading="lazy" allowfullscreen '
                  f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0"></iframe></div>')
    links = []
    if aparat:
        links.append(f'<a href="{aparat}" target="_blank" rel="noopener">مشاهده این ویدیو در آپارات</a>')
    if yt:
        links.append(f'<a href="{yt}" target="_blank" rel="noopener">مشاهده در یوتیوب</a>')
    if shorts:
        links.append(f'<a href="{shorts}" target="_blank" rel="noopener">نسخه کوتاه (Shorts)</a>')
    if links:
        block += '<p style="margin:0 0 18px">🎬 ' + " | ".join(links) + "</p>"
    pattern = r"<!-- wp:html -->\s*<div[^>]*dashed[^>]*>.*?</div>\s*<!-- /wp:html -->"
    new_block = f"<!-- wp:html -->\n{block}\n<!-- /wp:html -->\n"
    if re.search(pattern, raw, flags=re.S):
        new = re.sub(pattern, lambda _m: new_block, raw, count=1, flags=re.S)
    else:
        new = new_block + raw
    payload = {"content": new}
    if publish:
        payload["status"] = "publish"
    r = requests.post(f"{API}/posts/{pid}", auth=AUTH, json=payload, timeout=120)
    r.raise_for_status()
    print("updated post", pid, "| published:", publish, "|", r.json().get("link"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "attach":
        attach()
    else:
        main()
