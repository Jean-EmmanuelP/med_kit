<script lang="ts">
    import { env } from '$env/dynamic/public';
    import { loadStripe, type Stripe, type StripeElements, type StripePaymentElement, type StripeIbanElement, type StripePaymentRequest, type StripePaymentRequestButtonElement, type PaymentRequest } from '@stripe/stripe-js';
    import { onMount, tick } from 'svelte';
    import { i18n } from '$lib/i18n';
    import { fade } from 'svelte/transition';
    import { Copy, Check, AlertCircle } from 'lucide-svelte';

    // --- Config ---
    const stripePublicKey = env.PUBLIC_STRIPE_KEY;
    const DEFAULT_DONATION_EUR = 10;
    const presetAmounts = [5, 10, 20, 50];

    // --- Stripe State ---
    let stripe: Stripe | null = null;
    let elements: StripeElements | null = null; // General elements instance
    let cardElement: StripePaymentElement | null = null; // Specifically for card
    let ibanElement: StripeIbanElement | null = null; // Specifically for SEPA
    let prButton: PaymentRequest | null = null; // For Apple/Google Pay
    let paymentRequest: StripePaymentRequest | null = null;

    // --- Payment Intent State ---
    // Store secrets separately based on the intent type requested
    let clientSecretCard: string | null = $state(null);
    let clientSecretSepa: string | null = $state(null);
    // Keep track of which secret is currently active for element mounting/confirmation
    let activeClientSecret: string | null = $state(null);
    let activePaymentMethodType: 'card' | 'sepa_debit' | 'wallet' | null = $state(null);

    // --- UI & Form State ---
    let isLoadingStripe = $state(true);
    let isProcessingPayment = $state(false); // For confirmations
    let isLoadingPI = $state(false); // For PI creation
    let errorMessage = $state('');
    let successMessage = $state(''); // Not used in this flow (redirects)
    let currentAmount = $state(DEFAULT_DONATION_EUR);
    let customAmountInput = $state('');
    let isCustomAmountConfirmed = $state(false);
    let showCardForm = $state(false);
    let showSepaForm = $state(false);
    let canMakePrPayment = $state(false); // Availability of Apple/Google Pay
    let sepaMandateAccepted = $state(false); // Checkbox for SEPA mandate
    let sepaAccountHolderName = $state(''); // SEPA Account Holder Name

     // --- Share Text State ---
    let copyStatus = $state<'idle' | 'copied' | 'error'>('idle');
    let copyTimeoutId: ReturnType<typeof setTimeout> | null = null;
    const shareText = `🩺 Tu connais Veille Médicale ?
C'est un nouvel outil de veille scientifique qui t'envoie tous les articles essentiels de ta spécialité.
Déjà +1000 soignants inscrits.
Je recommande 👌
👉 https://veillemedicale.fr`;

    async function handleCopyShareText() {
        if (copyStatus === 'copied') return; // Don't do anything if already copied recently

        try {
            await navigator.clipboard.writeText(shareText);
            copyStatus = 'copied';
            console.log('Share text copied to clipboard');

            // Reset status after a delay
            if (copyTimeoutId) clearTimeout(copyTimeoutId); // Clear previous timeout if any
            copyTimeoutId = setTimeout(() => {
                copyStatus = 'idle';
                copyTimeoutId = null;
            }, 2000); // Reset after 2 seconds

        } catch (err) {
            copyStatus = 'error';
            console.error('Failed to copy share text:', err);
            // Optionally show an error message to the user
             if (copyTimeoutId) clearTimeout(copyTimeoutId);
             copyTimeoutId = setTimeout(() => {
                copyStatus = 'idle';
                copyTimeoutId = null;
            }, 3000); // Show error longer
        }
    }

    // --- Helper Functions ---
    function getAmountInCents(): number {
        if (customAmountInput && isCustomAmountConfirmed) {
            const val = parseFloat(customAmountInput.replace(/,/g, '.'));
            return Math.round(val * 100);
        }
        return currentAmount * 100;
    }

    // --- Create/Update Payment Intent (Handles Different Types) ---
    async function createOrUpdatePI(type: 'card' | 'sepa_debit') {
        const amountCents = getAmountInCents();
        if (amountCents < 50) {
            errorMessage = $i18n.donations.errors.invalidAmount;
            return null; // Don't proceed if amount is invalid
        }

        isLoadingPI = true;
        errorMessage = ''; // Clear previous errors
        let newClientSecret: string | null = null;

        try {
            console.log(`Requesting PI for type: ${type}, amount: ${amountCents}`);
            const res = await fetch('/api/create-donation-intent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amountCents, paymentMethodType: type })
            });
            if (!res.ok) {
                 const errorData = await res.json().catch(() => ({ message: `HTTP error ${res.status}` }));
                 throw new Error(errorData.message || `Failed to create PI (${res.status})`);
            }
            const data = await res.json();
            if (!data.clientSecret) throw new Error('Missing clientSecret from API');

            newClientSecret = data.clientSecret;
            console.log(`Received clientSecret for ${type}:`, newClientSecret);

            // Store the secret based on type
            if (type === 'card') clientSecretCard = newClientSecret;
            if (type === 'sepa_debit') clientSecretSepa = newClientSecret;

            // Update Payment Request Button if it exists (always uses 'card' intent)
            if (type === 'card' && paymentRequest) {
                paymentRequest.update({ total: { label: 'Don Veille Médicale', amount: amountCents } });
                console.log("PR Button amount updated.");
            }
             return newClientSecret; // Return the new secret

        } catch (err: any) {
            console.error(`Error creating/updating PI for ${type}:`, err);
            errorMessage = err.message || "Erreur lors de l'initialisation du paiement.";
             // Reset relevant secret on error
             if (type === 'card') clientSecretCard = null;
             if (type === 'sepa_debit') clientSecretSepa = null;
             return null; // Indicate failure
        } finally {
            isLoadingPI = false;
        }
    }

     // --- Initialize Stripe and Check PR Button ---
    onMount(async () => {
         if (!stripePublicKey) { /* ... handle error ... */ return; }
         try {
             isLoadingStripe = true;
             stripe = await loadStripe(stripePublicKey);
             if (!stripe) throw new Error("Stripe failed to load");

             // Check PR Button availability (it will need a 'card' intent later if used)
             await initializePaymentRequestButton(getAmountInCents());

             isLoadingStripe = false;
         } catch (error) {
             console.error("Stripe onMount error:", error);
             errorMessage = "Erreur d'initialisation Stripe.";
             isLoadingStripe = false;
         }
	});

     // --- Initialize Payment Request Button Logic ---
    async function initializePaymentRequestButton(amountCents: number) {
        if (!stripe) return; // Need stripe

        canMakePrPayment = false;
        if (prButton) prButton.destroy();

        paymentRequest = stripe.paymentRequest({
            country: 'FR', currency: 'eur',
            total: { label: 'Don Veille Médicale', amount: amountCents },
            requestPayerName: true, requestPayerEmail: true, requestShipping: false,
        });

        const result = await paymentRequest.canMakePayment();
        if (result) {
            console.log("PR Button available:", result);
            canMakePrPayment = true;
            // We defer element creation and mounting until the button is actually needed/clicked
            // or until a 'card' intent is ready.

            // Handle paymentmethod event
            paymentRequest.on('paymentmethod', async (ev) => {
                 isProcessingPayment = true; // Show loading indicator
                 errorMessage = '';

                 // Ensure we have a *card* client secret for the current amount
                 let secret = clientSecretCard;
                 if (!secret) { // If not already fetched for card, fetch it now
                     console.log("PR Button clicked, fetching 'card' intent...");
                     secret = await createOrUpdatePI('card');
                 }

                 if (!secret || !stripe) {
                     console.error("Cannot confirm PR payment: Stripe or Client Secret missing.");
                     ev.complete('fail');
                     errorMessage = "Erreur lors de la confirmation.";
                     isProcessingPayment = false;
                     return;
                 }

                 console.log("Confirming PR payment with secret:", secret);
                 const { paymentIntent, error: confirmError } = await stripe.confirmPayment({
                      clientSecret: secret, // Use the CARD secret
                      confirmParams: { payment_method: ev.paymentMethod.id },
                      redirect: 'if_required' // Handle 3DS
                 });

                  if (confirmError) {
                      console.error("PR confirmation error:", confirmError);
                      errorMessage = confirmError.message || "Erreur de paiement.";
                      ev.complete('fail');
                  } else if (paymentIntent?.status === 'succeeded') {
                      ev.complete('success');
                      window.location.href = `/donation-status?payment_intent=${paymentIntent.id}&payment_intent_client_secret=${secret}&redirect_status=succeeded`;
                  } else if (paymentIntent?.status === 'processing') {
                       ev.complete('success');
                       window.location.href = `/donation-status?payment_intent=${paymentIntent.id}&payment_intent_client_secret=${secret}&redirect_status=processing`;
                  } else {
                      console.warn("PR Payment status unexpected:", paymentIntent?.status);
                      errorMessage = "Statut de paiement inattendu.";
                      ev.complete('fail');
                  }
                  isProcessingPayment = false;
            });

        } else {
            console.log("PR Button not available.");
            canMakePrPayment = false;
        }
    }

    // --- Initialize and Mount Stripe Elements (Card or SEPA) ---
    async function initializeAndMountElement(type: 'card' | 'sepa_debit') {
        const secret = type === 'card' ? clientSecretCard : clientSecretSepa;
        const mountId = type === 'card' ? '#card-element' : '#iban-element';
        const existingElement = type === 'card' ? cardElement : ibanElement;

        if (!stripe || !secret || existingElement) {
            if (existingElement) console.log(`${type} element already initialized.`);
            else console.log(`Cannot initialize ${type} element: Stripe or Client Secret missing.`);
            return; // Don't re-initialize if already done, or if dependencies missing
        }

        errorMessage = ''; // Clear errors when showing form
        console.log(`Initializing ${type} element with secret: ${secret}`);
        const appearance = { 
            theme: 'night' as const, 
            labels: 'floating' as const,
            variables: {
                colorPrimary: '#ea580c',
                colorBackground: '#1f2937',
                colorText: '#f3f4f6',
                colorDanger: '#ef4444',
                fontFamily: 'system-ui, sans-serif',
                spacingUnit: '4px',
                borderRadius: '8px'
            }
        };
        elements = stripe.elements({ clientSecret: secret, appearance, locale: 'fr' });

        if (type === 'card') {
            if (cardElement) cardElement.destroy(); // Clean previous
            cardElement = elements.create('payment', { layout: "tabs" });
            await tick();
            cardElement.mount(mountId);
        } else { // sepa_debit
            if (ibanElement) ibanElement.destroy(); // Clean previous
            ibanElement = elements.create('iban', { 
                supportedCountries: ['SEPA'],
                style: {
                    base: {
                        fontSize: '16px',
                        color: '#f3f4f6',
                        backgroundColor: '#374151',
                        padding: '12px',
                        '::placeholder': {
                            color: '#9ca3af'
                        },
                        ':-webkit-autofill': {
                            color: '#f3f4f6'
                        }
                    },
                    invalid: {
                        color: '#ef4444',
                        iconColor: '#ef4444'
                    }
                }
            });
            await tick();
            ibanElement.mount(mountId);
        }
        console.log(`${type} element mounted.`);
    }

    // --- UI Actions ---
    async function selectCardPayment() {
        if (isProcessingPayment || isLoadingPI) return;
        showSepaForm = false; // Hide other form
        if (ibanElement) { ibanElement.destroy(); ibanElement = null; } // Cleanup SEPA if switching

        const secret = await createOrUpdatePI('card'); // Get/update 'card' intent
        if (secret) {
             activeClientSecret = secret;
             activePaymentMethodType = 'card';
             showCardForm = true;
             await initializeAndMountElement('card'); // Mount the card element
        } else {
            showCardForm = false; // Don't show if PI creation failed
        }
    }

    async function selectSepaPayment() {
        if (isProcessingPayment || isLoadingPI) return;
        showCardForm = false; // Hide other form
        if (cardElement) { cardElement.destroy(); cardElement = null; } // Cleanup card if switching

        const secret = await createOrUpdatePI('sepa_debit'); // Get/update 'sepa' intent
        if (secret) {
            activeClientSecret = secret;
            activePaymentMethodType = 'sepa_debit';
            showSepaForm = true;
            await initializeAndMountElement('sepa_debit'); // Mount the IBAN element
        } else {
            showSepaForm = false; // Don't show if PI creation failed
        }
    }

     // --- Mount Payment Request Button when it's actually needed ---
     async function mountPrButton() {
         if (!stripe || !elements || !paymentRequest || !canMakePrPayment || prButton) {
            if (prButton) console.log("PR button already mounted or initializing");
             return; // Only mount if available and not already mounted
         }
         // Ensure we have a card intent first
         let secret = clientSecretCard;
         if (!secret) {
            secret = await createOrUpdatePI('card');
         }
         if (!secret) {
            console.error("Cannot mount PR button without a card client secret.");
            return;
         }

         console.log("Mounting PR button.");
         // Recreate elements instance if necessary (e.g., if PI was just created)
         if (!elements) elements = stripe.elements({ clientSecret: secret });

         prButton = elements.create('paymentRequestButton', {
             paymentRequest: paymentRequest!,
             style: {
                 paymentRequestButton: { type: 'donate', theme: 'dark', height: '48px' },
             },
         });
         await tick();
         const prMountEl = document.getElementById('payment-request-button-mount-point');
         if (prMountEl) {
            prButton.mount(prMountEl);
         } else {
            console.warn("PR button mount point not found.");
         }
     }
     // Call mountPrButton when the PR button section should become active,
     // potentially after the initial `canMakePrPayment` check resolves true in onMount.
     $effect(() => {
        if(canMakePrPayment && !prButton) {
            mountPrButton();
        }
     })


    // --- Amount Selection/Confirmation (Simplified) ---
    function handleAmountChange() {
        // Reset secrets and hide forms when amount changes, forcing re-selection
        clientSecretCard = null;
        clientSecretSepa = null;
        activeClientSecret = null;
        activePaymentMethodType = null;
        showCardForm = false;
        showSepaForm = false;
        if (cardElement) { cardElement.destroy(); cardElement = null; }
        if (ibanElement) { ibanElement.destroy(); ibanElement = null; }
        if (prButton) { prButton.destroy(); prButton = null; } // Recreate PR button too
        elements = null; // Reset elements instance

        // Update PR button availability check with new amount
        initializePaymentRequestButton(getAmountInCents());

        console.log("Amount changed, secrets and forms reset.");
    }

    function selectAmount(amount: number) {
        if (isLoadingPI || isProcessingPayment) return;
        currentAmount = amount;
        customAmountInput = '';
        isCustomAmountConfirmed = false;
        handleAmountChange(); // Trigger reset and updates
    }

    function handleCustomAmountInput(ev: InputEvent) {
        const input = ev.target as HTMLInputElement;
        const value = input.value.replace(/[^0-9,.]/g, '');
        const parts = value.split(/[,.]/);
        
        if (parts.length > 2) {
            return;
        }
        
        if (parts.length === 2 && parts[1].length > 2) {
            return;
        }
        
        customAmountInput = value;
        isCustomAmountConfirmed = false;
    }

    function confirmCustomAmount() {
        if (isLoadingPI || isProcessingPayment) return;
        const value = customAmountInput.replace(/,/g, '.');
        const numericValue = parseFloat(value);
        if (!isNaN(numericValue) && numericValue >= 0.50) {
            currentAmount = numericValue; // Set the displayed amount
            isCustomAmountConfirmed = true;
            handleAmountChange(); // Trigger reset and updates
        } else {
             errorMessage = $i18n.donations.errors.invalidAmount;
             isCustomAmountConfirmed = false;
        }
    }


    // --- Payment Confirmation ---
    async function handleCardSubmit(event: Event) {
        event.preventDefault();
        if (!stripe || !cardElement || !clientSecretCard || isProcessingPayment || isLoadingPI) {
             errorMessage = "Le formulaire n'est pas prêt ou une opération est en cours.";
             return;
        }
        isProcessingPayment = true;
        errorMessage = '';

        console.log("Confirming Card/PaymentElement payment with secret:", clientSecretCard);
        
        // First submit the elements
        const { error: submitError } = await elements?.submit();
        if (submitError) {
            console.error("Elements submit error:", submitError);
            errorMessage = submitError.message || "Erreur lors de la soumission du formulaire.";
            isProcessingPayment = false;
            return;
        }

        // Then confirm the payment
        const { error } = await stripe.confirmPayment({
            elements, // Use the elements instance associated with cardElement
            clientSecret: clientSecretCard,
            confirmParams: {
                return_url: `${window.location.origin}/donation-status`,
            },
            // No redirect: 'if_required' needed here as confirmPayment handles it
        });

        if (error) {
            console.error("Card confirmation error:", error);
            errorMessage = error.message || "Erreur de paiement.";
            isProcessingPayment = false; // Re-enable form on client-side error
        }
        // If no error, Stripe handles the redirect based on payment status.
        // isProcessingPayment remains true to prevent further clicks.
    }

     async function handleSepaSubmit(event: Event) {
        event.preventDefault();
        if (!stripe || !ibanElement || !clientSecretSepa || !sepaMandateAccepted || !sepaAccountHolderName.trim() || isProcessingPayment || isLoadingPI) {
             if (!sepaMandateAccepted) errorMessage = "Veuillez accepter le mandat SEPA.";
             else if (!sepaAccountHolderName.trim()) errorMessage = "Veuillez entrer le nom du titulaire du compte.";
             else errorMessage = "Le formulaire n'est pas prêt ou une opération est en cours.";
             return;
        }
        isProcessingPayment = true;
        errorMessage = '';

        console.log("Confirming SEPA payment with secret:", clientSecretSepa);
        const { error } = await stripe.confirmSepaDebitPayment(clientSecretSepa, {
            payment_method: {
                sepa_debit: ibanElement,
                billing_details: {
                    name: sepaAccountHolderName.trim(),
                     // Email is strongly recommended for SEPA mandates
                     email: 'email@example.com', // <-- **IMPORTANT**: Get user's actual email
                },
            },
            // return_url is NOT used here directly, status polling or webhooks are needed for SEPA
        });

         if (error) {
            console.error("SEPA confirmation error:", error);
            errorMessage = error.message || "Erreur lors de la soumission du paiement SEPA.";
            isProcessingPayment = false;
        } else {
             // SEPA requires async confirmation. Redirect to a pending/success page immediately.
             // The actual success is confirmed later via webhooks or polling.
             console.log("SEPA payment submitted, confirmation pending.");
             // Redirect to a generic status page, DO NOT assume success yet.
             window.location.href = `/donation-status?payment_intent=${clientSecretSepa.split('_secret_')[0]}&payment_intent_client_secret=${clientSecretSepa}&redirect_status=processing`; // Use processing status
             // successMessage = "Paiement SEPA soumis. La confirmation peut prendre quelques jours.";
             // Keep isProcessingPayment true as we are redirecting
        }
    }

     // Cleanup effect
     $effect(() => {
        return () => {
            if (copyTimeoutId) {
                clearTimeout(copyTimeoutId);
            }
        };
    });

    function mountStripeElements() {
        if (!stripe || !clientSecretCard || !clientSecretSepa) return;

        const elements = stripe.elements({
            appearance: {
                theme: 'night',
                variables: {
                    colorPrimary: '#ea580c',
                    colorBackground: '#1f2937',
                    colorText: '#f3f4f6',
                    colorDanger: '#ef4444',
                    fontFamily: 'system-ui, sans-serif',
                    spacingUnit: '4px',
                    borderRadius: '8px'
                }
            },
            clientSecret: clientSecretCard
        });

        if (elements) {
            cardElement = elements.create('payment', {
                layout: 'tabs',
                defaultValues: {
                    billingDetails: {
                        name: 'John Doe',
                        email: 'john@example.com',
                        phone: '+33 6 12 34 56 78',
                        address: {
                            line1: '123 Rue de la Paix',
                            city: 'Paris',
                            postal_code: '75001',
                            country: 'FR'
                        }
                    }
                }
            });
            cardElement.mount('#card-element');

            ibanElement = elements.create('iban', {
                supportedCountries: ['SEPA'],
                placeholderCountry: 'FR',
                style: {
                    base: {
                        fontSize: '16px',
                        color: '#f3f4f6',
                        '::placeholder': {
                            color: '#9ca3af'
                        }
                    }
                }
            });
            ibanElement.mount('#iban-element');
        }
    }
