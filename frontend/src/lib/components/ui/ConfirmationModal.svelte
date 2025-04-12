<!-- src/lib/components/ui/ConfirmationModal.svelte -->
<script lang="ts">
	import { createEventDispatcher, tick } from 'svelte';
	import { fly } from 'svelte/transition';

	// Props
	const {
		isOpen = false,
		title = 'Confirmer',
		message = 'Êtes-vous sûr de vouloir continuer ?',
		confirmText = 'Confirmer',
		cancelText = 'Annuler',
		confirmColor = 'bg-red-600 hover:bg-red-700 focus-visible:ring-red-500', // Default to red for destructive actions
		cancelColor = 'bg-gray-600 hover:bg-gray-700 focus-visible:ring-gray-500'
	} = $props<{
		isOpen?: boolean;
		title?: string;
		message?: string;
		confirmText?: string;
		cancelText?: string;
		confirmColor?: string; // Allow customizing confirm button color
		cancelColor?: string;
	}>();

	const dispatch = createEventDispatcher<{ confirm: void; cancel: void }>();

	let modalElement: HTMLElement | null = null;

	function handleConfirm() {
		dispatch('confirm');
	}

	function handleCancel() {
		dispatch('cancel');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			handleCancel();
		}
		// Basic focus trapping (can be enhanced)
		if (event.key === 'Tab' && modalElement) {
			const focusableElements = modalElement.querySelectorAll<HTMLElement>(
				'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
			);
			const firstElement = focusableElements[0];
			const lastElement = focusableElements[focusableElements.length - 1];

			if (event.shiftKey) { // Shift + Tab
				if (document.activeElement === firstElement) {
					lastElement.focus();
					event.preventDefault();
				}
			} else { // Tab
				if (document.activeElement === lastElement) {
					firstElement.focus();
					event.preventDefault();
				}
			}
		}
	}

	// Focus the first button when the modal opens
	$effect(() => {
		if (isOpen && modalElement) {
			const firstButton = modalElement.querySelector<HTMLButtonElement>('button.confirm-button'); // Target confirm button first
			if (firstButton) {
				 void tick().then(() => firstButton.focus()); // Wait for render then focus
			}
		}
	});

</script>

{#if isOpen}
	<!-- svelte-ignore a11y-no-static-element-interactions a11y-click-events-have-key-events -->
	<div
		class="fixed inset-0 z-[250] flex items-center justify-center bg-black/70 backdrop-blur-sm"
		on:click|self={handleCancel}
		on:keydown={handleKeydown}
		role="alertdialog"
		aria-modal="true"
		aria-labelledby="confirm-modal-title"
		aria-describedby="confirm-modal-message"
		transition:fly={{ y: -20, duration: 200 }}
	>
		<div
			bind:this={modalElement}
			class="relative w-full max-w-md rounded-xl bg-gray-800 shadow-2xl p-6 mx-4"
		>
			<h2 id="confirm-modal-title" class="text-lg font-semibold text-white mb-3">
				{title}
			</h2>

			<p id="confirm-modal-message" class="text-sm text-gray-300 mb-6">
				{@html message}
			</p>

			<div class="flex justify-end space-x-3">
				<button
					type="button"
					on:click={handleCancel}
					class="cancel-button px-4 py-2 rounded-md text-sm font-medium text-white {cancelColor} transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
				>
					{cancelText}
				</button>
				<button
					type="button"
					on:click={handleConfirm}
					class="confirm-button px-4 py-2 rounded-md text-sm font-medium text-white {confirmColor} transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
				>
					{confirmText}
				</button>
			</div>
		</div>
	</div>
{/if}