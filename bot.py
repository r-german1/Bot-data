import sqlite3
import os
import urllib.request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# توکنا بۆتی و خودانێ سەرەکی
TOKEN = "8759983367:AAHm1mNaJEbdDhKEZdtm3YmnF2CwAPmh8EE"
OWNER = "YUSEEF_SURCHI"

# لینکێن ڕاستەوخۆ یێن فایلێن داتابەیسێ ژ گیتهەب Releases
DB_URLS = {
    "duhok": "https://github.com/r-german1/Bot-data/releases/download/v1.0.0/duhok.db",
    "erbil": "https://github.com/r-german1/Bot-data/releases/download/v1.0.0/erbil.db",
    "kirkuk": "https://github.com/r-german1/Bot-data/releases/download/v1.0.0/kirkuk.db",
    "sulaymaniyah": "https://github.com/r-german1/Bot-data/releases/download/v1.0.0/sulaymaniyah.db"
}

# دابەزاندنا فایلا داتابەیسێ ئەگەر ل سەر سێرڤەری نەبێت
def ensure_database(city):
    db_file = f"{city}.db"
    if not os.path.exists(db_file):
        print(f"📥 دابەزاندنا فایلا {db_file} ژ گیتهەب...")
        try:
            urllib.request.urlretrieve(DB_URLS[city], db_file)
            print(f"✅ فایلا {db_file} ب سەرکەفتیانە هاتە دابەزاندن!")
        except Exception as e:
            print(f"❌ هەلە د دابەزاندنا {db_file} دا: {e}")

# پەیاما /start و پێشوازیکرن
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"سلاڤ {user.first_name} ب خێر هاتێ بۆتێ! 👋\n\n👑 خودانێ بۆتی: @{OWNER}\n\nئەڤ بۆته بۆ گەرانا زانیاریێن کەسایەتی یە. ژ فەرمانا خوارێ یەکێک هەلبژێره:"
    
    keyboard = [
        [InlineKeyboardButton("🔍 گەران (Search)", callback_data="search_menu")],
        [InlineKeyboardButton("👤 پرۆفایلا من (Profile)", callback_data="my_profile"),
         InlineKeyboardButton("🛠️ خودانێن بۆتی (Owners)", callback_data="show_owners")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup)

# بوونێن کوپلان (Inline Buttons)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "show_owners":
        owners_text = f"👑 خودانێ ڤی بۆتی:\n▪️ @{OWNER}"
        keyboard = [[InlineKeyboardButton("🔙 ڤەگەر (Back)", callback_data="back_home")]]
        await query.message.edit_text(owners_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data == "my_profile":
        user = query.from_user
        username = f"@{user.username}" if user.username else "نەدیارە"
        profile_text = f"👤 پرۆفایلا تە:\n\n🆔 ئایدی: `{user.id}`\n🔗 یۆسەرنێم: {username}\n\n👑 خودانێ بۆتی: @{OWNER}"
        keyboard = [[InlineKeyboardButton("🔙 ڤەگەر (Back)", callback_data="back_home")]]
        await query.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data == "search_menu":
        search_text = "🔍 باژێرێ مەبەست بۆ گەرانێ هەلبژێره:"
        keyboard = [
            [InlineKeyboardButton("دهۆک (Duhok)", callback_data="city_duhok"),
             InlineKeyboardButton("هەولێر (Erbil)", callback_data="city_erbil")],
            [InlineKeyboardButton("کەرکوک (Kirkuk)", callback_data="city_kirkuk"),
             InlineKeyboardButton("سلێمانی (Sulaymaniyah)", callback_data="city_sulaymaniyah")],
            [InlineKeyboardButton("🔙 ڤەگەر (Back)", callback_data="back_home")]
        ]
        await query.message.edit_text(search_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data == "back_home":
        await start(update, context)
        
    elif data.startswith("city_"):
        city = data.split("_")[1]
        context.user_data['selected_city'] = city
        
        await query.message.reply_text(f"⏳ ل چاڤەڕێ بان، پشکنین و ئامادەکرنا داتابەیسا {city.upper()}...")
        ensure_database(city)
        
        await query.message.reply_text(f"✅ تە باژێرێ {city.upper()} هەلبژارد و داتابەیس ئامادەیە.\n\nنۆکە ناڤێ کەسی (یان پشکەک ژ ناڤی) بنڤیسە بۆ گەرانێ:")

# پشکا گەرانێ ل ناو داتابەیسێ
async def search_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'selected_city' not in context.user_data:
        await update.message.reply_text("⚠️ تکایە پاش پێشوازیکردنێ، ژ پشکا گەرانێ باژێری پێشوەخت هەلبژێره!")
        return
    
    city = context.user_data['selected_city']
    search_query = update.message.text.strip()
    db_file = f"{city}.db"
    
    ensure_database(city)
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(data);")
        columns_info = cursor.fetchall()
        
        if not columns_info:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            target_table = table_name
        else:
            target_table = "data"
            
        columns = [col[1] for col in columns_info]
        search_column = columns[0] if columns else "full_name"
        
        cursor.execute(f"SELECT * FROM {target_table} WHERE {search_column} LIKE ? LIMIT 5", ('%' + search_query + '%',))
        results = cursor.fetchall()
        conn.close()
        
        if results:
            response = f"🔍 ئەنجامێن گەرانێ ل باژێرێ {city.upper()} (خودان: @{OWNER}):\n\n"
            for row in results:
                response += f"▪️ زانیاری: {row}\n-------------------\n"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("❌ چ ئەنجام نەهاتن دیتن ل سەر ڤی ناڤی.")
            
    except Exception as e:
        await update.message.reply_text(f"⚠️ هەلە د خواندنا داتابەیسێ دا: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_database))
    
    print(f"Bot is running successfully by owner @{OWNER}...")
    app.run_polling()

if __name__ == '__main__':
    main()
