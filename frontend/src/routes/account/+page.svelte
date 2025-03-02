<script>
    import { i18n } from '$lib/i18n';
    import { goto } from '$app/navigation';
    import userProfileStore from '$lib/stores/user';
    import Footer from '$lib/components/Footer.svelte';
  
    export let data;
    export let form;
  
    // Options de fréquence des notifications (correspondant à celles de la table user_profiles)
    const notificationOptions = [
      'tous_les_jours',
      'tous_les_2_jours',
      'tous_les_3_jours',
      '1_fois_par_semaine',
      'tous_les_15_jours',
      '1_fois_par_mois'
    ];
  
    // Traductions des options pour l'affichage (correspondant à i18n.login.notificationOptions)
    const notificationDisplayOptions = {
      'tous_les_jours': $i18n.login.notificationOptions[0],
      'tous_les_2_jours': $i18n.login.notificationOptions[1],
      'tous_les_3_jours': $i18n.login.notificationOptions[2],
      '1_fois_par_semaine': $i18n.login.notificationOptions[3],
      'tous_les_15_jours': $i18n.login.notificationOptions[4],
      '1_fois_par_mois': $i18n.login.notificationOptions[5]
    };
  
    let selectedDisciplines = data.userPreferences ? data.userPreferences.disciplines : [];
  
    function toggleDiscipline(discipline) {
      if (selectedDisciplines.includes(discipline)) {
        selectedDisciplines = selectedDisciplines.filter(d => d !== discipline);
      } else {
        selectedDisciplines = [...selectedDisciplines, discipline];
      }
    }
  
    // Rafraîchir les disciplines après mise à jour
    if (form?.success && form?.action === 'updateDisciplines') {
      selectedDisciplines = form.updatedDisciplines;
    }
  </script>
  
  <div class="min-h-screen bg-gray-50 px-4 py-12">
    <div class="mx-auto max-w-4xl">
      <h1 class="mb-8 text-3xl font-bold text-blue-600">Mon Compte</h1>
  
      {#if data.error}
        <p class="text-red-500">{data.error}</p>
      {:else}
        <!-- Section pour changer la fréquence des notifications -->
        <div class="mb-12">
          <h2 class="mb-4 text-xl font-semibold text-gray-800">Fréquence des notifications</h2>
          <form action="?/updateNotificationFrequency" method="POST">
            <div class="flex flex-col sm:flex-row sm:items-center sm:space-x-4">
              <select
                name="notificationFrequency"
                class="w-full sm:w-64 border rounded px-3 py-2 mb-3 sm:mb-0 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
              >
                {#each notificationOptions as option}
                  <option value={option} selected={data.userPreferences.notificationFrequency === option}>
                    {notificationDisplayOptions[option]}
                  </option>
                {/each}
              </select>
              <button
                type="submit"
                class="w-full sm:w-auto rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 transition-colors duration-200"
              >
                Mettre à jour
              </button>
            </div>
            {#if form?.error && form?.action === 'updateNotificationFrequency'}
              <p class="mt-3 text-red-500">{form.error}</p>
            {/if}
            {#if form?.success && form?.action === 'updateNotificationFrequency'}
              <p class="mt-3 text-green-600">Fréquence des notifications mise à jour avec succès.</p>
            {/if}
          </form>
        </div>
  
        <!-- Section pour changer les disciplines -->
        <div class="mb-12">
          <h2 class="mb-4 text-xl font-semibold text-gray-800">Disciplines suivies</h2>
          <form action="?/updateDisciplines" method="POST">
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-4">
              {#each data.disciplinesList as discipline}
                <label class="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    name="disciplines"
                    value={discipline}
                    checked={selectedDisciplines.includes(discipline)}
                    on:change={() => toggleDiscipline(discipline)}
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span class="text-gray-700">{discipline}</span>
                </label>
              {/each}
            </div>
            <button
              type="submit"
              class="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 transition-colors duration-200"
            >
              Mettre à jour
            </button>
            {#if form?.error && form?.action === 'updateDisciplines'}
              <p class="mt-3 text-red-500">{form.error}</p>
            {/if}
            {#if form?.success && form?.action === 'updateDisciplines'}
              <p class="mt-3 text-green-600">Disciplines mises à jour avec succès.</p>
            {/if}
          </form>
        </div>
      {/if}
    </div>
  </div>