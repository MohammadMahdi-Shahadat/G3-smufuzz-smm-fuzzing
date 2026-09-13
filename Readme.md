![Logo](https://placehold.co/600x150/EEE/757D6F?text=SmuFuzz+Project\n+600x150&font=raleway)

# SmuFuzz: Deep System Management Mode Fuzzing in UEFI Runtime

## فهرست مطالب (Table of Contents)
1. [درباره پروژه (About The Project)](#about-the-project)
2. [ابزارها و تکنولوژی‌ها (Tools)](#tools)
3. [راهنمای اجرا (Getting Started)](#getting-started)
   - [جزئیات پیاده‌سازی (Implementation Details)](#implementation-details)
   - [نحوه اجرا (How to Run)](#how-to-run)
4. [نتایج و دستاوردها (Results)](#results)
5. [لینک‌های مرتبط (Related Links)](#related-links)
6. [اعضای تیم (Authors)](#authors)

## درباره پروژه (About The Project)

این پروژه با هدف کشف آسیب‌پذیری‌های تخریب حافظه (Memory Corruption) در ماژول‌های متن‌بسته (Closed-source) مربوط به حالت مدیریت سیستم (SMM) که توسط Vendorها توسعه یافته‌اند، طراحی شده است. حالت SMM با سطح دسترسی بسیار بالا (Ring -2) و کنترل کامل بر منابع سیستم، هدفی جذاب برای مهاجمین جهت استقرار بدافزارهای دائمی (Persistent Rootkits) محسوب می‌شود.

چالش اصلی در فازینگ (Fuzzing) این برنامه‌ها، فقدان یک محیط اجرایی کامل UEFI (UEFI Runtime Environment) برای بارگذاری و مقداردهی اولیه صحیح داده‌ها است که در روش‌های سنتی منجر به کرش‌های زودرس و نرخ بالای خطای مثبت کاذب (False-positive) می‌شود[cite: 13]. 
ما در این پروژه از طریق تکنیک بازمیزبانی جزئی (Partial Rehosting) و ایجاد یک زیرساخت تطبیقی، ماژول‌های SMM را آماده‌سازی، مقداردهی و ایزوله کرده ایم[cite: 13]. از ویژگی‌های منحصربه‌فرد این سیستم می‌توان به استنباط خودکار ساختار ورودی (Automated Semantics Inference) و مکانیزم ورودی‌های چندجریانی (Multi-stream Input) جهت کاوش عمیق کدهای SMM اشاره کرد[cite: 13].

## ابزارها و تکنولوژی‌ها (Tools)

در توسعه زیرساخت فازینگ و شبیه‌ساز این پروژه، از ابزارها و سخت‌افزارهای زیر استفاده شده است:

- **LibAFL QEMU**: شبیه‌ساز اصلی با قابلیت هوک کردن دسترسی‌های حافظه و رجیسترها جهت اجرای فریمور UEFI[cite: 13].
- **Rust (LibAFL)**: زبان برنامه‌نویسی امن و مدرن که برای توسعه موتور فازر ماژولار و پرسرعت پروژه به کار رفته است[cite: 13].
- **Python 3**: جهت توسعه اسکریپت‌های اتوماسیون استخراج، رهگیر حافظه (Interceptor) و هارنس‌های فازینگ.
- **UEFIExtract**: ابزار مهندسی معکوس برای پارس کردن ساختار FFS و استخراج ماژول‌های SMM از ایمیج‌های باینری فریمور[cite: 13].
- **OVMF (EDK II)**: فریمور ماشین مجازی متن‌باز (Open Virtual Machine Firmware) که به عنوان فریمور پایه برای شبیه‌سازی مراحل بوت UEFI استفاده شده است[cite: 13].

## راهنمای اجرا (Getting Started)

برای راه‌اندازی و اجرای پایپ‌لاین SmuFuzz در محیط محلی لینوکس ایزوله خود (Ubuntu 24.04 LTS)، مراحل زیر را دنبال کنید:

### جزئیات پیاده‌سازی (Implementation Details)

معماری سامانه SmuFuzz بر اساس چرخه حیات SMM به سه فاز متوالی تقسیم شده است[cite: 13]:

1. **فاز اول (Composing Phase):** ماژول‌های مشخص‌شده به عنوان SMM Core یا SMM Module از فریمور تجاری Vendor استخراج شده و به فریمور زیرساخت ما (Infrastructure Firmware) تزریق می‌شوند[cite: 13]. ماژول `PiSmmCpuDxeSmm` به صورت دستی حذف می‌گردد تا هندلر اکسپشن اختصاصی فازر بتواند کرش‌ها را رهگیری کند[cite: 13].
2. **فاز دوم (Initialization Phase):** فریمور پایه در شبیه‌ساز بوت می‌شود تا ماژول‌های SMM بارگذاری و مقداردهی (Initialize) شوند[cite: 13]. موتور SmuFuzz از داده‌های فازینگ برای ارضای متغیرهای NVRAM، بلوک‌های HOB و ثبات‌های MSR استفاده می‌کند تا ماژول‌ها بدون کرش‌های اولیه لود شوند[cite: 13]. در این فاز، نمونه‌های ساختگی (Dummy Instances) از پروتکل‌های اختصاصی DXE نیز سنتز می‌شوند[cite: 13].
3. **فاز سوم (Deep Fuzzing Phase):** پس از شبیه‌سازی رویداد قفل (Lock Event)، فازر به طور مستقیم (Explicitly) وقفه‌های SMI را برای کاوش منطق عمیق برنامه‌ها تریگر می‌کند[cite: 13]. ورودی‌ها به ۴ استریم مجزا (CommBuf, HandlerSel, IO, Mem) شکسته می‌شوند[cite: 13]. رهگیر حافظه (Interceptor) با هدایت دسترسی‌های غیر مجاز خارج از SMRAM به موتور فازر، آسیب‌پذیری‌های Double-fetch و دسترسی خارج از محدوده را شناسایی می‌کند[cite: 13].

### نحوه اجرا (How to Run)

برای اجرای کامل سناریوی پروژه، دستورات زیر را به ترتیب در ترمینال اجرا کنید:

1. **اجرای فاز ترکیب (Composing):** استخراج ماژول‌های PE32 اجرایی و سکشن‌های Depex از فریمور تارگت.
   ```bash
   python3 scripts/composing.py vendor_firmwares/OVMF_SMM.fd
اجرای فاز مقداردهی اولیه (Initialization): لود ماژول‌ها، حل وابستگی‌های پروتکلی DXE و شبیه‌سازی Lock Event.

Bash
python3 phase2_init/harness/init_fuzzer.py
python3 phase2_init/harness/grouping.py
python3 phase2_init/harness/lock_event.py
اجرای فاز فازینگ عمیق (Deep Fuzzing): اجرای موتور فازر Multi-stream جهت تریاژ آسیب‌پذیری‌های تخریب حافظه.

Bash
python3 phase3_fuzz/engine/fuzz_harness.py
نتایج و دستاوردها (Results)
پیاده‌سازی ما با موفقیت ۱۰۰٪ توانست تمام ۱۳۶ ماژول استخراج‌شده را لود و ۱۳۶ هندلر SMI را ثبت (Register) کند. با بهره‌گیری از رهگیر حافظه هوشمند و مکانیزم ورودی چندجریانی (Multi-stream)، سیستم توانست خطاهای مثبت کاذب ناشی از پوینترهای مقداردهی‌نشده را به صفر برساند. در ارزیابی فاز سوم، موتور SmuFuzz به طور قطعی آسیب‌پذیری‌های بحرانی CRASH_SMRAM_REDZONE_VIOLATION (دسترسی بدون چک پوینتر) را در ماژول‌های PcdPeim و UsbKbDxe کشف کرد.

در ارزیابی‌های گسترده‌تر بر روی ۳۱ فریمور مختلف، فریمورک SmuFuzz توانست 4.45x برابر Basic Block Coverage بیشتری نسبت به فازرهای مدرن نظیر RSFUZZER به دست آورد[cite: 13]. همچنین، SmuFuzz موفق به کشف ۳۸ آسیب‌پذیری Memory Corruption جدید در فریمورهای توسعه‌یافته توسط Vendorهای بزرگ شد و نرخ خطای کاذب را به ۲۸٪ کاهش داد[cite: 13].

لینک‌های مرتبط (Related Links)
SmuFuzz Source Code (GitHub) - Placeholder

EDK II / OVMF Repository

LibAFL Fuzzing Framework

UEFITool & UEFIExtract

اعضای تیم (Authors)
The authors and implementers of this project are:

@Amir Mohammad Rashidi (شماره دانشجویی: 401105967)

@Mohammad Mahdi Shahadat (شماره دانشجویی: 402109742)
