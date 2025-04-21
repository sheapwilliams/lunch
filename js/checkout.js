function initializeCheckout(stripePublicKey, clientSecret) {
    console.log('Checkout page JavaScript loading...');
    
    // Verify elements exist
    const form = document.getElementById('payment-form');
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    const paymentErrors = document.getElementById('payment-errors');
    
    console.log('Form element:', form);
    console.log('Submit button:', submitButton);
    console.log('Button text:', buttonText);
    console.log('Spinner:', spinner);
    console.log('Payment errors:', paymentErrors);
    
    if (!form || !submitButton || !buttonText || !spinner || !paymentErrors) {
        console.error('One or more required elements not found!');
        return;
    }

    console.log('Stripe public key:', stripePublicKey);
    console.log('Client secret:', clientSecret);
    
    const stripe = Stripe(stripePublicKey);
    const elements = stripe.elements({
        clientSecret: clientSecret,
        appearance: {
            theme: 'stripe',
        },
    });
    
    const paymentElement = elements.create('payment');
    paymentElement.mount('#payment-element');

    form.addEventListener('submit', async (event) => {
        console.log('Form submit event triggered');
        event.preventDefault();
        
        // Show spinner and disable button
        submitButton.disabled = true;
        buttonText.classList.add('d-none');
        spinner.classList.remove('d-none');
        paymentErrors.classList.add('d-none');

        try {
            console.log('Confirming payment...');
            const {error, paymentIntent} = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    return_url: window.location.origin + '/confirmation',
                },
                redirect: 'if_required'
            });

            if (error) {
                console.error('Payment error:', error);
                // Show error and reset button state
                paymentErrors.textContent = error.message;
                paymentErrors.classList.remove('d-none');
                submitButton.disabled = false;
                buttonText.classList.remove('d-none');
                spinner.classList.add('d-none');
            } else if (paymentIntent && paymentIntent.status === 'succeeded') {
                // Payment succeeded, redirect to confirmation page
                window.location.href = '/confirmation';
            } else {
                // Payment requires additional action
                console.log('Payment requires additional action:', paymentIntent);
                paymentErrors.textContent = 'Payment requires additional verification. Please check your email or try a different payment method.';
                paymentErrors.classList.remove('d-none');
                submitButton.disabled = false;
                buttonText.classList.remove('d-none');
                spinner.classList.add('d-none');
            }
        } catch (error) {
            console.error('Unexpected error:', error);
            // Show error and reset button state
            paymentErrors.textContent = 'An error occurred. Please try again.';
            paymentErrors.classList.remove('d-none');
            submitButton.disabled = false;
            buttonText.classList.remove('d-none');
            spinner.classList.add('d-none');
        }
    });
    
    console.log('Event listener attached');
} 