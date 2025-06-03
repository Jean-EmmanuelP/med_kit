<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { loadStripe, type StripeElements as StripeElementsType, type StripePaymentElement, type Stripe as StripeType } from '@stripe/stripe-js';
	import { AlertCircle, CreditCard } from 'lucide-svelte';
// Using CreditCard icon
	import { onMount, tick } from 'svelte';

	const stripePublicKey = env.PUBLIC_STRIPE_KEY;

	let stripe: StripeType | null = $state(null);
	let elements: StripeElementsType | null = $state(null);
	let paymentElement: StripePaymentElement | null = $state(null);
	let clientSecret: string | null = $state(null);

	let isLoadingStripe = $state(true);
	let isCreatingIntent = $state(false);
	let paymentProcessing = $state(false);
	let errorMessage = $state('');

	let selectedPlan = $state<'monthly' | 'yearly' | null>(null);
	let hasAttemptedInitForCurrentPlan = $state(false);

	const plans = {
		monthly: {
			id: 'monthly' as const,
			name: 'Mensuel',
			priceString: '€1.99',
			frequency: 'par mois',
		},
		yearly: {
			id: 'yearly' as const,
			name: 'Annuel',
			priceString: '€19.99',
			frequency: 'par an',
			originalMonthlyTotal: (1.99 * 12).toFixed(2)
		}
	};

	onMount(async () => {
		if (!stripePublicKey) {
			errorMessage = 'Clé publique Stripe non configurée.';
			isLoadingStripe = false;
			return;
		}
		try {
			stripe = await loadStripe(stripePublicKey);
			isLoadingStripe = false;
		} catch (error: any) {
			console.error("Erreur chargement Stripe.js:", error);
			errorMessage = error.message || 'Échec du chargement de Stripe.';
			isLoadingStripe = false;
		}
	});

	function selectPlanForPayment(planId: 'monthly' | 'yearly') {
		if (paymentProcessing || isCreatingIntent) return;
		if (selectedPlan === planId) return;

		selectedPlan = planId;
		errorMessage = '';
		clientSecret = null;
		if (paymentElement) {
			try { paymentElement.destroy(); } catch(e) { /* ignore */ }
			paymentElement = null;
		}
		elements = null;
		hasAttemptedInitForCurrentPlan = false;
	}

	async function initializeStripeElements() {
		if (!stripe || !selectedPlan || elements || clientSecret || isLoadingStripe || hasAttemptedInitForCurrentPlan) {
			return;
		}

		hasAttemptedInitForCurrentPlan = true;
		isCreatingIntent = true;
		errorMessage = '';

		try {
			const response = await fetch('/api/create-subscription', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ planIdentifier: selectedPlan })
			});

			const result = await response.json();

            console.log("result", result);
			if (!response.ok) {
				throw new Error(result.error || `Échec de création de l'abonnement (${response.status})`);
			}
			if (!result.clientSecret || !result.subscriptionId) {
				throw new Error('Client secret ou ID d\'abonnement manquant dans la réponse du serveur.');
			}

			clientSecret = result.clientSecret;

			const appearance = {
				theme: 'night' as const,
				labels: 'floating' as const,
				variables: {
					colorPrimary: '#ea580c',        // Orange for active elements/focus
                    colorBackground: '#2d3748',    // Darker gray (gray-800 from Tailwind) for element bg
                    colorText: '#e2e8f0',          // Light gray (gray-200) for text
                    colorDanger: '#e53e3e',        // Red (red-600) for errors
                    fontFamily: 'inherit',
                    spacingUnit: '4px',            // Default, fine
                    borderRadius: '0.375rem',      // Tailwind's rounded-md
                    colorTextPlaceholder: '#a0aec0' // Medium gray (gray-500) for placeholders
				}
			};
			elements = stripe.elements({ clientSecret, appearance, locale: 'fr' });
			paymentElement = elements.create('payment', {
				layout: {
					type: 'tabs',
					defaultCollapsed: false,
				}
			});

			await tick();
			const mountPoint = document.getElementById('card-element-placeholder');
			if (mountPoint) {
                mountPoint.innerHTML = '';
				paymentElement.mount(mountPoint);
			} else {
				throw new Error("L'élément de montage pour le paiement (#card-element-placeholder) n'a pas été trouvé.");
			}
			
			paymentElement.on('ready', () => {
				isCreatingIntent = false;
			});

			paymentElement.on('change', (event) => {
				if (event.error) {
					errorMessage = event.error.message ?? "Erreur de validation des informations de paiement.";
				} else {
					errorMessage = '';
				}
			});

		} catch (error: any) {
			console.error("Erreur d'initialisation Stripe Elements:", error);
			errorMessage = error.message || "Échec de l'initialisation du formulaire de paiement.";
			isCreatingIntent = false;
			clientSecret = null;
			elements = null;
			if (paymentElement) {
				try { paymentElement.destroy(); } catch(e) { /* ignore */ }
				paymentElement = null;
			}
		}
	}

	$effect(() => {
		if (selectedPlan && stripe && !isLoadingStripe && !elements && !clientSecret && !hasAttemptedInitForCurrentPlan) {
			initializeStripeElements();
		}
	});

	async function handleSubmit() {
		if (!stripe || !elements || !clientSecret || paymentProcessing || isCreatingIntent || !paymentElement) {
			if (isCreatingIntent) errorMessage = "Initialisation du paiement en cours...";
			else if (!selectedPlan) errorMessage = "Veuillez sélectionner un plan.";
			else if (!paymentElement) errorMessage = "Détails de paiement non chargés. Veuillez réessayer ou sélectionner un plan.";
			else errorMessage = "Système de paiement non prêt.";
			return;
		}

		paymentProcessing = true;
		errorMessage = '';

		const { error } = await stripe.confirmPayment({
			elements,
			confirmParams: {
				return_url: `${window.location.origin}/payment-status`,
			},
		});

		if (error) {
			console.error("Erreur de confirmation Stripe:", error);
			errorMessage = error.message || 'Une erreur inattendue est survenue lors du paiement.';
			paymentProcessing = false;
		}
	}
