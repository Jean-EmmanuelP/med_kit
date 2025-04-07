<!-- src/lib/components/CheckoutForm.svelte -->
<script>
    import { env } from '$env/dynamic/public';
    import { loadStripe } from '@stripe/stripe-js';
    import { onMount, tick } from 'svelte';

    const stripePublicKey = env.PUBLIC_STRIPE_KEY;

    // --- Component State ---
    let stripe = null;
    let elements = null;
    let paymentElement = null;
    let isLoadingStripe = true; // Loading Stripe library itself
    let isCreatingIntent = false;
    let errorMessage = '';
    let paymentProcessing = false;
    let selectedPlan = null; // 'monthly' or 'yearly'

    // --- Plan Details (customize as needed) ---
    const plans = {
        monthly: {
            id: 'monthly',
            name: 'Mensuel',
            price: 1.99, // Base price for display and calculation
            priceString: '€1.99',
            frequency: 'par mois',
            priceIdEnvVar: 'STRIPE_MONTHLY_PRICE_ID' // Reference for backend lookup
        },
        yearly: {
            id: 'yearly',
            name: 'Annuel',
            price: 19.99, // Actual yearly price
            priceString: '€19.99',
            frequency: 'par an',
            originalMonthlyTotal: (1.99 * 12).toFixed(2), // Calculate for strikethrough
            priceIdEnvVar: 'STRIPE_YEARLY_PRICE_ID' // Reference for backend lookup
        },
    };

    // --- Stripe Initialization ---
    onMount(async () => {
        if (!stripePublicKey) {
            errorMessage = 'Stripe publishable key not set.';
            isLoadingStripe = false;
            return;
        }
        try {
            stripe = await loadStripe(stripePublicKey);
            isLoadingStripe = false;
        } catch (error) {
            console.error("Stripe loading Error:", error);
            errorMessage = error.message || 'Failed to load Stripe.';
            isLoadingStripe = false;
        }
    });

    // --- Select Plan Function ---
    function selectPlan(planId) {
        if (isCreatingIntent || paymentProcessing) return; // Don't change plan while processing
        if (selectedPlan === planId) return; // Don't re-init if already selected

        console.log("Selected plan:", planId);
        selectedPlan = planId;
        // Reset previous elements if plan changes
        if (paymentElement) {
            paymentElement.destroy();
            paymentElement = null;
            elements = null;
        }
        errorMessage = ''; // Clear previous errors specific to element creation
        // Trigger element initialization via reactive statement below
    }


    // --- Create Payment Intent/Subscription when Plan is Selected ---
    async function initializeStripeElements() {
        // Guard conditions
        if (!stripe || !selectedPlan || isCreatingIntent || elements) {
            if (!stripe) console.warn("Stripe not loaded yet");
            if (!selectedPlan) console.warn("No plan selected");
            if (isCreatingIntent) console.warn("Intent creation already in progress");
            if (elements) console.warn("Elements already initialized for this plan");
            return;
        }

        isCreatingIntent = true;
        errorMessage = ''; // Clear previous errors

        console.log(`Initializing elements for plan: ${selectedPlan}`);

        try {
            const res = await fetch('/api/create-payment-intent', { // Or '/api/create-subscription'
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // Send the *identifier* ('monthly' or 'yearly'), backend uses env vars
                body: JSON.stringify({ plan: selectedPlan })
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ message: `HTTP error ${res.status}` }));
                throw new Error(errorData.message || `Failed to create subscription (${res.status})`);
            }

            const { clientSecret } = await res.json();

            if (!clientSecret) {
                 throw new Error('Missing clientSecret from server response.');
            }

            elements = stripe.elements({ clientSecret, appearance: { theme: 'night', labels: 'floating' }, locale: "fr" }); // Use night theme
            paymentElement = elements.create('payment');
            paymentElement.mount('#payment-element');

            // Add event listener for when the element is ready (optional, but good for UX)
            paymentElement.on('ready', () => {
                 console.log('Payment Element is ready.');
                 isCreatingIntent = false; // Element is ready, stop the "creating intent" state
            });

            // Add listener for validation errors within the element
            paymentElement.on('change', (event) => {
                if (event.error) {
                    errorMessage = event.error.message;
                } else {
                    errorMessage = ''; // Clear error if corrected
                }
            });


            // Wait a tick ensures Svelte updates the DOM *before* we potentially stop loading
            // However, the 'ready' event is more reliable for the element itself.
            await tick();


        } catch (error) {
            console.error("Initialization Error:", error);
            errorMessage = error.message || 'Failed to initialize payment details.';
            elements = null; // Reset on error
            paymentElement = null; // Reset on error
            isCreatingIntent = false; // Stop loading on error
        }
        // Note: isCreatingIntent is set to false inside the 'ready' event handler for better UX
    }

    // --- Reactive Trigger for Initialization ---
    // Run initializeStripeElements whenever selectedPlan changes (and meets conditions)
    $: if (selectedPlan && stripe && !isLoadingStripe && !elements && !isCreatingIntent) {
       initializeStripeElements();
    }


    // --- Handle Payment Submission ---
    async function handleSubmit() {
        // Add checks for isCreatingIntent and paymentElement readiness
        if (!stripe || !elements || paymentProcessing || isCreatingIntent || !paymentElement) {
            if (isCreatingIntent) errorMessage = "Please wait, initializing payment details...";
            else if (!paymentElement) errorMessage = "Please select a plan to load payment details.";
            else errorMessage = "Payment system not ready.";
            return;
        }

        paymentProcessing = true;
        errorMessage = ''; // Clear previous errors before attempting submission

        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: `${window.location.origin}/payment-status`,
            },
        });

        if (error) {
            // Errors like network issues, invalid card details *not caught by element validation*
            console.error("Stripe confirmation error:", error);
            errorMessage = error.message || 'An unexpected error occurred during payment.';
            paymentProcessing = false; // Re-enable button only on explicit submission error
        }
        // If no error, redirection should happen. Button remains disabled.
    }

