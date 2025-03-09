<script>
	import { i18n } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase';
	import { onMount } from 'svelte';

	let { data, form } = $props();

	let firstName = $userProfileStore?.first_name || '';
	let lastName = $userProfileStore?.last_name || '';
	let status = $userProfileStore?.status || '';
	let specialty = $userProfileStore?.specialty || '';
	let profilePicture = $userProfileStore?.profile_picture || null;
	let selectedDisciplines = $state(data.userPreferences?.disciplines || []); // Utilise $state pour réactivité
	let selectedNotificationFreq = data.userPreferences?.notificationFrequency || 'tous_les_jours';
	let dateOfBirth = data.userPreferences?.date_of_birth || '';
	let isSpecialtiesOpen = $state(false); // Nouvelle variable pour les spécialités
	let isNotificationsOpen = $state(false); // Nouvelle variable pour les notifications
	let isLoading = false;

	// Trier les disciplines par ordre alphabétique
	const sortedDisciplines = data.disciplinesList.sort((a, b) =>
		a.localeCompare(b, 'fr', { sensitivity: 'base' })
	);

	// Populate userProfileStore with data from the server
	onMount(() => {
		if (data.userProfile) {
			userProfileStore.set(data.userProfile);
		}

		// Update local state with userProfileStore values
		firstName = $userProfileStore?.first_name || '';
		lastName = $userProfileStore?.last_name || '';
		status = $userProfileStore?.status || '';
		specialty = $userProfileStore?.specialty || '';
		profilePicture = $userProfileStore?.profile_picture || null;
		selectedDisciplines = data.userPreferences?.disciplines || [];
		selectedNotificationFreq = data.userPreferences?.notificationFrequency || 'tous_les_jours';
		dateOfBirth = data.userPreferences?.date_of_birth || '';
	});

	const notificationOptions = [
		'tous_les_jours',
		'tous_les_2_jours',
		'tous_les_3_jours',
		'1_fois_par_semaine',
		'tous_les_15_jours',
		'1_fois_par_mois'
	];

	const notificationDisplayOptions = {
		tous_les_jours: $i18n.login.notificationOptions[0],
		tous_les_2_jours: $i18n.login.notificationOptions[1],
		tous_les_3_jours: $i18n.login.notificationOptions[2],
		'1_fois_par_semaine': $i18n.login.notificationOptions[3],
		tous_les_15_jours: $i18n.login.notificationOptions[4],
		'1_fois_par_mois': $i18n.login.notificationOptions[5]
	};

	function toggleDiscipline(discipline) {
		if (selectedDisciplines.includes(discipline)) {
			selectedDisciplines = selectedDisciplines.filter((d) => d !== discipline);
		} else {
			selectedDisciplines = [...selectedDisciplines, discipline];
		}
	}

	function selectNotificationFreq(option) {
		selectedNotificationFreq = option;
		isNotificationsOpen = false; // Ferme uniquement le menu des notifications
	}

	async function handleSubmit() {
		if (isLoading) return;
		isLoading = true;

		try {
			const { error } = await supabase
				.from('user_profiles')
				.update({
					first_name: firstName,
					last_name: lastName,
					status,
					specialty,
					disciplines: selectedDisciplines,
					notification_frequency: selectedNotificationFreq,
					date_of_birth: dateOfBirth || null
				})
				.eq('id', $userProfileStore.id);

			if (error) throw error;

			userProfileStore.set({
				...$userProfileStore,
				first_name: firstName,
				last_name: lastName,
				status,
				specialty,
				disciplines: selectedDisciplines,
				notification_frequency: selectedNotificationFreq,
				date_of_birth: dateOfBirth
			});

			alert('Modifications enregistrées avec succès.');
		} catch (error) {
			console.error('Error updating profile:', error);
			alert('Erreur lors de la mise à jour du profil.');
		} finally {
			isLoading = false;
		}
	}

	async function handleLogout() {
		try {
			const response = await fetch('/logout', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				const { error } = await response.json();
				console.error('Erreur lors de la déconnexion :', error);
				return;
			}

			userProfileStore.set(null); // Réinitialiser l'état immédiatement
			window.location.href = '/login'; // Recharge l'onglet et redirige vers /login
		} catch (error) {
			console.error('Erreur inattendue lors de la déconnexion :', error);
		}
	}
