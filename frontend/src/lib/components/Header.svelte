<script lang="ts">
	import MobileFeatureNoticeModal from '$lib/components/MobileFeatureNoticeModal.svelte';
	import NewFeatureNotice from '$lib/components/NewFeatureNotice.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase';
	import { onMount } from 'svelte';

	let showAccountMenu = $state(false);
	let showMobileMenu = $state(false);
	let showHeader = $state(true);
	let lastScrollY = $state(0);

	let showNotice = $state(false);
	let showMobileNoticeModal = $state(false);
	let isLoadingNoticeState = $state(false);

	$effect(() => {
		const currentUser = $userProfileStore;
		// console.log("Header $effect: User changed:", currentUser?.id);

		if (currentUser?.id) {
			isLoadingNoticeState = true;
			// console.log("Header: Fetching tooltip status for user", currentUser.id);
			supabase
				.from('user_profiles')
				.select('has_seen_tooltip')
				.eq('id', currentUser.id)
				.maybeSingle()
				.then(({ data, error }) => {
					if (error) {
						// console.error("Header: Error fetching tooltip status:", error);
						showNotice = false;
					} else {
						const seen = data?.has_seen_tooltip ?? false;
						// console.log("Header: Fetched tooltip status:", seen);
						showNotice = !seen;
					}
				})
				.finally(() => {
					isLoadingNoticeState = false;
					// console.log("Header: Final showNotice state after fetch:", showNotice);
				});
		} else {
			// console.log("Header: User logged out, hiding notice.");
			showNotice = false;
			isLoadingNoticeState = false;
		}
	});

	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
	}

	function closeMobileMenu() {
		showMobileMenu = false;
	}

	function handleOutsideClick(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (showAccountMenu && !target.closest('.account-menu')) {
			showAccountMenu = false;
		}
		if (
			showMobileMenu &&
			!target.closest('.mobile-menu') &&
			!target.closest('.burger-button')
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

	function openMobileNotice() {
		if (showNotice) {
			showMobileNoticeModal = true;
		}
	}

	async function handleDismissNotice() {
		const wasShowing = showNotice;
		showNotice = false;
		showMobileNoticeModal = false;

		if (wasShowing && $userProfileStore?.id) {
			// console.log("Header: Calling API to dismiss notice...");
			try {
				const response = await fetch('/api/dismiss-feature-notice', { method: 'POST' });
				if (!response.ok && response.status !== 204) {
					// console.error("Header: API Error dismissing notice:", response.status, await response.text());
				} else {
					// console.log("Header: Notice dismissed successfully via API.");
					userProfileStore.update(p => p ? { ...p, has_seen_tooltip: true } : null);
				}
			} catch (err) {
				// console.error("Header: Fetch error dismissing notice:", err);
			}
		} else {
			// console.log("Header: Dismiss called but notice wasn't showing or user logged out.");
		}
	}
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
					href="/articles"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					{$i18n.header.articles}
				</a>
				<a
					href="/ma-veille"
					class="rounded-sm px-4 font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					{$i18n.header.myVeille}
				</a>
				<a
					href="/favoris"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					Favoris
				</a>
				<a
					href="/qui-sommes-nous"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					Qui sommes-nous ?
				</a>
				<a
					href="/comite"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					Comité scientifique
				</a>
				<a
					href="/donations"
					class="font-sans text-sm font-medium {lastScrollY > 0
						? 'text-black hover:text-gray-700'
						: 'text-white hover:text-gray-300'} transition-colors duration-200"
				>
					{$i18n.header.donate}
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
							<a href="/account" class="block px-4 py-2 text-sm text-white hover:bg-white/10">
								{$i18n.header.settings}
							</a>
							{#if $userProfileStore?.is_admin}
								<a href="/dashboard" class="block px-4 py-2 text-sm text-white hover:bg-white/10">
									{$i18n.header.dashboard}
								</a>
							{/if}
						</div>

					{/if}
					<NewFeatureNotice isVisible={showNotice} on:dismiss={handleDismissNotice} />
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
			<!-- Mobile Header Area - Ensure buttons are side by side -->
			<div class="flex items-center gap-2">
				<!-- Mobile Notice Trigger Button -->
				{#if showNotice && $userProfileStore && !isLoadingNoticeState}
					<button
						type="button"
						onclick={openMobileNotice}
						class="notice-trigger-button flex h-10 w-10 items-center justify-center rounded-full p-2 text-teal-400 bg-gray-700/50 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-1 focus:ring-offset-black animate-pulse"
						aria-label="Afficher la notification de nouvelle fonctionnalité"
						title="Nouveautés dans les paramètres !"
					>
						<span class="text-lg leading-none">💡</span>
					</button>
				{/if}
				<!-- Burger Button -->
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
			</div>

			{#if showMobileMenu}
				<div
					class="mobile-menu animate-fade-in absolute top-full left-0 z-50 w-full bg-black shadow-lg"
				>
					{#if $userProfileStore}
						<a
							href="/articles"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							{$i18n.header.articles}
						</a>
						<a
							href="/ma-veille"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							{$i18n.header.myVeille}
						</a>
						<a
							href="/favoris"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							Favoris
						</a>
						<a
							href="/qui-sommes-nous"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							Qui sommes-nous ?
						</a>
						<a
							href="/comite"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							Comité scientifique
						</a>
						<a
							href="/donations"
							onclick={closeMobileMenu}
							class="block px-6 py-3 text-base hover:bg-gray-100"
						>
							{$i18n.header.donate}
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

<MobileFeatureNoticeModal
	isOpen={showMobileNoticeModal}
	on:closeAndDismiss={handleDismissNotice}
/>

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
