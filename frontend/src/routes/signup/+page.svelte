<!-- /routes/signup/+page.svelte -->
<script>
  import { i18n } from '$lib/i18n';
  import { goto } from '$app/navigation';
  import { supabase } from '$lib/supabase';
  import userProfileStore from '$lib/stores/user';
  import SignUpForm from '$lib/components/auth/SignUpForm.svelte';
  import MessageDisplay from '$lib/components/auth/MessageDisplay.svelte';
  import { enhance } from '$app/forms';

  let firstName = '';
  let lastName = '';
  let email = '';
  let password = '';
  let disciplines = [];
  let notificationFreq = 'tous_les_jours';
  let dateOfBirth = '';
  let education = '';
  let specialty = '';
  let status = '';
  let errorMessage = '';
  let successMessage = '';
  let isLoading = false;
</script>

<main class="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4 py-12">
  <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl transition-all duration-300 hover:shadow-3xl">
    <h1 class="mb-6 text-center text-3xl font-bold tracking-tight capitalize">
      {$i18n.login.title}
    </h1>

    <MessageDisplay bind:errorMessage bind:successMessage />
    {#if isLoading}
      <div class="flex items-center justify-center space-x-2 rounded-lg bg-blue-50 p-4 mb-4">
        <div class="h-5 w-5 animate-spin rounded-full border-4 border-t-blue-500"></div>
        <p class="text-blue-600 font-medium">Inscription en cours...</p>
      </div>
    {/if}

    <form
      method="POST"
      use:enhance={() => {
        isLoading = true;
        errorMessage = '';
        successMessage = '';
        return async ({ result }) => {
          isLoading = false;
          if (result.type === 'failure') {
            errorMessage = result.data?.error || 'Erreur lors de l’inscription';
          } else if (result.type === 'success') {
            if (result.data?.message) {
              // Email confirmation required
              successMessage = result.data.message;
              if (result.data?.redirectTo) {
                setTimeout(() => {
                  goto(result.data.redirectTo);
                }, 3000);
              }
            } else {
              // Immediate login
              const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
              if (sessionError || !sessionData.session) {
                errorMessage = 'Erreur lors de la récupération de la session après inscription';
                return;
              }
              userProfileStore.set(result.data?.profileData);
              successMessage = 'Inscription réussie ! Redirection...';
              if (result.data?.redirectTo) {
                setTimeout(() => {
                  goto(result.data.redirectTo);
                }, 1000);
              }
            }
          }
        };
      }}
      class="space-y-6"
    >
      <SignUpForm
        bind:firstName
        bind:lastName
        bind:email
        bind:password
        bind:disciplines
        bind:notificationFreq
        bind:dateOfBirth
        bind:education
        bind:specialty
        bind:status
        bind:errorMessage
        bind:successMessage
        bind:isLoading
      />
    </form>

    <p class="text-center text-sm text-gray-500 mt-4">
      {$i18n.login.alreadyHaveAccount}
    </p>
  </div>
</main>