<script>
	import { createEventDispatcher } from 'svelte';
	import { i18n } from '$lib/i18n';

	export let firstName = '';
	export let lastName = '';
	export let email = '';
	export let password = '';
	export let disciplines = [];
	export let notificationFreq = 'tous_les_jours';
	export let dateOfBirth = '';
	export let specialty = '';
	export let status = '';
	export let errorMessage = '';
	export let successMessage = '';
	export let isLoading = false;

	const dispatch = createEventDispatcher();

	// Alphabetically ordered disciplines list with missing ones added
	const availableDisciplines = [
		'Allergie et immunologie',
		'Anesthésie - Réanimation',
		'Cardiologie',
		'Chirurgie cardiaque',
		'Chirurgie digestive',
		'Chirurgie ORL',
		'Chirurgie orthopédique',
		'Chirurgie plastique',
		'Chirurgie thoracique',
		'Chirurgie vasculaire',
		'Dermatologie',
		'Endocrinologie-Diabétologie-Nutrition',
		'Génétique',
		'Gériatrie',
		'Gynécologie-obstétrique',
		'Hématologie',
		'Hépato-Gastroentérologie',
		'Maladies infectieuses',
		'Médecine de la douleur',
		'Médecine du Travail',
		'Médecine Générale',
		'Médecine Interne',
		'Médecine physique et réadaptation',
		'Néphrologie',
		'Neurochirurgie',
		'Neurologie',
		'Oncologie',
		'Ophtalmologie',
		'Pédiatrie',
		'Pneumologie',
		'Psychiatrie',
		'Rhumatologie',
		'Santé Publique',
		'Urgences',
		'Urologie'
	];

	// Variable pour la recherche
	let searchQuery = '';

	// Fonction pour basculer une discipline
	function toggleDiscipline(discipline) {
		if (disciplines.includes(discipline)) {
			disciplines = disciplines.filter((d) => d !== discipline);
		} else {
			disciplines = [...disciplines, discipline];
		}
	}

	// Filtrer les disciplines en fonction de la recherche
	$: filteredDisciplines = availableDisciplines.filter((discipline) =>
		discipline.toLowerCase().includes(searchQuery.toLowerCase())
	);

	// Gestion de la soumission avec chargement
	async function handleSubmit(event) {
		event.preventDefault();
		isLoading = true; // Activer le chargement avant d'envoyer au serveur

		try {
			const formData = new FormData(event.target);
			const response = await fetch('/signup', {
				method: 'POST',
				body: formData
			});

			const result = await response.json();

			if (result.error) {
				// Vérifier si l'erreur est "user_already_exists"
				if (result.error.includes('user_already_exists')) {
					errorMessage =
						'Cet email est déjà utilisé. Veuillez vous connecter ou utiliser un autre email.';
				} else {
					errorMessage = result.error; // Autres erreurs
				}
				successMessage = '';
			} else if (result.success) {
				successMessage = result.message;
				errorMessage = '';
				dispatch('signupSuccess'); // Événement pour informer le parent
				if (result.redirectTo) {
					window.location.href = result.redirectTo; // Redirection manuelle si nécessaire
				}
			}
		} catch (error) {
			errorMessage = 'Erreur lors de la soumission : ' + error.message;
			successMessage = '';
		} finally {
			isLoading = false; // Désactiver le chargement après la réponse
		}
	}
</script>

<div class="space-y-6">
	<div>
		<label for="firstName" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.firstName}</label
		>
		<input
			id="firstName"
			name="first_name"
			type="text"
			bind:value={firstName}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			required
		/>
	</div>

	<div>
		<label for="lastName" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.lastName}</label
		>
		<input
			id="lastName"
			name="last_name"
			type="text"
			bind:value={lastName}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			required
		/>
	</div>

	<div>
		<label for="email" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.emailLabel}</label
		>
		<input
			id="email"
			name="email"
			type="email"
			bind:value={email}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			placeholder={$i18n.login.emailPlaceholder}
			required
		/>
	</div>

	<div>
		<label for="password" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.passwordLabel}</label
		>
		<input
			id="password"
			name="password"
			type="password"
			bind:value={password}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			placeholder={$i18n.login.passwordPlaceholder}
			required
		/>
	</div>

	<div>
		<label for="dateOfBirth" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.dateOfBirth}</label
		>
		<input
			id="dateOfBirth"
			name="date_of_birth"
			type="date"
			bind:value={dateOfBirth}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
		/>
	</div>

	<div>
		<label for="specialty" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.specialty}</label
		>
		<input
			id="specialty"
			name="specialty"
			type="text"
			bind:value={specialty}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			placeholder={$i18n.login.specialtyPlaceholder}
		/>
	</div>

	<div>
		<label for="status" class="block text-sm font-medium text-gray-700">{$i18n.login.status}</label>
		<select
			id="status"
			name="status"
			bind:value={status}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
		>
			<option value="" disabled>Choisissez un statut</option>
			{#each $i18n.login.statusOptions as option}
				<option value={option}>{option}</option>
			{/each}
		</select>
	</div>

	<div>
		<label class="block text-sm font-medium text-gray-700">{$i18n.login.disciplines}</label>
		<div class="relative mt-1">
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Rechercher une discipline..."
				class="w-full rounded-t-lg border border-gray-300 px-4 py-2 pr-10 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			/>
			<div class="max-h-32 overflow-y-auto rounded-b-lg border border-t-0 border-gray-300">
				{#each filteredDisciplines as discipline}
					<label class="flex items-center space-x-2 px-4 py-2 hover:bg-gray-100">
						<input
							type="checkbox"
							name="disciplines"
							value={discipline}
							checked={disciplines.includes(discipline)}
							on:change={() => toggleDiscipline(discipline)}
							class="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
						/>
						<span class="text-gray-700">{discipline}</span>
					</label>
				{/each}
			</div>
		</div>
	</div>

	<div>
		<label for="notificationFreq" class="block text-sm font-medium text-gray-700"
			>{$i18n.login.notifications}</label
		>
		<select
			id="notificationFreq"
			name="notification_frequency"
			bind:value={notificationFreq}
			class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
			required
		>
			<option value="" disabled>{$i18n.login.notificationsPlaceholder}</option>
			{#each $i18n.login.notificationOptions as option}
				<option value={option.replace(/ /g, '_')}>{option}</option>
			{/each}
		</select>
	</div>

	<button
		type="submit"
		disabled={isLoading}
		class="w-full rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:bg-blue-400"
	>
		{#if isLoading}
			<svg class="mr-2 inline-block h-5 w-5 animate-spin text-white" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				/>
			</svg>
			Inscription en cours...
		{:else}
			{$i18n.login.submitSignup}
		{/if}
	</button>
</div>
