<script lang="ts">
    import DonationForm from '$lib/components/DonationForm.svelte';
    import { i18n } from '$lib/i18n';

    // Define props or logic specific to the donation page if needed
    // For now, it just renders the form.
</script>

<svelte:head>
    <title>{$i18n.donations.pageTitle} - Veille Médicale</title>
    <meta name="description" content={$i18n.donations.metaDescription} />
</svelte:head>

<main class="min-h-screen bg-black px-4 py-12 pt-20 text-white">
    <div class="mx-auto max-w-lg">
        <h1 class="mb-6 text-center text-3xl font-bold tracking-tight">
            {$i18n.donations.pageTitle}
        </h1>
        <p class="mb-8 text-center text-lg text-gray-300">
            {$i18n.donations.introText}
        </p>

        <div class="rounded-lg bg-gray-800 p-6 shadow-lg md:p-8">
            <DonationForm />
        </div>

        <p class="mt-8 text-center text-sm text-gray-500">
            {$i18n.donations.securityNote}
        </p>
    </div>
</main>