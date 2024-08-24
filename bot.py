from aiogram import Dispatcher, Bot, types, executor
from aiogram.dispatcher import filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from main import MintCalendar
import os


scheduler = AsyncIOScheduler()
scheduler.configure(timezones=utc)
bot = Bot(token=os.environ["API_TOKEN"])
dp = Dispatcher(bot=bot)
timezones = {}
mint_calendar = MintCalendar()
collects = []


def get_mints(timezone: int) -> types.InlineKeyboardMarkup:
    mint_calendar.update()
    global collects
    try:
        collects = mint_calendar.get_todays_collects(timezone)
    except KeyError:
        print(timezones)
    keyboard = types.InlineKeyboardMarkup()
    for i in range(len(collects)):
        keyboard.add(types.InlineKeyboardButton(text="⏰" + collects[i]["mintTime"] + ": " + collects[i]["name"], callback_data=str(i)))
    return keyboard


@dp.message_handler(commands=["start"])
async def welcome_message(message: types.Message):
    await message.answer(f"Привет, это mint календарь от ♨️ DAO Бойлерной ♨️\n\nВведите свой часовой пояс относительно UTC, чтобы я мог настроить расписание mint'ов под тебя")

@dp.message_handler(lambda message: message.text.isdigit())
async def add_timezone(message: types.Message):
    timezones[message.chat.id] = int(message.text)
    keyboard = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton("Проверить минты")]], resize_keyboard=True)
    await message.reply("Запомнил", reply_markup=keyboard)

@dp.message_handler(commands=["help"])
async def help_message(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.add("")
    await message.answer("Это mint календарь от ♨️ DAO Бойлерной ♨️\n\nПоявились какие-то вопросы? Пиши сюда:\n - @muhalifmohammed")

@dp.message_handler(filters.Text(equals=["Проверить минты"]))
async def send_mints(message: types.Message, is_new_msg: bool = True):
    keyboard = get_mints(timezones[message.chat.id])
    if is_new_msg:
        await bot.send_message(chat_id=message.chat.id, text="🗓 Расписание минтов на сегодня:", reply_markup=keyboard)
    else:
        await message.edit_text("📆 Расписание минтов на сегодня:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.isdigit())
async def mint_button_clck(call: types.CallbackQuery):
    global collects
    collect = collects[int(call.data)]
    keyboard = types.InlineKeyboardMarkup()
    if collect["discordUrl"]:
        keyboard.add(types.InlineKeyboardButton(text="Discord", url=collect["discordUrl"], callback_data="discord"))
    if collect["twitterUrl"]:
        keyboard.add(types.InlineKeyboardButton(text="Twitter", url=collect["twitterUrl"], callback_data="twitter"))
    keyboard.add(
        types.InlineKeyboardButton(text="⭐️", callback_data="add_to_favorite"),
        types.InlineKeyboardButton(text="Назад", callback_data="back_to_list")
    )
    await call.message.edit_text(
        f"""<b>{collect["name"]}</b>\n"""
        f"""\nwlPrice: {collect["wlPrice"]}"""
        f"""\npubPrice: {collect["pubPrice"]}"""
        f"""\nВремя: {collect["mintTime"]}⏰""",
        parse_mode=types.ParseMode.HTML,
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "back_to_list")
async def back_to_list(call: types.CallbackQuery):
    await send_mints(call.message, False)


def everyday_sender():
    for user_id, timezone in timezones:
        scheduler.add_job(
            bot.send_message(chat_id=user_id, text="🗓 Расписание минтов на сегодня:", reply_markup=get_mints(timezone)),
            trigger="time",

        )
        


if __name__ == "__main__":
    executor.start_polling(dp)