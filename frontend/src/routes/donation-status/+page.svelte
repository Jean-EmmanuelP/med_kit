--- File Path ---
frontend/src/routes/donation-status/+page.svelte

<script lang="ts">
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import { CheckCircle, XCircle, Loader } from 'lucide-svelte'; // Using lucide icons
    import { i18n } from '$lib/i18n';

    let status: 'loading' | 'success' | 'error' | 'processing' = $state('loading');
    let errorMessage = $state('');
    let paymentIntentId = $state<string | null>(null);
    let donationAmount = $state<number | null>(null);

    onMount(async () => {
        const clientSecret = $page.url.searchParams.get('payment_intent_client_secret');
        paymentIntentId = $page.url.searchParams.get('payment_intent');
        const redirectStatus = $page.url.searchParams.get('redirect_status');

        if (!clientSecret || !paymentIntentId) {
            errorMessage = $i18n.donations.status.errorMissingParams;
            status = 'error';
            return;
        }

        // No need to fetch Stripe client-side here if just checking status
        // Can add if needed for more details later

        if (redirectStatus === 'succeeded') {
            status = 'success';
            // Optionally fetch amount from backend if needed, but for now just show success
            // Try to get amount from local storage or pass via state if possible
        } else if (redirectStatus === 'processing') {
            status = 'processing';
        } else {
            status = 'error';
            // Try to get a more specific error message if provided by Stripe
            errorMessage = $page.url.searchParams.get('error_message') || $i18n.donations.status.errorGeneric;
        }
    });
</script>

<svelte:head>
    <title>{$i18n.donations.status.title} - Veille Médicale</title>
</svelte:head>

<main class="flex min-h-screen flex-col items-center justify-center bg-black px-4 py-12 text-white">
    <div class="w-full max-w-md rounded-lg bg-gray-800 p-8 text-center shadow-lg">
        {#if status === 'loading'}
            <Loader class="mx-auto mb-4 h-16 w-16 animate-spin text-orange-500" />
            <h1 class="mb-2 text-2xl font-semibold">{$i18n.donations.status.loadingTitle}</h1>
            <p class="text-gray-400">{$i18n.donations.status.loadingText}</p>
        {:else if status === 'success'}
            <CheckCircle class="mx-auto mb-4 h-16 w-16 text-green-500" />
            <h1 class="mb-2 text-2xl font-semibold">{$i18n.donations.status.successTitle}</h1>
            <p class="text-gray-300">
                {$i18n.donations.status.successText}
                {#if paymentIntentId}
                    <span class="mt-2 block text-xs text-gray-500">ID: {paymentIntentId}</span>
                {/if}
            </p>
            <a href="/" class="mt-6 inline-block rounded-lg bg-orange-600 px-6 py-2 font-medium text-white transition hover:bg-orange-700">
                {$i18n.donations.status.backHomeButton}
            </a>
        {:else if status === 'processing'}
             <Loader class="mx-auto mb-4 h-16 w-16 animate-spin text-orange-500" />
             <h1 class="mb-2 text-2xl font-semibold">{$i18n.donations.status.processingTitle}</h1>
             <p class="text-gray-300">{$i18n.donations.status.processingText}</p>
             {#if paymentIntentId}
                <span class="mt-2 block text-xs text-gray-500">ID: {paymentIntentId}</span>
             {/if}
             <a href="/" class="mt-6 inline-block rounded-lg bg-gray-600 px-6 py-2 font-medium text-white transition hover:bg-gray-700">
                {$i18n.donations.status.backHomeButton}
            </a>
        {:else if status === 'error'}
            <XCircle class="mx-auto mb-4 h-16 w-16 text-red-500" />
            <h1 class="mb-2 text-2xl font-semibold">{$i18n.donations.status.errorTitle}</h1>
            <p class="text-gray-300">
                {errorMessage || $i18n.donations.status.errorGeneric}
            </p>
             {#if paymentIntentId}
                <span class="mt-2 block text-xs text-gray-500">ID: {paymentIntentId}</span>
             {/if}
            <a href="/donations" class="mt-6 inline-block rounded-lg bg-orange-600 px-6 py-2 font-medium text-white transition hover:bg-orange-700">
                {$i18n.donations.status.retryButton}
            </a>
        {/if}
    </div>
</main>