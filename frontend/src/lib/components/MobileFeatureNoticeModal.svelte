<!-- src/lib/components/MobileFeatureNoticeModal.svelte -->
<script lang="ts">
	import { X } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';
	import { fly } from 'svelte/transition';

	// Prop to control modal visibility
	let { isOpen = false } = $props<{ isOpen: boolean }>();

	// Event dispatcher to signal dismissal to the parent (Header.svelte)
	const dispatch = createEventDispatcher<{ closeAndDismiss: void }>();

	function closeAndDismiss() {
		// Signal parent to close modal AND handle the API call/state update
		dispatch('closeAndDismiss');
	}

	function handleBackdropClick(event: MouseEvent) {
		// Close if clicking the backdrop itself
		if (event.target === event.currentTarget) {
			closeAndDismiss();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		// Close on Escape key
		if (event.key === 'Escape') {
			closeAndDismiss();
		}
	}

</script>

{#if isOpen}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
		on:click={handleBackdropClick}
		on:keydown={handleKeydown}
		role="dialog"
		aria-modal="true"
		aria-labelledby="mobile-notice-title"
		transition:fly={{ y: 20, duration: 200 }}
	>
		<div class="relative w-full max-w-sm rounded-xl bg-gray-800 p-6 shadow-2xl text-white">
			<!-- Close Button -->
			<button
				type="button"
				on:click={closeAndDismiss}
				class="absolute top-2 right-2 rounded-full p-1.5 text-gray-400 transition-colors hover:bg-gray-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800"
				aria-label="Fermer la notification et ne plus afficher"
			>
				<X class="h-5 w-5" />
			</button>

			<!-- Notice Content -->
			<h4 id="mobile-notice-title" class="mb-3 text-base font-semibold text-white pr-6">
				🛠️ Nouveauté dans Paramètres !
			</h4>
			<ul class="mb-4 list-none space-y-1.5 pl-0 text-sm text-gray-300">
				<li>🎯 <strong class="font-medium text-teal-400">Sous-spécialités</strong> : affine tes domaines.</li>
				<li>🔬 <strong class="font-medium text-teal-400">Niveau de preuve</strong> : choisis tes grades (A, B, C).</li>
			</ul>
			<a href="/account" on:click={closeAndDismiss} class="mb-4 block text-sm font-medium text-teal-400 hover:text-teal-300 hover:underline">
				👉 Clique ici pour personnaliser !
			</a>
			<p class="border-t border-gray-700 pt-3 text-sm text-gray-400">
				➕ N'oublie pas de compléter ton profil ! (nom, statut, etc.)
			</p>
		</div>
	</div>
{/if}