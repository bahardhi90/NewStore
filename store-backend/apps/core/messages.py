"""All user-facing Persian messages in one place."""

VALIDATION_ERROR = "اطلاعات ارسالی معتبر نیست."
NOT_AUTHENTICATED = "لطفاً وارد حساب کاربری شوید."
PERMISSION_DENIED = "شما اجازه انجام این کار را ندارید."
NOT_FOUND = "یافت نشد."
METHOD_NOT_ALLOWED = "این متد مجاز نیست."
PARSE_ERROR = "درخواست ارسالی قابل خواندن نیست."
UNSUPPORTED_MEDIA = "نوع محتوای درخواست پشتیبانی نمی‌شود."
THROTTLED = "تعداد درخواست‌ها زیاد است. {seconds} ثانیه دیگر تلاش کنید."
SERVER_ERROR = "خطای داخلی سرور. لطفاً بعداً تلاش کنید."

PHONE_INVALID = "شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد."
POSTAL_CODE_INVALID = "کد پستی باید ۱۰ رقم باشد."

OTP_SENT = "کد تأیید ارسال شد."
OTP_INVALID = "کد تأیید اشتباه است."
OTP_EXPIRED = "کد تأیید منقضی شده است. دوباره درخواست کنید."
OTP_MAX_ATTEMPTS = "تعداد تلاش‌های ناموفق زیاد است. کد جدید درخواست کنید."
OTP_RESEND_WAIT = "برای دریافت کد جدید {seconds} ثانیه صبر کنید."
OTP_TOO_MANY = "تعداد درخواست کد بیش از حد مجاز است. بعداً تلاش کنید."
USER_INACTIVE = "حساب کاربری شما غیرفعال است."

ADDRESS_LIMIT = "حداکثر {count} آدرس می‌توانید ثبت کنید."
ADDRESS_NOT_FOUND = "آدرس انتخاب‌شده یافت نشد."

VARIANT_NOT_FOUND = "این محصول یافت نشد یا دیگر فروخته نمی‌شود."
OUT_OF_STOCK = "موجودی کافی نیست."
ONLY_N_IN_STOCK = "از این مدل فقط {count} عدد موجود است."
SOLD_OUT = "این مدل ناموجود است."
PRODUCT_UNAVAILABLE = "این محصول دیگر موجود نیست."
MAX_QUANTITY = "حداکثر {count} عدد از هر مدل قابل سفارش است."
MERGE_SKIPPED = "«{title}» به سبد اضافه نشد: {reason}"
MERGE_REDUCED = "تعداد «{title}» به {count} عدد کاهش یافت (موجودی محدود)."

CART_EMPTY = "سبد خرید شما خالی است."
SHIPPING_NOT_FOUND = "روش ارسال انتخاب‌شده معتبر نیست."
ITEM_OUT_OF_STOCK = "«{title}» ({size}، {color}): {reason}"
ORDER_NOT_PAYABLE = "این سفارش قابل پرداخت نیست."

GATEWAY_ERROR = "ارتباط با درگاه پرداخت برقرار نشد. لطفاً دوباره تلاش کنید."
PAYMENT_SUCCESS = "پرداخت با موفقیت انجام شد."
PAYMENT_FAILED = "پرداخت ناموفق بود. در صورت کسر وجه، مبلغ تا ۷۲ ساعت به حساب شما بازمی‌گردد."
PAYMENT_CANCELLED = "پرداخت لغو شد."
PAYMENT_AMOUNT_MISMATCH = "مبلغ پرداخت با مبلغ سفارش مطابقت ندارد."
PAYMENT_ORDER_EXPIRED = "پرداخت انجام شد اما مهلت سفارش تمام شده بود. مبلغ به حساب شما بازگردانده می‌شود."
PAYMENT_METHOD_UNAVAILABLE = "این روش پرداخت برای سفارش شما در دسترس نیست."

ORDER_STATUS_LABELS = {
    "pending": "در انتظار پرداخت",
    "paid": "پرداخت‌شده",
    "processing": "در حال پردازش",
    "shipped": "ارسال‌شده",
    "delivered": "تحویل‌شده",
    "cancelled": "لغوشده",
    "refunded": "مسترد شده",
}
