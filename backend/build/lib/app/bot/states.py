from aiogram.fsm.state import State, StatesGroup


class AuthStates(StatesGroup):
    waiting_invite_code = State()


class ReportStates(StatesGroup):
    choosing_mode = State()
    choosing_category = State()
    waiting_text = State()
    waiting_attachments = State()
    waiting_confirmation = State()
