/**
 * Интеграция с Telegram ботом системы заказов
 * Файл: js/bar.js
 */

// Конфигурация
const CONFIG = {
    API_URL: 'https://bar.pelikan-alakol.kz/api/order',
    // или для локальной разработки: 'http://localhost:8080/api/order'
};

// Состояние корзины
let cart = [];

/**
 * Отправка заказа на сервер
 */
async function sendOrderToBot(orderData) {
    try {
        // Показываем индикатор загрузки
        showLoading(true);
        
        // Формируем данные заказа
        const order = {
            orderId: Date.now().toString(),
            name: orderData.name,
            room: orderData.room,
            telegram: orderData.telegram || '',
            items: cart.map(item => ({
                name: item.name,
                price: item.price,
                quantity: item.quantity || 1
            })),
            total: calculateTotal(),
            timestamp: new Date().toLocaleString('ru-RU', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            })
        };
        
        console.log('Отправка заказа:', order);
        
        // Отправляем запрос
        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(order)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Ответ сервера:', result);
        
        if (result.status === 'ok') {
            // Успешно
            showSuccess(result.order_id);
            clearCart();
        } else {
            throw new Error(result.message || 'Неизвестная ошибка');
        }
        
    } catch (error) {
        console.error('Ошибка при отправке заказа:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Добавление товара в корзину
 */
function addToCart(item) {
    const existingItem = cart.find(i => i.id === item.id);
    
    if (existingItem) {
        existingItem.quantity = (existingItem.quantity || 1) + 1;
    } else {
        cart.push({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: 1
        });
    }
    
    updateCartUI();
    saveCartToLocalStorage();
}

/**
 * Удаление товара из корзины
 */
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    updateCartUI();
    saveCartToLocalStorage();
}

/**
 * Изменение количества товара
 */
function updateQuantity(itemId, quantity) {
    const item = cart.find(i => i.id === itemId);
    if (item) {
        if (quantity <= 0) {
            removeFromCart(itemId);
        } else {
            item.quantity = quantity;
            updateCartUI();
            saveCartToLocalStorage();
        }
    }
}

/**
 * Подсчёт итоговой суммы
 */
function calculateTotal() {
    return cart.reduce((sum, item) => {
        return sum + (item.price * (item.quantity || 1));
    }, 0);
}

/**
 * Очистка корзины
 */
function clearCart() {
    cart = [];
    updateCartUI();
    localStorage.removeItem('pelikan_cart');
}

/**
 * Сохранение корзины в localStorage
 */
function saveCartToLocalStorage() {
    localStorage.setItem('pelikan_cart', JSON.stringify(cart));
}

/**
 * Загрузка корзины из localStorage
 */
function loadCartFromLocalStorage() {
    const saved = localStorage.getItem('pelikan_cart');
    if (saved) {
        try {
            cart = JSON.parse(saved);
            updateCartUI();
        } catch (e) {
            console.error('Ошибка загрузки корзины:', e);
            cart = [];
        }
    }
}

/**
 * Обновление UI корзины
 */
function updateCartUI() {
    const cartContainer = document.getElementById('cart-items');
    const totalElement = document.getElementById('cart-total');
    const cartCount = document.getElementById('cart-count');
    
    if (!cartContainer) return;
    
    // Количество товаров
    const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
    if (cartCount) {
        cartCount.textContent = totalItems;
        cartCount.style.display = totalItems > 0 ? 'inline' : 'none';
    }
    
    // Список товаров
    if (cart.length === 0) {
        cartContainer.innerHTML = '<p class="empty-cart">Корзина пуста</p>';
        if (totalElement) totalElement.textContent = '0';
        return;
    }
    
    cartContainer.innerHTML = cart.map(item => `
        <div class="cart-item" data-item-id="${item.id}">
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <p class="price">${item.price} ₸</p>
            </div>
            <div class="cart-item-controls">
                <button class="btn-quantity" onclick="updateQuantity('${item.id}', ${item.quantity - 1})">−</button>
                <span class="quantity">${item.quantity || 1}</span>
                <button class="btn-quantity" onclick="updateQuantity('${item.id}', ${item.quantity + 1})">+</button>
                <button class="btn-remove" onclick="removeFromCart('${item.id}')">🗑️</button>
            </div>
        </div>
    `).join('');
    
    // Итоговая сумма
    const total = calculateTotal();
    if (totalElement) {
        totalElement.textContent = total.toLocaleString('ru-RU');
    }
}

/**
 * Показать форму оформления заказа
 */
function showCheckoutForm() {
    if (cart.length === 0) {
        alert('Корзина пуста! Добавьте товары для заказа.');
        return;
    }
    
    const modal = document.getElementById('checkout-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

/**
 * Закрыть форму оформления
 */
function closeCheckoutForm() {
    const modal = document.getElementById('checkout-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Обработка отправки формы заказа
 */
function handleCheckoutSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const orderData = {
        name: formData.get('name').trim(),
        room: formData.get('room').trim(),
        telegram: formData.get('telegram').trim()
    };
    
    // Валидация
    if (!orderData.name || orderData.name.length < 2) {
        alert('Пожалуйста, укажите ваше имя');
        return;
    }
    
    if (!orderData.room || orderData.room.length < 1) {
        alert('Пожалуйста, укажите номер комнаты');
        return;
    }
    
    // Отправляем заказ
    sendOrderToBot(orderData);
}

/**
 * Показать индикатор загрузки
 */
function showLoading(show) {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
    
    const submitBtn = document.querySelector('#checkout-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = show;
        submitBtn.textContent = show ? 'Отправка...' : 'Оформить заказ';
    }
}

/**
 * Показать сообщение об успехе
 */
function showSuccess(orderId) {
    closeCheckoutForm();
    
    const message = `
        ✅ Заказ #${orderId} успешно оформлен!
        
        Вы получите уведомление в Telegram.
        Для проверки статуса напишите боту @pelikan_alakol_bot команду:
        /status ${orderId}
        
        Оплата при получении в баре.
    `;
    
    alert(message);
    
    // Можно также показать красивое модальное окно
    // showModal('Заказ оформлен', message, 'success');
}

/**
 * Показать сообщение об ошибке
 */
function showError(errorMessage) {
    alert(`❌ Ошибка при оформлении заказа:\n${errorMessage}\n\nПопробуйте ещё раз или свяжитесь с администратором.`);
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем корзину из localStorage
    loadCartFromLocalStorage();
    
    // Обработчик формы оформления заказа
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', handleCheckoutSubmit);
    }
    
    // Закрытие модального окна по клику вне формы
    const modal = document.getElementById('checkout-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeCheckoutForm();
            }
        });
    }
    
    // Клавиша Escape для закрытия модального окна
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeCheckoutForm();
        }
    });
    
    console.log('Интеграция с Telegram ботом загружена');
});

// Экспорт функций для использования в HTML
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateQuantity = updateQuantity;
window.showCheckoutForm = showCheckoutForm;
window.closeCheckoutForm = closeCheckoutForm;
window.clearCart = clearCart;
