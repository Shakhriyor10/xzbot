from aiogram.fsm.state import State, StatesGroup


class SpamReportState(StatesGroup):
    waiting_for_proof = State()

class AddAdminState(StatesGroup):
    waiting_for_input = State()

class AddAccountState(StatesGroup):
    waiting_for_api_id = State()
    waiting_for_api_hash = State()
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_2fa = State()
    waiting_for_forward = State()

