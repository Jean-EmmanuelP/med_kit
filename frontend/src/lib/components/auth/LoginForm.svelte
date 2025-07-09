<!-- /lib/components/auth/LoginForm.svelte -->
<script>
	import { i18n } from '$lib/i18n';
  
	export let email = '';
	export let password = '';
	export let errorMessage = '';
	export let successMessage = '';
	export let isLoading = false;
  </script>
  
  <div class="space-y-6">
	<div>
	  <label for="email" class="block text-sm font-medium text-gray-700">{$i18n.login.emailLabel}</label>
	  <input
		id="email"
		name="email"
		type="email"
		bind:value={email}
		class="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200"
		placeholder={$i18n.login.emailPlaceholder}
		required
	  />
	</div>
  
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
	  <div class="text-right mt-1">
		<a href="/reset-password" class="text-xs text-blue-600 hover:underline">{$i18n.login.forgotPassword}</a>
	  </div>
	</div>
  
	<button
	  type="submit"
	  disabled={isLoading}
	  class="w-full rounded-lg bg-black px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 disabled:bg-blue-400 disabled:cursor-not-allowed"
	>
	  {#if isLoading}
		<svg class="animate-spin h-5 w-5 mr-2 inline-block text-white" viewBox="0 0 24 24">
		  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
		  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
		</svg>
		{$i18n.login.loggingIn}
	  {:else}
		{$i18n.login.submitLogin}
	  {/if}
	</button>
  </div>