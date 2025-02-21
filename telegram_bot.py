import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import technical_analysis

# 📌 راه‌اندازی ربات
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

# 📌 کیبورد اصلی
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.row(KeyboardButton("📊 تحلیل تکنیکال"), KeyboardButton("📈 تحلیل فاندامنتال (به زودی)"))
main_keyboard.row(KeyboardButton("📞 پشتیبانی"))

# 📌 کیبورد تایم‌فریم
timeframe_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
timeframe_keyboard.row(KeyboardButton("1h"), KeyboardButton("4h"), KeyboardButton("1d"))
timeframe_keyboard.row(KeyboardButton("🔙 بازگشت"))

# 📌 استارت ربات
@bot.message_handler(commands=['start'])
def start(message):
    first_name = message.from_user.first_name  # دریافت نام کاربر
    welcome_text = f"👋 سلام {first_name} عزیز!\n\n"
    welcome_text += "به ربات تحلیل تکنیکال و فاندامنتال خوش آمدید! 🎯\n\n"
    welcome_text += "🔹 برای استفاده از ربات، لطفاً ابتدا در کانال‌های ما عضو شوید: 👇"

    # لینک‌های کانال تلگرام و یوتیوب
    telegram_channel_link = "https://t.me/AFSalehi"
    youtube_channel_link = "https://youtube.com/@politikarrr?si=L8qVFFtfoYBU50NX"

    # ساخت دکمه‌ها
    markup = InlineKeyboardMarkup()
    btn_telegram = InlineKeyboardButton("📢 کانال تلگرام", url=telegram_channel_link)
    btn_youtube = InlineKeyboardButton("🎥 کانال یوتیوب", url=youtube_channel_link)
    btn_confirm = InlineKeyboardButton("✅ تایید عضویت", callback_data="confirm_subscription")

    # اضافه کردن دکمه‌ها
    markup.add(btn_telegram, btn_youtube)
    markup.add(btn_confirm)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# 📌 مدیریت دکمه "✅ تایید عضویت"
@bot.callback_query_handler(func=lambda call: call.data == "confirm_subscription")
def confirm_subscription(call):
    first_name = call.from_user.first_name
    response_text = f"🎉 {first_name} عزیز، عضویت شما تأیید شد!\n\n"
    response_text += "🚀 این ربات ساخته شده در **افغانستان** است و برای پیشرفت به حمایت شما نیاز دارد.\n"
    response_text += "📊 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"

    # دکمه‌های مرحله بعد
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📊 تحلیل تکنیکال", callback_data="technical_analysis"))
    markup.add(InlineKeyboardButton("📢 تحلیل فاندامنتال (به زودی)", callback_data="fundamental_analysis"))
    markup.add(InlineKeyboardButton("📞 پشتیبانی", callback_data="support"))

    bot.edit_message_text(response_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# 📌 مدیریت دکمه "📊 تحلیل تکنیکال"
@bot.callback_query_handler(func=lambda call: call.data == "technical_analysis")
def request_timeframe(call):
    bot.send_message(call.message.chat.id, "⏳ لطفاً تایم فریم مورد نظر خود را انتخاب کنید:", reply_markup=timeframe_keyboard)
    bot.register_next_step_handler(call.message, request_pair)

# 📌 دریافت جفت‌ارز بعد از تایم‌فریم
def request_pair(message):
    if message.text == "🔙 بازگشت":
        bot.send_message(message.chat.id, "🔙 بازگشت به منوی اصلی", reply_markup=main_keyboard)
        return
    
    timeframe = message.text
    bot.send_message(message.chat.id, "🔎 لطفاً جفت‌ارز مورد نظر خود را وارد کنید (مثلاً: BTC/USDT):")
    bot.register_next_step_handler(message, process_analysis, timeframe)

# 📌 پردازش تحلیل تکنیکال
def process_analysis(message, timeframe):
    pair = message.text.upper()

    try:
        df = technical_analysis.fetch_market_data(pair, timeframe)
        if isinstance(df, str):
            bot.send_message(message.chat.id, f"❌ خطا در دریافت داده‌ها: {df}")
            return

        price = df['close'].iloc[-1]
        supports, resistances = technical_analysis.find_support_resistance(df, price)
        trend_analysis = technical_analysis.determine_trend(df)

        scenario = ""
        if len(supports) >= 2 and len(resistances) >= 2:
            scenario = (f"📊 **سناریو احتمالی:**\n"
                        f"اگر مقاومت اول ({resistances[0]:.2f}) شکسته شود، قیمت احتمالاً به مقاومت دوم ({resistances[1]:.2f}) خواهد رسید.\n"
                        f"اگر حمایت اول ({supports[0]:.2f}) شکسته شود، قیمت احتمالاً به حمایت دوم ({supports[1]:.2f}) سقوط خواهد کرد.")

        price_display = f"${price:.2f}"
        support_display = "\n".join([f"🟢 حمایت {i+1}: ${supports[i]:.2f}" for i in range(len(supports))])
        resistance_display = "\n".join([f"🔴 مقاومت {i+1}: ${resistances[i]:.2f}" for i in range(len(resistances))])

        chart_path = technical_analysis.plot_advanced_chart(pair, df, supports, resistances)

        caption = (f"🌊 **چارت {pair} ({timeframe})**\n"
                   f"💰 **قیمت فعلی:** {price_display}\n"
                   f"{trend_analysis}\n"
                   f"{support_display}\n"
                   f"{resistance_display}\n"
                   f"{scenario}")

        with open(chart_path, "rb") as chart:
            bot.send_photo(message.chat.id, chart, caption=caption, parse_mode="Markdown")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

# 📌 مدیریت دکمه "📞 پشتیبانی"
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_info(call):
    bot.send_message(call.message.chat.id, "📩 برای پشتیبانی می‌توانید از راه‌های زیر اقدام کنید:\n"
                                           "📌 تلگرام: @hasibmuradi\n"
                                           "📧 ایمیل: hasib.muradih01@gmail.com")

# 📌 اجرای ربات
print("✅ Bot is running...")
bot.polling()
