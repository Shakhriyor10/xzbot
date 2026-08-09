from aiogram.fsm.state import State, StatesGroup

class SpamReportState(StatesGroup):
    waiting_for_proof = State()

class AddAdminState(StatesGroup):
    waiting_for_input = State()

class AddAccountState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_session = State()

