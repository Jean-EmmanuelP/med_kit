<script>
import { i18n } from '$lib/i18n';
import { supabase } from '$lib/supabase';
import MessageDisplay from '$lib/components/auth/MessageDisplay.svelte';

let password = '';
let errorMessage = '';
let successMessage = '';
let isLoading = false;

async function handleUpdatePassword(e) {
  e.preventDefault();
  errorMessage = '';
  successMessage = '';
  isLoading = true;
  const { error } = await supabase.auth.updateUser({ password });
  if (error) {
    errorMessage = $i18n.login.updatePasswordError;
  } else {
    successMessage = $i18n.login.updatePasswordSuccess;
  }
  isLoading = false;
}
</script>

<main class="flex min-h-screen items-center justify-center bg-black px-4 py-12">
  <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl">
    <h1 class="mb-6 text-center text-3xl font-bold tracking-tight capitalize">{$i18n.login.updatePasswordTitle}</h1>
    <p class="mb-4 text-center text-gray-600">{$i18n.login.updatePasswordInstruction}</p>
    <MessageDisplay bind:errorMessage bind:successMessage />
    <form class="space-y-6" on:submit={handleUpdatePassword}>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">{$i18n.login.passwordLabel}</label>
        <input
          id="password"
          name="password"
          type="password"
          bind:value={password}
          class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
          placeholder={$i18n.login.passwordPlaceholder}
          required
        />
      </div>
      <button
        type="submit"
        class="w-full rounded-lg bg-black px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 disabled:bg-blue-400 disabled:cursor-not-allowed"
        disabled={isLoading}
      >
        {#if isLoading}
          <span>{$i18n.login.loggingIn}</span>
        {:else}
          {$i18n.login.updatePasswordButton}
        {/if}
      </button>
    </form>
  </div>
</main> 