</script>

<div class="checkout-container">
	{#if isLoadingStripe}
		<div class="loading-text">Chargement de Stripe...</div>
	{:else if !selectedPlan}
	    <h3 class="instruction-text">Choisissez votre plan :</h3>
    {/if}

	<div class="plan-selection-cards">
		<div
			class="plan-card"
			class:selected={selectedPlan === plans.monthly.id}
			on:click={() => selectPlanForPayment(plans.monthly.id)}
			role="button"
			tabindex="0"
			on:keydown={(e) => e.key === 'Enter' && selectPlanForPayment(plans.monthly.id)}
		>
			<h4>{plans.monthly.name}</h4>
			<div class="price">{plans.monthly.priceString}</div>
			<div class="frequency">{plans.monthly.frequency}</div>
		</div>

		<div
			class="plan-card"
			class:selected={selectedPlan === plans.yearly.id}
			on:click={() => selectPlanForPayment(plans.yearly.id)}
			role="button"
			tabindex="0"
			on:keydown={(e) => e.key === 'Enter' && selectPlanForPayment(plans.yearly.id)}
		>
			<span class="savings-badge">Économisez !</span>
			<h4>{plans.yearly.name}</h4>
			<div class="price">{plans.yearly.priceString}</div>
			<div class="frequency">{plans.yearly.frequency}</div>
			<div class="original-price">
				<s>€{plans.yearly.originalMonthlyTotal}</s>
			</div>
		</div>
	</div>

	{#if selectedPlan}
		<div class="payment-details-box mt-8 rounded-lg bg-gray-800 p-6 shadow-lg md:p-8">
			<div class="payment-method-header mb-5 flex items-center gap-2 border-b-2 border-orange-500 pb-3">
				<CreditCard class="h-5 w-5 text-orange-500" />
				<h3 class="font-semibold text-lg text-white">Paiement par Carte Bancaire</h3>
			</div>
            
			<div id="card-element-container" class="rounded-md bg-gray-900 p-1 border border-gray-700">
				<div id="card-element-placeholder" class="min-h-[180px] md:min-h-[200px]">
					{#if isCreatingIntent}
						<div class="flex items-center justify-center text-gray-400 italic h-full p-3">
							Initialisation du formulaire de paiement...
						</div>
					{:else if !paymentElement && !errorMessage && hasAttemptedInitForCurrentPlan}
						 <div class="flex items-center justify-center text-gray-500 italic h-full p-3">
							Impossible de charger le formulaire. Vérifiez votre connexion et réessayez.
						</div>
					{:else if !paymentElement && !errorMessage && !hasAttemptedInitForCurrentPlan}
						 <div class="flex items-center justify-center text-gray-500 italic h-full p-3">
							Chargement du formulaire de carte...
						</div>
					{/if}
				</div>
			</div>
            <p class="mt-4 text-xs text-gray-400">
                En fournissant vos informations de carte bancaire, vous autorisez Veille Médicale à débiter votre carte pour les paiements futurs conformément à ses conditions.
            </p>
		</div>
	{/if}

	{#if errorMessage && !isCreatingIntent}
		<div class="error-message mt-6 flex items-center gap-2" role="alert">
			<AlertCircle class="h-5 w-5 shrink-0 text-red-400" />
			<span class="text-red-400">{errorMessage}</span>
		</div>
	{/if}

	{#if selectedPlan}
		<form id="payment-form" on:submit|preventDefault={handleSubmit} class="mt-8">
			<button
				type="submit"
				disabled={paymentProcessing || isLoadingStripe || isCreatingIntent || !stripe || !elements || !paymentElement}
				class:processing={paymentProcessing}
				class="w-full rounded-lg bg-orange-600 px-6 py-3 text-base font-semibold text-white shadow-md transition-all duration-300 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
			>
				{#if paymentProcessing}
					<span class="flex items-center justify-center">
                        <svg class="mr-2 h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>
                        Traitement...
                    </span>
				{:else if isLoadingStripe || isCreatingIntent}
					Chargement...
				{:else}
					S'abonner {selectedPlan === "monthly" ? "mensuellement" : 'annuellement'}
				{/if}
			</button>
		</form>
	{/if}
</div>

<style>
	.checkout-container {
		background-color: #1e1e1e; /* gray-900 */
		padding: 2rem;
		border-radius: 0.5rem; /* rounded-lg */
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* shadow-lg */
		width: 100%;
		max-width: 28rem; /* max-w-md */
		margin: 2rem auto;
        color: #d1d5db; /* gray-300 */
        font-family: inherit; /* From global */
	}
    .loading-text, .instruction-text {
		text-align: center;
		margin-bottom: 1.5rem; /* mb-6 */
		color: #9ca3af; /* gray-400 */
		font-size: 1.25rem; /* text-xl */
		font-weight: 500; /* font-medium */
	}
	.plan-selection-cards {
		display: flex;
		gap: 1rem; /* gap-4 */
		margin-bottom: 1rem; /* mb-4 */
	}
	.plan-card {
		flex: 1;
		background-color: #374151; /* gray-700 */
		border: 2px solid #4b5563; /* gray-600 */
		border-radius: 0.5rem; /* rounded-lg */
		padding: 1.5rem 1rem; /* p-6 px-4 */
		text-align: center;
		cursor: pointer;
		transition: all 0.2s ease-in-out;
		position: relative;
	}
	.plan-card:hover {
		background-color: #4b5563; /* gray-600 */
		border-color: #6b7280; /* gray-500 */
		transform: translateY(-2px);
	}
	.plan-card.selected {
		border-color: #f97316; /* orange-500 */
		background-color: #c2410c; /* orange-700 (darker for selected) */
		box-shadow: 0 0 15px rgba(249, 115, 22, 0.3); /* orange-500 shadow */
		color: white;
	}
    .plan-card.selected .price, .plan-card.selected h4, .plan-card.selected .frequency, .plan-card.selected .original-price {
        color: white;
    }
	.plan-card h4 { margin-top: 0; margin-bottom: 0.5rem; font-size: 1.125rem; /* text-lg */ font-weight: 600; /* font-semibold */ color: #f3f4f6; /* gray-100 */ }
	.plan-card .price { font-size: 2.25rem; /* text-4xl */ font-weight: 700; /* font-bold */ color: #f97316; /* orange-500 */ margin-bottom: 0.25rem; line-height: 1.1; }
	.plan-card .frequency { font-size: 0.875rem; /* text-sm */ color: #9ca3af; /* gray-400 */ margin-bottom: 0.5rem; }
	.plan-card .original-price { font-size: 0.875rem; color: #6b7280; /* gray-500 */ margin-top: 0.25rem; }
	.plan-card .savings-badge {
		position: absolute; top: -0.625rem; /* -top-2.5 */ right: -0.625rem; /* -right-2.5 */
		background-color: #14b8a6; /* teal-500 */
		color: #111827; /* gray-900 */
		padding: 0.25em 0.625em; /* px-2.5 py-1 */ border-radius: 0.25rem; /* rounded */
		font-size: 0.75rem; /* text-xs */ font-weight: 700; line-height: 1;
	}

    .payment-details-box {
        background-color: #374151; /* gray-700 */
    }
    .payment-method-header {
        border-bottom-color: #f97316; /* orange-500 */
    }

    /* Container for Stripe Element for better background control */
    #card-element-container {
		background-color: #1f2937; /* gray-800 or Stripe's 'night' theme default if it matches */
        border-radius: 0.375rem; /* rounded-md */
	}
	#card-element-placeholder {
        /* This div itself will be styled by Stripe Elements via appearance API.
           We just need to provide a min-height for when it's empty or loading. */
        padding-top: 1rem;
        padding-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
	}

	.error-message {
		color: #fca5a5; /* red-300 */
		background-color: rgba(239, 68, 68, 0.1); /* bg-red-500/10 */
		border: 1px solid #ef4444; /* red-500 */
		padding: 0.75rem 1rem; /* p-3 px-4 */
		border-radius: 0.375rem; /* rounded-md */
		font-size: 0.875rem; /* text-sm */
	}
</style>