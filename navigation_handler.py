#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль навигации - построение маршрутов к курорту и важным точкам
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

router = Router()

# Координаты важных точек
LOCATIONS = {
    "resort": {
        "name": "🏨 Курорт Пеликан Алаколь",
        "lat": 45.955000,
        "lon": 81.571389,
        "address": "с. Акши, Алакольский р-он, Жетісу обл.",
        "description": "База отдыха на берегу озера Алаколь",
        "phone": "+7 (776) 727 58 41"
    },
    "office": {
        "name": "🏢 Офис продаж (Алматы)",
        "lat": 43.240556,
        "lon": 76.956389,
        "address": "ул. Досмухамедова, 89, БЦ Каспи, офис 101/1",
        "description": "Офис бронирования и консультаций",
        "phone": "+7 (727) 292-78-99"
    },
    "airport": {
        "name": "✈️ Аэропорт Ушарал",
        "lat": 46.183237,
        "lon": 80.853441,
        "address": "г. Ушарал, Жетісу обл.",
        "description": "Ближайший аэропорт к курорту (90 км)",
        "phone": ""
    },
    "station": {
        "name": "🚂 ЖД станция Акши",
        "lat": 45.954860,
        "lon": 81.537759,
        "address": "с. Акши",
        "description": "Железнодорожная станция (2 км от курорта)",
        "phone": ""
    },
    "hospital": {
        "name": "🏥 Больница Ушарал",
        "lat": 46.16711658386218,
        "lon": 80.95427999623365,
        "address": "г. Ушарал, ул. Абая",
        "description": "Ближайшая больница с круглосуточным приёмом (85 км от курорта)",
        "phone": "+7 (72837) 2-14-03"
    },
    "pharmacy": {
        "name": "💊 Аптека Акши",
        "lat": 45.95210554045593,
        "lon": 81.54832241566287,
        "address": "с. Акши, центр села",
        "description": "Аптека и медпункт (1.5 км от курорта)",
        "phone": "+7 (72833) 2-11-22"
    }
}

def get_navigation_keyboard():
    """Клавиатура выбора точки назначения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏨 Курорт Пеликан", callback_data="nav_resort")],
        [InlineKeyboardButton(text="🏢 Офис в Алматы", callback_data="nav_office")],
        [InlineKeyboardButton(text="✈️ Аэропорт Ушарал", callback_data="nav_airport")],
        [InlineKeyboardButton(text="🚂 ЖД станция Акши", callback_data="nav_station")],
        [InlineKeyboardButton(text="🏥 Больница Ушарал", callback_data="nav_hospital")],
        [InlineKeyboardButton(text="💊 Аптека Акши", callback_data="nav_pharmacy")],
        [InlineKeyboardButton(text="ℹ️ Полезная информация", callback_data="travel_info")],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_main")]
    ])
    return keyboard

def get_maps_keyboard(lat: float, lon: float, name: str):
    """Клавиатура с кнопками открытия в разных картах"""
    
    # URL для разных карт
    yandex_url = f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
    google_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    gis_url = f"https://2gis.kz/geo/{lon},{lat}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Яндекс.Карты", url=yandex_url)],
        [InlineKeyboardButton(text="🌍 Google Maps", url=google_url)],
        [InlineKeyboardButton(text="🗺️ 2ГИС", url=gis_url)],
        [InlineKeyboardButton(text="📞 Контакты для связи", callback_data="call_reception")],
        [InlineKeyboardButton(text="« Другая точка", callback_data="navigation")]
    ])
    return keyboard

@router.message(Command("navigation"))
@router.callback_query(F.data == "navigation")
async def cmd_navigation(update: Message | CallbackQuery):
    """Главное меню навигации"""
    
    text = """
🗺️ <b>Как добраться</b>

Выберите точку назначения, и я помогу построить маршрут в удобном для вас приложении.

<b>Доступные точки:</b>
🏨 Курорт Пеликан - база отдыха на озере
🏢 Офис в Алматы - бронирование и консультации
✈️ Аэропорт Ушарал - ближайший к курорту (90 км)
🚂 ЖД станция Акши - 2 км от курорта
🏥 Больница Ушарал - круглосуточная помощь (85 км)
💊 Аптека Акши - медпункт (1.5 км)

