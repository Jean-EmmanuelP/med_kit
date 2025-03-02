<!-- /lib/components/Header.svelte -->
<script>
	import { i18n } from '$lib/i18n';
	import { supabaseStore } from '$lib/stores/supabase';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
  
	let showAccountMenu = false;
	let showMobileMenu = false;
  
	async function handleLogout() {
	  try {
		const { error } = await $supabaseStore.auth.signOut();
		if (error) {
		  console.error('Erreur lors de la déconnexion :', error);
		  return;
		}
		userProfileStore.set(null);
		goto('/');
	  } catch (error) {
		console.error('Erreur inattendue lors de la déconnexion :', error);
	  }
	}
  
	function handleOutsideClick(event) {
	  if (showAccountMenu && !event.target.closest('.account-menu')) {
		showAccountMenu = false;
	  }
	  if (showMobileMenu && !event.target.closest('.mobile-menu')) {
		showMobileMenu = false;
	  }
	}
  
	onMount(() => {
	  document.addEventListener('click', handleOutsideClick);
	  return () => {
		document.removeEventListener('click', handleOutsideClick);
	  };
	});
  </script>
  
  <header class="bg-white shadow-sm fixed z-[100] w-screen">
	<nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
	  <!-- Logo -->
	  <div class="flex items-center">
		<a href="/" class="text-2xl font-bold text-black font-sans-bold">
		  Veille
		</a>
	  </div>
  
	  <!-- Navigation -->
	  <div class="hidden md:flex items-center space-x-6">
		{#if $userProfileStore}
		  <a
			href="/my-articles"
			class="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200 font-sans"
		  >
			{$i18n.header.myArticles}
		  </a>
		  <a
			href="/articles"
			class="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200 font-sans"
		  >
			{$i18n.header.articles}
		  </a>
		  <div class="relative account-menu">
			<button
			  on:click={() => (showAccountMenu = !showAccountMenu)}
			  class="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200 focus:outline-none font-sans flex items-center"
			>
			  {$i18n.header.account}
			  <svg
				class="w-4 h-4 ml-1"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				xmlns="http://www.w3.org/2000/svg"
			  >
				<path
				  stroke-linecap="round"
				  stroke-linejoin="round"
				  stroke-width="2"
				  d="M19 9l-7 7-7-7"
				/>
			  </svg>
			</button>
			{#if showAccountMenu}
			  <div
				class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-10 animate-fade-in"
			  >
				<button
				  on:click={handleLogout}
				  class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-100 transition-colors duration-200 font-sans"
				>
				  Déconnexion
				</button>
			  </div>
			{/if}
		  </div>
		{:else}
		  <a
			href="/login"
			class="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200 font-sans flex items-center"
		  >
			<svg
			  class="w-4 h-4 mr-1"
			  fill="none"
			  stroke="currentColor"
			  viewBox="0 0 24 24"
			  xmlns="http://www.w3.org/2000/svg"
			>
			  <path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
			  />
			</svg>
			Se connecter
		  </a>
		{/if}
		<!-- <button
		  class="text-gray-700 hover:text-blue-600 transition-colors duration-200"
		  aria-label="Rechercher"
		>
		  <svg
			class="w-5 h-5"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
		  >
			<path
			  stroke-linecap="round"
			  stroke-linejoin="round"
			  stroke-width="2"
			  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
			/>
		  </svg>
		</button> -->
	  </div>
  
	  <div class="md:hidden">
		<button
		  on:click={() => (showMobileMenu = !showMobileMenu)}
		  class="focus:outline-none"
		  aria-label="Toggle menu"
		>
		  <svg
			class="w-6 h-6 text-gray-700"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
		  >
			<path
			  stroke-linecap="round"
			  stroke-linejoin="round"
			  stroke-width="2"
			  d="M4 6h16M4 12h16M4 18h16"
			/>
		  </svg>
		</button>
		{#if showMobileMenu}
		  <div
			class="absolute top-16 left-0 w-full bg-white shadow-lg z-10 animate-fade-in mobile-menu"
		  >
			{#if $userProfileStore}
			  <a
				href="/my-articles"
				class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-100 transition-colors duration-200 font-sans"
			  >
				{$i18n.header.myArticles}
			  </a>
			  <a
				href="/articles"
				class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-100 transition-colors duration-200 font-sans"
			  >
				{$i18n.header.articles}
			  </a>
			  <button
				on:click={handleLogout}
				class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-100 transition-colors duration-200 font-sans"
			  >
				Déconnexion
			  </button>
			{:else}
			  <a
				href="/login"
				class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-100 transition-colors duration-200 font-sans"
			  >
				Se connecter
			  </a>
			{/if}
		  </div>
		{/if}
	  </div>
	</nav>
  </header>
  
  <style>
	.animate-fade-in {
	  animation: fadeIn 0.2s ease-out;
	}
  
	@keyframes fadeIn {
	  from {
		opacity: 0;
		transform: translateY(-5px);
	  }
	  to {
		opacity: 1;
		transform: translateY(0);
	  }
	}
  </style>