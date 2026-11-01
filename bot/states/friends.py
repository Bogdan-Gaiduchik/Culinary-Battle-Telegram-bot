from aiogram.fsm.state import State, StatesGroup


class FriendBattleStates(StatesGroup):
    entering_dish_a = State()
    entering_dish_b = State()
