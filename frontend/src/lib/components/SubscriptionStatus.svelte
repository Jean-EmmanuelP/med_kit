<!-- $lib/components/SubscriptionStatus.svelte -->
<script lang="ts">
	export interface StripeSubscription {
		id: number;
		user_profile_id: string;
		stripe_customer_id: string | null;
		stripe_subscription_id: string | null;
		stripe_price_id: string | null;
		status: 'active' | 'trialing' | 'canceled' | 'past_due' | 'incomplete' | 'incomplete_expired' | 'unpaid' | string | null;
		current_period_start: string | null;
		current_period_end: string | null;
		cancel_at_period_end: boolean | null;
		canceled_at: string | null;
		trial_start: string | null;
		trial_end: string | null;
		metadata: Record<string, any> | null;
		created_at: string;
		updated_at: string;
	}
	import { AlertTriangle, CheckCircle, Info, Loader2, XCircle } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	let { subscription }: { subscription: StripeSubscription | null | undefined } = $props();
	let isLoading = $state(false); // Internal loading state for this component's actions

	const dispatch = createEventDispatcher<{ subscriptionUpdated: void, manageSubscription: void }>();


	function formatDate(dateString: string | null | undefined): string {
		if (!dateString) return 'N/A';
		try {
			return new Date(dateString).toLocaleDateString('fr-FR', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		} catch (e) {
			return 'Date invalide';
		}
	}

	function getSubscriptionStatusText(status: string | null | undefined): string {
		if (!status) return 'Inconnu';
		switch (status) {
			case 'active': return 'Actif';
			case 'trialing': return 'En période d\'essai';
			case 'canceled': return 'Annulé';
			case 'past_due': return 'Paiement en attente';
			case 'incomplete': return 'Incomplet';
			case 'incomplete_expired': return 'Expiré (incomplet)';
			case 'unpaid': return 'Impayé';
			default: return status.charAt(0).toUpperCase() + status.slice(1);
		}
	}

	async function handleCancelSubscription() {
		if (!subscription?.stripe_subscription_id) {
			alert('Erreur: ID d\'abonnement introuvable.');
			return;
		}

		if (!confirm('Êtes-vous sûr de vouloir annuler votre abonnement ? Il restera actif jusqu\'à la fin de la période en cours.')) {
			return;
		}

		isLoading = true;
		let localErrorMessage = ''; // Local error message for this action

		try {
			const response = await fetch('/api/cancel-stripe-subscription', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ stripeSubscriptionId: subscription.stripe_subscription_id })
			});

			const result = await response.json();

			if (!response.ok) {
				throw new Error(result.message || `Erreur ${response.status} lors de l'annulation.`);
			}

			alert('Votre demande d\'annulation a été prise en compte. Votre abonnement prendra fin à la date indiquée.');
			dispatch('subscriptionUpdated'); // Notify parent to re-fetch data

		} catch (err: any) {
			localErrorMessage = err.message || "Une erreur est survenue lors de l'annulation.";
			alert(`Erreur: ${localErrorMessage}`); // Show error to user
		} finally {
			isLoading = false;
		}
	}

	async function handleManageSubscription() {
		// This will call a backend endpoint that creates a Stripe Customer Portal session
		// and then redirects the user to Stripe's portal.
		isLoading = true;
		let localErrorMessage = '';
		try {
			const response = await fetch('/api/create-customer-portal-session', {
				method: 'POST',
			});
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.message || `HTTP Error ${response.status}`);
			}
			if (result.url) {
				window.location.href = result.url;
			} else {
				throw new Error('URL du portail client non reçue.');
			}
		} catch (err: any) {
			localErrorMessage = err.message || 'Erreur lors de la redirection vers le portail de gestion.';
			alert(`Erreur: ${localErrorMessage}`);
		} finally {
			isLoading = false;
		}
	}

    const statusText = $derived(getSubscriptionStatusText(subscription?.status));
    const currentPeriodEndDate = $derived(formatDate(subscription?.current_period_end));
    const trialEndDate = $derived(formatDate(subscription?.trial_end || subscription?.current_period_end));
    const canceledAtDate = $derived(formatDate(subscription?.canceled_at));
    const isEffectivelyActive = $derived(subscription && (subscription.status === 'active' || subscription.status === 'trialing'));
    const showSubscriptionCard = $derived(
        subscription && (
            subscription.status === 'active' ||
            subscription.status === 'trialing' ||
            subscription.status === 'canceled' ||
            subscription.status === 'past_due' ||
            subscription.status === 'unpaid' ||
            subscription.status === 'incomplete'
        )
    );
</script>

