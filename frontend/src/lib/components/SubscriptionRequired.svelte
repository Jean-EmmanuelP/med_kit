<!-- frontend/src/lib/components/SubscriptionRequired.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { Lock, X } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Props for customization, though defaults are provided
	let {
		title = "Accès Restreint",
		message = "Le contenu de cette page est réservé à nos abonnés.",
		ctaText = "S'abonner maintenant pour y accéder",
		subscribeUrl = "/checkout", // Default based on your CheckoutForm path
		homeUrl = "/"
	} = $props<{
		title?: string;
		message?: string;
		ctaText?: string;
		subscribeUrl?: string;
		homeUrl?: string;
	}>();

	function navigateToSubscribe() {
		goto(subscribeUrl);
	}

    function navigateToHome() {
        goto(homeUrl);
    }

    function handleBackdropClick(event: MouseEvent) {
        if (event.target === event.currentTarget) {
            dispatch('close');
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            dispatch('close');
        }
    }

    function handleClose() {
        dispatch('close');
    }
</script>

<svelte:window on:keydown={handleKeydown} />

<div 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-[2px]"
    on:click={handleBackdropClick}
    role="dialog"
    aria-modal="true"
>
    <div class="relative w-full max-w-md rounded-xl bg-gray-800 p-8 shadow-2xl">
        <button
            on:click={handleClose}
            class="absolute -right-2 -top-2 rounded-full bg-gray-700 p-1.5 text-gray-400 transition-colors hover:bg-gray-600 hover:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            aria-label="Fermer"
        >
            <X class="h-5 w-5" />
        </button>

        <div class="mb-6 flex justify-center">
            <Lock class="h-16 w-16 text-orange-500" stroke-width="1.5" />
        </div>

        <h2 class="mb-3 text-3xl font-bold text-white text-center">
            {title}
        </h2>

        <p class="mb-8 text-gray-300 text-center">
            {message}
        </p>

        <div class="space-y-4">
            <button
                on:click={navigateToSubscribe}
                class="w-full rounded-lg bg-orange-600 px-6 py-3 text-base font-semibold text-white shadow-md transition-all duration-300 ease-in-out hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            >
                {ctaText}
            </button>

            <button
                on:click={navigateToHome}
                class="w-full rounded-lg border-2 border-gray-600 px-6 py-3 text-base font-semibold text-gray-300 transition-colors duration-300 ease-in-out hover:border-gray-500 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            >
                Retour à l'accueil
            </button>
        </div>
        <!-- Optional: Link to learn more about subscription benefits -->
        <!--
        <p class="mt-6 text-sm text-gray-400">
            <a href="/pricing" class="underline hover:text-teal-400">
                Découvrir les avantages de l'abonnement
            </a>
        </p>
        -->
    </div>
</div>

<style>
    /* You can add any component-specific global styles here if needed,
       but Tailwind should handle most of it. */
</style>