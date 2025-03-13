<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { onMount } from 'svelte';

	let showAccountMenu = false;
	let showMobileMenu = false;
	let showHeader = true;
	let lastScrollY = 0;

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
		lastScrollY = window.scrollY;
		const handleScroll = () => {
			const currentScrollY = window.scrollY;

			if (currentScrollY > lastScrollY && currentScrollY > 80) {
				showHeader = false;
			} else {
				showHeader = true;
			}

			lastScrollY = currentScrollY;
		};

		window.addEventListener('scroll', handleScroll);
		document.addEventListener('click', handleOutsideClick);

		return () => {
			window.removeEventListener('scroll', handleScroll);
			document.removeEventListener('click', handleOutsideClick);
		};
	});
</script>

<header
	class="fixed z-[100] w-screen transition-transform duration-300 ease-in-out"
	class:bg-black={showHeader && lastScrollY === 0}
	class:bg-white={lastScrollY > 0}
	class:shadow-sm={lastScrollY > 0}
	style="transform: translateY({showHeader ? '0%' : '-100%'});"
>
	<nav class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
		<div class="flex items-center">
			<a
				href="/"
				class="font-sans text-3xl font-bold {lastScrollY > 0 ? 'text-black' : 'text-white'}"
			>
				Veille
			</a>
		</div>

		<div class="hidden items-center space-x-6 md:flex">
			{#if $userProfileStore}
				<a
					href="/qui-sommes-nous"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					Qui sommes-nous ?
				</a>
				<a
					href="/ma-veille"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					{$i18n.header.myVeille}
				</a>
				<a
					href="/articles"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					{$i18n.header.articles}
				</a>
				<div class="account-menu relative">
					<button
						onclick={() => (showAccountMenu = !showAccountMenu)}
						class="flex items-center font-sans text-sm font-medium {lastScrollY > 0
							? 'text-black hover:text-gray-700'
							: 'text-white hover:text-gray-300'} transition-colors duration-200 focus:outline-none"
					>
						{$i18n.header.account}
						<svg class="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
							class="animate-fade-in absolute right-0 z-10 mt-2 w-48 rounded-md bg-black py-1 shadow-lg"
						>
							<a href="/account" class="block px-4 py-2 text-sm text-black hover:bg-black/80">
								{$i18n.header.settings}
							</a>
						</div>
					{/if}
				</div>
			{:else}
				<a
					href="/login"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					{$i18n.header.login}
				</a>
			{/if}
		</div>

		<div class="md:hidden">
			<button onclick={toggleMobileMenu} class="burger-button p-2">
				<svg
					class="h-6 w-6 {lastScrollY > 0 ? 'text-black' : 'text-white'}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
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
					class="mobile-menu animate-fade-in absolute top-full left-0 z-50 w-full bg-black shadow-lg"
				>
					{#if $userProfileStore}
						<a
							href="/qui-sommes-nous"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							Qui sommes-nous ?
						</a>
						<a
							href="/ma-veille"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							{$i18n.header.myVeille}
						</a>
						<a
							href="/articles"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							{$i18n.header.articles}
						</a>
						<a
							href="/account"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							{$i18n.header.settings}
						</a>
					{:else}
						<a
							href="/login"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
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

	/* Ajustements spécifiques pour le style Ledger */
	header.bg-black a,
	header.bg-black button {
		color: white;
	}

	header.bg-white a,
	header.bg-white button {
		color: black;
	}

	header.bg-black {
		background-color: #000000;
		border-bottom: 1px solid #333;
	}

	header.bg-white {
		background-color: #ffffff;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.burger-button svg {
		transition: color 0.3s ease;
	}

	.account-menu button svg {
		transition: stroke 0.3s ease;
	}
</style>
