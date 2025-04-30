<!-- src/lib/components/SupportCommitteeNotice.svelte -->
<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { X } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	// Define the event this component can dispatch
	const dispatch = createEventDispatcher<{ dismiss: void }>();

	// Receive visibility state directly from the parent
	let { isVisible = false } = $props<{ isVisible: boolean }>();

	// Function to handle the dismiss action
	function dismiss() {
		// Signal the parent component to handle the logic (API call, state update)
		dispatch('dismiss');
	}

	// CSS classes for the notice box
	const wrapperClasses = $derived(cn(
		"w-72 rounded-lg border border-gray-700 bg-gray-800 p-4 shadow-lg animate-fade-in text-white", // Wider for new content
		"absolute top-full right-0 z-20 mt-2" // Desktop positioning
	));

	// CSS classes for the close button
	const closeButtonClasses = $derived(cn(
		"absolute top-1.5 right-1.5 rounded-full p-1 text-gray-400 transition-colors hover:bg-gray-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800"
	));

</script>

{#if isVisible}
	<div
		class={wrapperClasses}
		role="status"
		aria-live="polite"
	>
		<button
			type="button"
			on:click={dismiss}
			class={closeButtonClasses}
			aria-label="Fermer la notification"
		>
			<X class="h-4 w-4" />
		</button>

		<!-- Notice Content -->
		<h4 class="mb-2 text-sm font-semibold text-white">💖 Contribuez à Veille Médicale !</h4>
		<ul class="mb-3 list-none space-y-1 pl-0 text-xs text-gray-300">
			<li>
                🙏 <strong class="font-medium text-teal-400">Soutenez-nous</strong> : Aidez à maintenir le service via un
                <a href="/donations" class="font-medium text-teal-500 hover:text-teal-400 hover:underline">don</a>.
            </li>
			<li>
                🧑‍🔬 <strong class="font-medium text-teal-400">Comité Scientifique</strong> : Envie de participer ?
                <a href="/comite" class="font-medium text-teal-500 hover:text-teal-400 hover:underline">Rejoignez-nous</a> !
            </li>
		</ul>
		<p class="border-t border-gray-700 pt-2 text-xs text-gray-400">
			Votre soutien et votre expertise sont précieux !
		</p>
	</div>
{/if}

<style>
	.animate-fade-in {
		animation: fadeIn 0.3s ease-out forwards;
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