</script>

<div class="checkout-container">

    {#if isLoadingStripe}
        <p class="loading-text">Chargement ...</p>
    {:else if !selectedPlan}
        <h3 class="instruction-text">Choisissez votre plan:</h3>
    {/if}

    <!-- Plan Selection Boxes -->
    <div class="plan-selection-cards" class:hidden={isLoadingStripe}>
        <!-- Monthly Plan Card -->
        <div
            class="plan-card"
            class:selected={selectedPlan === plans.monthly.id}
            on:click={() => selectPlan(plans.monthly.id)}
            role="button"
            tabindex="0"
            on:keydown={(e) => e.key === 'Enter' && selectPlan(plans.monthly.id)}
        >
            <h4>{plans.monthly.name}</h4>
            <div class="price">{plans.monthly.priceString}</div>
            <div class="frequency">{plans.monthly.frequency}</div>
        </div>

        <!-- Yearly Plan Card -->
        <div
            class="plan-card"
            class:selected={selectedPlan === plans.yearly.id}
            on:click={() => selectPlan(plans.yearly.id)}
            role="button"
            tabindex="0"
            on:keydown={(e) => e.key === 'Enter' && selectPlan(plans.yearly.id)}
        >
            <span class="savings-badge">Économisez!</span>
            <h4>{plans.yearly.name}</h4>
            <div class="price">{plans.yearly.priceString}</div>
            <div class="frequency">{plans.yearly.frequency}</div>
            <div class="original-price">
                <s>€{plans.yearly.originalMonthlyTotal}</s>
                <!-- <span class="frequency"> (si payé mensuellement)</span> -->
            </div>
        </div>
    </div>

    {#if errorMessage}
        <div class="error-message" role="alert">{errorMessage}</div>
    {/if}

    <!-- Payment Form Area -->
    {#if selectedPlan}
        <form id="payment-form" on:submit|preventDefault={handleSubmit} class:fade-in={paymentElement}>

            {#if isCreatingIntent}
                <div class="loading-payment-element">Initialisation du paiement ...</div>
            {/if}

            <!-- Stripe Payment Element will be inserted here -->
            <div id="payment-element" class:hidden={isCreatingIntent}></div>

            <button
                type="submit"
                disabled={isLoadingStripe || isCreatingIntent || !stripe || !elements || paymentProcessing || !paymentElement}
                class:processing={paymentProcessing}
            >
                {#if paymentProcessing}
                    Traitement...
                {:else if isCreatingIntent}
                    Chargement...
                {:else}
                    S'abonner {selectedPlan == "monthly" ? "mensuellement" : 'annuellement'}
                {/if}
            </button>
        </form>
    {/if}

</div>
<style>
    /* Base styles */
    :global(body) { /* Apply base dark background to body */
       background-color: #121212; /* Dark background */
       color: #e0e0e0; /* Light text */
       font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
       display: flex;
       justify-content: center;
       align-items: flex-start; /* Align to top */
       min-height: 100vh;
       padding-top: 2rem; /* Add some space at the top */
       box-sizing: border-box;
    }

    .checkout-container {
        background-color: #1e1e1e; /* Slightly lighter dark shade for the container */
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        width: 100%;
        max-width: 480px; /* Control max width */
        margin: 0 auto; /* Center horizontally */
        box-sizing: border-box;
    }

    .loading-text, .instruction-text {
        text-align: center;
        margin-bottom: 1.5rem;
        color: #b0b0b0;
    }

    .instruction-text {
        font-size: 1.2rem;
        font-weight: 500;
    }

    /* Plan Selection Cards */
    .plan-selection-cards {
        display: flex;
        gap: 1rem; /* Space between cards */
        margin-bottom: 2rem;
    }

    .plan-card {
        flex: 1; /* Each card takes equal space */
        background-color: #2a2a2a; /* Card background */
        border: 2px solid #444; /* Subtle border */
        border-radius: 6px;
        padding: 1.5rem 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        position: relative; /* For badge positioning */
    }

    .plan-card:hover {
        background-color: #333;
        border-color: #666;
        transform: translateY(-3px); /* Slight lift on hover */
    }

    .plan-card.selected {
        border-color: #ea580c; /* orange-600 */
        background-color: #4d280a; /* Darker orange-ish background */
        box-shadow: 0 0 15px rgba(234, 88, 12, 0.3); /* orange-600 shadow */
    }

    .plan-card h4 {
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
    }

    .plan-card .price {
        font-size: 1.9rem;
        font-weight: bold;
        color: #ea580c; /* orange-600 */
        margin-bottom: 0.2rem;
        line-height: 1.1;
    }

    .plan-card .frequency {
        font-size: 0.85rem;
        color: #aaa;
        margin-bottom: 0.8rem;
    }

    .plan-card .original-price {
        font-size: 0.85rem;
        color: #888;
        margin-top: 0.5rem;
    }
     .plan-card .original-price .frequency {
         display: inline; /* Keep on same line as strikethrough */
         margin-bottom: 0;
     }

    .plan-card .savings-badge {
        position: absolute;
        top: -10px;
        right: -10px;
        background-color: #03dac6; /* Teal accent (contrasts well with orange) */
        color: #121212; /* Dark text on light badge */
        padding: 0.3em 0.7em;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        line-height: 1;
    }


    /* Form Styling */
    #payment-form {
       margin-top: 1.5rem;
       opacity: 0; /* Start hidden for fade-in */
       transition: opacity 0.5s ease-in-out;
    }

    #payment-form.fade-in {
        opacity: 1;
    }

    .loading-payment-element {
        text-align: center;
        padding: 2rem 1rem;
        color: #aaa;
        background-color: #2a2a2a;
        border-radius: 6px;
        margin-bottom: 1.5rem;
    }

    #payment-element {
        margin-bottom: 1.5rem;
        /* Stripe's Appearance API (theme: night) will handle most styling */
        /* Add min-height if it collapses weirdly during load */
         min-height: 150px;
         padding: 10px; /* Minimal padding for structure */
         border: 1px solid #444; /* Match card border */
         border-radius: 6px;
         background-color: #2a2a2a; /* Match card background */
    }
    #payment-element.hidden {
        display: none;
    }

    /* Error Message */
    .error-message {
        color: #cf6679; /* Material Design dark theme error color */
        background-color: rgba(207, 102, 121, 0.1); /* Subtle error background */
        border: 1px solid #cf6679;
        padding: 0.8em 1em;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }

    /* Button */
    button {
        /* Orange gradient: orange-500 (#f97316) to orange-700 (#c2410c) */
        background: linear-gradient(to right, #f97316, #c2410c);
        color: white;
        font-family: inherit;
        font-size: 1rem;
        font-weight: 600;
        border: none;
        padding: 12px 16px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: block;
        width: 100%;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3); /* Add slight shadow for contrast */
    }
    button:hover:not(:disabled) {
        filter: brightness(1.1);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background: #555; /* Darker disabled state */
        box-shadow: none;
        text-shadow: none;
    }
    button.processing {
        /* Optional: add specific styles for processing state */
         opacity: 0.7;
    }

    /* Utility */
    .hidden {
        display: none;
    }

</style>