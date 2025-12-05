import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import base64
import os
import re
from flask import Flask
from threading import Thread
import google.generativeai as genai

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Khởi tạo Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "Bot is alive"}

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# Khởi tạo Gemini AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        # Thử model gemini-pro trước
        model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini AI (gemini-pro) đã được khởi tạo")
    except:
        try:
            # Nếu lỗi, thử gemini-1.0-pro
            model = genai.GenerativeModel('gemini-1.0-pro')
            logger.info("Gemini AI (gemini-1.0-pro) đã được khởi tạo")
        except Exception as e:
            model = None
            logger.error(f"Không thể khởi tạo Gemini: {e}")
else:
    model = None
    logger.warning("Không tìm thấy GEMINI_API_KEY - Tính năng AI sẽ bị tắt")

# Hàm encode code thành base64
def encode_to_base64(code: str) -> str:
    try:
        code_bytes = code.encode('utf-8')
        base64_bytes = base64.b64encode(code_bytes)
        return base64_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Lỗi khi encode: {e}")
        return None

# Hàm decode base64 về code
def decode_from_base64(base64_string: str) -> str:
    try:
        base64_bytes = base64_string.encode('utf-8')
        code_bytes = base64.b64decode(base64_bytes)
        return code_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Lỗi khi decode: {e}")
        return None

# Hàm phân tích code bằng AI
async def ai_analyze_code(code: str) -> str:
    if not model:
        return "❌ Tính năng AI chưa được kích hoạt. Vui lòng liên hệ admin."
    
    try:
        prompt = f"""
Phân tích đoạn code JavaScript/Python sau đây đã bị obfuscate/encode:

{code}

Hãy:
1. Xác định các kỹ thuật obfuscation được sử dụng (hex encoding, base64, string array, dead code injection...)
2. Giải thích logic chính của code
3. Tìm và decode các chuỗi base64 hoặc hex nếu có
4. Nhận diện các hành vi nguy hiểm (cookie stealer, keylogger, malware...)
5. Đưa ra kết luận về mục đích của code

Trả lời bằng tiếng Việt, ngắn gọn và dễ hiểu.
"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Lỗi khi phân tích AI: {e}")
        return f"❌ Đã xảy ra lỗi khi phân tích: {str(e)}"

# Hàm tìm và decode base64 trong code
def find_and_decode_base64(code: str) -> list:
    # Regex để tìm chuỗi base64 (tối thiểu 20 ký tự)
    base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
    matches = re.findall(base64_pattern, code)
    
    results = []
    for match in matches:
        decoded = decode_from_base64(match)
        if decoded and decoded.isprintable():
            results.append({
                'encoded': match[:50] + '...' if len(match) > 50 else match,
                'decoded': decoded[:100] + '...' if len(decoded) > 100 else decoded
            })
    
    return results

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """
🤖 *Chào mừng bạn đến với Code Encoder Bot!*

Bot này giúp bạn mã hóa code thành base64 và phân tích code đã bị obfuscate.

📝 *Các lệnh có sẵn:*
/start - Hiển thị hướng dẫn
/encode - Mã hóa code thành base64
/decode - Giải mã base64 về code gốc
/analyze - Phân tích code obfuscated bằng AI
/findb64 - Tìm và decode base64 trong code
/help - Trợ giúp chi tiết

*Cách sử dụng:*
• Gửi `/encode` kèm code của bạn
• Gửi `/decode` kèm chuỗi base64
• Gửi file (.js, .py, .txt) để phân tích
• Dùng `/analyze` để phân tích code phức tạp
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Command /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 *Hướng dẫn sử dụng chi tiết:*

*1. Mã hóa code:*
/encode <code của bạn>
Ví dụ: `/encode print("Hello World")`

*2. Giải mã base64:*
/decode <chuỗi base64>
Ví dụ: `/decode cHJpbnQoIkhlbGxvIFdvcmxkIik=`

*3. Phân tích code bằng AI:*
/analyze <code đã obfuscate>
Hoặc gửi file trực tiếp (.js, .py, .txt)

*4. Tìm base64 trong code:*
/findb64 <code chứa base64>

*5. Gửi file:*
Chỉ cần gửi file code và bot sẽ tự động phân tích

*Lưu ý:*
• AI có thể phân tích code bị obfuscate phức tạp
• Giới hạn 3000 ký tự cho mỗi lần phân tích
• Hỗ trợ JavaScript, Python và các ngôn ngữ phổ biến
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Command /encode
async def encode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp code cần mã hóa!\n\n"
            "Cách dùng: /encode <code của bạn>"
        )
        return
    
    code = ' '.join(context.args)
    encoded = encode_to_base64(code)
    
    if encoded:
        response = f"""
✅ *Mã hóa thành công!*

📝 *Code gốc:*
`{code}`

🔑 *Chuỗi base64:*
`{encoded}`

💡 *Lưu ý:* Không chia sẻ chuỗi base64 ở nơi công cộng nếu code chứa thông tin nhạy cảm.
"""
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Đã xảy ra lỗi trong quá trình mã hóa.")

