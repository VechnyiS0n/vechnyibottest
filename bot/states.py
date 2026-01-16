from aiogram.fsm.state import State, StatesGroup

class Flow(StatesGroup):
    waiting_lesson_code = State()
    waiting_mood = State()
    waiting_rating = State()
    waiting_comment = State()
    waiting_question = State()
