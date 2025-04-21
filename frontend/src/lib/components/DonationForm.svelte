<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { i18n } from '$lib/i18n';
    import { fade } from 'svelte/transition';
    import { AlertCircle } from 'lucide-svelte';

    // --- Props & Events ---
    const dispatch = createEventDispatcher<{ amountChange: number }>();

	// --- Component State ---
	let errorMessage = $state(''); // Keep for amount validation
    let currentAmount = $state(10); // Default donation amount in EUR
    let customAmountInput = $state('');
    let isCustomAmountConfirmed = $state(false); // Track if the current amount is from confirmed custom input
    const presetAmounts = [5, 10, 20, 50];
    let { disabled = false } = $props<{ disabled?: boolean }>(); // Allow disabling from parent

    // --- Amount Selection Logic (Simplified) ---
    function selectAmount(amount: number) {
        if (disabled) return;
        currentAmount = amount;
        isCustomAmountConfirmed = false;
        customAmountInput = '';
        errorMessage = ''; // Clear error on preset selection
        dispatch('amountChange', amount * 100); // Dispatch amount in cents
    }

    function handleCustomAmountChange(event: Event) {
        if (disabled) return;
        const input = event.target as HTMLInputElement;
        const value = input.value.replace(/,/g, '.');
        const numericValue = parseFloat(value);
        isCustomAmountConfirmed = false; // Input changed, needs reconfirmation

        if (value === '') {
            errorMessage = '';
        } else if (isNaN(numericValue) || numericValue < 0.50) {
            errorMessage = $i18n.donations.errors.invalidAmount;
        } else {
            errorMessage = '';
        }
        customAmountInput = input.value; // Update display value immediately
    }

    function confirmCustomAmount() {
        if (disabled) return;
        const value = customAmountInput.replace(/,/g, '.');
        const numericValue = parseFloat(value);

        if (!isNaN(numericValue) && numericValue >= 0.50) {
            currentAmount = numericValue; // Update internal amount state if needed
            isCustomAmountConfirmed = true;
            errorMessage = '';
            dispatch('amountChange', Math.round(numericValue * 100)); // Dispatch confirmed amount
        } else {
            errorMessage = $i18n.donations.errors.invalidAmount;
            isCustomAmountConfirmed = false;
        }
    }
</script>

<div class="donation-amount-selector text-white">
    <div class="mb-6">
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {#each presetAmounts as amount}
                <button type="button" on:click={() => selectAmount(amount)}
                     class="rounded-md border-2 px-4 py-3 text-center font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-60 disabled:cursor-not-allowed"
                     class:border-orange-500={currentAmount === amount && !customAmountInput}
                     class:bg-orange-600={currentAmount === amount && !customAmountInput}
                     class:text-white={currentAmount === amount && !customAmountInput}
                     class:border-gray-600={!(currentAmount === amount && !customAmountInput)}
                     class:hover:border-orange-400={currentAmount !== amount || !!customAmountInput}
                     class:hover:bg-gray-700={currentAmount !== amount || !!customAmountInput}
                     class:text-gray-300={!(currentAmount === amount && !customAmountInput)}
                     disabled={disabled}>
                     {amount} €
                </button>
            {/each}
        </div>
        <div class="mt-4 flex items-center gap-2">
            <div class="relative flex-grow">
                <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">€</span>
                <input type="text" id="custom-amount-input" inputmode="decimal"
                     placeholder="Autre montant" bind:value={customAmountInput}
                     on:input={handleCustomAmountChange}
                     class="w-full rounded-md border-2 bg-gray-700 py-3 pl-8 pr-4 text-white placeholder-gray-400 transition-colors duration-200 focus:z-10 focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:ring-offset-0 disabled:opacity-60 disabled:cursor-not-allowed"
                     class:border-orange-500={customAmountInput !== '' && isCustomAmountConfirmed}
                     class:border-gray-600={customAmountInput === '' || !isCustomAmountConfirmed}
                     class:border-yellow-500={customAmountInput !== '' && !isCustomAmountConfirmed}
                     disabled={disabled} />
            </div>
            <button type="button" on:click={confirmCustomAmount}
                 class="shrink-0 rounded-md border-2 bg-gray-600 px-4 py-3 font-medium text-white transition-colors hover:bg-gray-500 focus:z-10 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-60"
                 class:border-orange-500={customAmountInput !== '' && isCustomAmountConfirmed}
                 class:border-gray-600={customAmountInput === ''}
                 class:border-yellow-500={customAmountInput !== '' && !isCustomAmountConfirmed}
                 disabled={disabled || customAmountInput === '' || (customAmountInput !== '' && parseFloat(customAmountInput.replace(/,/g, '.')) < 0.50) || isCustomAmountConfirmed}
                 title="Valider ce montant">
                 OK
             </button>
        </div>
         {#if errorMessage}
            <p class="mt-2 text-sm text-red-400 flex items-center gap-1"><AlertCircle class="w-4 h-4"/> {errorMessage}</p>
         {/if}
    </div>
</div>

<style>
    /* ... styles for amount buttons/input if needed ... */
</style>