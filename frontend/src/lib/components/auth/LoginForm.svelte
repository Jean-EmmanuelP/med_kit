<!-- /components/auth/LoginForm.svelte -->
<script>
  import { i18n } from '$lib/i18n';
  import userProfileStore from '$lib/stores/user';
  import { goto } from '$app/navigation';

  export let email = '';
  export let password = '';
  export let errorMessage = '';
  export let successMessage = '';
  export let isLoading = false;

  async function handleLogin(event) {
    event.preventDefault();

    isLoading = true;
    errorMessage = '';
    successMessage = '';

    const response = await fetch('/api/sign_in', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const result = await response.json();
    isLoading = false;

    if (!response.ok) {
      errorMessage = result.error || 'Erreur lors de la connexion';
      console.error('Erreur lors de la connexion :', result.error);
      return;
    }

    successMessage = 'Connexion réussie ! Redirection en cours...';
    userProfileStore.set(result.data);
    setTimeout(() => goto('/'), 1500);
  }
</script>

<form on:submit={handleLogin} class="space-y-4">
  <div>
    <label for="login-email" class="block text-sm font-medium text-gray-700">
      {$i18n.login.email}
    </label>
    <input
      id="login-email"
      type="email"
      bind:value={email}
      class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
      required
      placeholder="votre@email.com"
    />
  </div>

  <div>
    <label for="login-password" class="block text-sm font-medium text-gray-700">
      {$i18n.login.password}
    </label>
    <input
      id="login-password"
      type="password"
      bind:value={password}
      class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
      required
      placeholder="Mot de passe"
    />
  </div>

  <div class="text-right">
    <a href="/forgot-password" class="text-sm text-blue-600 hover:underline">
      Mot de passe oublié ?
    </a>
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
      Se connecter
    {/if}
  </button>
</form>