</script>

<svelte:head>
    <title>Soutenez-nous - Veille Médicale</title>
    <meta name="description" content="Soutenez Veille Médicale par un don, en donnant votre avis ou en partageant l'outil." />
</svelte:head>

<main class="min-h-screen bg-black px-4 py-12 pt-20 text-white">
    <div class="mx-auto max-w-lg">
        <h1 class="mb-4 text-center text-4xl font-bold tracking-tight">🧡 Soutenez-nous</h1>
        <p class="mb-10 text-center text-xl text-gray-300">🙌 Vous aimez notre travail ? Aidez-nous à aller plus loin.</p>
        <h2 class="mb-6 text-center text-2xl font-semibold">🤗 Comment contribuer ?</h2>

        <div class="mb-8 space-y-6 rounded-lg bg-gray-800 p-6 shadow-lg md:p-8">
            <!-- Amount Selection Section -->
            <div>
                <p class="mb-4 text-lg font-medium">💰 Choisissez un montant (EUR)</p>
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {#each presetAmounts as amount}
                        <button type="button" on:click={() => selectAmount(amount)}
                            class="rounded-md border-2 px-4 py-3 text-center font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800"
                            class:border-orange-500={currentAmount === amount && !customAmountInput}
                            class:bg-orange-600={currentAmount === amount && !customAmountInput}
                            class:text-white={currentAmount === amount && !customAmountInput}
                            class:border-gray-600={!(currentAmount === amount && !customAmountInput)}
                            class:hover:border-orange-400={currentAmount !== amount || !!customAmountInput}
                            class:hover:bg-gray-700={currentAmount !== amount || !!customAmountInput}
                            class:text-gray-300={!(currentAmount === amount && !customAmountInput)}
                            disabled={isProcessingPayment || isLoadingPI}>
                            {amount} €
                        </button>
                    {/each}
                </div>
                <div class="mt-4 flex items-center gap-2">
                    <div class="relative flex-grow">
                        <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">€</span>
                        <input type="text" id="custom-amount" inputmode="decimal"
                            placeholder="Autre montant" value={customAmountInput}
                            on:input={handleCustomAmountInput}
                            class="w-full rounded-md border-2 bg-gray-700 py-3 pl-8 pr-4 text-white placeholder-gray-400 transition-colors duration-200 focus:z-10 focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:ring-offset-0"
                            class:border-orange-500={customAmountInput !== '' && isCustomAmountConfirmed}
                            class:border-gray-600={customAmountInput === '' || !isCustomAmountConfirmed}
                            class:border-yellow-500={customAmountInput !== '' && !isCustomAmountConfirmed}
                            disabled={isProcessingPayment || isLoadingPI} />
                    </div>
                    <button type="button" on:click={confirmCustomAmount}
                        class="shrink-0 rounded-md border-2 bg-gray-600 px-4 py-3 font-medium text-white transition-colors hover:bg-gray-500 focus:z-10 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-60"
                        class:border-orange-500={customAmountInput !== '' && isCustomAmountConfirmed}
                        class:border-gray-600={customAmountInput === ''}
                        class:border-yellow-500={customAmountInput !== '' && !isCustomAmountConfirmed}
                        disabled={isProcessingPayment || isLoadingPI || customAmountInput === '' || (customAmountInput !== '' && parseFloat(customAmountInput.replace(/,/g, '.')) < 0.50) || isCustomAmountConfirmed}
                        title="Valider ce montant">
                        OK
                    </button>
                </div>
                {#if errorMessage}
                    <p class="mt-2 text-sm text-red-400 flex items-center gap-1"><AlertCircle class="w-4 h-4"/> {errorMessage}</p>
                {/if}
            </div>

            <hr class="border-gray-700"/>

            <!-- Payment Method Section -->
            <div>
                <p class="mb-4 text-lg font-medium">✅ Choisissez votre méthode de paiement</p>
                {#if isLoadingPI}
                    <div class="flex justify-center items-center gap-2 text-gray-400">
                        <svg class="h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>
                        <span>Chargement...</span>
                    </div>
                {:else}
                    <div class="space-y-3">
                        {#if canMakePrPayment}
                            <div id="payment-request-button-mount-point" class={!prButton ? 'h-[48px] bg-gray-700 animate-pulse rounded-lg' : ''}>
                                <!-- PR Button will be mounted here by `mountPrButton` -->
                            </div>
                        {/if}

                        <!-- Card Payment Option -->
                        <button type="button" on:click={selectCardPayment}
                            class="w-full rounded-lg border-2 p-4 text-left transition-colors"
                            class:border-orange-500={showCardForm} class:bg-gray-600={showCardForm}
                            class:border-gray-600={!showCardForm} class:bg-gray-700={!showCardForm}
                            class:hover:border-orange-500={!showCardForm} class:hover:bg-gray-600={!showCardForm}
                            disabled={isProcessingPayment}>
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <span class="text-2xl">💳</span>
                                    <h3 class="font-semibold">Carte bancaire</h3>
                                </div>
                                <span class="text-gray-400">{showCardForm ? '▲' : '▼'}</span>
                            </div>
                        </button>

                        {#if showCardForm}
                            <form on:submit={handleCardSubmit} class="mt-4 space-y-4 rounded-lg border border-gray-700 p-4">
                                <div id="card-element">
                                    {#if !cardElement}<p class="text-sm text-gray-400">Chargement du formulaire de carte...</p>{/if}
                                </div>
                                <button type="submit" disabled={!stripe || !cardElement || isProcessingPayment}
                                    class="w-full rounded-lg bg-orange-600 px-6 py-3 text-lg font-semibold text-white shadow-md transition-all duration-300 hover:bg-orange-700 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-70">
                                    {#if isProcessingPayment && activePaymentMethodType === 'card'}
                                        <span class="flex items-center justify-center">
                                            <svg class="mr-2 h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>
                                            Traitement...
                                        </span>
                                    {:else}
                                        Payer {getAmountInCents() / 100} € par Carte
                                    {/if}
                                </button>
                            </form>
                        {/if}

                        <!-- SEPA Payment Option -->
                        <button type="button" on:click={selectSepaPayment}
                            class="w-full rounded-lg border-2 p-4 text-left transition-colors"
                            class:border-indigo-500={showSepaForm} class:bg-gray-600={showSepaForm}
                            class:border-gray-600={!showSepaForm} class:bg-gray-700={!showSepaForm}
                            class:hover:border-indigo-500={!showSepaForm} class:hover:bg-gray-600={!showSepaForm}
                            disabled={isProcessingPayment}>
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <span class="text-2xl">🏦</span>
                                    <h3 class="font-semibold">Prélèvement SEPA (IBAN)</h3>
                                </div>
                                <span class="text-gray-400">{showSepaForm ? '▲' : '▼'}</span>
                            </div>
                        </button>

                        {#if showSepaForm}
                            <form on:submit={handleSepaSubmit} class="mt-4 space-y-4 rounded-lg border border-gray-700 p-4">
                                <div>
                                    <label for="sepa-name" class="block text-sm font-medium text-gray-300 mb-1">Nom du titulaire du compte</label>
                                    <input type="text" id="sepa-name" bind:value={sepaAccountHolderName} required
                                        class="w-full rounded-md border-2 bg-gray-700 py-3 px-4 text-white placeholder-gray-400 transition-colors duration-200 focus:z-10 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0" />
                                </div>
                                <div>
                                    <label for="iban-element" class="block text-sm font-medium text-gray-300 mb-1">IBAN</label>
                                    <div class="relative w-full">
                                        <div class="w-full rounded-md border-2 border-gray-600 bg-[#374151] py-3 px-4 text-white transition-colors duration-200 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-0">
                                            <div id="iban-element" class="w-full">
                                                {#if !ibanElement}<p class="text-sm text-gray-400">Chargement du formulaire IBAN...</p>{/if}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="flex items-start space-x-2">
                                    <input type="checkbox" id="sepa-mandate" bind:checked={sepaMandateAccepted} required
                                        class="h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500 mt-1"/>
                                    <label for="sepa-mandate" class="text-xs text-gray-400">
                                        En fournissant votre IBAN et en confirmant ce paiement, vous autorisez Veille Médicale et Stripe, notre prestataire de services de paiement, à envoyer des instructions à votre banque pour débiter votre compte conformément à ces instructions. Vous avez droit à un remboursement de la part de votre banque selon les termes et conditions de votre convention avec votre banque. Une demande de remboursement doit être présentée dans les 8 semaines suivant la date à laquelle votre compte a été débité. Vos droits sont expliqués dans un relevé que vous pouvez obtenir auprès de votre banque.
                                    </label>
                                </div>
                                <button type="submit" disabled={!stripe || !ibanElement || !sepaMandateAccepted || !sepaAccountHolderName.trim() || isProcessingPayment}
                                    class="w-full rounded-lg bg-indigo-600 px-6 py-3 text-lg font-semibold text-white shadow-md transition-all duration-300 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-70">
                                    {#if isProcessingPayment && activePaymentMethodType === 'sepa_debit'}
                                        <span class="flex items-center justify-center">
                                            <svg class="mr-2 h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>
                                            Soumission...
                                        </span>
                                    {:else}
                                        Payer {getAmountInCents() / 100} € par Prélèvement SEPA
                                    {/if}
                                </button>
                            </form>
                        {/if}
                    </div>
                {/if}
            </div>

            <hr class="border-gray-700" />

            <!-- Feedback Section -->
            <div>
                <p class="mb-4 text-lg font-medium">💌 Chaque retour = une vraie source d'idées</p>
                <a
                    href="mailto:contact@veillemedicale.fr"
                    class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors duration-200 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                >
                    💌 Faire un retour
                </a>
            </div>

            <hr class="border-gray-700" />

            <!-- Share Section -->
            <div>
                <p class="mb-2 text-lg font-medium">📣 Partagez l'outil !</p>
                <p class="mb-3 text-sm text-gray-400">Aidez vos collègues, internes, et amis soignants à rester à jour.</p>
                <p class="mb-2 text-sm font-semibold">👉 Texte à copier-coller :</p>
                <pre class="mb-3 whitespace-pre-wrap rounded-md bg-gray-700 p-3 font-mono text-xs text-gray-200">{shareText}</pre>
                <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-lg border border-teal-500 px-4 py-2 text-sm font-medium text-teal-400 transition-colors duration-150 hover:bg-teal-500/10 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50"
                    on:click={handleCopyShareText}
                    disabled={copyStatus === 'copied'}
                >
                    {#if copyStatus === 'copied'}
                        <Check class="h-4 w-4 text-green-500" />
                        Copié !
                    {:else if copyStatus === 'error'}
                        <Copy class="h-4 w-4 text-red-500" />
                        Erreur
                    {:else}
                        <Copy class="h-4 w-4" />
                        Copier le texte
                    {/if}
                </button>
            </div>
        </div>
    </div>
</main>