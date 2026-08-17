from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import OWNER_ID, OWNER_IDS

BTN_USER_1 = "𝗥𝗲𝗸𝗹𝗮𝗺𝗮"
BTN_USER_2 = "𝗠𝗮𝗳𝗶𝗮 𝗥𝗼𝗹𝗹𝗮𝗿𝗶"
BTN_USER_3 = "𝗦𝗵𝗶𝗸𝗼𝘆𝗮𝘁"

BTN_ADMIN_4 = "𝗥𝗲𝗸𝗹𝗮𝗺𝗮 𝗚𝘂𝗿𝘂𝗵𝗹𝗮𝗿𝗶"
BTN_ADMIN_5 = "𝗕𝘂𝗴𝘂𝗻𝗴𝗶 𝗥𝗲𝗸𝗹𝗮𝗺𝗮𝗹𝗮𝗿"
BTN_ADMIN_6 = "𝗥𝗲𝗸𝗹𝗮𝗺𝗮 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗸𝗮𝘀𝗶"
BTN_ADMIN_7 = "📱 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗥𝗲𝗸𝗹𝗮𝗺𝗮𝘀𝗶"
BTN_ADMIN_8 = "𝗧𝗼𝗽 𝟱 𝗔𝗸𝘁𝗶𝘃"

BTN_OWNER_9 = "𝗔𝗱𝗺𝗶𝗻 𝗕𝗼𝘀𝗵𝗾𝗮𝗿𝘂𝘃𝗶"
BTN_BACK = "𝗢𝗿𝗾𝗮𝗴𝗮"

back_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_BACK, icon_custom_emoji_id="5877536313623711363", style="primary")]],
    resize_keyboard=True
)

