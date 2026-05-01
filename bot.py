import asyncio
import random
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    PollAnswerHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

# ====== CONFIG ======
TOKEN = os.getenv("TOKEN")
CHAT_ID = "@botlootzone"

QUIZ_INTERVAL = 60
QUIZ_DURATION = 2400

# ====== DATA ======
scores = {}
correct_answers = {}

# ====== QUESTIONS ======
raw_quizzes = [
    {
        "q": "ভারতের জাতীয় পাখি কোনটি?",
        "o": ["ময়ূর", "কাক", "টিয়া", "হাঁস"],
        "correct": 0
    },
    {
        "q": "ভারতের রাজধানী কোথায়?",
        "o": ["মুম্বাই", "কলকাতা", "নয়াদিল্লি", "চেন্নাই"],
        "correct": 2
    }
]

quizzes = [
    {
        "question": q["q"],
        "options": q["o"],
        "correct": q["correct"]
    }
    for q in raw_quizzes
]

# ====== SEND QUIZ ======
async def send_quiz(app):
    start_time = asyncio.get_event_loop().time()

    await app.bot.send_message(chat_id=CHAT_ID, text="🔥 Daily MCQ Started!")

    while True:
        if asyncio.get_event_loop().time() - start_time > QUIZ_DURATION:
            break

        quiz = random.choice(quizzes)

        try:
            msg = await app.bot.send_poll(
                chat_id=CHAT_ID,
                question=quiz["question"],
                options=quiz["options"],
                type="quiz",
                correct_option_id=quiz["correct"],
                is_anonymous=True
            )

            correct_answers[msg.poll.id] = quiz["correct"]

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(QUIZ_INTERVAL)

# ====== HANDLE ANSWERS ======
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = update.poll_answer
    user_id = ans.user.id

    if not ans.option_ids:
        return

    selected = ans.option_ids[0]
    poll_id = ans.poll_id

    if poll_id in correct_answers:
        if selected == correct_answers[poll_id]:
            scores[user_id] = scores.get(user_id, 0) + 1

# ====== LEADERBOARD ======
async def show_leaderboard(app):
    if not scores:
        await app.bot.send_message(chat_id=CHAT_ID, text="No participants 😅")
        return

    text = "🏆 FINAL LEADERBOARD 🏆\n\n"

    sorted_users = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    for i, (user, score) in enumerate(sorted_users, start=1):
        text += f"{i}. User {user} — {score} pts\n"

    await app.bot.send_message(chat_id=CHAT_ID, text=text)

# ====== DAILY SCHEDULER ======
async def scheduler(app):
    while True:
        await asyncio.sleep(86400)

        scores.clear()
        correct_answers.clear()

        await send_quiz(app)
        await show_leaderboard(app)

# ====== MAIN ======
async def main():
    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60
    )

    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(PollAnswerHandler(handle_answer))

    await app.initialize()
    await app.start()

    print("Bot is running...")
