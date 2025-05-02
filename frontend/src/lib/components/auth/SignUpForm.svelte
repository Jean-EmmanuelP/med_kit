<!-- $lib/components/auth/SignUpForm.svelte -->
<script>
	import { i18n } from '$lib/i18n';
	import { createEventDispatcher } from 'svelte';
 // Import i18n
  
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
  
	// --- State for Password Confirmation & Visibility (Step 1) ---
	let passwordConfirm = '';
	let showPassword = false;
	let passwordMismatchError = '';
  
	const dispatch = createEventDispatcher();
  
	// --- Data (Keep as is) ---
	const availableDisciplines = [
	  'Allergie et immunologie', 'Anesthésie - Réanimation', 'Cardiologie',
	  'Chirurgie cardiaque', 'Chirurgie digestive', 'Chirurgie ORL',
	  'Chirurgie orthopédique', 'Chirurgie plastique', 'Chirurgie thoracique',
	  'Chirurgie vasculaire', 'Dermatologie', 'Endocrinologie-Diabétologie-Nutrition',
	  'Génétique', 'Gériatrie', 'Gynécologie-obstétrique', 'Hématologie',
	  'Hépato-Gastroentérologie', 'Maladies infectieuses', 'Médecine de la douleur',
	  'Médecine du Travail', 'Médecine Générale', 'Médecine Interne',
	  'Médecine physique et réadaptation', 'Néphrologie', 'Neurochirurgie',
	  'Neurologie', 'Oncologie', 'Ophtalmologie', 'Pédiatrie', 'Pneumologie',
	  'Psychiatrie', 'Rhumatologie', 'Santé Publique', 'Urgences', 'Urologie'
	];
	const notificationOptions = [
	  'Tous les jours', 'Tous les 2 jours', 'Tous les 3 jours',
	  '1 fois par semaine', 'Tous les 15 jours', '1 fois par mois'
	];
  
	let searchQuery = '';
	$: filteredDisciplines = availableDisciplines.filter((discipline) =>
	  discipline.toLowerCase().includes(searchQuery.toLowerCase())
	);
  
	// --- Functions (Keep discipline/notification logic) ---
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
  
	function togglePasswordVisibility() {
	  showPassword = !showPassword;
	}
  
	$: {
	  if (step === 1 && passwordConfirm && password !== passwordConfirm) {
		passwordMismatchError = $i18n.signup.passwordsDoNotMatch; // Assuming this key exists in i18n
	  } else {
		passwordMismatchError = '';
	  }
	}
  
	function nextStep(event) {
	  // event.preventDefault(); // Removed - using on:submit|preventDefault on form
	  if (step === 1) {
		errorMessage = '';
		if (!email || !password) {
		  errorMessage = $i18n.signup.missingEmailPassword; // Use signup context
		  return;
		}
		if (password !== passwordConfirm) {
		   passwordMismatchError = $i18n.signup.passwordsDoNotMatch; // Use signup context
		   return;
		}
		passwordMismatchError = '';
		step = 2;
		showDisciplineModal = true;
	  } else if (step === 2) {
		errorMessage = '';
		if (disciplines.length === 0) {
		  errorMessage = $i18n.signup.missingDisciplines; // Use signup context
		  return;
		}
		step = 3;
		showDisciplineModal = false;
		showNotificationModal = true;
	  }
	}
  
	function goBack() {
	  errorMessage = '';
	  successMessage = '';
	  passwordMismatchError = '';
	  if (step === 2) {
		step = 1;
		showDisciplineModal = false;
	  } else if (step === 3) {
		step = 2;
		showNotificationModal = false;
		showDisciplineModal = true;
	  }
	}
  </script>
  
  <!-- ========================== -->
  <!--        STEP 1: EMAIL/PW    -->
  <!-- ========================== -->
  {#if step === 1}
	<!-- Use the original space-y-6 -->
	<form on:submit|preventDefault={nextStep} class="space-y-6">
	  <!-- Email Input (Original Style) -->
	  <div>
		<label for="email" class="block text-sm font-medium text-gray-700">{$i18n.signup.emailLabel}</label>
		<input
		  id="email"
		  name="email"
		  type="email"
		  bind:value={email}
		  class="mt-1 w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
		  placeholder={$i18n.signup.emailPlaceholder}
		  required
		/>
	  </div>
  
	  <!-- Password Input (Original Style + Dynamic Type) -->
	  <div>
		<label for="password" class="block text-sm font-medium text-gray-700">{$i18n.signup.passwordLabel}</label>
		<input
		  id="password"
		  name="password"
		  type={showPassword ? 'text' : 'password'}
		  bind:value={password}
		  class="mt-1 w-full rounded-lg border border-gray-300 bg-blue-50 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
		  placeholder={$i18n.signup.passwordPlaceholder}
		  required
		/>
	  </div>
  
	  <!-- Password Confirmation Input (Original Style Base + Dynamic Type + Error State) -->
	  <div>
		<label for="password-confirm" class="block text-sm font-medium text-gray-700">{$i18n.signup.passwordConfirmLabel}</label>
		<input
		  id="password-confirm"
		  name="password_confirm"
		  type={showPassword ? 'text' : 'password'}
		  bind:value={passwordConfirm}
		  class="mt-1 w-full rounded-lg border bg-blue-50 px-4 py-2 transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200 {passwordMismatchError ? 'border-red-500' : 'border-gray-300'}"
		  placeholder={$i18n.signup.passwordConfirmPlaceholder}
		  required
		  aria-invalid={!!passwordMismatchError}
		  aria-describedby={passwordMismatchError ? 'password-mismatch-error-step1' : undefined}
		/>
		 {#if passwordMismatchError}
		   <p id="password-mismatch-error-step1" class="mt-1 text-xs text-red-600">{passwordMismatchError}</p>
		 {/if}
	  </div>
  
	   <!-- Show/Hide Password Button (Simple text button, minimal styling) -->
	   <div class="text-right"> <!-- Align button to the right -->
		 <button
		   type="button"
		   on:click={togglePasswordVisibility}
		   class="text-sm font-medium text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-300 rounded px-1 py-0.5"
		   aria-label={showPassword ? $i18n.signup.hidePassword : $i18n.signup.showPassword}
		 >
		   {#if showPassword}
			 {$i18n.signup.hidePassword}
		   {:else}
			 {$i18n.signup.showPassword}
		   {/if}
		 </button>
	   </div>
  
	  <!-- Next Button (Original Style) -->
	  <button
		type="submit"
		disabled={!!passwordMismatchError}
		class="w-full rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
	  >
		{$i18n.signup.nextButton}
	  </button>
	</form>
  {/if}
  
  <!-- ================================= -->
  <!-- MODALS (Steps 2 & 3 - Unchanged) -->
  <!-- ================================= -->
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
								  aria-label="Remove {discipline}"
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
				  {:else}
					  <p class="px-4 py-2 text-sm text-gray-500 italic">Aucune discipline correspondante.</p>
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
					  disabled={disciplines.length === 0}
					  class="rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
				  >
					  Suivant
				  </button>
			  </div>
		  </div>
	  </div>
  {/if}
  
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
				  Vous pourrez modifier cette préférence plus tard.
			  </p>
  
			  <!-- Champs cachés pour envoyer toutes les données -->
			  <input type="hidden" name="email" value={email} />
			  <input type="hidden" name="password" value={password} />
			  {#each disciplines as discipline}
				  <input type="hidden" name="disciplines[]" value={discipline} />
			  {/each}
			  <input type="hidden" name="notification_frequency" value={notificationFreq} />
  
			  <div class="space-y-2">
				  {#each notificationOptions as option}
					  {@const freqValue = option.replace(/ /g, '_').toLowerCase()}
					  <button
						  type="button"
						  on:click={() => { notificationFreq = freqValue; }}
						  class="flex w-full items-center rounded-lg border px-4 py-2 transition-all duration-200 {notificationFreq === freqValue
							  ? 'border-blue-500 bg-blue-100'
							  : 'border-gray-300 hover:bg-gray-100'}"
					  >
						  <span class="flex-1 text-left">{option}</span>
						  {#if notificationFreq === freqValue}
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
					  type="submit"
					  disabled={isLoading}
					  class="flex items-center justify-center rounded-lg bg-black px-4 py-2 text-white transition-all duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400"
				  >
					  {#if isLoading}
						  <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						   </svg>
						  {$i18n.signup.signingUp} <!-- Use signup context -->
					  {:else}
						  {$i18n.signup.signupButton} <!-- Use signup context -->
					  {/if}
				  </button>
			  </div>
		  </div>
	  </form>
  {/if}
  
  <!-- Keep existing style tag -->
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
	  /* Add custom styles if needed, but avoid conflicting with Tailwind */
	  .text-xs { /* Tailwind class for small error text */
		  font-size: 0.75rem; /* 12px */
		  line-height: 1rem; /* 16px */
	  }
	  .text-red-600 { /* Tailwind class for error color */
		  --tw-text-opacity: 1;
		  color: rgb(220 38 38 / var(--tw-text-opacity));
	  }
	  .border-red-500 { /* Tailwind class for error border */
		   --tw-border-opacity: 1;
		   border-color: rgb(239 68 68 / var(--tw-border-opacity));
	  }
  </style>