<!-- /components/auth/SignUpForm.svelte -->
<script>
    import { i18n } from '$lib/i18n';
    import userProfileStore from '$lib/stores/user';
    import { goto } from '$app/navigation';
  
    export let firstName = '';
    export let lastName = '';
    export let email = '';
    export let password = '';
    export let disciplines = [];
    export let notificationFreq = '';
    export let errorMessage = '';
    export let successMessage = '';
    export let isLoading = false;
  
    const disciplineOptions = [
      'Médecine Générale', 'Urgences', 'Médecine du Travail', 'Santé Publique', 'Médecine Interne',
      'Endocrinologie-Diabétologie-Nutrition', 'Cardiologie', 'Dermatologie', 'Hépato-Gastroentérologie',
      'Génétique', 'Gériatrie', 'Hématologie', 'Maladies infectieuses', 'Néphrologie', 'Neurologie',
      'Oncologie', 'Médecine physique et réadaptation', 'Pneumologie', 'Gynécologie-obstétrique',
      'Pédiatrie', 'Psychiatrie', 'Anesthésie - Réanimation', 'Rhumatologie', 'Chirurgie cardiaque',
      'Chirurgie digestive', 'Chirurgie ORL', 'Neurochirurgie', 'Ophtalmologie', 'Chirurgie orthopédique',
      'Chirurgie thoracique', 'Urologie', 'Chirurgie vasculaire', 'Médecine de la douleur'
    ];
  
    const notificationFreqMap = {
      'Tous les jours': 'tous_les_jours',
      'Tous les 2 jours': 'tous_les_2_jours',
      'Tous les 3 jours': 'tous_les_3_jours',
      '1 fois par semaine': '1_fois_par_semaine',
      'Tous les 15 jours': 'tous_les_15_jours',
      '1 fois par mois': '1_fois_par_mois'
    };
  
    async function handleSignUp(event) {
      event.preventDefault();
  
      const mappedNotificationFreq = notificationFreqMap[notificationFreq];
      if (!mappedNotificationFreq) {
        errorMessage = 'Fréquence de notification invalide.';
        console.error('Fréquence invalide :', notificationFreq);
        return;
      }
  
      isLoading = true;
      errorMessage = '';
      successMessage = '';
  
      const response = await fetch('/api/sign_up', {
        method: 'POST',
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
          password,
          disciplines,
          notification_frequency: mappedNotificationFreq
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
  
      const result = await response.json();
      isLoading = false;
  
      if (!response.ok) {
        errorMessage = result.error || 'Erreur lors de l’inscription';
        console.error('Erreur lors de l’inscription :', result.error);
        return;
      }
  
      // Vérifier si l'utilisateur doit confirmer son email
      if (result.message) {
        successMessage = result.message; // Par ex., "Inscription réussie. Veuillez vérifier votre email."
      } else {
        successMessage = 'Inscription réussie ! Redirection en cours...';
        userProfileStore.set(result.data);
        setTimeout(() => goto('/'), 1500);
      }
    }
  </script>
  
  <form on:submit={handleSignUp} class="space-y-6">
    <div>
      <label for="firstName" class="block text-sm font-medium text-gray-700">
        {$i18n.login.firstName}
      </label>
      <input
        id="firstName"
        type="text"
        bind:value={firstName}
        class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
        required
        placeholder="Votre prénom"
      />
    </div>
  
    <div>
      <label for="lastName" class="block text-sm font-medium text-gray-700">
        {$i18n.login.lastName}
      </label>
      <input
        id="lastName"
        type="text"
        bind:value={lastName}
        class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
        required
        placeholder="Votre nom"
      />
    </div>
  
    <div>
      <label for="signup-email" class="block text-sm font-medium text-gray-700">
        {$i18n.login.email}
      </label>
      <input
        id="signup-email"
        type="email"
        bind:value={email}
        class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
        required
        placeholder="votre@email.com"
      />
    </div>
  
    <div>
      <label for="signup-password" class="block text-sm font-medium text-gray-700">
        {$i18n.login.password}
      </label>
      <input
        id="signup-password"
        type="password"
        bind:value={password}
        class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
        required
        placeholder="Mot de passe"
      />
    </div>
  
    <div>
      <label for="disciplines" class="block text-sm font-medium text-gray-700">
        {$i18n.login.disciplines}
      </label>
      <select
        id="disciplines"
        multiple
        bind:value={disciplines}
        class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200 max-h-40 overflow-y-auto"
        required
      >
        {#each disciplineOptions as discipline}
          <option value={discipline} class="py-1">{discipline}</option>
        {/each}
      </select>
    </div>
  
    <div>
      <label for="notifications" class="block text-sm font-medium text-gray-700">
        {$i18n.login.notifications}
      </label>
      <select
        id="notifications"
        bind:value={notificationFreq}
        class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
        required
      >
        <option value="" disabled selected>Choisissez une fréquence</option>
        {#each $i18n.login.notificationOptions as option}
          <option value={option}>{option}</option>
        {/each}
      </select>
    </div>
  
    <button
      type="submit"
      disabled={isLoading}
      class="w-full rounded-lg bg-blue-600 py-3 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 disabled:bg-blue-400 disabled:cursor-not-allowed"
    >
      {#if isLoading}
        <span class="flex items-center justify-center">
          <svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          En cours...
        </span>
      {:else}
        {$i18n.login.submit}
      {/if}
    </button>
  
    <p class="text-center text-sm text-gray-500">
      {$i18n.login.footer}
    </p>
  </form>