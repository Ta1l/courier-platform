"""
states/application.py — FSM States for the application test flow.
Defines the sequential steps the user goes through when submitting an application.
"""

from aiogram.fsm.state import State, StatesGroup


class ApplicationForm(StatesGroup):
    """
    Finite State Machine states for the courier application process.

    Flow:
        1. waiting_for_phone  — User sends their phone contact
        2. waiting_for_name   — User enters their name
        3. waiting_for_age    — User enters their age
        4. waiting_for_citizenship — User selects citizenship from inline buttons
    """

    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_citizenship = State()
