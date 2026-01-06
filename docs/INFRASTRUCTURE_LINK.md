# 🔗 Добавление ссылки на онлайн-заказ в инфраструктуру

## 📍 Где находится блок "Блюда на заказ"

В вашем файле `infrastructure.json`:

```json
{
  "title": "Блюда на заказ",
  "description": "Онлайн заказ",
  "icon": "images/infra/restoran.svg"
}
```

## ✅ Решение: Добавить ссылку на bar.html

### Вариант 1: Изменить JSON (рекомендуется)

Обновите `infrastructure.json`:

```json
{
  "title": "Блюда на заказ",
  "description": "Онлайн заказ из меню бара. <a href=\"bar.html\" style=\"color: #FFD700; font-weight: bold; text-decoration: underline;\">👉 Сделать заказ</a>",
  "icon": "images/infra/restoran.svg"
}
```

### Вариант 2: Изменить JavaScript рендеринг

Если вы генерируете карточки инфраструктуры через JS (файл `js/infrastructure.js`), добавьте обработку кликабельности:

```javascript
function renderInfrastructure(data) {
  const container = document.getElementById('infrastructureContainer');
  
  container.innerHTML = data.infrastructure.map(item => {
    // Специальная обработка для "Блюда на заказ"
    if (item.title === "Блюда на заказ") {
      return `
        <div class="scroll-item" onclick="window.location.href='bar.html'" style="cursor: pointer;">
          <img src="${item.icon}" alt="${item.title}">
          <h3>${item.title}</h3>
          <p>${item.description}</p>
          <button class="add-btn" style="margin-top: 10px;">
            <i class="fas fa-utensils"></i> Перейти к заказу
          </button>
        </div>
      `;
    }
    
    // Обычные карточки
    return `
      <div class="scroll-item">
        <img src="${item.icon}" alt="${item.title}">
        <h3>${item.title}</h3>
        <p>${item.description}</p>
      </div>
    `;
  }).join('');
}
```

### Вариант 3: Добавить кнопку в описание через HTML

В `infrastructure.json`:

```json
{
  "title": "Блюда на заказ",
  "description": "Закажите еду прямо в номер!<br><a href=\"bar.html\" class=\"order-btn\" style=\"display: inline-block; margin-top: 10px; padding: 10px 20px; background: linear-gradient(135deg, #FFD700, #FFA500); color: #000; border-radius: 25px; text-decoration: none; font-weight: bold;\">🍽 Открыть меню</a>",
  "icon": "images/infra/restoran.svg"
}
```

## 🎨 Улучшенный вариант с модальным окном

Если хотите показывать меню в модальном окне прямо на главной странице:

### 1. Добавьте в index.html (перед `</body>`):

```html
<!-- Модальное окно меню бара -->
<div class="modal" id="barModal">
  <div class="modal-content" style="max-width: 95%; max-height: 90vh;">
    <button class="modal-close" onclick="closeBarModal()">&times;</button>
    <h2><i class="fas fa-utensils"></i> Меню бара</h2>
    <iframe 
      src="bar.html" 
      style="width: 100%; height: 70vh; border: none; border-radius: 10px;"
      id="barIframe"
    ></iframe>
  </div>
</div>
```

### 2. Добавьте в JavaScript (в конец файла):

```javascript
function openBarModal() {
  document.getElementById('barModal').classList.add('active');
}

function closeBarModal() {
  document.getElementById('barModal').classList.remove('active');
}

// Закрытие по клику на фон
document.getElementById('barModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'barModal') closeBarModal();
});
```

### 3. Обновите infrastructure.json:

```json
{
  "title": "Блюда на заказ",
  "description": "Онлайн заказ из меню бара. <a href=\"#\" onclick=\"openBarModal(); return false;\" style=\"color: #FFD700; font-weight: bold; text-decoration: underline;\">👉 Открыть меню</a>",
  "icon": "images/infra/restoran.svg"
}
```

## 📋 Полный код для infrastructure.json

Вот ваш обновлённый файл:

```json
[
  {
    "title": "СТОЛОВАЯ",
    "description": "Полноценное трёхразовое питание. <a href=\"index_menu.html\" style=\"color: #e74c3c; font-weight: bold; text-decoration: underline;\">👉 Посмотреть меню</a>",
    "icon": "images/infra/stolovay.svg"
  },
  {
    "title": "Блюда на заказ",
    "description": "Закажите блюда из бара с доставкой в номер! <a href=\"bar.html\" style=\"color: #FFD700; font-weight: bold; text-decoration: underline;\">👉 Сделать заказ</a>",
    "icon": "images/infra/restoran.svg"
  },
  {
    "title": "Магазин/Бар",
    "description": "Магазин Бар",
    "icon": "images/infra/magazin.svg"
  },
  {
    "title": "Детский досуг",
    "description": "Лепка рисование игры",
    "icon": "images/infra/dosug.svg"
  },
  {
    "title": "Паром/Пляж",
    "description": "Паром ПЛЯЖ ",
    "icon": "images/infra/parom.svg"
  },
  {
    "title": "Трансфер с/из жд.вокзала Акши",
    "description": "ТРАНСФЕР ",
    "icon": "images/infra/transfer.svg"
  },
  {
    "title": "Бассейны / Бани / Массаж",
    "description": "Бассейны / Бани / Массаж",
    "icon": "images/infra/baseyn.svg"
  },
  {
    "title": "Прачечная / Бытовые услуги",
    "description": "Прачечная ",
    "icon": "images/infra/prachechnay.svg"
  },
  {
    "title": "Бильярд/теннис",
    "description": "Бильярд,настольный теннис",
    "icon": "images/infra/biliard.svg"
  }
]
```

## 🎯 Какой вариант выбрать?

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| **Вариант 1: Ссылка в JSON** | ✅ Просто<br>✅ Быстро | ⚠️ Открывает новую страницу |
| **Вариант 2: JS обработка** | ✅ Больше контроля<br>✅ Можно добавить кнопку | ⚠️ Требует изменения JS |
| **Вариант 3: Модальное окно** | ✅ Не покидаем страницу<br>✅ Современный UX | ⚠️ Требует больше кода |

**Рекомендация:** Начните с **Варианта 1** (самый простой), потом при желании улучшите до Варианта 3.

## 🧪 Тестирование

После внесения изменений:

1. Откройте `index.html`
2. Прокрутите до раздела "Наши услуги"
3. Найдите карточку "Блюда на заказ"
4. Нажмите на ссылку
5. Должна открыться страница `bar.html`

## 🔧 Если не работает

**Проблема:** Ссылка не кликабельна

**Решение:** Проверьте, что в `js/infrastructure.js` используется `innerHTML`, а не `textContent`:

```javascript
// ❌ Неправильно
element.textContent = item.description;

// ✅ Правильно
element.innerHTML = item.description;
```

**Проблема:** Стили ссылки не применяются

**Решение:** Добавьте стили в `css/main.css`:

```css
.scroll-item a {
    color: #FFD700;
    font-weight: bold;
    text-decoration: underline;
    transition: color 0.3s;
}

.scroll-item a:hover {
    color: #FFA500;
}
```

## ✅ Готово!

Теперь у вас есть рабочая ссылка на систему онлайн-заказов в разделе инфраструктуры!

---

**Следующий шаг:** [Интеграция с Telegram ботом](INTEGRATION.md)
