<!-- frontend/src/lib/components/SubscriptionRequired.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { Lock } from 'lucide-svelte';
 // Using Lock icon

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
</script>

<div class="flex min-h-[calc(100vh-100px)] flex-col items-center justify-center bg-black p-6 text-center text-white sm:p-8">
    <div class="w-full max-w-md rounded-xl bg-gray-800 p-8 shadow-2xl">
        <div class="mb-6 flex justify-center">
            <Lock class="h-16 w-16 text-orange-500" stroke-width="1.5" />
        </div>

        <h2 class="mb-3 text-3xl font-bold text-white">
            {title}
        </h2>

        <p class="mb-8 text-gray-300">
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