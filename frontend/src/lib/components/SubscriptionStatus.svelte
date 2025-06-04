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

	// Props
	let { subscription, isLoading = false }: { subscription: StripeSubscription | null | undefined, isLoading?: boolean } = $props();

	// Helper Functions
	function formatDate(dateString: string | null | undefined): string {
		if (!dateString) return 'N/A';
		try {
			return new Date(dateString).toLocaleDateString('fr-FR', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		} catch (e) {
			console.error("Error formatting date:", dateString, e);
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

	// Placeholder Action Handlers
	async function handleCancelSubscription() {
		console.log('Attempting to cancel subscription (placeholder)');
		alert("La fonctionnalité d'annulation d'abonnement n'est pas encore implémentée.\nSi vous souhaitez annuler, veuillez nous contacter.");
        // Example:
        // parentIsLoading = true; // This would need to be emitted or handled via a store
        // try {
        //   const response = await fetch('/api/cancel-subscription', { method: 'POST' });
        //   if (!response.ok) throw new Error('Failed to cancel');
        //   // Parent component would need to re-fetch data or update UI optimistically
        // } catch (e) {
        //   // Show error via parent
        // } finally {
        //   parentIsLoading = false;
        // }
	}

	async function handleManageSubscription() {
		console.log('Attempting to manage subscription (placeholder)');
		alert("La fonctionnalité de gestion d'abonnement (ex: portail de facturation) n'est pas encore implémentée.\nPour modifier votre abonnement ou vos informations de paiement, veuillez nous contacter.");
        // Example:
        // parentIsLoading = true;
        // try {
        //   const response = await fetch('/api/create-customer-portal-session', { method: 'POST' });
        //   const { url } = await response.json();
        //   if (url) window.location.href = url;
        //   else throw new Error('Could not retrieve portal URL');
        // } catch (e) {
        //   // Show error via parent
        // } finally {
        //   parentIsLoading = false;
        // }
	}

    // Derived state for better readability in template
    const statusText = $derived(getSubscriptionStatusText(subscription?.status));
    const currentPeriodEndDate = $derived(formatDate(subscription?.current_period_end));
    const trialEndDate = $derived(formatDate(subscription?.trial_end || subscription?.current_period_end)); // Fallback to current_period_end for trial if trial_end is null
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
	<div class="mb-8 rounded-lg bg-gray-800 p-6 md:p-8 shadow-lg text-white">
		<h2 class="text-xl md:text-2xl font-semibold text-white border-b border-gray-700 pb-3 mb-6 flex items-center">
            {#if subscription.status === 'active'} <CheckCircle class="h-6 w-6 mr-3 text-green-400 shrink-0" />
            {:else if subscription.status === 'trialing'} <Info class="h-6 w-6 mr-3 text-blue-400 shrink-0" />
            {:else if subscription.status === 'canceled'} <XCircle class="h-6 w-6 mr-3 text-gray-500 shrink-0" />
            {:else if subscription.status === 'past_due' || subscription.status === 'unpaid' || subscription.status === 'incomplete'} <AlertTriangle class="h-6 w-6 mr-3 text-yellow-400 shrink-0" />
            {/if}
			Votre abonnement
		</h2>
		<div class="space-y-3">
			<p class="text-sm text-gray-300">
				Statut : <span class="font-medium text-white ml-1">{statusText}</span>
			</p>

			{#if subscription.status === 'active' || subscription.status === 'trialing'}
				{#if subscription.cancel_at_period_end}
					<p class="text-sm text-gray-300">
						Votre abonnement {subscription.status === 'trialing' ? "d'essai " : ""}
						prendra fin le <span class="font-medium text-white">{currentPeriodEndDate}</span>.
						Vous ne serez pas facturé à nouveau.
					</p>
				{:else}
					<p class="text-sm text-gray-300">
						{#if subscription.status === 'trialing'}
							Votre période d'essai est active jusqu'au <span class="font-medium text-white">{trialEndDate}</span>.
							Votre abonnement payant débutera ensuite, sauf annulation avant cette date.
						{:else} <!-- status is 'active' -->
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

			<div class="flex flex-col sm:flex-row gap-4 pt-3">
				{#if isEffectivelyActive && !subscription?.cancel_at_period_end}
					<button type="button" on:click={handleCancelSubscription}
							class="w-full sm:w-auto rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-60 flex items-center justify-center"
							disabled={isLoading}>
                            {#if isLoading} <Loader2 class="mr-2 h-4 w-4 animate-spin" /> Annulation... {:else} Annuler l'abonnement {/if}
					</button>
				{/if}
                {#if subscription.status !== 'canceled'}
                    <button type="button" on:click={handleManageSubscription}
                            class="w-full sm:w-auto rounded-lg bg-gray-600 px-5 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-60 flex items-center justify-center"
                            disabled={isLoading}>
                        {#if isLoading} <Loader2 class="mr-2 h-4 w-4 animate-spin" /> Chargement... {:else} Gérer mon abonnement {/if}
                    </button>
                {/if}
			</div>
		</div>
	</div>
{:else}
    <div class="mb-8 rounded-lg bg-gray-800 p-6 md:p-8 shadow-lg text-white">
        <h2 class="text-xl md:text-2xl font-semibold text-white border-b border-gray-700 pb-3 mb-6 flex items-center">
            <Info class="h-6 w-6 mr-3 text-blue-400 shrink-0" />
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