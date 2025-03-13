<!-- +page.svelte -->
<script>
	import { i18n } from '$lib/i18n';
	import SignUpForm from '$lib/components/auth/SignUpForm.svelte';
	import MessageDisplay from '$lib/components/auth/MessageDisplay.svelte';

	// Variables pour les étapes
	let email = '';
	let password = '';
	let disciplines = [];
	let notificationFreq = 'tous_les_jours';
	let errorMessage = '';
	let successMessage = '';
	let isLoading = false;
</script>

<main class="flex min-h-screen items-center justify-center bg-black px-4 py-12">
	<div
		class="hover:shadow-3xl flex w-full max-w-md shadow-2xl transition-all duration-300 sm:max-w-[60vw]"
	>
		<div class="w-full rounded-lg bg-white p-8">
			<h1 class="mb-6 text-left text-3xl font-bold tracking-tight capitalize">
				{$i18n.login.title}
			</h1>

			<MessageDisplay bind:errorMessage bind:successMessage />
			{#if isLoading}
				<div class="mb-4 flex items-center justify-center space-x-2 rounded-lg bg-blue-50 p-4">
					<div class="h-5 w-5 animate-spin rounded-full border-4 border-t-blue-500"></div>
					<p class="font-medium text-blue-600">Inscription en cours...</p>
				</div>
			{/if}

			<SignUpForm
				bind:email
				bind:password
				bind:disciplines
				bind:notificationFreq
				bind:errorMessage
				bind:successMessage
				bind:isLoading
			/>
			<a href="/login">
				<p class="mt-4 text-center text-sm text-gray-500">
					{$i18n.login.alreadyHaveAccount}
				</p>
			</a>
		</div>
	</div>
</main>