def get_main_menu(user_id: int, admins_list: list) -> InlineKeyboardMarkup:
    """✨ Premium asosiy menyu."""

    try:
        admin_ids = {int(x) for x in admins_list}
    except (TypeError, ValueError):
        admin_ids = set()

    is_admin = (
        int(user_id) in OWNER_IDS
        or int(user_id) in admin_ids
    )

    # 👤 Oddiy foydalanuvchi menyusi
    buttons = [
        [
            InlineKeyboardButton(
                text="Account ulash",
                callback_data="acc:menu",
                icon_custom_emoji_id="5440739780298036971",
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                text="𝗕𝗼𝘁 𝗛𝗮𝗾𝗶𝗱𝗮",
                callback_data="bot_about",
                icon_custom_emoji_id="5931415565955503486",
                style="success"
            )
        ],
        [
            InlineKeyboardButton(
                text=BTN_USER_1,
                callback_data="menu_ad",
                icon_custom_emoji_id="5440725903258704836",
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                text=BTN_USER_2,
                callback_data="menu_roles",
                icon_custom_emoji_id="5429247186548309037",
                style="success"
            ),
            InlineKeyboardButton(
                text=BTN_USER_3,
                callback_data="menu_complaint",
                icon_custom_emoji_id="5188463524568926712",
                style="danger"
            )
        ]
    ]

    # 👑 Admin paneli
    if is_admin:
        buttons.extend([
            [
                InlineKeyboardButton(
                    text=BTN_ADMIN_4,
                    callback_data="menu_groups",
                    icon_custom_emoji_id="5438256705085400686",
                    style="primary"
                ),
                InlineKeyboardButton(
                    text=BTN_ADMIN_5,
                    callback_data="menu_today_ads",
                    icon_custom_emoji_id="5440715101415956697",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text=BTN_ADMIN_6,
                    callback_data="menu_statistics",
                    icon_custom_emoji_id="5438525819146233895",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text=BTN_ADMIN_8,
                    callback_data="menu_top_active",
                    icon_custom_emoji_id="5438162795625474405",
                    style="success"
                )
            ]
        ])

    # 👑 Faqat bot egasi
    if int(user_id) in OWNER_IDS:
        buttons.append([
            InlineKeyboardButton(
                text=BTN_OWNER_9,
                callback_data="menu_admin_manage",
                icon_custom_emoji_id="5440735356481724855",
                style="danger"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

BOT_ABOUT_TEXT = (
    '<tg-emoji emoji-id="5370935802844946281">⭐</tg-emoji> '
    '<b>𝐌𝐚𝐟𝐢𝐚 𝐆𝐮𝐫𝐮𝐡𝐥𝐚𝐫 𝐔𝐜𝐡𝐮𝐧 𝐏𝐫𝐨 𝐝𝐚𝐫𝐚𝐣𝐚𝐝𝐚𝐠𝐢 𝐁𝐨𝐭</b>'
)

REKLAMA_INFO = (
    '<tg-emoji emoji-id="5438256705085400686">⭐</tg-emoji> '
    '<b>𝐆𝐮𝐫𝐮𝐡𝐢𝐧𝐠𝐢𝐳𝐠𝐚 𝐑𝐞𝐤𝐥𝐚𝐦𝐚 𝐊𝐞𝐥𝐬𝐚 𝐔𝐥𝐚𝐫𝐧𝐢 𝐗𝐢𝐬𝐨𝐛𝐥𝐚𝐲𝐝𝐢 - 𝐯𝐚 𝐤𝐞𝐥𝐠𝐚𝐧 𝐫𝐞𝐤𝐥𝐚𝐦𝐚𝐠𝐚 𝐚𝐭𝐯𝐞𝐭 𝐪𝐢𝐥𝐚𝐝𝐢 - 𝐲𝐚𝐧𝐢 𝐚𝐯𝐭𝐨 𝐫𝐞𝐤 𝐬𝐳𝐠𝐚 𝐤𝐞𝐥𝐠𝐚𝐧 𝐦𝐚𝐟𝐢𝐚 𝐠𝐮𝐫𝐮𝐡𝐧𝐢 𝐚𝐝𝐦𝐢𝐧 𝐮𝐬𝐞𝐫𝐥𝐚𝐧𝐢 𝐭𝐞𝐫𝐢𝐛 𝐠𝐮𝐫𝐮𝐡𝐢𝐧𝐠𝐳𝐝𝐚𝐧 𝐛𝐚𝐧𝐥𝐚𝐲𝐝𝐢 - 𝐎𝐝𝐝𝐢𝐲 𝐅𝐨𝐲𝐝𝐚𝐥𝐚𝐧𝐮𝐯𝐜𝐡𝐢𝐥𝐚𝐫𝐠𝐚 𝐬𝐢𝐳𝐧𝐢𝐧𝐠 𝐠𝐮𝐫𝐮𝐡𝐢𝐧𝐠𝐳𝐧𝐢 𝐫𝐞𝐤𝐥𝐚𝐦𝐚 𝐪𝐢𝐥𝐚𝐝𝐢</b> '
    '<tg-emoji emoji-id="5440802843302843874">⭐</tg-emoji> '

)

ADMINS_INFO = (
    '<tg-emoji emoji-id="5440855774479800882">⭐</tg-emoji> '
    "<b>𝐀𝐝𝐦𝐢𝐧𝐥𝐚𝐫𝐧𝐢 𝐁𝐨𝐬𝐡𝐪𝐚𝐫𝐚𝐝𝐢 - 𝐎𝐠𝐨𝐡𝐥𝐚𝐧𝐭𝐫𝐢𝐬𝐡 𝐁𝐞𝐫𝐚𝐝𝐢 - 𝟓𝟎 𝐭𝐚𝐠𝐚𝐜𝐡𝐚 𝐁𝐚𝐧𝐥𝐚𝐬𝐡 𝐋𝐢𝐦𝐢𝐭𝐢 - 𝐥𝐢𝐦𝐢𝐭𝐝𝐚𝐧 𝐨'𝐭𝐬𝐚 𝐀𝐝𝐦𝐢𝐧𝐥𝐢𝐤𝐝𝐚𝐧 𝐎𝐥𝐢𝐧𝐚𝐝𝐢</b> "
    '<tg-emoji emoji-id="5438279988103109482">⭐</tg-emoji> '

)

ACTIVE_INFO = (
    '<tg-emoji emoji-id="5438525819146233895">⭐</tg-emoji> '
    "<b>𝐆𝐮𝐫𝐮𝐡𝐢𝐧𝐠𝐳𝐝𝐚 𝐀𝐝𝐦𝐢𝐧𝐥𝐚𝐫 𝐕𝐚 𝐎𝐝𝐝𝐢𝐲 𝐅𝐨𝐲𝐝𝐚𝐥𝐚𝐧𝐮𝐯𝐜𝐡𝐢𝐥𝐚𝐫 𝐀𝐤𝐭𝐢𝐯𝐥𝐢𝐤𝐧𝐢 𝐊𝐨'𝐫𝐬𝐡𝐢𝐧𝐠𝐢𝐳 𝐦𝐮𝐦𝐤𝐢𝐧 /aktiv 𝐛𝐮𝐲𝐫𝐮𝐠'𝐢 𝐛𝐢𝐥𝐚𝐧</b> "
    '<tg-emoji emoji-id="5438279988103109482">⭐</tg-emoji> '

)

GROUP_HELP_INFO = (
    '<tg-emoji emoji-id="5217763885951520694">⭐</tg-emoji> '
    '<b>𝐆𝐮𝐫𝐮𝐡𝐢𝐧𝐠𝐢𝐳 𝐌𝐚𝐟𝐢𝐚 𝐆𝐮𝐫𝐮𝐡 𝐫𝐞𝐣𝐢𝐦𝐝𝐚 𝐁𝐨𝐬𝐡𝐪𝐚𝐫𝐥𝐚𝐝𝐢</b> '
    '<tg-emoji emoji-id="5219680536582196906">⭐</tg-emoji> '
    "<b>𝐌𝐚𝐟𝐢𝐚 𝐎'𝐲𝐢𝐧𝐢 𝐮𝐜𝐡𝐮𝐧 𝐦𝐨𝐬𝐥𝐚𝐬𝐡𝐭𝐫𝐢𝐥𝐠𝐚𝐧 𝐁𝐨𝐭</b> "
    '<tg-emoji emoji-id="5217952701303788099">⭐</tg-emoji> '

)

def get_bot_about_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="𝐑𝐞𝐤𝐥𝐚𝐦𝐚 𝐍𝐚𝐳𝐨𝐫𝐚𝐭𝐢", callback_data="about_ads", icon_custom_emoji_id="5440770128536951370", style="success")],
        [InlineKeyboardButton(text="𝐀𝐝𝐦𝐢𝐧𝐥𝐚𝐫 𝐍𝐚𝐳𝐨𝐫𝐚𝐭𝐢", callback_data="about_admins", icon_custom_emoji_id="5440770128536951370", style="success")],
        [InlineKeyboardButton(text="𝐀𝐤𝐭𝐢𝐯 𝐍𝐚𝐳𝐨𝐫𝐚𝐭𝐢", callback_data="about_active", icon_custom_emoji_id="5440770128536951370", style="success")],
        [InlineKeyboardButton(text="𝐆𝐫𝐨𝐮𝐩 𝐇𝐞𝐥𝐩 𝐌𝐚𝐟𝐢𝐚 𝐑𝐞𝐣𝐢𝐦 𝐁𝐨𝐭", callback_data="about_group_help", icon_custom_emoji_id="5440770128536951370", style="success")],
        [InlineKeyboardButton(text="Бахром", url="https://t.me/skroozy", icon_custom_emoji_id="5438105423452335670", style="danger")],
    ])

