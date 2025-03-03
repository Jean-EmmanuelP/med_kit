<!-- /routes/login/+page.svelte -->
<script>
	import { i18n } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import LoginForm from '$lib/components/auth/LoginForm.svelte';
	import MessageDisplay from '$lib/components/auth/MessageDisplay.svelte';
	import { enhance } from '$app/forms';
	import { supabase } from '$lib/supabase';
	import userProfileStore from '$lib/stores/user';
  
	let email = '';
	let password = '';
	let errorMessage = '';
	let successMessage = '';
	let isLoading = false;
  
	async function ensureSession() {
	  let attempts = 0;
	  const maxAttempts = 5;
	  const delay = 500;
  
	  while (attempts < maxAttempts) {
		const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
		if (sessionError) {
		  console.error('Session retrieval error:', sessionError);
		}
		if (sessionData.session) {
		  return sessionData.session;
		}
  
		// Try refreshing the session
		const { data: refreshedSession, error: refreshError } = await supabase.auth.refreshSession();
		if (refreshError) {
		  console.error('Session refresh error:', refreshError);
		}
		if (refreshedSession?.session) {
		  return refreshedSession.session;
		}
  
		attempts++;
		await new Promise(resolve => setTimeout(resolve, delay));
	  }
	  return null;
	}
  </script>
  
  <main class="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4 py-12">
	<div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl transition-all duration-300 hover:shadow-3xl">
	  <h1 class="mb-6 text-center text-3xl font-bold tracking-tight capitalize">
		{$i18n.login.loginTitle}
	  </h1>
  
	  <MessageDisplay bind:errorMessage bind:successMessage />
	  {#if isLoading}
		<div class="flex items-center justify-center space-x-2 rounded-lg bg-blue-50 p-4 mb-4">
		  <div class="h-5 w-5 animate-spin rounded-full border-4 border-t-blue-500"></div>
		  <p class="text-blue-600 font-medium">{$i18n.login.loggingIn}</p>
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
			  errorMessage = result.data?.error || 'Erreur lors de la connexion';
			} else if (result.type === 'success') {
			  console.log('Login result:', result);
			  const session = await ensureSession();
			  if (!session) {
				errorMessage = 'Erreur lors de la récupération de la session après connexion';
				return;
			  }
			  userProfileStore.set(result.data?.profileData);
			  successMessage = $i18n.login.successLogin;
			  if (result.data?.redirectTo) {
				setTimeout(() => {
				  goto(result.data.redirectTo);
				}, 1000);
			  }
			}
		  };
		}}
		class="space-y-6"
	  >
		<LoginForm
		  bind:email
		  bind:password
		  bind:errorMessage
		  bind:successMessage
		  bind:isLoading
		/>
	  </form>
	  <a href="/signup" class="hover:underline">
		<p class="text-center text-sm text-gray-500 mt-4">
		  {$i18n.login.needAccount}
		</p>
	  </a>
	</div>
  </main>