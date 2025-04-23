let stripe;
let elements;

function initializeCheckout(stripePublicKey, clientSecret) {
    stripe = Stripe(stripePublicKey);
    elements = stripe.elements({
        clientSecret: clientSecret,
        appearance: {
            theme: 'stripe'
        }
    });

    const paymentElement = elements.create('payment');
    paymentElement.mount('#payment-element');
}

// Handle the form submission
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('payment-form');
    const messageContainer = document.querySelector('#payment-errors');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        // Show spinner and disable button
        const submitButton = document.querySelector('#submit-button');
        const buttonText = document.querySelector('#button-text');
        const spinner = document.querySelector('#spinner');

        submitButton.disabled = true;
        buttonText.classList.add('d-none');
        spinner.classList.remove('d-none');
        messageContainer.classList.add('d-none');

        try {
            const { error } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    return_url: `${window.location.origin}/confirmation`,
                }
            });

            if (error) {
                // Handle payment error
                messageContainer.textContent = error.message;
                messageContainer.classList.remove('d-none');
                submitButton.disabled = false;
                buttonText.classList.remove('d-none');
                spinner.classList.add('d-none');
            }
            // Don't need an else clause - confirmPayment will redirect on success with payment_intent in the URL
        } catch (error) {
            // Handle unexpected errors
            messageContainer.textContent = 'An unexpected error occurred. Please try again.';
            messageContainer.classList.remove('d-none');
            submitButton.disabled = false;
            buttonText.classList.remove('d-none');
            spinner.classList.add('d-none');
        }
    });
}); 