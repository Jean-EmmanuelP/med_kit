<!-- $lib/components/auth/SignUpForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	export let email = '';
	export let password = '';
	export let disciplines = [];
	export let notificationFreq = 'tous_les_jours';
	export let errorMessage = '';
	export let successMessage = '';
	export let isLoading = false;

	let step = 1;
	let showDisciplineModal = false;
	let showNotificationModal = false;

	const dispatch = createEventDispatcher();

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

	const notificationOptions = [
		'Tous les jours',
		'Tous les 2 jours',
		'Tous les 3 jours',
		'1 fois par semaine',
		'Tous les 15 jours',
		'1 fois par mois'
	];

	let searchQuery = '';
	$: filteredDisciplines = availableDisciplines.filter((discipline) =>
		discipline.toLowerCase().includes(searchQuery.toLowerCase())
	);

	function toggleDiscipline(discipline) {
		if (disciplines.includes(discipline)) {
			disciplines = disciplines.filter((d) => d !== discipline);
		} else {
			disciplines = [...disciplines, discipline];
		}
	}

	function removeDiscipline(discipline) {
		disciplines = disciplines.filter((d) => d !== discipline);
	}

	function nextStep(event) {
		event.preventDefault();
		if (step === 1) {
			if (!email || !password) {
				errorMessage = 'Veuillez remplir l’email et le mot de passe.';
				return;
			}
			step = 2;
			errorMessage = '';
			showDisciplineModal = true;
		} else if (step === 2) {
			if (disciplines.length === 0) {
				errorMessage = 'Veuillez sélectionner au moins une discipline.';
				return;
			}
			step = 3;
			errorMessage = '';
			showDisciplineModal = false;
			showNotificationModal = true;
		}
	}

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

<!-- Étape 1 : Email et Mot de passe -->
{#if step === 1}
	<form on:submit|preventDefault={nextStep} class="space-y-6">
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
	</form>
{/if}

<!-- Modal pour les disciplines (Étape 2) -->
{#if showDisciplineModal}
	<div class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black">
		<div class="mx-4 w-full max-w-md rounded-lg bg-white p-6">
			<h2 class="mb-2 text-xl font-bold text-gray-900">Quelles disciplines voulez-vous suivre ?</h2>
			<p class="mb-4 text-sm text-gray-600">(une ou plusieurs)</p>

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
					on:click={nextStep}
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
	<form
		method="POST"
		action="/signup"
		class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black"
	>
		<div class="mx-4 w-full max-w-md rounded-lg bg-white p-6">
			<h2 class="mb-2 text-xl font-bold text-gray-900">
				À quelle fréquence souhaitez-vous être alerté ?
			</h2>
			<p class="mb-4 text-sm text-gray-600">
				Ainsi, vous pourrez bénéficier d’une veille personnalisée selon la fréquence que vous
				souhaitez (que vous pouvez modifier par la suite).
			</p>

			<!-- Champs cachés pour envoyer toutes les données -->
			<input type="hidden" name="email" value={email} />
			<input type="hidden" name="password" value={password} />
			<input type="hidden" name="first_name" value={email.split('@')[0] || ''} />
			<input type="hidden" name="last_name" value="" />
			<input type="hidden" name="date_of_birth" value="" />
			{#each disciplines as discipline}
				<input type="hidden" name="disciplines[]" value={discipline} />
			{/each}

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

			<!-- Champ caché pour notification_frequency -->
			<input type="hidden" name="notification_frequency" value={notificationFreq} />

			<div class="mt-6 flex justify-between">
				<button
					type="button"
					on:click={goBack}
					class="rounded-lg px-4 py-2 text-gray-700 transition-all duration-200 hover:bg-gray-100 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
				>
					Retour
				</button>
				<button
					type="submit"
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
	</form>
{/if}

<style>
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
