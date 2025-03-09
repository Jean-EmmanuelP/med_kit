<script>
	import { i18n } from '$lib/i18n';
	import { supabaseStore } from '$lib/stores/supabase';
	import userProfileStore from '$lib/stores/user';
	import { onMount } from 'svelte';

	let showAccountMenu = $state(false);
	let showMobileMenu = $state(false);

	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
	}

	function closeMobileMenu() {
		showMobileMenu = false;
	}

	function handleOutsideClick(event) {
		if (showAccountMenu && !event.target.closest('.account-menu')) {
			showAccountMenu = false;
		}
		if (
			showMobileMenu &&
			!event.target.closest('.mobile-menu') &&
			!event.target.closest('.burger-button')
		) {
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

<header class="fixed z-[100] w-screen bg-white shadow-sm">
	<nav class="mx-auto flex max-w-7xl items-center justify-between px-4 py-6 sm:px-6 lg:px-8">
		<!-- Logo -->
		<div class="flex items-center">
			<a href="/" class="font-sans text-3xl font-bold text-black">Veille</a>
		</div>

		<!-- Navigation -->
		<div class="hidden items-center space-x-8 md:flex">
			{#if $userProfileStore}
				<a
					href="/qui-sommes-nous"
					class="font-sans text-base font-medium text-black transition-colors duration-200 hover:text-gray-700"
				>
					Qui sommes-nous ?
				</a>
				<a
					href="/ma-veille"
					class="font-sans text-base font-medium text-black transition-colors duration-200 hover:text-gray-700"
				>
					{$i18n.header.myVeille}
				</a>
				<div class="account-menu relative">
					<button
						onclick={() => (showAccountMenu = !showAccountMenu)}
						class="flex items-center font-sans text-base font-medium text-black transition-colors duration-200 hover:text-gray-700 focus:outline-none"
					>
						{$i18n.header.account}
						<svg
							class="ml-2 h-5 w-5"
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
							class="animate-fade-in absolute right-0 z-10 mt-2 w-48 rounded-lg bg-white py-2 shadow-lg"
						>
							<a
								href="/account"
								class="block px-4 py-3 font-sans text-base text-black transition-colors duration-200 hover:bg-gray-100"
							>
								{$i18n.header.settings}
							</a>
						</div>
					{/if}
				</div>
			{:else}
				<a
					href="/login"
					class="flex items-center font-sans text-base font-medium text-black transition-colors duration-200"
				>
					<svg
						class="mr-2 h-5 w-5"
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
					{$i18n.header.login}
				</a>
			{/if}
		</div>

		<!-- Burger Menu for Mobile -->
		<div class="md:hidden">
			<button
				onclick={toggleMobileMenu}
				class="burger-button p-2 focus:outline-none"
				aria-label="Toggle menu"
			>
				<svg
					class="h-8 w-8 text-black"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d={showMobileMenu ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'}
					/>
				</svg>
			</button>
			{#if showMobileMenu}
				<div
					class="animate-fade-in mobile-menu absolute top-20 left-0 z-[100] w-full bg-white shadow-lg"
				>
					{#if $userProfileStore}
						<a
							href="/qui-sommes-nous"
							onclick={closeMobileMenu}
							class="block px-6 py-4 font-sans text-base text-black transition-colors duration-200 hover:bg-gray-100"
						>
							Qui sommes-nous ?
						</a>
						<a
							href="/ma-veille"
							onclick={closeMobileMenu}
							class="block px-6 py-4 font-sans text-base text-black transition-colors duration-200 hover:bg-gray-100"
						>
							{$i18n.header.myVeille}
						</a>
						<a
							href="/account"
							onclick={closeMobileMenu}
							class="block px-6 py-4 font-sans text-base text-black transition-colors duration-200 hover:bg-gray-100"
						>
							{$i18n.header.settings}
						</a>
					{:else}
						<a
							href="/login"
							onclick={closeMobileMenu}
							class="block px-6 py-4 font-sans text-base text-black transition-colors duration-200 hover:bg-gray-100"
						>
							{$i18n.header.login}
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
