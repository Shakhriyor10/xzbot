from handlers.user_handlers import parse_group_link


def test_parse_public_group_link_accepts_username_and_urls():
    expected = ("@mygroup", "https://t.me/mygroup")

    assert parse_group_link("@mygroup") == expected
    assert parse_group_link("https://t.me/mygroup/") == expected
    assert parse_group_link("http://t.me/mygroup") == expected
    assert parse_group_link("t.me/mygroup/?start=1") == expected
    assert parse_group_link("www.t.me/mygroup/") == expected


def test_parse_group_link_accepts_private_invite_link():
    assert parse_group_link("https://t.me/+gJEe78RRo_xmNDE6") == (
        None,
        "https://t.me/+gJEe78RRo_xmNDE6",
    )


def test_parse_public_group_link_rejects_invalid_or_private_links():
    assert parse_group_link("not a link") is None
    assert parse_group_link("https://example.com/mygroup") is None
    assert parse_group_link("https://t.me/+") is None
