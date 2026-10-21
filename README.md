# راهنمای راه‌اندازی (یک بار، حدود ۲۰ دقیقه)

## ۱) وردپرس
1. افزونه **Rank Math SEO** را نصب و فعال کنید (نام درست: Rank Math).
2. وارد پنل شوید: **کاربران ← پروفایل شما ← پایین صفحه، بخش Application Passwords**.
   نام بنویسید (مثلاً `bot`) و «افزودن» بزنید. رمز نمایش‌داده‌شده را کپی کنید (فقط یک بار دیده می‌شود).
3. اگر پیام «Application Passwords غیرفعال است» دیدید، سایت باید HTTPS باشد یا افزونه امنیتی آن را بسته است.
4. محدودیت حجم آپلود هاست را بررسی کنید (ویدیوها حدود ۵ تا ۲۵ مگابایت‌اند). اگر کم است از هاست بخواهید `upload_max_filesize` را روی ۶۴ مگابایت بگذارند.

## ۲) کلید رایگان Gemini
در سایت aistudio.google.com با حساب گوگل وارد شوید ← **Get API key** ← کلید را کپی کنید.

## ۳) GitHub
1. در github.com حساب رایگان بسازید.
2. مخزن جدید **Private** بسازید (مثلاً `firecastle-bot`).
3. «uploading an existing file» را بزنید و **همه فایل‌های این پوشه (از جمله پوشه .github)** را بکشید و رها کنید و Commit بزنید.
   (اگر پوشه `.github` مخفی بود، فایل `daily.yml` را از مسیر `.github/workflows/` به صورت دستی با Add file ← Create new file بسازید.)
4. **Settings ← Secrets and variables ← Actions ← New repository secret** و این‌ها را بسازید:
   - `WP_USER` = نام کاربری وردپرس
   - `WP_APP_PASSWORD` = رمز Application Password
   - `GEMINI_API_KEY` = کلید گوگل
   - `PEXELS_API_KEY` = (اختیاری) کلید رایگان از pexels.com/api
5. **Settings ← Actions ← General ← Workflow permissions ← Read and write permissions** را فعال و ذخیره کنید.

## ۴) تست
تب **Actions ← daily-content ← Run workflow**. بعد از چند دقیقه یک **پیش‌نویس** در وردپرس می‌بینید.
بعد از اینکه از کیفیت راضی بودید، در فایل `.github/workflows/daily.yml` مقدار `POST_STATUS: draft` را به `publish` تغییر دهید.

## نکات
- هر روز حدود ساعت ۷:۳۰ صبح اجرا می‌شود (قابل تغییر در `cron`).
- عکس‌ها اول از **کتابخانه رسانه‌ی سایت** انتخاب می‌شوند. فقط عکس‌های مناسب (محصول، کارگاه) را در آن نگه دارید؛ عکس‌های کوچک‌تر از ۸۰۰ پیکسل نادیده گرفته می‌شوند.
- صدای گوینده: در `config.py` مقدار `VOICE` را `fa-IR-DilaraNeural` کنید تا صدای زن شود.
- موضوعات در `topics.json` هستند؛ وقتی تمام شدند، خودش موضوع جدید می‌سازد.
