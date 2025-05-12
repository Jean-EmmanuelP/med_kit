<!-- $lib/components/auth/SignUpForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	export let email = '';
	export let password = '';
	export let errorMessage = '';
	export let isLoading = false;

	let successMessage = '';
	let confirmPassword = '';
	let showPassword = false;

	const dispatch = createEventDispatcher();

	async function handleSubmit(event) {
		event.preventDefault();
		errorMessage = '';
		successMessage = '';

		if (!email || !password || !confirmPassword) {
			errorMessage = 'Veuillez remplir tous les champs.';
			return;
		}
		if (password !== confirmPassword) {
			errorMessage = 'Les mots de passe ne correspondent pas.';
			return;
		}
		if (password.length < 6) {
			errorMessage = 'Le mot de passe doit contenir au moins 6 caractères.';
			return;
		}

		isLoading = true;

		try {
			// NOTE: These fields are sent because the original backend might expect them,
			// even if the simplified action doesn't use them directly for validation.
			const firstName = email.split('@')[0] || '';
			const lastName = '';
			const dateOfBirth = '';

			const formData = new FormData();
			formData.append('first_name', firstName);
			formData.append('last_name', lastName);
			formData.append('email', email);
			formData.append('password', password);
			formData.append('date_of_birth', dateOfBirth);

			// No disciplines or frequency sent from this simplified form

			const response = await fetch('/signup', { // Assumes this component lives on a page with this action
				method: 'POST',
				body: formData
			});

			// Attempt to parse error JSON only if response is not ok and looks like JSON
			if (!response.ok && response.headers.get('content-type')?.includes('application/json')) {
				const result = await response.json();
				errorMessage = result.error || `Erreur ${response.status}`; // Use error from JSON or generic
			} else if (!response.ok) {
                 errorMessage = `Erreur lors de l'inscription (${response.status})`;
            } else {
				// Success: Assume backend handled user/profile creation & session
                isLoading = false;
                successMessage = 'Compte créé avec succès ! Vous allez être redirigé...';
				dispatch('signupSuccess');

				setTimeout(() => {
					// Redirect target depends on whether backend auto-logs in
					// If Supabase email confirmation is ON, user might not be logged in yet.
					// Adjust target (/account, /login, /ma-veille) as needed based on backend behavior.
					window.location.href = '/ma-veille';
				}, 2500);
				return;
			}
		} catch (error) {
			errorMessage = 'Erreur de connexion lors de l’inscription.';
			console.error("Signup Fetch Error:", error); // Keep one log for debugging network errors
		} finally {
            if (!successMessage) {
			    isLoading = false;
            }
		}
	}

	function togglePasswordVisibility() {
		showPassword = !showPassword;
	}
</script>

{#if successMessage}
	<div class="rounded-md bg-green-50 p-4 text-center">
		<div class="flex flex-col items-center">
			<svg class="h-12 w-12 text-green-400 mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
			</svg>
			<p class="text-lg font-medium text-green-800">{successMessage}</p>
		</div>
	</div>
{:else}
	<form on:submit={handleSubmit} class="space-y-4">
		<div>
			<label for="email" class="block text-sm font-medium text-gray-700">Email</label>
			<input
				id="email"
				name="email"
				type="email"
				bind:value={email}
				disabled={isLoading}
				class="mt-1 w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-50"
				placeholder="votre.email@example.com"
				required
			/>
		</div>

		<div>
			<label for="password" class="block text-sm font-medium text-gray-700">Mot de passe</label>
			<div class="relative mt-1">
				<input
					id="password"
					name="password"
					type={showPassword ? 'text' : 'password'}
					bind:value={password}
					disabled={isLoading}
					class="w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 pr-10 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-50"
					placeholder="••••••••"
					required
					minlength="6"
				/>
				<button
					type="button"
					on:click={togglePasswordVisibility}
					class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 focus:outline-none"
					aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
					disabled={isLoading}
				>
					{#if showPassword}
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L6.228 6.228" /></svg>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
					{/if}
				</button>
			</div>
		</div>

		<div>
			<label for="confirmPassword" class="block text-sm font-medium text-gray-700">Confirmer le mot de passe</label>
			<div class="relative mt-1">
				<input
					id="confirmPassword"
					name="confirmPassword"
					type={showPassword ? 'text' : 'password'}
					bind:value={confirmPassword}
					disabled={isLoading}
					class="w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 pr-10 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-50"
					placeholder="••••••••"
					required
					minlength="6"
				/>
			</div>
		</div>

		{#if errorMessage}
			<p class="text-sm text-red-600 pt-2">{errorMessage}</p>
		{/if}

		<div class="pt-2">
			<button
				type="submit"
				disabled={isLoading}
				class="w-full rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400"
			>
				{#if isLoading}
					<svg class="mr-2 inline-block h-5 w-5 animate-spin text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
					Inscription en cours...
				{:else}
					S’inscrire
				{/if}
			</button>
		</div>
	</form>
{/if}

<style>
	.relative input:focus + button {
		z-index: 10; /* Ensure visibility button is clickable when input is focused */
	}
</style>