def get_about_back_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="𝐎𝐫𝐭𝐠𝐚", callback_data="bot_about", icon_custom_emoji_id="5877341274863832725", style="danger")],
    ])

def get_roles_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # 1] TINCH AHOLILAR TOMONDA
            [InlineKeyboardButton(text="👨🏼 Tinch aholi", callback_data="role_fuqaro", style="success"), InlineKeyboardButton(text="💃 Kezuvchi", callback_data="role_kezuvchi", style="success")],
            [InlineKeyboardButton(text="👮🏻‍♂ Serjant", callback_data="role_serjant", style="success"), InlineKeyboardButton(text="🕵🏻‍♂ Komissar katani", callback_data="role_komissar", style="success")],
            [InlineKeyboardButton(text="👨🏻‍⚕ Doktor", callback_data="role_doktor", style="success"), InlineKeyboardButton(text="🧙‍♂ Daydi", callback_data="role_daydi", style="success")],
            [InlineKeyboardButton(text="🧞‍♂️ Afsungar", callback_data="role_afsungar", style="success"), InlineKeyboardButton(text="🤞 Omadli", callback_data="role_omadli", style="success")],
            [InlineKeyboardButton(text="🎖️ Janob", callback_data="role_janob", style="success")],

            # 2] MAFIYA TOMONDA
            [InlineKeyboardButton(text="🤵🏻 Don", callback_data="role_don", style="success"), InlineKeyboardButton(text="🤵🏼 Mafiya", callback_data="role_mafia", style="success")],
            [InlineKeyboardButton(text="👨‍💼 Advokat", callback_data="role_advokat", style="success"), InlineKeyboardButton(text="🕴 Убийца", callback_data="role_ubiyca", style="success")],
            [InlineKeyboardButton(text="👩‍💻 Jurnalist", callback_data="role_jurnalist", style="success")],

            # 3] ERKIN VA YAKKAXON ROLLAR
            [InlineKeyboardButton(text="🔪 Qotil", callback_data="role_qotil", style="success"), InlineKeyboardButton(text="🐺 Bo'ri", callback_data="role_bori", style="success")],
            [InlineKeyboardButton(text="🤓 Sotqin", callback_data="role_sotqin", style="success"), InlineKeyboardButton(text="🧙‍ Sexrgar", callback_data="role_sehrgar", style="success")],
            [InlineKeyboardButton(text="🧟 G'azabkor", callback_data="role_gazabkor", style="success"), InlineKeyboardButton(text="🤹 Aferist", callback_data="role_aferist", style="success")],

            # 💬 PROFILE LINK TUGMA
            [InlineKeyboardButton(text="Batafsil so'rash uchun", url="https://t.me/skroozy", icon_custom_emoji_id="5438105423452335670", style="danger")]
        ]
    )

