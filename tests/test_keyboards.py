from aiogram.types import InlineKeyboardMarkup

import keyboards


def _assert_valid_callbacks(markup: InlineKeyboardMarkup):
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data is not None:
                assert len(button.callback_data.encode("utf-8")) <= 64


def test_all_static_keyboards_have_valid_callback_sizes():
    markups = [
        keyboards.get_main_menu(1, []),
        keyboards.get_roles_inline_keyboard(),
        keyboards.get_back_to_roles_inline(),
        keyboards.get_admin_manage_inline(),
        keyboards.get_admins_delete_inline([]),
        keyboards.get_back_inline(),
        keyboards.get_admin_region_keyboard(),
        keyboards.get_admin_country_keyboard(),
    ]
    for markup in markups:
        _assert_valid_callbacks(markup)
