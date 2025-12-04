import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import base64
import os
from flask import Flask
from threading import Thread
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

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ALLOWED_USER_ID = 5266362838  # Thay bằng ChatID của bạn
    if update.message.from_user.id != ALLOWED_USER_ID:
        return
    
    welcome_message = """
🤖 *Chào mừng bạn đến với Code Encoder Bot!*

Bot này giúp bạn mã hóa code thành base64 để bảo vệ source code.

📝 *Các lệnh có sẵn:*
/start - Hiển thị hướng dẫn
/encode - Mã hóa code thành base64
/decode - Giải mã base64 về code gốc
/help - Trợ giúp

*Cách sử dụng:*
• Gửi `/encode` kèm code của bạn
• Gửi `/decode` kèm chuỗi base64
• Hoặc chỉ cần gửi code/base64 trực tiếp
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Command /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 *Hướng dẫn sử dụng:*

*1. Mã hóa code:*
/encode <code của bạn>

Ví dụ:
`/encode print("Hello World")`

*2. Giải mã base64:*
/decode <chuỗi base64>

Ví dụ:
`/decode cHJpbnQoIkhlbGxvIFdvcmxkIik=`

*3. Gửi trực tiếp:*
Bạn cũng có thể gửi code hoặc base64 trực tiếp mà không cần lệnh.
Bot sẽ tự động phát hiện và xử lý.
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

📝 *Code gốc:* `{code}`

🔑 *Chuỗi base64:* `{encoded}`


*Lưu ý: *

• File sẽ tự động xóa sau 1 giờ.
• Không chia sẻ chuỗi base64 ở nơi công cộng nếu code chứa thông tin nhạy cảm.
"""
        await update.message.reply_text(response, parse_mode='Markdown')
        
        # Ghi chuỗi base64 vào file
        try:
            with open('/tmp/encoded_file.b64', 'w') as f:
                f.write(encoded)
        except Exception as e:
            logger.error(f"Lỗi khi ghi file: {e}")
            await update.message.reply_text("❌ Lỗi khi tạo file tải xuống.")
    else:
        await update.message.reply_text("❌ Đã xảy ra lỗi trong quá trình mã hóa. Vui lòng thử lại sau.")

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

🔑 *Chuỗi base64:* `{base64_string}`

📝 *Code gốc:* `{decoded}`

*Lưu ý: *

• File sẽ tự động xóa sau 1 giờ.
• Kiểm tra kỹ code trước khi chạy, đặc biệt là thông tin nhạy cảm.
"""
        await update.message.reply_text(response, parse_mode='Markdown')
        
        # Ghi code gốc vào file
        try:
            with open('/tmp/decoded_file.py', 'w') as f:
                f.write(decoded)
        except Exception as e:
            logger.error(f"Lỗi khi ghi file: {e}")
            await update.message.reply_text("❌ Lỗi khi tạo file tải xuống.")
    else:
        await update.message.reply_text("❌ Đã xảy ra lỗi trong quá trình giải mã. Vui lòng thử lại sau.")

# Xử lý tin nhắn văn bản
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Bỏ qua tin nhắn rỗng
    if not text:
        return
    
    # Kiểm tra và xử lý mã hóa
    if text.startswith('/encode '):
        context.args = text[len('/encode '):].split()
        await encode_command(update, context)
    # Kiểm tra và xử lý giải mã
    elif text.startswith('/decode '):
        context.args = text[len('/decode '):].split()
        await decode_command(update, context)
    # Gửi hướng dẫn sử dụng nếu không nhận diện được lệnh
    else:
        await start(update, context)

# Xử lý tin nhắn text (tự động phát hiện)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Kiểm tra xem có phải base64 không
    if all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in text.strip()):
        decoded = decode_from_base64(text)
        if decoded:
            response = f"""
🔍 *Phát hiện base64 - Đã giải mã!*

🔐 *Base64:* `{text}`

📝 *Code gốc:* `{decoded}`

*Lưu ý: *

• File sẽ tự động xóa sau 1 giờ.
• Kiểm tra kỹ code trước khi chạy, đặc biệt là thông tin nhạy cảm.
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            
            # Ghi code gốc vào file
            try:
                with open('/tmp/decoded_file.py', 'w') as f:
                    f.write(decoded)
            except Exception as e:
                logger.error(f"Lỗi khi ghi file: {e}")
                await update.message.reply_text("❌ Lỗi khi tạo file tải xuống.")
        else:
            await update.message.reply_text("❌ Đã xảy ra lỗi trong quá trình giải mã. Vui lòng thử lại sau.")
    # Nếu không phải base64, kiểm tra và xử lý như tin nhắn văn bản bình thường
    else:
        await handle_text(update, context)

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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Bắt đầu bot
    logger.info("Bot đang khởi động...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()