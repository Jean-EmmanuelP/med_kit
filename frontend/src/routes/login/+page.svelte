<!-- /routes/login/+page.svelte -->
<script>
	import { i18n } from '$lib/i18n';
	import LoginForm from '$lib/components/auth/LoginForm.svelte';
	import MessageDisplay from '$lib/components/auth/MessageDisplay.svelte';
  
	let email = '';
	let password = '';
	let errorMessage = '';
	let successMessage = '';
	let isLoading = false;
  </script>
  
  <main class="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4 py-12">
	<div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl transition-all duration-300 hover:shadow-3xl">
	  <h1 class="mb-6 text-center text-3xl font-bold text-blue-700 tracking-tight">
		{$i18n.login.loginTitle}
	  </h1>
  
	  <MessageDisplay bind:errorMessage bind:successMessage />
	  {#if isLoading}
		<div class="flex items-center justify-center space-x-2 rounded-lg bg-blue-50 p-4 mb-4">
		  <div class="h-5 w-5 animate-spin rounded-full border-4 border-t-blue-500"></div>
		  <p class="text-blue-600 font-medium">Connexion en cours...</p>
		</div>
	  {/if}
  
	  <LoginForm
		bind:email
		bind:password
		bind:errorMessage
		bind:successMessage
		bind:isLoading
	  />
  
	  <p class="text-center text-sm text-gray-500 mt-4">
		Pas encore de compte ? <a href="/signup" class="text-blue-600 hover:underline">S'inscrire</a>
	  </p>
	</div>
  </main>