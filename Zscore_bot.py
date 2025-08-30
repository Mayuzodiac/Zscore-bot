import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
import asyncio

# Environment variable එකෙන් token එක ගන්න
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8015111651:AAFdho0ace7htI8HUN0aXN8IALUv8FyzQ2o')
PRIVATE_CHANNEL_ID = -1002681348717  # ඔබගේ private channel ID එක මෙතනට දාන්න

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
MARKS_PHYSICS, MARKS_CHEMISTRY, MARKS_MATHS = range(3)

# Z-score data (2023 දත්ත අයින් කරන ලදී)
z_score_data = {
    '2017': {'physics': {'mu': 42.38, 'sigma': 15.68}, 'chemistry': {'mu': 44.10, 'sigma': 17.28}, 'maths': {'mu': 43.18, 'sigma': 23.94}},
    '2018': {'physics': {'mu': 44.05, 'sigma': 15.44}, 'chemistry': {'mu': 44.61, 'sigma': 18.53}, 'maths': {'mu': 41.04, 'sigma': 22.33}},
    '2019': {'physics': {'mu': 39.88, 'sigma': 18.90}, 'chemistry': {'mu': 41.72, 'sigma': 21.35}, 'maths': {'mu': 40.63, 'sigma': 22.71}},
    '2020': {'physics': {'mu': 41.15, 'sigma': 18.30}, 'chemistry': {'mu': 44.73, 'sigma': 20.00}, 'maths': {'mu': 40.78, 'sigma': 22.50}},
    '2021': {'physics': {'mu': 43.52, 'sigma': 20.63}, 'chemistry': {'mu': 46.82, 'sigma': 20.96}, 'maths': {'mu': 47.86, 'sigma': 19.03}},
    # 2023 දත්ත අයින් කරන ලදී
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a welcome message and prompts for the first mark."""
    await update.message.reply_text(
        "Hello! I'm the Z-Score Calculator bot. Let's find your estimated Z-score. "
        "Please enter your **Physics** mark."
    )
    return MARKS_PHYSICS

async def get_physics_mark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes the Physics mark and asks for the Chemistry mark."""
    try:
        physics_mark = float(update.message.text)
        if not 0 <= physics_mark <= 100:
            await update.message.reply_text("That's not a valid mark. Please enter a number between 0 and 100.")
            return MARKS_PHYSICS
        
        context.user_data['physics'] = physics_mark
        
        # Forward the user's message to the private channel
        await context.bot.forward_message(
            chat_id=PRIVATE_CHANNEL_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        
        await update.message.reply_text("Great! Now, please enter your **Chemistry** mark.")
        return MARKS_CHEMISTRY
    except (ValueError, TypeError):
        await update.message.reply_text("Please enter a valid number for your Physics mark.")
        return MARKS_PHYSICS

async def get_chemistry_mark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes the Chemistry mark and asks for the Maths mark."""
    try:
        chemistry_mark = float(update.message.text)
        if not 0 <= chemistry_mark <= 100:
            await update.message.reply_text("That's not a valid mark. Please enter a number between 0 and 100.")
            return MARKS_CHEMISTRY
            
        context.user_data['chemistry'] = chemistry_mark
        
        await context.bot.forward_message(
            chat_id=PRIVATE_CHANNEL_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        
        await update.message.reply_text("Awesome! Finally, please enter your **Combined Mathematics** mark.")
        return MARKS_MATHS
    except (ValueError, TypeError):
        await update.message.reply_text("Please enter a valid number for your Chemistry mark.")
        return MARKS_CHEMISTRY

async def calculate_z_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes the Maths mark, calculates the final Z-score, and sends the result."""
    try:
        maths_mark = float(update.message.text)
        if not 0 <= maths_mark <= 100:
            await update.message.reply_text("That's not a valid mark. Please enter a number between 0 and 100.")
            return MARKS_MATHS

        context.user_data['maths'] = maths_mark

        await context.bot.forward_message(
            chat_id=PRIVATE_CHANNEL_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )

        total_z_score_sum = 0
        number_of_years = len(z_score_data)

        for year, data in z_score_data.items():
            physics_z = (context.user_data['physics'] - data['physics']['mu']) / data['physics']['sigma']
            chemistry_z = (context.user_data['chemistry'] - data['chemistry']['mu']) / data['chemistry']['sigma']
            maths_z = (context.user_data['maths'] - data['maths']['mu']) / data['maths']['sigma']
            
            average_z_for_year = (physics_z + chemistry_z + maths_z) / 3
            total_z_score_sum += average_z_for_year

        final_z_score = total_z_score_sum / number_of_years

        message = (
            f"Based on your marks:\n"
            f"Physics: **{context.user_data['physics']}**\n"
            f"Chemistry: **{context.user_data['chemistry']}**\n"
            f"Combined Mathematics: **{context.user_data['maths']}**\n\n"
            f"Your estimated average Z-score is: **{final_z_score:.4f}**\n\n"
            f"This is just an estimate. The actual Z-score can vary. "
            f"To start a new calculation, just type **/start** again!"
        )
        await update.message.reply_text(message, parse_mode='Markdown')

        return ConversationHandler.END

    except (ValueError, TypeError):
        await update.message.reply_text("Please enter a valid number for your Combined Mathematics mark.")
        return MARKS_MATHS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text('Calculation canceled. Feel free to start again with /start.')
    return ConversationHandler.END

def main() -> None:
    """Starts the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MARKS_PHYSICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_physics_mark)],
            MARKS_CHEMISTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chemistry_mark)],
            MARKS_MATHS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_z_score)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    logger.info("Bot starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