{#if showSubscriptionCard && subscription}
	<div class="mb-8 rounded-lg bg-gray-800 p-6 text-white shadow-lg md:p-8">
		<h2 class="mb-6 flex items-center border-b border-gray-700 pb-3 text-xl font-semibold text-white md:text-2xl">
            {#if subscription.status === 'active'} <CheckCircle class="mr-3 h-6 w-6 shrink-0 text-green-400" />
            {:else if subscription.status === 'trialing'} <Info class="mr-3 h-6 w-6 shrink-0 text-blue-400" />
            {:else if subscription.status === 'canceled'} <XCircle class="mr-3 h-6 w-6 shrink-0 text-gray-500" />
            {:else if subscription.status === 'past_due' || subscription.status === 'unpaid' || subscription.status === 'incomplete'} <AlertTriangle class="mr-3 h-6 w-6 shrink-0 text-yellow-400" />
            {/if}
			Votre abonnement
		</h2>
		<div class="space-y-3">
			<p class="text-sm text-gray-300">
				Statut : <span class="ml-1 font-medium text-white">{statusText}</span>
			</p>

			{#if subscription.status === 'active' || subscription.status === 'trialing'}
				{#if subscription.cancel_at_period_end}
					<p class="text-sm text-gray-300">
						Votre abonnement {subscription.status === 'trialing' ? "d'essai " : ""}
						prendra fin le <span class="font-medium text-white">{currentPeriodEndDate}</span>.
						Vous continuerez à bénéficier de tous les avantages jusqu'à cette date.
					</p>
				{:else}
					<p class="text-sm text-gray-300">
						{#if subscription.status === 'trialing'}
							Votre période d'essai est active jusqu'au <span class="font-medium text-white">{trialEndDate}</span>.
							Votre abonnement payant débutera ensuite, sauf annulation avant cette date.
						{:else}
							Votre abonnement est actif et sera renouvelé automatiquement le
							<span class="font-medium text-white">{currentPeriodEndDate}</span>.
						{/if}
					</p>
				{/if}
			{/if}

			{#if subscription.status === 'canceled'}
				<p class="text-sm text-gray-300">
					Votre abonnement a été annulé
					{#if subscription.canceled_at} le <span class="font-medium text-white">{canceledAtDate}</span>{/if}.
					Il a pris fin le <span class="font-medium text-white">{currentPeriodEndDate}</span>.
				</p>
			{/if}

			{#if subscription.status === 'past_due' || subscription.status === 'unpaid' || subscription.status === 'incomplete'}
				<p class="text-sm text-yellow-300">
					{#if subscription.status === 'past_due'}
						Votre dernier paiement a échoué. Veuillez mettre à jour vos informations de paiement pour réactiver votre abonnement.
					{:else if subscription.status === 'unpaid'}
						Votre abonnement est impayé. Veuillez mettre à jour vos informations de paiement.
					{:else if subscription.status === 'incomplete'}
						La configuration de votre abonnement est incomplète. Veuillez finaliser le paiement.
					{/if}
				</p>
			{/if}

			<div class="flex flex-col gap-4 pt-3 sm:flex-row">
				{#if isEffectivelyActive && !subscription?.cancel_at_period_end}
					<button type="button" on:click={handleCancelSubscription}
							class="flex w-full items-center justify-center rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-60 sm:w-auto"
							disabled={isLoading}>
                            {#if isLoading} <Loader2 class="mr-2 h-4 w-4 animate-spin" /> Annulation... {:else} Annuler l'abonnement {/if}
					</button>
				{/if}
                {#if subscription.status !== 'canceled'}
                    <button type="button" on:click={handleManageSubscription}
                            class="flex w-full items-center justify-center rounded-lg bg-gray-600 px-5 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-60 sm:w-auto"
                            disabled={isLoading}>
                        {#if isLoading} <Loader2 class="mr-2 h-4 w-4 animate-spin" /> Chargement... {:else} Gérer mon abonnement {/if}
                    </button>
                {/if}
			</div>
		</div>
	</div>
{:else}
    <div class="mb-8 rounded-lg bg-gray-800 p-6 text-white shadow-lg md:p-8">
        <h2 class="mb-6 flex items-center border-b border-gray-700 pb-3 text-xl font-semibold text-white md:text-2xl">
            <Info class="mr-3 h-6 w-6 shrink-0 text-blue-400" />
            Abonnement
        </h2>
        <div class="space-y-4">
            <p class="text-gray-300">
                Vous n'avez pas encore d'abonnement actif.
            </p>
            <a href="/checkout"
               class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800">
                S'abonner maintenant
            </a>
        </div>
    </div>
{/if}