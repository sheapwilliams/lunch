// Handle the form submission
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    // Show spinner and disable button
    const submitButton = document.querySelector('#submit-button');
    const buttonText = document.querySelector('#button-text');
    const spinner = document.querySelector('#spinner');
    const messageContainer = document.querySelector('#error-message');
    
    submitButton.disabled = true;
    buttonText.classList.add('d-none');
    spinner.classList.remove('d-none');
    messageContainer.classList.add('d-none');
    
    try {
        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: `${window.location.origin}/confirmation?payment_intent={PAYMENT_INTENT}`,
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
        // Don't need an else clause - confirmPayment will redirect on success
    } catch (error) {
        // Handle unexpected errors
        messageContainer.textContent = 'An unexpected error occurred. Please try again.';
        messageContainer.classList.remove('d-none');
        submitButton.disabled = false;
        buttonText.classList.remove('d-none');
        spinner.classList.add('d-none');
    }
}); 