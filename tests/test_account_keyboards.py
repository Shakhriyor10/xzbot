from handlers.account_handlers import (
    account_actions_keyboard,
    account_menu_keyboard,
    group_actions_keyboard,
    text_menu_keyboard,
)


def _callbacks(markup):
    return [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data
    ]


def test_account_callbacks_are_namespaced_and_within_telegram_limit(monkeypatch):
    monkeypatch.setattr(
        "handlers.account_handlers.get_connected_accounts",
        lambda _owner: [(123, "account", "Account", "session")],
    )
    markups = [
        account_menu_keyboard(1),
        account_actions_keyboard(123),
        text_menu_keyboard(123),
        group_actions_keyboard(123, 456),
    ]
    for markup in markups:
        for callback in _callbacks(markup):
            assert len(callback.encode()) <= 64
            assert callback.startswith("acc:") or callback == "main_menu"
