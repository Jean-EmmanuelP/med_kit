<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { loadStripe, type Stripe, type StripeElements, type StripePaymentElement } from '@stripe/stripe-js';
	import { onMount, tick } from 'svelte';
	import { i18n } from '$lib/i18n';
    import { fade } from 'svelte/transition';

	const stripePublicKey = env.PUBLIC_STRIPE_KEY;

	// --- Component State ---
	let stripe: Stripe | null = null;
	let elements: StripeElements | null = null;
	let paymentElement: StripePaymentElement | null = null;
	let isLoadingStripe = $state(true); // Loading Stripe library
	let isProcessingPayment = $state(false); // Processing the actual donation
	let errorMessage = $state('');
	let successMessage = $state('');
    let clientSecret = $state<string | null>(null);
    let currentAmount = $state(10); // Default donation amount in EUR
    let customAmountInput = $state('');
    let isCustomAmountConfirmed = $state(false); // Track if the current amount is from confirmed custom input
    const presetAmounts = [5, 10, 20, 50];

	// --- Stripe Initialization ---
	onMount(async () => {
		if (!stripePublicKey) {
			errorMessage = $i18n.donations.errors.stripeKeyMissing;
			isLoadingStripe = false;
			return;
		}
		try {
			stripe = await loadStripe(stripePublicKey);
			isLoadingStripe = false;
            // Initial creation of Payment Intent with default amount
            await createPaymentIntent(currentAmount * 100); // Convert EUR to cents
		} catch (error: any) {
			console.error("Stripe loading Error:", error);
			errorMessage = error.message || $i18n.donations.errors.stripeLoadFailed;
			isLoadingStripe = false;
		}
	});

    // --- Create/Update Payment Intent ---
    async function createPaymentIntent(amountInCents: number) {
        if (!stripe || amountInCents <= 0) {
            // console.warn("Stripe not loaded or invalid amount, skipping PI creation.");
            return;
        }

        // Destroy existing elements if they exist to avoid conflicts
        if (paymentElement) {
            paymentElement.destroy();
            paymentElement = null;
            elements = null; // Reset elements object as well
        }

        isProcessingPayment = true; // Use this to show loading state for PI creation
        errorMessage = '';
        successMessage = '';

        try {
            const res = await fetch('/api/create-donation-intent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amountInCents }) // Send amount in cents
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ message: `HTTP error ${res.status}` }));
                throw new Error(errorData.message || `Failed to create payment intent (${res.status})`);
            }

            const { clientSecret: newClientSecret } = await res.json();

            if (!newClientSecret) {
                 throw new Error($i18n.donations.errors.clientSecretMissing);
            }

            clientSecret = newClientSecret; // Store the client secret

            // Now initialize Elements with the new client secret
            initializeStripeElements(clientSecret);

        } catch (error: any) {
            console.error("Payment Intent Creation/Update Error:", error);
            errorMessage = error.message || $i18n.donations.errors.intentCreationFailed;
            clientSecret = null; // Reset client secret on error
            isProcessingPayment = false; // Stop loading on error
        }
        // isProcessingPayment will be set to false inside initializeStripeElements's 'ready' event
    }

    // --- Initialize Stripe Elements ---
    async function initializeStripeElements(secret: string) {
        if (!stripe || elements) { // Only initialize if Stripe is loaded and elements aren't already there
             // console.log("Skipping element initialization (Stripe not loaded or elements exist)");
             return;
        }
        // console.log("Initializing Stripe Elements with clientSecret:", secret);

        const appearance = {
            theme: 'night',
            labels: 'floating',
            variables: {
                colorPrimary: '#ea580c', // orange-600
                colorBackground: '#1f2937', // gray-800
                colorText: '#e5e7eb', // gray-200
                colorDanger: '#f87171', // red-400
                fontFamily: 'Ideal Sans, system-ui, sans-serif',
                spacingUnit: '4px',
                borderRadius: '6px',
            }
        };
        elements = stripe.elements({ clientSecret: secret, appearance, locale: "fr" });

        paymentElement = elements.create('payment', {
            layout: "tabs", // or "accordion"
            fields: {
                billingDetails: {
                    address: {
                        country: 'never', // Don't collect full address unless needed
                    }
                }
            }
        });
        paymentElement.mount('#payment-element');

        paymentElement.on('ready', () => {
            console.log('Payment Element is ready.');
            isProcessingPayment = false; // Payment element is ready, stop the loading state
            // Ensure the payment element is visible now
             const paymentElContainer = document.getElementById('payment-element');
             if (paymentElContainer) paymentElContainer.style.display = 'block';
        });

        paymentElement.on('change', (event) => {
            if (event.error) {
                errorMessage = event.error.message;
                successMessage = '';
            } else {
                errorMessage = '';
            }
        });

        await tick(); // Ensure Svelte updates the DOM
    }


    // --- Handle Amount Selection ---
    function selectAmount(amount: number) {
        if (isProcessingPayment) return; // Prevent changes while processing
        currentAmount = amount;
        isCustomAmountConfirmed = false; // Reset custom confirmation flag
        customAmountInput = ''; // Clear custom input when preset is clicked
        createPaymentIntent(amount * 100);
    }

    // --- Handle Custom Amount Input ---
    function handleCustomAmountChange(event: Event) {
        if (isProcessingPayment) return; // Prevent changes while processing
        const input = event.target as HTMLInputElement;
        const value = input.value.replace(/,/g, '.'); // Allow comma as decimal separator
        const numericValue = parseFloat(value);
        isCustomAmountConfirmed = false; // Input changed, needs reconfirmation

        if (value === '') {
            // Maybe clear currentAmount or revert to last valid? For now, just update input.
            errorMessage = '';
        } else if (isNaN(numericValue) || numericValue < 0.5) { // Use Stripe minimum (e.g., 0.50 EUR)
            errorMessage = $i18n.donations.errors.invalidAmount;
            // Don't update currentAmount yet, wait for confirmation
        } else {
            errorMessage = '';
            // DO NOT update PI here anymore
        }
        // Keep customAmountInput reflecting user's raw input for display
        customAmountInput = input.value;
    }

    // --- NEW: Confirm Custom Amount ---
    function confirmCustomAmount() {
        if (isProcessingPayment) return;
        const value = customAmountInput.replace(/,/g, '.');
        const numericValue = parseFloat(value);

        if (!isNaN(numericValue) && numericValue >= 0.50) { // Check valid minimum amount
            currentAmount = numericValue;
            isCustomAmountConfirmed = true;
            createPaymentIntent(Math.round(numericValue * 100));
        } else {
            errorMessage = $i18n.donations.errors.invalidAmount;
        }
    }

    // --- Handle Payment Submission ---
    async function handleSubmit() {
        if (!stripe || !elements || !paymentElement || isProcessingPayment || !clientSecret) {
            if (!stripe || !elements) errorMessage = $i18n.donations.errors.stripeNotReady;
            else if (!paymentElement) errorMessage = $i18n.donations.errors.paymentElementNotReady;
            else if (!clientSecret) errorMessage = $i18n.donations.errors.intentCreationFailed; // Should have been caught earlier
            else errorMessage = $i18n.donations.processing; // Already processing
            return;
        }
        // Check if a custom amount was entered but not confirmed
        if (customAmountInput !== '' && !isCustomAmountConfirmed) {
            errorMessage = $i18n.donations.errors.confirmCustomAmount || "Veuillez valider le montant personnalisé."; // Add to i18n
            return;
        }
        if (currentAmount < 0.50) { // Check minimum amount
            errorMessage = $i18n.donations.errors.selectAmount;
            return;
        }

        isProcessingPayment = true;
        errorMessage = '';
        successMessage = '';

        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                // Use window.location.origin for dynamic return URL
                return_url: `${window.location.origin}/donation-status`, // Create this status page
                payment_method_data: {
                    billing_details: {
                        // Optionally prefill name/email if user is logged in
                        // name: loggedInUserName,
                        // email: loggedInUserEmail,
                        address: {
                            country: 'FR' // Provide the country code since we set 'never' in fields
                        }
                    }
                }
            },
        });

        if (error) {
            console.error("Stripe confirmation error:", error);
            errorMessage = error.message || $i18n.donations.errors.paymentFailed;
            isProcessingPayment = false;
        } else {
            // Success will be handled by the redirect to return_url
            successMessage = $i18n.donations.redirecting;
            // Button remains disabled as redirection is expected
        }
    }

