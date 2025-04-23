// Handle the form submission
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const { error: submitError } = await stripe.confirmPayment({
        elements,
        confirmParams: {
            return_url: `${window.location.origin}/confirmation`,
        },
        redirect: "if_required"
    });

    if (submitError) {
        const messageContainer = document.querySelector('#error-message');
        messageContainer.textContent = submitError.message;
        return;
    }

    // Payment successful, get the payment intent ID
    const { paymentIntent } = await stripe.retrievePaymentIntent(clientSecret);
    
    // Send the payment intent ID to the backend
    try {
        const response = await fetch('/confirm-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                payment_intent_id: paymentIntent.id
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = '/confirmation';
        } else {
            const messageContainer = document.querySelector('#error-message');
            messageContainer.textContent = result.error || 'An error occurred during payment confirmation';
        }
    } catch (error) {
        const messageContainer = document.querySelector('#error-message');
        messageContainer.textContent = 'An error occurred during payment confirmation';
    }
}); 