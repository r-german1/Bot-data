import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# توكنا بۆتی و خودانێ سەرەکی
TOKEN = "BOT_TOKEN_HERE"
OWNER = "YUSEEF_SURCHI"

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
        
        # دیارکرنا ناڤێ فایلا داتابەیسێ بەپێی باژێری
        db_files = {
            "duhok": "duhok.db",
            "erbil": "erbil.db",
            "kirkuk": "kirkuk.db",
            "sulaymaniyah": "sulaymaniyah.db"
        }
        
        await query.message.reply_text(f"✅ تە باژێرێ {city.upper()} هەلبژارد.\n📂 فایلا داتابەیسێ: `{db_files[city]}`\n\nنۆکە ناڤێ کەسی (یان پشکەک ژ ناڤی) بنڤیسە بۆ گەرانێ:")

# پشکا گەرانێ ل ناو داتابەیسێ
async def search_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'selected_city' not in context.user_data:
        await update.message.reply_text("⚠️ تکایە پاش پێشوازیکردنێ، ژ پشکا گەرانێ باژێری پێشوەخت هەلبژێره!")
        return
    
    city = context.user_data['selected_city']
    search_query = update.message.text.strip()
    
    # فایلا داتابەیسێ ya دەستنیشانکری
    db_file = f"{city}.db"
    
    if not os.path.exists(db_file):
        await update.message.reply_text(f"❌ فایلا داتابەیسێ `{db_file}` ل ڤی پوشتەی نینە! تکایە ڤرەکە ناو هەمەن فۆڵدەر.")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # سەرنج: ئەگەر ناڤێ ستوونێن داتابەیسا تە جودا بن، دەستکارییا ڤی قەبارەی بکە
        # ل ڤێرە مە گەران کریە ل سەر ناڤی، ناڤێ بابێ، سالا ژدایکبوونێ و هتد
        query = "SELECT * FROM data WHERE full_name LIKE ? OR name LIKE ?"
        
        # لێرە مەیڵە ئەگەر ستوونا تە تنێ `name` یان `full_name` بێت، گۆڕانکاری تێدا بکە
        # بۆ تاقیکرنێ مەیڵە گەرانەکا گشتی ل سەر ستوونێن سەرەکی بکە:
        cursor.execute("PRAGMA table_info(data);")
        columns = [col[1] for col in cursor.fetchall()]
        
        # گەران ب رێکا LIKE ل سەر تابلۆیا سەرەکی
        cursor.execute(f"SELECT * FROM data WHERE {columns[0]} LIKE ? LIMIT 5", ('%' + search_query + '%',))
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
        # ئەگەر ناڤێ تابلۆی یان ستوونان جودا بیت، دێ ڤی هەڵەی ڤەشێرێت یان نیشان دەت
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            # فەرمانا گەرانا گشتی بێ دیارکرنا ناڤێ ستوونی
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()[0]
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample = cursor.fetchall()
            conn.close()
            await update.message.reply_text(f"⚠️ ئەگەرەک هەبوو. ناڤێ تابلۆیا داتابەیسا تە: `{table_name}`\nنموونەیا داتایێ: {sample}")
        except Exception as err:
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
