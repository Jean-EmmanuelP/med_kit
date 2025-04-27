<script lang="ts">
	import { AlertTriangle, CheckCircle, Loader2, X } from 'lucide-svelte';
// Import necessary icons
	import { createEventDispatcher, tick } from 'svelte';

	const dispatch = createEventDispatcher();

	let { isOpen = $bindable() } = $props<{ isOpen: boolean }>();

	// Form state - These will now hold the full French strings
	let contentUseful: string | null = $state(null);
	let formatSuitable: string | null = $state(null);
	let desiredFeatures = $state('');
	let willingToPay: string | null = $state(null); // Will hold "Oui" or "Non"
	let priceSuggestion = $state('');
	let reasonNotToPay = $state('');
	let improvements = $state('');

	// Submission state
	let submissionStatus: 'idle' | 'loading' | 'success' | 'error' = $state('idle');
	let submissionMessage = $state('');

	// Update feedback modal timestamp when opened
	$effect(() => {
		if (isOpen) {
			fetch('/api/update-feedback-modal', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			}).catch(err => {
				console.error('Failed to update feedback modal timestamp:', err);
			});
		}
	});

	function closeModal() {
		isOpen = false;
		dispatch('close');
		// Reset state after closing
		resetForm();
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget && submissionStatus !== 'loading') {
			closeModal();
		}
	}

	function resetForm() {
		contentUseful = null;
		formatSuitable = null;
		desiredFeatures = '';
		willingToPay = null;
		priceSuggestion = '';
		reasonNotToPay = '';
		improvements = '';
		submissionStatus = 'idle';
		submissionMessage = '';
	}

	async function handleSubmit() {
		// Validate required fields
		if (!contentUseful) {
			submissionStatus = 'error';
			submissionMessage = 'Veuillez indiquer si le contenu vous est utile.';
			return;
		}
		if (!formatSuitable) {
			submissionStatus = 'error';
			submissionMessage = 'Veuillez indiquer si le format vous convient.';
			return;
		}
		if (!willingToPay) {
			submissionStatus = 'error';
			submissionMessage = 'Veuillez indiquer si vous seriez prêt·e à payer.';
			return;
		}

		submissionStatus = 'loading';
		submissionMessage = '';

        // This object now naturally contains the full French answers
		const feedback = {
			contentUseful,
			formatSuitable,
			desiredFeatures,
			willingToPay,
			priceSuggestion,
			reasonNotToPay,
			improvements
		};

		try {
			const response = await fetch('/api/submit-feedback', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(feedback)
			});

			const result = await response.json().catch(() => ({}));

			if (!response.ok) {
				throw new Error(result.message || `Erreur ${response.status}: La requête a échoué.`);
			}

			// Update the feedback modal timestamp
			await fetch('/api/update-feedback-modal', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			}).catch(err => {
				console.error('Failed to update feedback modal timestamp:', err);
			});

			submissionStatus = 'success';
			submissionMessage = result.message || 'Merci, votre retour a bien été envoyé !';

			await tick();
			setTimeout(() => {
				if (submissionStatus === 'success' && isOpen) {
					closeModal();
				}
			}, 2500);

		} catch (err: any) {
			console.error("Feedback submission error:", err);
			submissionStatus = 'error';
			submissionMessage = err.message || "Une erreur inattendue est survenue lors de l'envoi.";
		}
	}

	// Prevent body scroll when modal is open
	$effect(() => {
		const body = document.body;
		let originalOverflow: string | null = null;

		if (isOpen) {
			originalOverflow = body.style.overflow;
			body.style.overflow = 'hidden';
		}

		return () => {
			if (originalOverflow !== null) {
				body.style.overflow = originalOverflow;
			} else {
				body.style.overflow = '';
			}
			if (!isOpen && submissionStatus !== 'idle') {
				resetForm();
			}
		};
	});

</script>

