<script>
  import { i18n } from '$lib/i18n';
  import SignUpForm from '$lib/components/auth/SignUpForm.svelte';
  import MessageDisplay from '$lib/components/auth/MessageDisplay.svelte';

  let firstName = '';
  let lastName = '';
  let email = '';
  let password = '';
  let disciplines = [];
  let notificationFreq = 'tous_les_jours';
  let dateOfBirth = '';
  let specialty = '';
  let status = '';
  let errorMessage = '';
  let successMessage = '';
  let isLoading = false;
</script>

<main class="flex min-h-screen items-center justify-center bg-black px-4 py-12">
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
      action="/signup"
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