// Initialize cart from server data
const cart = JSON.parse(document.getElementById('cart-data').textContent);
const lunchOptions = JSON.parse(document.getElementById('lunch-options-data').textContent);

function updateCartDisplay() {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = Object.keys(cart).length;
    }
}

// Update cart count on page load
updateCartDisplay(); 