</script>

<div class="min-h-screen bg-gradient-to-br from-gray-50 to-white px-4 py-12">
	<div class="mx-auto max-w-4xl">
		<h1 class="animate-fade-in mb-8 text-4xl font-bold text-gray-900">Mon Compte</h1>

		{#if data.error}
			<p class="text-gray-900">{data.error}</p>
		{:else}
			<!-- Section pour modifier les informations personnelles -->
			<div class="mb-12">
				<h2 class="animate-fade-in-delayed mb-6 text-2xl font-semibold text-gray-900">
					Paramètres
				</h2>
				<form on:submit|preventDefault={handleSubmit} class="space-y-8">
					<!-- Photo (not implemented for now) -->
					<div>
						<label for="profilePicture" class="mb-2 block text-sm font-medium text-gray-900">
							{$i18n.account.profilePicture}
						</label>
						<input
							id="profilePicture"
							type="text"
							value="Non implémenté"
							disabled
							class="mt-1 w-full rounded-lg border border-gray-300 bg-gray-100 px-4 py-3 text-gray-900 transition-all duration-200"
						/>
						<p class="mt-1 text-sm text-gray-600">
							La gestion des photos n’est pas encore implémentée.
						</p>
					</div>

					<div>
						<label for="firstName" class="mb-2 block text-sm font-medium text-gray-900">
							{$i18n.login.firstName}
						</label>
						<input
							id="firstName"
							type="text"
							bind:value={firstName}
							class="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
							required
						/>
					</div>

					<div>
						<label for="lastName" class="mb-2 block text-sm font-medium text-gray-900">
							{$i18n.login.lastName}
						</label>
						<input
							id="lastName"
							type="text"
							bind:value={lastName}
							class="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
							required
						/>
					</div>

					<div>
						<label for="status" class="mb-2 block text-sm font-medium text-gray-900">
							{$i18n.account.status}
						</label>
						<select
							id="status"
							bind:value={status}
							class="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
							required
						>
							<option value="" disabled>Choisissez un statut</option>
							{#each $i18n.login.statusOptions as option}
								<option value={option}>{option}</option>
							{/each}
						</select>
					</div>

					<div>
						<label for="specialty" class="mb-2 block text-sm font-medium text-gray-900">
							{$i18n.account.specialty}
						</label>
						<input
							id="specialty"
							type="text"
							bind:value={specialty}
							class="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
							placeholder="Ex: Médecine Générale, Diabétologie"
						/>
					</div>

					<div>
						<label for="dateOfBirth" class="mb-2 block text-sm font-medium text-gray-900">
							{$i18n.login.dateOfBirth}
						</label>
						<input
							id="dateOfBirth"
							type="date"
							bind:value={dateOfBirth}
							class="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
						/>
					</div>

					<!-- Section pour changer les spécialités (menu déroulant avec choix multiples) -->
					<div class="mb-12">
						<h3 class="mb-4 text-lg font-semibold text-gray-900">
							Spécialités que je souhaite suivre
						</h3>
						<div class="relative">
							<button
								type="button"
								on:click={() => {
									isSpecialtiesOpen = !isSpecialtiesOpen; // Ouvre/ferme uniquement les spécialités
									isNotificationsOpen = false; // Ferme les notifications si ouvertes
								}}
								class="flex w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-4 py-3 text-left text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
							>
								<span class="flex-1 truncate">
									{selectedDisciplines.length > 0
										? selectedDisciplines.slice(0, 2).join(', ') +
											(selectedDisciplines.length > 2 ? ` +${selectedDisciplines.length - 2}` : '')
										: 'Sélectionner des spécialités'}
								</span>
								<svg
									class="ml-2 h-5 w-5"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 9l-7 7-7-7"
									/>
								</svg>
							</button>
							{#if isSpecialtiesOpen}
								<div
									class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-gray-300 bg-white shadow-lg"
								>
									{#each sortedDisciplines as discipline}
										<label
											class="flex cursor-pointer items-center px-4 py-2 transition-colors duration-200 hover:bg-gray-100"
										>
											<input
												type="checkbox"
												checked={selectedDisciplines.includes(discipline)}
												on:change={() => toggleDiscipline(discipline)}
												class="mr-2 h-4 w-4 text-blue-500 focus:ring-blue-500"
											/>
											<span class="text-gray-900">{discipline}</span>
										</label>
									{/each}
								</div>
							{/if}
						</div>
					</div>

					<!-- Section pour changer la fréquence des notifications -->
					<div class="mb-12">
						<h3 class="mb-4 text-lg font-semibold text-gray-900">Fréquence des notifications</h3>
						<div class="flex flex-col sm:flex-row sm:items-center sm:space-x-4">
							<!-- On mobile, show a select dropdown -->
							<select
								bind:value={selectedNotificationFreq}
								class="mb-3 w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200 sm:hidden"
							>
								{#each notificationOptions as option}
									<option value={option}>{notificationDisplayOptions[option]}</option>
								{/each}
							</select>

							<!-- On desktop, show a button with a dropdown menu -->
							<div class="relative hidden sm:block">
								<button
									type="button"
									on:click={() => {
										isNotificationsOpen = !isNotificationsOpen; // Ouvre/ferme uniquement les notifications
										isSpecialtiesOpen = false; // Ferme les spécialités si ouvertes
									}}
									class="w-64 rounded-lg border border-gray-300 bg-white px-4 py-3 text-left text-gray-900 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
								>
									{notificationDisplayOptions[selectedNotificationFreq]}
								</button>
								{#if isNotificationsOpen}
									<div
										class="absolute z-10 mt-1 w-64 rounded-lg border border-gray-300 bg-white shadow-lg"
									>
										{#each notificationOptions as option}
											<button
												type="button"
												on:click={() => selectNotificationFreq(option)}
												class="block w-full px-4 py-2 text-left text-gray-900 hover:bg-gray-100"
											>
												{notificationDisplayOptions[option]}
											</button>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					</div>

					<button
						type="submit"
						disabled={isLoading}
						class="relative rounded-lg bg-black px-8 py-3 text-white transition-all duration-300 hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-600"
					>
						{#if isLoading}
							<svg
								class="absolute top-1/2 left-4 mr-2 h-5 w-5 -translate-y-1/2 transform animate-spin text-white"
								viewBox="0 0 24 24"
							>
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
							<span class="opacity-0">{$i18n.account.saveChanges}</span>
						{:else}
							{$i18n.account.saveChanges}
						{/if}
					</button>
				</form>
			</div>
		{/if}

		<!-- Bouton de déconnexion en bas -->
		{#if $userProfileStore}
			<div class="mt-12 text-center">
				<button
					on:click={handleLogout}
					class="rounded-lg bg-red-600 px-6 py-3 text-white transition-colors duration-200 hover:bg-red-700"
				>
					{$i18n.header.logout}
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Fade-in animation for title */
	@keyframes fade-in {
		0% {
			opacity: 0;
			transform: translateY(10px);
		}
		100% {
			opacity: 1;
			transform: translateY(0);
		}
	}
	.animate-fade-in {
		animation: fade-in 1s ease-out;
	}

	/* Delayed fade-in for subtitle and other elements */
	@keyframes fade-in-delayed {
		0% {
			opacity: 0;
			transform: translateY(10px);
		}
		100% {
			opacity: 1;
			transform: translateY(0);
		}
	}
	.animate-fade-in-delayed {
		animation: fade-in-delayed 1.2s ease-out;
	}
</style>