# Command /decode
async def decode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp chuỗi base64 cần giải mã!\n\n"
            "Cách dùng: /decode <chuỗi base64>"
        )
        return
    
    base64_string = ' '.join(context.args)
    decoded = decode_from_base64(base64_string)
    
    if decoded:
        response = f"""
✅ *Giải mã thành công!*

🔑 *Chuỗi base64:*
`{base64_string}`

📝 *Code gốc:*
`{decoded}`

💡 *Lưu ý:* Kiểm tra kỹ code trước khi chạy.
"""
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Chuỗi base64 không hợp lệ.")

# Command /analyze - Phân tích code bằng AI
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp code cần phân tích!\n\n"
            "Cách dùng: /analyze <code đã obfuscate>\n"
            "Hoặc gửi file trực tiếp (.js, .py, .txt)"
        )
        return
    
    code = ' '.join(context.args)
    
    await update.message.reply_text("🔍 Đang phân tích code bằng AI... Vui lòng đợi...")
    
    analysis = await ai_analyze_code(code)
    
    # Chia nhỏ phản hồi nếu quá dài
    max_length = 4000
    if len(analysis) > max_length:
        parts = [analysis[i:i+max_length] for i in range(0, len(analysis), max_length)]
        for i, part in enumerate(parts):
            await update.message.reply_text(f"📊 *Phân tích AI (Phần {i+1}/{len(parts)}):*\n\n{part}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"📊 *Phân tích AI:*\n\n{analysis}", parse_mode='Markdown')

# Command /findb64 - Tìm base64 trong code
async def findb64_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp code chứa base64!\n\n"
            "Cách dùng: /findb64 <code của bạn>"
        )
        return
    
    code = ' '.join(context.args)
    results = find_and_decode_base64(code)
    
    if results:
        response = "🔍 *Đã tìm thấy các chuỗi base64:*\n\n"
        for i, result in enumerate(results[:5], 1):  # Giới hạn 5 kết quả
            response += f"*{i}. Encoded:*\n`{result['encoded']}`\n\n"
            response += f"*Decoded:*\n`{result['decoded']}`\n\n"
            response += "---\n\n"
        
        if len(results) > 5:
            response += f"_(Còn {len(results) - 5} kết quả khác...)_"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Không tìm thấy chuỗi base64 nào trong code.")

# Xử lý file upload
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    
    # Chỉ chấp nhận file code
    allowed_extensions = ['.js', '.py', '.txt', '.json', '.html', '.css']
    if not any(document.file_name.endswith(ext) for ext in allowed_extensions):
        await update.message.reply_text(
            "❌ Chỉ hỗ trợ file: .js, .py, .txt, .json, .html, .css"
        )
        return
    
    # Giới hạn kích thước file (1MB)
    if document.file_size > 1024 * 1024:
        await update.message.reply_text("❌ File quá lớn! Giới hạn 1MB.")
        return
    
    await update.message.reply_text("📥 Đang tải file... Vui lòng đợi...")
    
    # Tải file
    file = await context.bot.get_file(document.file_id)
    file_content = await file.download_as_bytearray()
    
    try:
        code = file_content.decode('utf-8')
    except:
        await update.message.reply_text("❌ Không thể đọc file. Đảm bảo file là UTF-8.")
        return
    
    await update.message.reply_text("🔍 Đang phân tích code bằng AI... Vui lòng đợi...")
    
    # Phân tích bằng AI
    analysis = await ai_analyze_code(code)
    
    # Tìm base64
    base64_results = find_and_decode_base64(code)
    
    response = f"📊 *Phân tích file: {document.file_name}*\n\n"
    response += f"📏 Kích thước: {len(code)} ký tự\n\n"
    response += f"🔍 *Phân tích AI:*\n{analysis}\n\n"
    
    if base64_results:
        response += f"\n🔑 *Tìm thấy {len(base64_results)} chuỗi base64*\n"
    
    # Chia nhỏ phản hồi nếu quá dài
    max_length = 4000
    if len(response) > max_length:
        parts = [response[i:i+max_length] for i in range(0, len(response), max_length)]
        for i, part in enumerate(parts):
            await update.message.reply_text(f"*Phần {i+1}/{len(parts)}:*\n\n{part}", parse_mode='Markdown')
    else:
        await update.message.reply_text(response, parse_mode='Markdown')

def main():
    # Lấy token từ biến môi trường
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("Không tìm thấy BOT_TOKEN trong biến môi trường!")
        return
    
    # Chạy Flask server trong thread riêng
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask server đã khởi động")
    
    # Tạo application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Đăng ký các handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("encode", encode_command))
    application.add_handler(CommandHandler("decode", decode_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("findb64", findb64_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Bắt đầu bot
    logger.info("Bot đang khởi động...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()