💡 Также доступна полезная информация о маршрутах и трансфере.
"""
    
    keyboard = get_navigation_keyboard()
    
    if isinstance(update, CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await update.answer()
    else:
        await update.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("nav_"))
async def show_location(callback: CallbackQuery):
    """Показать информацию о выбранной точке и кнопки карт"""
    
    location_key = callback.data.replace("nav_", "")
    location = LOCATIONS.get(location_key)
    
    if not location:
        await callback.answer("❌ Локация не найдена")
        return
    
    # Формируем текст с контактами если есть
    contact_info = ""
    if location.get("phone"):
        contact_info = f"\n📞 <b>Телефон:</b> {location['phone']}"
    
    text = f"""
{location['name']}

📍 <b>Адрес:</b> {location['address']}
📝 <b>Описание:</b> {location['description']}{contact_info}

🗺️ <b>Координаты:</b>
{location['lat']}, {location['lon']}

<i>Нажмите на кнопку нужного приложения, чтобы построить маршрут:</i>
"""
    
    keyboard = get_maps_keyboard(location['lat'], location['lon'], location['name'])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "call_reception")
async def show_contacts(callback: CallbackQuery):
    """Показать контакты для связи"""
    
    text = """
📞 <b>Контакты для связи</b>

<b>Ресепшн (оз. Алаколь):</b>
📞 +7 (72833) 30002
📱 +7 (776) 727 58 41 (WhatsApp)
📧 pelikan-alakol@mail.ru

<b>Офис продаж (Алматы):</b>
📞 +7 (727) 292-78-99
📱 +7 (701) 771 47 33 (WhatsApp)
📱 +7 (705) 806 78 33 (WhatsApp)
📧 pelikan-08@mail.ru

<b>Режим работы:</b>
Ежедневно с 9:00 до 21:00
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад к навигации", callback_data="navigation")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "travel_info")
async def show_travel_info(callback: CallbackQuery):
    """Полезная информация о маршрутах"""
    
    text = """
ℹ️ <b>Полезная информация о маршрутах</b>

<b>✈️ Из аэропорта Ушарал:</b>
• Расстояние: 90 км (~1.5 часа)
• Примерная стоимость такси: 10,000₸
• Можно заказать трансфер

<b>🚂 От ЖД станции Акши:</b>
• Расстояние: 2 км (~5 минут на авто)
• Примерная стоимость такси: 500₸
• Пешком: около 25 минут

<b>🚗 Из Алматы на машине:</b>
• Расстояние: ~450 км
• Время в пути: ~6 часов
• Маршрут: Алматы → Талдыкорган → Ушарал → Акши
• Дорога хорошая, платных участков нет

<b>🚌 На общественном транспорте:</b>
• Автобус Алматы → Акши (ежедневно)
• Поезд до станции Акши
• От станции - такси или трансфер

<b>🏥 Медицинская помощь:</b>
• На территории курорта: аптечка первой помощи
• Аптека в Акши: 1.5 км (лекарства, базовая помощь)
• Больница в Ушарале: 85 км (полный спектр услуг)
• Скорая помощь: 103

<b>🚗 Трансфер:</b>
Мы можем организовать трансфер от аэропорта или вокзала.
Для бронирования свяжитесь с нами заранее.

<i>При необходимости срочной медицинской помощи обращайтесь на ресепшн - мы поможем вызвать врача или организовать транспортировку.</i>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Заказать трансфер", callback_data="order_transfer")],
        [InlineKeyboardButton(text="« Назад к навигации", callback_data="navigation")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "order_transfer")
async def order_transfer(callback: CallbackQuery):
    """Форма заказа трансфера"""
    
    text = """
🚗 <b>Заказ трансфера</b>

Для бронирования трансфера свяжитесь с нами любым удобным способом:

📱 <b>WhatsApp:</b>
+7 (776) 727 58 41
+7 (701) 771 47 33

📞 <b>Телефон:</b>
+7 (727) 292-78-99 (Алматы)
+7 (72833) 30002 (Алаколь)

<b>Укажите при бронировании:</b>
✓ Дату и время прибытия
✓ Откуда (аэропорт/вокзал/адрес)
✓ Количество пассажиров
✓ Количество багажа

Мы подтвердим бронирование и вышлем детали встречи.

<i>Рекомендуем бронировать трансфер минимум за сутки до прибытия.</i>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="travel_info")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.delete()
    await callback.answer("Возвращаемся в главное меню...")
