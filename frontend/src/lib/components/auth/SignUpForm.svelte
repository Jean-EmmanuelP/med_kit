<!-- $lib/components/auth/SignUpForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	// Variables exportées
	export let email = '';
	export let password = '';
	export let disciplines = [];
	export let notificationFreq = 'tous_les_jours';
	export let errorMessage = '';
	export let successMessage = '';
	export let isLoading = false;

	// État global
	let step = 1;
	let showDisciplineModal = false;
	let showNotificationModal = false;

	const dispatch = createEventDispatcher();

	// Liste des disciplines disponibles
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

	// Options de fréquence des notifications
	const notificationOptions = [
		'Tous les jours',
		'Tous les 2 jours',
		'Tous les 3 jours',
		'1 fois par semaine',
		'Tous les 15 jours',
		'1 fois par mois'
	];

	// Recherche dans les disciplines
	let searchQuery = '';
	$: filteredDisciplines = availableDisciplines.filter((discipline) =>
		discipline.toLowerCase().includes(searchQuery.toLowerCase())
	);

	// Basculer une discipline
	function toggleDiscipline(discipline) {
		if (disciplines.includes(discipline)) {
			disciplines = disciplines.filter((d) => d !== discipline);
		} else {
			disciplines = [...disciplines, discipline];
		}
	}

	// Supprimer une discipline depuis les bulles
	function removeDiscipline(discipline) {
		disciplines = disciplines.filter((d) => d !== discipline);
	}

	// Gestion de la soumission
	async function handleSubmit(event) {
		event.preventDefault();

		if (step === 1) {
			// Vérification simple avant de passer à l'étape 2
			if (!email || !password) {
				errorMessage = 'Veuillez remplir l’email et le mot de passe.';
				return;
			}
			step = 2; // Passer à l'étape 2
			errorMessage = '';
			showDisciplineModal = true; // Ouvre la modal pour les disciplines
		} else if (step === 2) {
			if (disciplines.length === 0) {
				errorMessage = 'Veuillez sélectionner au moins une discipline.';
				return;
			}
			step = 3; // Passer à l'étape 3
			errorMessage = '';
			showDisciplineModal = false; // Ferme la modal des disciplines
			showNotificationModal = true; // Ouvre la modal pour les notifications
		} else if (step === 3) {
			isLoading = true;
			errorMessage = '';
			successMessage = '';

			try {
				// Extraction du "first_name" depuis l'email
				const firstName = email.split('@')[0];
				const lastName = ''; // Pas de nom de famille
				const dateOfBirth = ''; // Pas de date de naissance
				const status = ''; // Pas de statut

				const formData = new FormData();
				formData.append('first_name', firstName);
				formData.append('last_name', lastName);
				formData.append('email', email);
				formData.append('password', password);
				formData.append('date_of_birth', dateOfBirth);
				formData.append('notification_frequency', notificationFreq);
				disciplines.forEach((discipline) => formData.append('disciplines[]', discipline));

				const response = await fetch('/signup', {
					method: 'POST',
					body: formData
				});

				const result = await response.json();

				if (result.error) {
					if (result.error.includes('user_already_exists')) {
						errorMessage = 'Cet email est déjà utilisé. Veuillez en choisir un autre.';
					} else {
						errorMessage = result.error;
					}
					successMessage = '';
					step = 1; // Retour à l'étape 1 en cas d'erreur
				} else if (result.success) {
					successMessage = result.message || 'Inscription réussie !';
					errorMessage = '';
					dispatch('signupSuccess');
					if (result.redirectTo) {
						window.location.href = result.redirectTo;
					}
				}
			} catch (error) {
				errorMessage = 'Erreur lors de l’inscription : ' + error.message;
				successMessage = '';
				step = 1; // Retour à l'étape 1 en cas d'erreur
			} finally {
				isLoading = false;
				showNotificationModal = false;
			}
		}
	}

	// Fonction pour revenir à l'étape précédente
	function goBack() {
		if (step === 2) {
			step = 1;
			showDisciplineModal = false;
		} else if (step === 3) {
			step = 2;
			showNotificationModal = false;
			showDisciplineModal = true;
		}
		errorMessage = '';
		successMessage = '';
	}
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
	{#if step === 1}
		<!-- Étape 1 : Email et Mot de passe -->
		<div>
			<label for="email" class="block text-sm font-medium text-gray-700">Email</label>
			<input
				id="email"
				name="email"
				type="email"
				bind:value={email}
				class="mt-1 w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
				placeholder="jperrama@gmail.com"
				required
			/>
		</div>

		<div>
			<label for="password" class="block text-sm font-medium text-gray-700">Mot de passe</label>
			<input
				id="password"
				name="password"
				type="password"
				bind:value={password}
				class="mt-1 w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
				placeholder="••••••"
				required
			/>
		</div>

		<button
			type="submit"
			class="w-full rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
		>
			Suivant
		</button>
	{/if}
</form>

<!-- Modal pour les disciplines (Étape 2) -->
{#if showDisciplineModal}
	<div class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black">
		<div class="mx-4 w-full max-w-md rounded-lg bg-white p-6">
			<h2 class="mb-2 text-xl font-bold text-gray-900">Quelles disciplines voulez-vous suivre ?</h2>
			<p class="mb-4 text-sm text-gray-600">(une ou plusieurs)</p>

			<!-- Affichage des disciplines sélectionnées sous forme de bulles -->
			{#if disciplines.length > 0}
				<div class="mb-4 flex flex-wrap gap-2">
					{#each disciplines as discipline}
						<div
							class="flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800"
						>
							<span>{discipline}</span>
							<button
								type="button"
								on:click={() => removeDiscipline(discipline)}
								class="ml-2 focus:outline-none"
							>
								<svg
									class="h-4 w-4 text-blue-800"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M6 18L18 6M6 6l12 12"
									/>
								</svg>
							</button>
						</div>
					{/each}
				</div>
			{/if}

			<div class="relative mb-4">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Rechercher une discipline..."
					class="w-full rounded-lg border border-gray-300 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
				/>
			</div>

			<div class="mb-4 max-h-48 overflow-y-auto">
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

			<div class="flex justify-between">
				<button
					type="button"
					on:click={goBack}
					class="rounded-lg px-4 py-2 text-gray-700 transition-all duration-200 hover:bg-gray-100 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
				>
					Retour
				</button>
				<button
					type="button"
					on:click={handleSubmit}
					class="rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
				>
					Suivant
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Modal pour la fréquence des notifications (Étape 3) -->
{#if showNotificationModal}
	<div class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black">
		<div class="mx-4 w-full max-w-md rounded-lg bg-white p-6">
			<h2 class="mb-2 text-xl font-bold text-gray-900">
				À quelle fréquence souhaitez-vous être alerté ?
			</h2>
			<p class="mb-4 text-sm text-gray-600">
				Ainsi, vous pourrez bénéficier d’une veille personnalisée selon la fréquence que vous
				souhaitez (que vous pouvez modifier par la suite).
			</p>

			<div class="space-y-2">
				{#each notificationOptions as option}
					<button
						type="button"
						on:click={() => {
							notificationFreq = option.replace(/ /g, '_').toLowerCase();
						}}
						class="flex w-full items-center rounded-lg border px-4 py-2 transition-all duration-200 {notificationFreq ===
						option.replace(/ /g, '_').toLowerCase()
							? 'border-blue-500 bg-blue-100'
							: 'border-gray-300 hover:bg-gray-100'}"
					>
						<span class="flex-1 text-left">{option}</span>
						{#if notificationFreq === option.replace(/ /g, '_').toLowerCase()}
							<svg
								class="h-5 w-5 text-blue-500"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M5 13l4 4L19 7"
								/>
							</svg>
						{/if}
					</button>
				{/each}
			</div>

			<div class="mt-6 flex justify-between">
				<button
					type="button"
					on:click={goBack}
					class="rounded-lg px-4 py-2 text-gray-700 transition-all duration-200 hover:bg-gray-100 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
				>
					Retour
				</button>
				<button
					type="button"
					on:click={handleSubmit}
					disabled={isLoading}
					class="rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400"
				>
					{#if isLoading}
						<svg class="mr-2 inline-block h-5 w-5 animate-spin text-white" viewBox="0 0 24 24">
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
						Inscription en cours...
					{:else}
						S’inscrire
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Responsive design pour les modals */
	@media (max-width: 640px) {
		.max-w-md {
			max-width: 100%;
			padding: 1rem;
		}
		h1 {
			font-size: 1.75rem;
		}
		h2 {
			font-size: 1.25rem;
		}
	}
</style>