{#if isOpen}
    <div
        class="fixed inset-0 z-50 flex items-start justify-center bg-black bg-opacity-70 backdrop-blur-sm overflow-y-auto pt-20 pb-10"
        on:click={handleBackdropClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="feedback-modal-title"
    >
        <div class="relative w-full max-w-2xl rounded-lg bg-gray-800 text-white shadow-xl mx-4 my-auto">
            <button
                class="absolute right-4 top-4 rounded-full p-1 text-gray-400 transition-colors hover:bg-gray-700 hover:text-white disabled:opacity-50"
                on:click={closeModal}
                disabled={submissionStatus === 'loading'}
                aria-label="Fermer la fenêtre"
            >
                <X class="h-6 w-6" />
            </button>

            <div class="p-6 sm:p-8">
                <h2 id="feedback-modal-title" class="mb-4 text-xl sm:text-2xl font-bold">🔍 Donne-nous ton avis en 1 minute !</h2>

                {#if submissionStatus !== 'success'}
                    <p class="mb-6 text-sm sm:text-base text-gray-300">
                        On veut rendre notre outil vraiment utile pour toi. Tes retours sont précieux 🙏
                    </p>

                    <form on:submit|preventDefault={handleSubmit} class="space-y-5 sm:space-y-6">
                        <!-- Question 1 -->
                        <fieldset>
                            <legend class="mb-2 font-medium text-sm sm:text-base">1. Est-ce que le contenu proposé t'est utile ?</legend>
                            <div class="space-y-1 sm:space-y-2 text-sm sm:text-base">
                                {#each [
                                    { value: 'Oui, très utile', label: 'Oui, très utile' },
                                    { value: 'Oui, plutôt utile', label: 'Oui, plutôt utile' },
                                    { value: 'Bof, peu utile', label: 'Bof, peu utile' },
                                    { value: 'Pas du tout utile', label: 'Pas du tout utile' }
                                ] as option}
                                <label class="flex items-center cursor-pointer">
                                    <!-- Changed value attribute -->
                                    <input type="radio" name="contentUseful" value={option.value} bind:group={contentUseful} class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 bg-gray-700" />
                                    {option.label}
                                </label>
                                {/each}
                            </div>
                        </fieldset>

                        <!-- Question 2 -->
                        <fieldset>
                            <legend class="mb-2 font-medium text-sm sm:text-base">2. Est-ce que le format te convient ?</legend>
                             <div class="space-y-1 sm:space-y-2 text-sm sm:text-base">
                                {#each [
                                    { value: 'Parfaitement (court, clair, pertinent)', label: 'Parfaitement (court, clair, pertinent)' },
                                    { value: 'Ça pourrait être mieux (trop long/technique…)', label: 'Ça pourrait être mieux (trop long/technique…)' },
                                    { value: 'Pas du tout adapté', label: 'Pas du tout adapté' }
                                ] as option}
                                <label class="flex items-center cursor-pointer">
                                    <!-- Changed value attribute -->
                                    <input type="radio" name="formatSuitable" value={option.value} bind:group={formatSuitable} class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 bg-gray-700" />
                                    {option.label}
                                </label>
                                {/each}
                            </div>
                        </fieldset>

                        <!-- Question 3 (No change needed) -->
                        <div>
                            <label for="desiredFeatures" class="block mb-2 font-medium text-sm sm:text-base">3. Quelles fonctionnalités aimerais-tu voir sur le site ?</label>
                            <textarea id="desiredFeatures"
                                bind:value={desiredFeatures}
                                placeholder="ex : recommandations personnalisées, filtres, recherche, audio…"
                                class="w-full rounded-md bg-gray-700 p-3 text-sm sm:text-base text-white placeholder-gray-400 border border-gray-600 focus:ring-blue-500 focus:border-blue-500"
                                rows="3"
                            ></textarea>
                        </div>

                        <!-- Question 4 -->
                        <fieldset>
                            <legend class="mb-2 font-medium text-sm sm:text-base">4. Serais-tu prêt·e à payer pour cet outil ?</legend>
                            <div class="mb-3 space-y-1 sm:space-y-2 text-sm sm:text-base">
                                {#each [ { value: 'Oui', label: 'Oui' }, { value: 'Non', label: 'Non' } ] as option}
                                <label class="flex items-center cursor-pointer">
                                     <!-- Changed value attribute -->
                                    <input type="radio" name="willingToPay" value={option.value} bind:group={willingToPay} class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 bg-gray-700" />
                                    {option.label}
                                </label>
                                {/each}
                            </div>

                             <!-- Conditional fields based on "Oui" or "Non" -->
                            {#if willingToPay === 'Oui'}
                                <div class="mb-3 transition-opacity duration-300 ease-in-out">
                                    <label for="priceSuggestion" class="block mb-2 text-sm sm:text-base">Si oui, à quel prix (par mois) ?</label>
                                    <input id="priceSuggestion"
                                        type="text"
                                        bind:value={priceSuggestion}
                                        placeholder="ex : 1€, 2€, 5€…"
                                        class="w-full rounded-md bg-gray-700 p-3 text-sm sm:text-base text-white placeholder-gray-400 border border-gray-600 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                            {:else if willingToPay === 'Non'}
                                <div class="mb-3 transition-opacity duration-300 ease-in-out">
                                    <label for="reasonNotToPay" class="block mb-2 text-sm sm:text-base">Si non, qu'est-ce qui te manquerait pour envisager de payer ?</label>
                                    <textarea id="reasonNotToPay"
                                        bind:value={reasonNotToPay}
                                        class="w-full rounded-md bg-gray-700 p-3 text-sm sm:text-base text-white placeholder-gray-400 border border-gray-600 focus:ring-blue-500 focus:border-blue-500"
                                        rows="2"
                                    ></textarea>
                                </div>
                            {/if}
                        </fieldset>

                        <!-- Question 5 (No change needed) -->
                        <div>
                            <label for="improvements" class="block mb-2 font-medium text-sm sm:text-base">5. Tu as 30 secondes de plus ? Dis-nous ce qu'on pourrait améliorer 👇</label>
                            <textarea id="improvements"
                                bind:value={improvements}
                                placeholder="Suggestions, bugs rencontrés, idées..."
                                class="w-full rounded-md bg-gray-700 p-3 text-sm sm:text-base text-white placeholder-gray-400 border border-gray-600 focus:ring-blue-500 focus:border-blue-500"
                                rows="3"
                            ></textarea>
                        </div>

                        <!-- Submission Area (No change needed) -->
                        <div class="flex flex-col items-end gap-3 pt-2">
                             {#if submissionStatus === 'error'}
                                <p class="text-sm text-red-400 flex items-center gap-1 w-full justify-start" role="alert">
                                    <AlertTriangle class="h-4 w-4 flex-shrink-0"/> {submissionMessage}
                                </p>
                             {/if}
                             <button
                                type="submit"
                                class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
                                disabled={submissionStatus === 'loading'}
                            >
                                {#if submissionStatus === 'loading'}
                                    <Loader2 class="mr-2 h-5 w-5 animate-spin" />
                                    Envoi en cours...
                                {:else}
                                    Envoyer le retour
                                {/if}
                            </button>
                        </div>
                    </form>

                {:else if submissionStatus === 'success'}
                     <!-- Success State (No change needed) -->
                    <div class="flex flex-col items-center justify-center text-center py-8 px-4">
                        <CheckCircle class="h-16 w-16 text-green-500 mb-4" />
                        <h3 class="text-xl font-semibold mb-2">Retour envoyé !</h3>
                        <p class="text-gray-300 mb-6">{submissionMessage}</p>
                        <p class="text-xs text-gray-400">Cette fenêtre se fermera automatiquement.</p>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
 /* Optional: Add some transition for the modal appearance */
    .fixed {
        transition: opacity 0.3s ease-in-out;
    }
</style>