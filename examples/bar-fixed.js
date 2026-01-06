// ============================================================================
// bar.js - Интеграция меню бара с Telegram ботом "Пеликан Алаколь"
// ============================================================================

// Конфигурация
const CONFIG = {
    API_URL: 'https://bar.pelikan-alakol.kz/api/order', // URL вашего webhook сервера
    // Для локальной разработки используйте: 'http://localhost:8080/api/order'
    MENU_JSON: 'barzakaz.json'
};

// Состояние корзины
let cart = [];
let menuData = [];

// ============================================================================
// ЗАГРУЗКА МЕНЮ
// ============================================================================

/**
 * Загружает меню из JSON файла
 */
async function loadMenuData() {
    try {
        const response = await fetch(CONFIG.MENU_JSON);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        menuData = await response.json();
        
        // Добавляем ID к блюдам, если их нет
        menuData = menuData.map((item, index) => ({
            id: item.id || `dish-${index}`,
            name: item.name,
            category: item.category,
            price: item.price,
            description: item.description || ''
        }));
        
        renderMenu(menuData);
    } catch (error) {
        console.error('Ошибка загрузки меню:', error);
        const container = document.getElementById('menu');
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #FFD700;">
                    <h2>❌ Ошибка загрузки меню</h2>
                    <p>${error.message}</p>
                    <button onclick="loadMenuData()" class="add-btn" style="margin-top: 20px;">
                        🔄 Попробовать снова
                    </button>
                </div>
            `;
        }
    }
}

/**
 * Отображает меню на странице
 */
function renderMenu(data) {
    const container = document.getElementById('menu');
    if (!container) return;

    container.innerHTML = '';

    // Группируем по категориям
    const categories = data.reduce((acc, item) => {
        if (!acc[item.category]) acc[item.category] = [];
        acc[item.category].push(item);
        return acc;
    }, {});

    // Рендерим каждую категорию
    Object.keys(categories).forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category';

        const categoryTitle = document.createElement('h2');
        categoryTitle.textContent = category;
        categoryDiv.appendChild(categoryTitle);

        const grid = document.createElement('div');
        grid.className = 'menu-grid';

        categories[category].forEach(item => {
            const card = createDishCard(item);
            grid.appendChild(card);
        });

        categoryDiv.appendChild(grid);
        container.appendChild(categoryDiv);
    });
}

/**
 * Создаёт карточку блюда
 */
function createDishCard(item) {
    const card = document.createElement('div');
    card.className = 'dish-card';

    // Генерируем имя файла изображения из названия блюда
    const imageName = item.name.toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-zа-яё0-9-]/g, '')
        .replace(/^-+|-+$/g, '');
    
    const imageUrl = `img/${imageName}.jpg`;

    card.innerHTML = `
        <img 
            src="${imageUrl}" 
            class="dish-img" 
            alt="${item.name}"
            onerror="this.src='img/placeholder.jpg'"
        >
        <div class="dish-info">
            <h3 class="dish-name">${item.name}</h3>
            ${item.description ? `<p class="dish-description">${item.description}</p>` : ''}
            <p class="dish-price">${item.price.toLocaleString('ru-RU')} ₸</p>
            <button 
                class="add-btn" 
                onclick="addToCart('${item.id}', \`${item.name}\`, ${item.price})"
            >
                <i class="fas fa-cart-plus"></i> Добавить
            </button>
        </div>
    `;

    return card;
}

// ============================================================================
// КОРЗИНА
// ============================================================================

/**
 * Добавляет товар в корзину
 */
function addToCart(id, name, price) {
    const existingItem = cart.find(item => item.id === id);

    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({
            id: id,
            name: name,
            price: price,
            quantity: 1
        });
    }

    updateCart();
    saveCartToLocalStorage();
    showNotification(`${name} добавлен в корзину!`);
}

/**
 * Удаляет товар из корзины
 */
function removeFromCart(id) {
    cart = cart.filter(item => item.id !== id);
    updateCart();
    saveCartToLocalStorage();
}

/**
 * Изменяет количество товара
 */
function updateQuantity(id, newQuantity) {
    const item = cart.find(i => i.id === id);
    
    if (!item) return;

    if (newQuantity <= 0) {
        removeFromCart(id);
    } else {
        item.quantity = newQuantity;
        updateCart();
        saveCartToLocalStorage();
    }
}

/**
 * Очищает всю корзину
 */
function clearCart() {
    if (cart.length === 0) return;

    if (confirm('Вы уверены, что хотите очистить корзину?')) {
        cart = [];
        updateCart();
        localStorage.removeItem('pelikan_cart');
        showNotification('Корзина очищена');
    }
}

/**
 * Подсчитывает итоговую сумму
 */
function calculateTotal() {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

/**
 * Обновляет отображение корзины
 */
function updateCart() {
    const cartItems = document.getElementById('cart-items');
    const totalElement = document.getElementById('total');
    const submitButton = document.querySelector('#order-form button[type="submit"]');

    if (!cartItems || !totalElement) return;

    // Обновляем список товаров
    if (cart.length === 0) {
        cartItems.innerHTML = '<li class="empty-cart">Корзина пуста</li>';
        totalElement.textContent = 'Итого: 0 ₸';
        if (submitButton) submitButton.disabled = true;
        return;
    }

    cartItems.innerHTML = cart.map(item => `
        <li>
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">${item.price.toLocaleString('ru-RU')} ₸ × ${item.quantity}</div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button 
                    class="btn-quantity" 
                    onclick="updateQuantity('${item.id}', ${item.quantity - 1})"
                >−</button>
                <span style="min-width: 30px; text-align: center; font-weight: bold;">${item.quantity}</span>
                <button 
                    class="btn-quantity" 
                    onclick="updateQuantity('${item.id}', ${item.quantity + 1})"
                >+</button>
                <button 
                    class="remove-btn" 
                    onclick="removeFromCart('${item.id}')"
                    title="Удалить"
                >🗑️</button>
            </div>
        </li>
    `).join('');

    // Обновляем итоговую сумму
    const total = calculateTotal();
    totalElement.textContent = `Итого: ${total.toLocaleString('ru-RU')} ₸`;

    // Активируем кнопку заказа
    if (submitButton) submitButton.disabled = false;
}

/**
 * Сохраняет корзину в localStorage
 */
function saveCartToLocalStorage() {
    localStorage.setItem('pelikan_cart', JSON.stringify(cart));
}

/**
 * Загружает корзину из localStorage
 */
function loadCartFromLocalStorage() {
    const saved = localStorage.getItem('pelikan_cart');
    if (saved) {
        try {
            cart = JSON.parse(saved);
            updateCart();
        } catch (e) {
            console.error('Ошибка загрузки корзины:', e);
            cart = [];
        }
    }
}

// ============================================================================
// ОФОРМЛЕНИЕ ЗАКАЗА
// ============================================================================

/**
 * Обрабатывает отправку формы заказа
 */
async function handleOrderSubmit(event) {
    event.preventDefault();

    if (cart.length === 0) {
        showNotification('Корзина пуста! Добавьте блюда для заказа.', 'error');
        return;
    }

    const form = event.target;
    const formData = new FormData(form);

    const orderData = {
        orderId: Date.now().toString(),
        name: formData.get('name').trim(),
        room: formData.get('room').trim(),
        telegram: formData.get('telegram').trim().replace('@', ''),
        items: cart,
        total: calculateTotal(),
        timestamp: new Date().toLocaleString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        })
    };

    // Валидация
    if (!orderData.name || orderData.name.length < 2) {
        showNotification('Пожалуйста, укажите ваше имя', 'error');
        return;
    }

    if (!orderData.room || orderData.room.length < 1) {
        showNotification('Пожалуйста, укажите номер комнаты', 'error');
        return;
    }

    // Показываем индикатор загрузки
    showLoading(true);

    try {
        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.status === 'ok') {
            // Успешно
            showSuccessMessage(result.order_id, orderData.telegram);
            
            // Очищаем форму и корзину
            form.reset();
            cart = [];
            updateCart();
            localStorage.removeItem('pelikan_cart');
        } else {
            throw new Error(result.message || 'Неизвестная ошибка');
        }

    } catch (error) {
        console.error('Ошибка отправки заказа:', error);
        showNotification(
            'Ошибка при оформлении заказа. Пожалуйста, попробуйте ещё раз или свяжитесь с администратором.',
            'error'
        );
    } finally {
        showLoading(false);
    }
}

/**
 * Показывает сообщение об успешном заказе
 */
function showSuccessMessage(orderId, telegram) {
    const message = telegram 
        ? `
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: #4CAF50; margin-bottom: 15px;">✅ Заказ успешно оформлен!</h2>
                <p style="font-size: 1.2em; margin-bottom: 10px;">Номер заказа: <strong>#${orderId}</strong></p>
                <p>Вы получите уведомление в Telegram.</p>
                <p>Для проверки статуса напишите боту <strong>@pelikan_alakol_bot</strong>:</p>
                <p style="font-family: monospace; background: #f0f0f0; padding: 10px; border-radius: 5px; color: #333;">
                    /status ${orderId}
                </p>
                <p style="margin-top: 15px; color: #666;">💳 Оплата при получении в баре.</p>
            </div>
        `
        : `
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: #4CAF50; margin-bottom: 15px;">✅ Заказ успешно оформлен!</h2>
                <p style="font-size: 1.2em; margin-bottom: 10px;">Номер заказа: <strong>#${orderId}</strong></p>
                <p>Запомните номер заказа для отслеживания статуса.</p>
                <p style="margin-top: 15px; color: #666;">💳 Оплата при получении в баре.</p>
            </div>
        `;

    // Создаём модальное окно с сообщением
    const modal = document.createElement('div');
    modal.className = 'notification-modal';
    modal.innerHTML = `
        <div class="notification-modal-content">
            ${message}
            <button onclick="this.parentElement.parentElement.remove()" class="add-btn" style="margin-top: 20px;">
                Закрыть
            </button>
        </div>
    `;
    document.body.appendChild(modal);

    // Автоматически удаляем через 10 секунд
    setTimeout(() => modal.remove(), 10000);
}

/**
 * Показывает/скрывает индикатор загрузки
 */
function showLoading(show) {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }

    const submitBtn = document.querySelector('#order-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = show;
        submitBtn.textContent = show ? 'Отправка...' : 'Оформить заказ';
    }
}

/**
 * Показывает уведомление
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================================================
// ИНИЦИАЛИЗАЦИЯ
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🍽 Инициализация системы заказов бара...');

    // Загружаем меню
    loadMenuData();

    // Загружаем корзину из localStorage
    loadCartFromLocalStorage();

    // Привязываем обработчик формы
    const orderForm = document.getElementById('order-form');
    if (orderForm) {
        orderForm.addEventListener('submit', handleOrderSubmit);
    }

    // Обработчик кнопки очистки корзины
    const clearBtn = document.querySelector('.clear-cart-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearCart);
    }

    console.log('✅ Система заказов готова к работе!');
});

// Экспортируем функции для использования в HTML
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateQuantity = updateQuantity;
window.clearCart = clearCart;