def get_back_to_roles_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Rollar ro'yxatiga qaytish", callback_data="roles_list", icon_custom_emoji_id="5219793021775679085", style="success")],
            [InlineKeyboardButton(text="Batafsil so'rash uchun", url="https://t.me/skroozy", icon_custom_emoji_id="5438105423452335670", style="danger")]
        ]
    )

def get_admin_manage_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Admin Qo'shish",
                callback_data="admin_add_start",
                icon_custom_emoji_id="5220102237946153327",
                style="success"
            )],
            [InlineKeyboardButton(
                text="Adminlar Ro'yxati / Olish",
                callback_data="admin_list_show",
                icon_custom_emoji_id="5438256705085400686",
                style="primary"
            )],
            [InlineKeyboardButton(
                text="Adminlar Haqida Ma'lumot",
                callback_data="admin_info_list",
                icon_custom_emoji_id="5438610236728437908",
                style="primary"
            )],
            [InlineKeyboardButton(
                text="Asosiy menyu",
                callback_data="main_menu",
                icon_custom_emoji_id="5438151302292988650",
                style="primary"
            )]
        ]
    )

def get_admins_delete_inline(admins_data) -> InlineKeyboardMarkup:
    buttons = []

    for uid, name, username, region, birth_date, phone in admins_data:
        display_name = name if name else f"ID: {uid}"
        buttons.append([
            InlineKeyboardButton(
                text=f"{display_name} ({uid})",
                callback_data=f"admin_del_{uid}",
                icon_custom_emoji_id="5440831228741708298",
                style="danger"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="Orqaga",
            callback_data="menu_admin_manage",
            icon_custom_emoji_id="5877536313623711363",
            style="primary"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Orqaga", callback_data="main_menu", icon_custom_emoji_id="5877536313623711363", style="primary")]
        ]
    )

# ============================================================
# 🗺 ADMIN VILOYAT / DAVLAT TANLASH
# ============================================================

def get_admin_region_keyboard() -> InlineKeyboardMarkup:
    regions = [
        ("Qoraqalpog‘iston", "admin_region_Qoraqalpog‘iston", "5318986077455795572", "success"),
        ("Toshkent shahri", "admin_region_Toshkent shahri", "5318986077455795572", "success"),
        ("Andijon viloyati", "admin_region_Andijon viloyati", "5318986077455795572", "success"),
        ("Buxoro viloyati", "admin_region_Buxoro viloyati", "5318986077455795572", "success"),
        ("Jizzax viloyati", "admin_region_Jizzax viloyati", "5318986077455795572", "success"),
        ("Qashqadaryo viloyati", "admin_region_Qashqadaryo viloyati", "5318986077455795572", "success"),
        ("Navoiy viloyati", "admin_region_Navoiy viloyati", "5318986077455795572", "success"),
        ("Namangan viloyati", "admin_region_Namangan viloyati", "5318986077455795572", "success"),
        ("Samarqand viloyati", "admin_region_Samarqand viloyati", "5318986077455795572", "success"),
        ("Sirdaryo viloyati", "admin_region_Sirdaryo viloyati", "5318986077455795572", "success"),
        ("Surxondaryo viloyati", "admin_region_Surxondaryo viloyati", "5318986077455795572", "success"),
        ("Toshkent viloyati", "admin_region_Toshkent viloyati", "5318986077455795572", "success"),
        ("Farg‘ona viloyati", "admin_region_Farg‘ona viloyati", "5318986077455795572", "success"),
        ("Xorazm viloyati", "admin_region_Xorazm viloyati", "5318986077455795572", "success"),
        ("Boshqa davlat", "admin_region_other", "5217952701303788099", "primary"),
    ]

    buttons = []

    for text, callback_data, emoji_id, style in regions:
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
                icon_custom_emoji_id=emoji_id,
                style=style
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="Orqaga",
            callback_data="menu_admin_manage",
            icon_custom_emoji_id="5877536313623711363",
            style="primary"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 🌍 ADMIN UCHUN DAVLATLAR
def get_admin_country_keyboard() -> InlineKeyboardMarkup:
    countries = [
        ("O‘zbekiston", "admin_country_O‘zbekiston", "5318986077455795572", "success"),
        ("Rossiya", "admin_country_Rossiya", "5318986077455795572", "success"),
        ("Qozog‘iston", "admin_country_Qozog‘iston", "5318986077455795572", "success"),
        ("Qirg‘iziston", "admin_country_Qirg‘iziston", "5318986077455795572", "success"),
        ("Tojikiston", "admin_country_Tojikiston", "5318986077455795572", "success"),
        ("Turkmaniston", "admin_country_Turkmaniston", "5318986077455795572", "success"),
        ("Turkiya", "admin_country_Turkiya", "5318986077455795572", "success"),
        ("BAA", "admin_country_BAA", "5318986077455795572", "success"),
        ("AQSh", "admin_country_AQSh", "5318986077455795572", "success"),
        ("Buyuk Britaniya", "admin_country_Buyuk Britaniya", "5318986077455795572", "success"),
        ("Germaniya", "admin_country_Germaniya", "5318986077455795572", "success"),
        ("Fransiya", "admin_country_Fransiya", "5318986077455795572", "success"),
        ("Janubiy Koreya", "admin_country_Janubiy Koreya", "5318986077455795572", "success"),
        ("Xitoy", "admin_country_Xitoy", "5318986077455795572", "success"),
        ("Yaponiya", "admin_country_Yaponiya", "5318986077455795572", "success"),
        ("Boshqa", "admin_country_other", "5217952701303788099", "primary"),
    ]

    buttons = []

    for text, callback_data, emoji_id, style in countries:
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
                icon_custom_emoji_id=emoji_id,
                style=style
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="Orqaga",
            callback_data="admin_region_back",
            icon_custom_emoji_id="5877536313623711363",
            style="primary"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