</script>

<div class="donation-form-container text-white">

    {#if isLoadingStripe}
        <div class="loading-indicator">{$i18n.donations.loadingStripe}...</div>
    {:else}
        <form id="donation-form" on:submit|preventDefault={handleSubmit}>
            <!-- Amount Selection -->
            <div class="mb-6">
                <label class="mb-3 block text-lg font-semibold text-gray-200">{$i18n.donations.chooseAmount}</label>
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {#each presetAmounts as amount}
                        <button
                            type="button"
                            on:click={() => selectAmount(amount)}
                            class="rounded-md border-2 px-4 py-3 text-center font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800"
                            class:border-orange-500={currentAmount === amount && customAmountInput === ''}
                            class:bg-orange-600={currentAmount === amount && customAmountInput === ''}
                            class:text-white={currentAmount === amount && customAmountInput === ''}
                            class:border-gray-600={!(currentAmount === amount && customAmountInput === '')}
                            class:hover:border-orange-400={currentAmount !== amount || customAmountInput !== ''}
                            class:hover:bg-gray-700={currentAmount !== amount || customAmountInput !== ''}
                            class:text-gray-300={!(currentAmount === amount && customAmountInput === '')}
                            disabled={isProcessingPayment}
                        >
                            {amount} €
                        </button>
                    {/each}
                </div>
                <div class="mt-4 flex items-center gap-2">
                    <label for="custom-amount" class="sr-only">{$i18n.donations.customAmountLabel}</label>
                    <div class="relative flex-grow">
                        <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">€</span>
                        <input
                            type="text"
                            id="custom-amount"
                            inputmode="decimal"
                            placeholder={$i18n.donations.customAmountPlaceholder}
                            value={customAmountInput}
                            on:input={handleCustomAmountChange}
                            class="w-full rounded-md border-2 bg-gray-700 py-3 pl-8 pr-4 text-white placeholder-gray-400 transition-colors duration-200 focus:z-10 focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:ring-offset-0"
                            class:border-orange-500={customAmountInput !== '' && isCustomAmountConfirmed}
                            class:border-gray-600={customAmountInput === ''}
                            class:border-yellow-500={customAmountInput !== '' && !isCustomAmountConfirmed}
                            disabled={isProcessingPayment}
                        />
                    </div>
                    <button
                        type="button"
                        on:click={confirmCustomAmount}
                        class="shrink-0 rounded-md border-2 bg-gray-600 px-4 py-3 font-medium text-white transition-colors hover:bg-gray-500 focus:z-10 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-60"
                        class:border-orange-500={customAmountInput !== '' && isCustomAmountConfirmed}
                        class:border-gray-600={customAmountInput === ''}
                        class:border-yellow-500={customAmountInput !== '' && !isCustomAmountConfirmed}
                        disabled={isProcessingPayment || customAmountInput === '' || (customAmountInput !== '' && parseFloat(customAmountInput.replace(/,/g, '.')) < 0.50) || isCustomAmountConfirmed}
                        title={$i18n.donations.confirmCustomAmount || 'Valider ce montant'}
                    >
                        {$i18n.donations.validateButton || 'OK'}
                    </button>
                </div>
            </div>

            {#if errorMessage}
                 <div class="mb-4 rounded-md bg-red-900/50 p-3 text-center text-sm text-red-300" role="alert" transition:fade>
                    {errorMessage}
                 </div>
            {/if}

             {#if successMessage}
                 <div class="mb-4 rounded-md bg-green-900/50 p-3 text-center text-sm text-green-300" role="status" transition:fade>
                    {successMessage}
                 </div>
            {/if}


            <!-- Payment Element -->
            <div class="mb-6">
                <label class="mb-3 block text-lg font-semibold text-gray-200">{$i18n.donations.paymentDetails}</label>
                {#if isProcessingPayment && !paymentElement}
                    <div class="loading-indicator">{$i18n.donations.loadingPayment}...</div>
                {/if}
                <div id="payment-element" class="payment-element-style" style:display={isProcessingPayment && !paymentElement ? 'none' : 'block'}>
                    <!-- Stripe Payment Element will mount here -->
                </div>
            </div>

            <!-- Submit Button -->
            <button
                type="submit"
                disabled={isLoadingStripe || isProcessingPayment || !stripe || !elements || currentAmount < 0.50 || (customAmountInput !== '' && !isCustomAmountConfirmed)}
                class="w-full rounded-lg bg-orange-600 px-6 py-3 text-lg font-semibold text-white shadow-md transition-all duration-300 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-70"
            >
                {#if isProcessingPayment}
                    <span class="flex items-center justify-center">
                        <svg class="mr-2 h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {$i18n.donations.processing}...
                    </span>
                {:else}
                    {#if currentAmount >= 0.50}
                        {$i18n.donations.donateButton} {currentAmount.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
                    {:else}
                        {$i18n.donations.donateButtonFallback}
                    {/if}
                {/if}
            </button>
        </form>
    {/if}

</div>

<style>
    .loading-indicator {
        text-align: center;
        padding: 2rem 1rem;
        color: #aaa;
        background-color: #2a2a2a;
        border-radius: 6px;
        margin-bottom: 1.5rem;
    }
    .payment-element-style {
        padding: 1rem;
        border: 1px solid #4b5563; /* gray-600 */
        border-radius: 6px;
        background-color: #1f2937; /* gray-800 based on appearance */
        min-height: 180px; /* Adjust as needed */
    }
</style>