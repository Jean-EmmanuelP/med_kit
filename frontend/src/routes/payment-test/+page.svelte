<script>
    import { onMount } from 'svelte';
    import { loadStripe } from '@stripe/stripe-js';
    import { goto } from '$app/navigation';

    let stripe;
    let elements;
    let paymentRequest;
    let paymentRequestButton;
    let ibanElement;
    let clientSecret;
    let paymentError = '';
    let paymentSuccess = '';

    onMount(async () => {
        // Charger Stripe avec la clé publique de test
        stripe = await loadStripe('pk_test_51PKxSICA4R4AS5AvZ1R27K63b98kvj9wr0QE4IhfsXtcEDwI7K0myfhlY8mZAST7kkFOu3wD7eF9k17JU1tDzJQs00vYGXcbqE');

        // Créer un Payment Intent au chargement de la page (par défaut mensuel)
        await createPaymentIntent('monthly');

        // Configurer le PaymentRequestButton pour Apple Pay, Revolut Pay, et Link
        paymentRequest = stripe.paymentRequest({
            country: 'FR', // Remplacez par le pays cible (ex: 'FR' pour France)
            currency: 'eur', // Devise utilisée
            total: {
                label: 'Abonnement Mensuel',
                amount: 99 // 0,99 € en centimes
            },
            requestPayerName: true,
            requestPayerEmail: true,
            requestPayerPhone: true,
            paymentMethodTypes: ['apple_pay', 'revolut_pay', 'link'] // Inclure Apple Pay, Revolut Pay, et Link
        });

        // Vérifier si le PaymentRequestButton est disponible
        const canMakePayment = await paymentRequest.canMakePayment();
        if (canMakePayment) {
            elements = stripe.elements({ clientSecret });
            paymentRequestButton = elements.create('paymentRequestButton', {
                paymentRequest
            });
            paymentRequestButton.mount('#payment-request-button');
        } else {
            paymentError = 'Aucune méthode de paiement express (Apple Pay, Revolut Pay, Link) n’est disponible sur cet appareil.';
        }

        // Configurer SEPA Direct Debit (RIB)
        elements = stripe.elements({ clientSecret });
        ibanElement = elements.create('iban', { supportedCountries: ['SEPA'] });
        ibanElement.mount('#iban-element');

        // Écouter les événements de paiement du PaymentRequestButton
        paymentRequest.on('paymentmethod', async (ev) => {
            const { paymentIntent, error } = await stripe.confirmPayment({
                elements,
                clientSecret,
                confirmParams: {
                    return_url: `${window.location.origin}/thank-you`
                },
                redirect: 'if_required'
            });

            if (error) {
                paymentError = error.message;
                ev.complete('fail');
            } else {
                paymentSuccess = 'Paiement réussi !';
                ev.complete('success');
                await goto('/thank-you');
            }
        });
    });

    // Créer un Payment Intent
    async function createPaymentIntent(plan) {
        paymentError = '';
        paymentSuccess = '';
        const amount = plan === 'yearly' ? 1000 : 99; // 10 € ou 0,99 €
        const response = await fetch('/api/create-payment-intent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, currency: 'eur', plan })
        });

        const { clientSecret: newClientSecret } = await response.json();
        clientSecret = newClientSecret;

        // Mettre à jour le montant dans le PaymentRequestButton
        if (paymentRequest) {
            paymentRequest.update({
                total: {
                    label: plan === 'yearly' ? 'Abonnement Annuel' : 'Abonnement Mensuel',
                    amount
                }
            });
        }
    }

    // Confirmer le paiement SEPA
    async function confirmSepaPayment() {
        if (!stripe || !clientSecret) return;

        try {
            const result = await stripe.confirmSepaDebitPayment(clientSecret, {
                payment_method: {
                    iban: ibanElement,
                    billing_details: { name: 'Test User' }
                }
            });

            if (result.error) {
                paymentError = result.error.message;
            } else {
                paymentSuccess = 'Paiement SEPA réussi !';
                await goto('/thank-you');
            }
        } catch (error) {
            paymentError = error.message;
        }
    }
</script>

<div class="max-w-md mx-auto p-6 space-y-6">
    <h1 class="text-2xl font-bold">Page de test - Abonnement</h1>

    <!-- Sélection du plan -->
    <div class="space-y-4">
        <button
            on:click={() => createPaymentIntent('monthly')}
            class="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
        >
            0,99 €/mois (sans engagement)
        </button>
        <button
            on:click={() => createPaymentIntent('yearly')}
            class="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
        >
            10 €/an
        </button>
    </div>

    <!-- Options de paiement -->
    <div class="space-y-4">
        <h2 class="text-lg font-semibold">Choisissez une méthode de paiement :</h2>

        <!-- PaymentRequestButton pour Apple Pay, Revolut Pay, et Link -->
        <div id="payment-request-button" class="border p-2 rounded">
            <!-- Le bouton sera affiché ici si une méthode de paiement express est disponible -->
            {#if !paymentRequestButton}
                <p class="text-gray-500">Aucun bouton de paiement express disponible (vérifiez Apple Pay ou Revolut Pay sur cet appareil).</p>
            {/if}
        </div>

        <!-- SEPA Direct Debit (RIB) -->
        <div>
            <label class="block text-sm font-medium text-gray-700">IBAN</label>
            <div id="iban-element" class="border p-2 rounded"></div>
            <button
                on:click={confirmSepaPayment}
                class="mt-2 w-full bg-gray-500 text-white py-2 rounded hover:bg-gray-600"
                disabled={!clientSecret}
            >
                Payer avec SEPA Direct Debit
            </button>
        </div>
    </div>

    <!-- Messages de feedback -->
    {#if paymentError}
        <p class="text-red-500">{paymentError}</p>
    {/if}
    {#if paymentSuccess}
        <p class="text-green-500">{paymentSuccess}</p>
    {/if}
</div>