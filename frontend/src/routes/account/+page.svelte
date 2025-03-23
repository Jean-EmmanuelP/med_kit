<script>
	import { i18n } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase';
	import { onMount } from 'svelte';
	import * as Select from '$lib/components/ui/select/index.js';

	// Récupération des props avec $props rune
	const { data, form } = $props();

	// Définir les variables réactives avec $state
	let firstName = $state($userProfileStore?.first_name || '');
	let lastName = $state($userProfileStore?.last_name || '');
	let status = $state($userProfileStore?.status || '');
	let specialty = $state($userProfileStore?.specialty || '');
	let profilePicture = $state($userProfileStore?.profile_picture || null);
	let selectedDisciplines = $state(data.userPreferences?.disciplines || []);
	let selectedNotificationFreq = $state(
		data.userPreferences?.notificationFrequency || 'tous_les_jours'
	);
	let dateOfBirth = $state(data.userPreferences?.date_of_birth || '');
	let isLoading = $state(false);

	// Trier les disciplines par ordre alphabétique
	const sortedDisciplines = $state(
		data.disciplinesList.sort((a, b) => a.localeCompare(b, 'fr', { sensitivity: 'base' }))
	);

	// Compute the display label for the selected disciplines
	const triggerDisciplineContent = $derived(
		selectedDisciplines.length > 0
			? selectedDisciplines.slice(0, 2).join(', ') +
					(selectedDisciplines.length > 2 ? ` +${selectedDisciplines.length - 2}` : '')
			: 'Sélectionner des spécialités'
	);

	// Compute the display label for the selected notification frequency
	const triggerNotificationContent = $derived(
		$i18n.login.notificationOptions[notificationOptions.indexOf(selectedNotificationFreq)] ||
			'Choisir une fréquence'
	);

	// Compute the display label for the selected status
	const triggerStatusContent = $derived(
		$i18n.login.statusOptions.includes(status) ? status : 'Choisissez un statut'
	);

	// Populate userProfileStore with data from the server
	onMount(() => {
		if (data.userProfile) {
			userProfileStore.set(data.userProfile);
		}
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

	function toggleDiscipline(discipline) {
		if (selectedDisciplines.includes(discipline)) {
			selectedDisciplines = selectedDisciplines.filter((d) => d !== discipline);
		} else {
			selectedDisciplines = [...selectedDisciplines, discipline];
		}
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

			userProfileStore.set(null);
			window.location.href = '/login';
		} catch (error) {
			console.error('Erreur inattendue lors de la déconnexion :', error);
		}
	}
</script>

<div class="min-h-screen bg-black px-4 py-12 text-white">
	<div class="mx-auto max-w-4xl">
		<!-- En-tête -->
		<h1 class="mb-8 text-4xl font-bold text-white">Mon compte</h1>

		{#if data.error}
			<p class="mb-6 text-red-500">{data.error}</p>
		{:else}
			<!-- Section pour modifier les informations personnelles -->
			<div class="mb-12">
				<h2 class="mb-6 text-2xl font-semibold text-white">Vos informations</h2>
				<form on:submit|preventDefault={handleSubmit} class="space-y-8">
					<!-- Nom et Prénom sur la même ligne pour web -->
					<div class="flex flex-col space-y-6 sm:flex-row sm:space-y-0 sm:space-x-4">
						<div class="w-full sm:w-1/2">
							<label for="firstName" class="mb-2 block text-sm font-medium text-gray-300">
								{$i18n.login.firstName}
							</label>
							<input
								id="firstName"
								type="text"
								bind:value={firstName}
								class="mt-1 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-700"
								required
							/>
						</div>
						<div class="w-full sm:w-1/2">
							<label for="lastName" class="mb-2 block text-sm font-medium text-gray-300">
								{$i18n.login.lastName}
							</label>
							<input
								id="lastName"
								type="text"
								bind:value={lastName}
								class="mt-1 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-700"
								required
							/>
						</div>
					</div>

					<!-- Statut et Spécialité sur la même ligne pour web -->
					<div class="flex flex-col space-y-6 sm:flex-row sm:space-y-0 sm:space-x-4">
						<div class="w-full sm:w-1/2">
							<label for="status" class="mb-2 block text-sm font-medium text-gray-300">
								{$i18n.account.status}
							</label>
							<div class="relative w-full">
								<Select.Root type="single" name="status" bind:value={status}>
									<Select.Trigger
										class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
									>
										{triggerStatusContent}
									</Select.Trigger>
									<Select.Content
										class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
									>
										<Select.Group>
											<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400"
												>Statuts</Select.GroupHeading
											>
											{#each $i18n.login.statusOptions as option (option)}
												<Select.Item
													value={option}
													label={option}
													class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
												/>
											{/each}
										</Select.Group>
									</Select.Content>
								</Select.Root>
							</div>
						</div>
						<div class="w-full sm:w-1/2">
							<label for="specialty" class="mb-2 block text-sm font-medium text-gray-300">
								{$i18n.account.specialty}
							</label>
							<input
								id="specialty"
								type="text"
								bind:value={specialty}
								class="mt-1 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-700"
								placeholder="Ex: Médecine Générale, Diabétologie"
							/>
						</div>
					</div>

					<!-- Date de naissance -->
					<div>
						<label for="dateOfBirth" class="mb-2 block text-sm font-medium text-gray-300">
							{$i18n.login.dateOfBirth}
						</label>
						<input
							id="dateOfBirth"
							type="date"
							bind:value={dateOfBirth}
							class="mt-1 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-700"
						/>
					</div>

					<br />

					<h2 class="mb-6 text-2xl font-semibold text-white">Vos préférences</h2>

					<!-- Spécialités que je souhaite suivre -->
					<div>
						<label class="mb-2 block text-sm font-medium text-gray-300">
							{$i18n.account.disciplinesToFollow}
						</label>
						<div class="relative w-full">
							<Select.Root
								type="multiple"
								name="selectedDisciplines"
								bind:value={selectedDisciplines}
							>
								<Select.Trigger
									class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
								>
									{triggerDisciplineContent}
								</Select.Trigger>
								<Select.Content
									class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
								>
									<Select.Group>
										<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400"
											>Spécialités</Select.GroupHeading
										>
										{#each sortedDisciplines as discipline (discipline)}
											<Select.Item
												value={discipline}
												label={discipline}
												class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
											/>
										{/each}
									</Select.Group>
								</Select.Content>
							</Select.Root>
						</div>
					</div>

					<!-- Fréquence des notifications -->
					<div>
						<label class="mb-2 block text-sm font-medium text-gray-300">
							{$i18n.account.notificationFrequency}
						</label>
						<div class="relative w-full">
							<Select.Root
								type="single"
								name="selectedNotificationFreq"
								bind:value={selectedNotificationFreq}
							>
								<Select.Trigger
									class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
								>
									{triggerNotificationContent}
								</Select.Trigger>
								<Select.Content
									class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
								>
									<Select.Group>
										<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400"
											>Fréquences</Select.GroupHeading
										>
										{#each notificationOptions as option (option)}
											<Select.Item
												value={option}
												label={$i18n.login.notificationOptions[notificationOptions.indexOf(option)]}
												class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
											/>
										{/each}
									</Select.Group>
								</Select.Content>
							</Select.Root>
						</div>
					</div>

					<button
						type="submit"
						disabled={isLoading}
						class="mt-6 flex w-full items-center justify-center rounded-lg bg-orange-600 px-8 py-3 text-white transition-all duration-300 hover:bg-orange-700 disabled:cursor-not-allowed disabled:bg-gray-600"
					>
						{#if isLoading}
							<svg class="mr-2 h-5 w-5 animate-spin text-white" viewBox="0 0 24 24">
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
							<span>{$i18n.account.saveChanges}</span>
						{:else}
							{$i18n.account.saveChanges}
						{/if}
					</button>
				</form>
			</div>
		{/if}

		<!-- Bouton de déconnexion en bas -->
		{#if $userProfileStore}
			<div class="mt-12 text-left">
				<h2 class="mb-4 text-2xl font-bold text-white">Se déconnecter</h2>
				<button
					on:click={handleLogout}
					class="rounded-lg bg-black px-6 py-3 text-white transition-colors duration-200 hover:bg-gray-800"
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

	/* Custom scrollbar for the select dropdown */
	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #1f2937;
	}

	.scrollbar-thin::-webkit-scrollbar {
		width: 8px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: #1f2937;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6;
		border-radius: 6px;
		border: 2px solid #1f2937;
	}
</style>
