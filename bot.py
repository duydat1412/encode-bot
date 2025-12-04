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

📝 *Code gốc:*