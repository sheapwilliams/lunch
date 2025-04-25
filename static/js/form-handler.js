// Handle form submission on Enter key press in password field
document.addEventListener('DOMContentLoaded', function() {
    const passwordField = document.getElementById('password');
    if (passwordField) {
        passwordField.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const form = document.getElementById('loginForm') || document.getElementById('registerForm');
                if (form) {
                    form.submit();
                }
            }
        });
    }
}); 