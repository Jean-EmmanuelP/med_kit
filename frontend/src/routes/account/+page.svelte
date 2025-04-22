<!-- /routes/account/+page.svelte -->
<script lang="ts">
	import { i18n } from '$lib/i18n'; // Assuming i18n setup is client-side friendly
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase'; // Use the browser client for API calls
	import { onMount } from 'svelte';
	import * as Select from '$lib/components/ui/select/index.js';
    import { AlertCircle, Check, ChevronDown, ChevronUp, Loader2 } from 'lucide-svelte'; // Import icons

	// Get props (data from load function)
	let { data } = $props();

    // --- Reactive State ---
    // Profile fields
	let firstName = $state(data.userProfile?.first_name || '');
	let lastName = $state(data.userProfile?.last_name || '');
	let status = $state(data.userProfile?.status || '');
	let specialty = $state(data.userProfile?.specialty || '');
	let dateOfBirth = $state(data.userProfile?.date_of_birth || '');

    // Subscription state
    let currentSubscriptions = $state(new Set<string>(data.userSubscriptions || []));

    // UI State
	let isLoading = $state(false);
    let saveSuccess = $state(false);
    let saveError = $state('');
    let openDisciplines = $state(new Set<number>()); // Store IDs of open disciplines

    // Data from load function
    const allDisciplines = $derived(data.allDisciplines || []);
    const statusOptions = $derived(data.statusOptions || []); // Use options from server

    // Define the notification options
    const notificationOptions = [
        { value: 'tous_les_jours', label: 'Tous les jours' },
        { value: 'tous_les_2_jours', label: 'Tous les 2 jours' },
        { value: 'tous_les_3_jours', label: 'Tous les 3 jours' },
        { value: '1_fois_par_semaine', label: 'Une fois par semaine' },
        { value: 'tous_les_15_jours', label: 'Tous les 15 jours' },
        { value: '1_fois_par_mois', label: 'Une fois par mois' }
    ];

    // Make sure the initial value exactly matches one of the enum values
    let selectedNotificationFreq = $state(
        notificationOptions.some(opt => opt.value === data.userProfile?.notification_frequency)
            ? data.userProfile?.notification_frequency
            : 'tous_les_jours'
    );

    // Update the trigger content to always show the selected option's label
    const triggerNotificationContent = $derived(
        notificationOptions.find(o => o.value === selectedNotificationFreq)?.label || 'Choisir une fréquence'
    );

	// Compute display labels for dropdowns
	const triggerStatusContent = $derived(
		statusOptions.find(o => o === status) ?? 'Choisissez un statut'
	);

	// --- Effects ---
	$effect(() => {
        // This effect was removing user input on store changes, which is likely not desired.
        // Removed the logic that reset the state variables here.
        // The initial state is set correctly using $state(data.userProfile?.field || '')
    });

    $effect(() => {
        if (saveSuccess || saveError) {
            const timer = setTimeout(() => {
                saveSuccess = false;
                saveError = '';
            }, 4000);
            return () => clearTimeout(timer);
        }
    });

     // --- Initialize open disciplines based on current subscriptions ---
     $effect(() => {
        const initialOpen = new Set<number>();
        currentSubscriptions.forEach(key => {
            if (key.startsWith('s:')) {
                const subId = parseInt(key.split(':')[1], 10);
                if (!isNaN(subId)) {
                    for (const discipline of allDisciplines) {
                        if (discipline.sub_disciplines?.some(sub => sub.id === subId)) {
                            initialOpen.add(discipline.id);
                            break; // Found the parent, move to next key
                        }
                    }
                }
            } else if (key.startsWith('d:')) {
                const discId = parseInt(key.split(':')[1], 10);
                if (!isNaN(discId)) {
                     // Optionally auto-open if the main discipline is checked,
                     // but the toggle logic handles opening when checked now.
                }
            }
        });
        // Only set openDisciplines on the initial load or if it hasn't been set yet
        // to avoid overriding user interactions. Let's remove this auto-open based on
        // current subs, as the new logic handles opening when a main is checked.
        // openDisciplines = initialOpen;
     });


    // --- Functions ---
    function toggleDisciplineSection(disciplineId: number) {
        const newSet = new Set(openDisciplines);
        if (newSet.has(disciplineId)) {
            newSet.delete(disciplineId);
        } else {
            newSet.add(disciplineId);
        }
        openDisciplines = newSet;
    }

    function handleMainDisciplineChange(disciplineId: number, isChecked: boolean) {
        const key = `d:${disciplineId}`;
        const newSubs = new Set(currentSubscriptions);
        const newOpen = new Set(openDisciplines); // Get current open state
        const discipline = allDisciplines.find(d => d.id === disciplineId);

        if (isChecked) {
            newSubs.add(key);
            // Select all sub-disciplines
            discipline?.sub_disciplines.forEach(sub => {
                 newSubs.add(`s:${sub.id}`);
            });
            // Expand the section
            newOpen.add(disciplineId);
        } else {
            newSubs.delete(key);
            // Deselect all sub-disciplines
            discipline?.sub_disciplines.forEach(sub => {
                 newSubs.delete(`s:${sub.id}`);
            });
            // Collapse the section
            newOpen.delete(disciplineId);
        }
        currentSubscriptions = newSubs;
        openDisciplines = newOpen; // Update open state
    }

    function handleSubDisciplineChange(subDisciplineId: number, disciplineId: number, isChecked: boolean) {
        const key = `s:${subDisciplineId}`;
        const mainKey = `d:${disciplineId}`;
        const newSubs = new Set(currentSubscriptions);

        if (isChecked) {
            newSubs.add(key);
            // Automatically check the parent discipline if it's not already checked
            if (!newSubs.has(mainKey)) {
                newSubs.add(mainKey);
            }
        } else {
            newSubs.delete(key);
            // Optional: Uncheck parent ONLY if no other subs under it are checked
            const discipline = allDisciplines.find(d => d.id === disciplineId);
            const hasOtherCheckedSubs = discipline?.sub_disciplines.some(
                sub => sub.id !== subDisciplineId && newSubs.has(`s:${sub.id}`)
            ) ?? false;

            if (!hasOtherCheckedSubs && newSubs.has(mainKey)) {
                 // If you want to auto-uncheck parent when last sub is unchecked:
                 // newSubs.delete(mainKey);
                 // Keeping parent checked is usually less confusing, so we'll leave it checked for now.
            }
        }
        currentSubscriptions = newSubs;
    }

	async function handleSubmit() {
		if (isLoading) return;
		isLoading = true;
        saveSuccess = false;
        saveError = '';

        const profileUpdates = {
            first_name: firstName,
            last_name: lastName,
            status: status || null,
            specialty: specialty || null,
            notification_frequency: selectedNotificationFreq,
            date_of_birth: dateOfBirth || null,
            // 'disciplines' field in user_profiles is no longer updated directly
        };

        const subscriptionsPayload: { discipline_id: number; sub_discipline_id: number | null }[] = [];
        currentSubscriptions.forEach(key => {
            const [type, idStr] = key.split(':');
            const id = parseInt(idStr, 10);
            if (!isNaN(id)) {
                if (type === 'd') {
                    // Check if ANY sub-discipline for this main discipline is also selected.
                    // If so, we only need to insert the sub-discipline rows.
                    // If not, we insert the main discipline row (sub_discipline_id: null).
                    const discipline = allDisciplines.find(d => d.id === id);
                    const hasAnySubSelected = discipline?.sub_disciplines.some(sub => currentSubscriptions.has(`s:${sub.id}`)) ?? false;
                    if (!hasAnySubSelected) {
                         subscriptionsPayload.push({ discipline_id: id, sub_discipline_id: null });
                    }
                } else if (type === 's') {
                    let parentDisciplineId: number | null = null;
                    for (const disc of allDisciplines) {
                        if (disc.sub_disciplines.some(sub => sub.id === id)) {
                            parentDisciplineId = disc.id;
                            break;
                        }
                    }
                    if (parentDisciplineId !== null) {
                        subscriptionsPayload.push({ discipline_id: parentDisciplineId, sub_discipline_id: id });
                    } else {
                         console.warn(`Could not find parent discipline for sub_discipline_id: ${id}`);
                    }
                }
            }
        });

        // Ensure distinct entries (e.g., if both main and sub were added programmatically somehow)
        // Although the logic above should prevent duplicates if a sub is selected
        const distinctSubscriptionsPayload = Array.from(new Map(subscriptionsPayload.map(item => [`${item.discipline_id}-${item.sub_discipline_id}`, item])).values());

        try {
			const response = await fetch('/api/update-profile-and-subscriptions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile: profileUpdates,
                    subscriptions: distinctSubscriptionsPayload // Send distinct list
                })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || `HTTP Error ${response.status}`);

            // Update local user profile store only with profile fields
			userProfileStore.update(current => {
                if (current) {
                    return {
                        ...current,
                        first_name: profileUpdates.first_name,
                        last_name: profileUpdates.last_name,
                        status: profileUpdates.status,
                        specialty: profileUpdates.specialty,
                        notification_frequency: profileUpdates.notification_frequency,
                        date_of_birth: profileUpdates.date_of_birth,
                        // Keep the old 'disciplines' array in the store for now if needed elsewhere,
                        // but it's not directly synced with the new subscription model here.
                        // You might want to update it based on `distinctSubscriptionsPayload` if necessary.
                    };
                }
                return null;
            });
            saveSuccess = true;
		} catch (err: any) {
			console.error('Error updating profile/subscriptions:', err);
			saveError = err.message || 'Erreur lors de la mise à jour.';
		} finally {
			isLoading = false;
		}
	}

	async function handleLogout() {
		try {
			isLoading = true;
            saveError = '';
			const { error } = await supabase.auth.signOut();
			if (error) throw error;
			userProfileStore.set(null);
			window.location.href = '/login';
		} catch (error: any) {
			console.error('Erreur lors de la déconnexion :', error);
            saveError = `Erreur de déconnexion: ${error.message}`;
            isLoading = false;
		}
	}
</script>

<div class="min-h-screen bg-black px-4 py-12 text-white pt-20 md:pt-24">
	<div class="mx-auto max-w-3xl">
		<h1 class="mb-8 text-3xl md:text-4xl font-bold text-white">Mon compte</h1>

		{#if data.error}
			<p class="mb-6 rounded border border-red-700 bg-red-900/30 p-4 text-red-300">{data.error}</p>
		{:else if !data.userProfile}
            <p class="mb-6 rounded border border-yellow-700 bg-yellow-900/30 p-4 text-yellow-300">Chargement du profil...</p>
        {:else}
			<!-- Form Section -->
			<form on:submit|preventDefault={handleSubmit} class="space-y-8 rounded-lg bg-gray-800 p-6 md:p-8 shadow-lg">

				<!-- Vos Informations Section -->
				<div>
                    <h2 class="text-xl md:text-2xl font-semibold text-white border-b border-gray-700 pb-3 mb-6">Vos informations</h2>
                    <div class="space-y-6">
                        <div>
                            <label for="firstName" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.login.firstName}</label>
                            <input
                                id="firstName"
                                type="text"
                                bind:value={firstName}
                                on:input={(e) => firstName = e.target.value || ''}
                                class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50"
                                required />
                        </div>
                        <div>
                            <label for="lastName" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.login.lastName}</label>
                            <input
                                id="lastName"
                                type="text"
                                bind:value={lastName}
                                on:input={(e) => lastName = e.target.value || ''}
                                class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50"
                                required />
                        </div>
                        <div>
                            <label for="status" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.account.status}</label>
                            <select
                                id="status"
                                bind:value={status}
                                class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-sm text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50 appearance-none"
                            >
                                <option value="">-- Choisir --</option> 
                                {#each statusOptions as option}
                                    <option value={option}>{option}</option>
                                {/each}
                            </select>
                        </div>
                        <div>
                            <label for="specialty" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.account.specialty}</label>
                            <input
                                id="specialty"
                                type="text"
                                bind:value={specialty}
                                on:input={(e) => specialty = e.target.value || ''}
                                class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50"
                                placeholder="Ex: Médecine Générale" />
                        </div>
                        <div>
                            <label for="dateOfBirth" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.login.dateOfBirth}</label>
                            <input
                                id="dateOfBirth"
                                type="date"
                                bind:value={dateOfBirth}
                                on:input={(e) => dateOfBirth = e.target.value || ''}
                                class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50" />
                        </div>
                    </div>
                </div>

				<hr class="border-gray-700" />

                <!-- Vos Préférences Section -->
				<div>
                    <h2 class="text-xl md:text-2xl font-semibold text-white border-b border-gray-700 pb-3 mb-6">Vos préférences de veille</h2>

                    <!-- Notification Frequency -->
                    <div class="mb-8">
                        <label for="notificationFrequency" class="mb-2 block text-sm font-medium text-gray-300">Fréquence des notifications</label>
                        <select
                            id="notificationFrequency"
                            bind:value={selectedNotificationFreq}
                            class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-sm text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50 appearance-none"
                        >
                            {#each notificationOptions as option}
                                <option value={option.value}>{option.label}</option>
                            {/each}
                        </select>
                    </div>

                    <!-- Discipline/Sub-discipline Subscriptions -->
                    <div>
                        <label class="mb-4 block text-sm font-medium text-gray-300">Spécialités et sous-spécialités suivies</label>
                        <div class="space-y-4 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-teal-600 scrollbar-track-gray-700 rounded-md border border-gray-600 p-4 bg-gray-700/50">
                             {#each allDisciplines as discipline (discipline.id)}
                                <div class="discipline-group">
                                    <div class="flex items-center justify-between">
                                        <label class="flex items-center cursor-pointer select-none py-1 flex-grow">
                                            <input
                                                type="checkbox"
                                                class="h-4 w-4 rounded border-gray-500 bg-gray-600 text-teal-500 focus:ring-teal-600 focus:ring-offset-gray-800 mr-3 shrink-0"
                                                checked={currentSubscriptions.has(`d:${discipline.id}`)}
                                                on:change={(e) => handleMainDisciplineChange(discipline.id, e.currentTarget.checked)}
                                            />
                                            <span class="font-medium text-gray-100">{discipline.name}</span>
                                        </label>
                                        {#if discipline.sub_disciplines && discipline.sub_disciplines.length > 0}
                                             <button type="button" on:click={() => toggleDisciplineSection(discipline.id)} class="text-gray-400 hover:text-gray-200 p-1 -mr-1 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-1 focus:ring-offset-gray-800 shrink-0 ml-2">
                                                 {#if openDisciplines.has(discipline.id)} <ChevronUp class="h-4 w-4" /> {:else} <ChevronDown class="h-4 w-4" /> {/if}
                                             </button>
                                        {/if}
                                    </div>
                                    {#if openDisciplines.has(discipline.id) && discipline.sub_disciplines && discipline.sub_disciplines.length > 0}
                                        <div class="mt-2 pl-6 border-l border-gray-600 ml-2 space-y-1.5">
                                             {#each discipline.sub_disciplines as sub (sub.id)}
                                                  <label class="flex items-center cursor-pointer select-none py-0.5">
                                                      <input
                                                          type="checkbox"
                                                          class="h-4 w-4 rounded border-gray-500 bg-gray-600 text-teal-500 focus:ring-teal-600 focus:ring-offset-gray-800 mr-3 shrink-0"
                                                          checked={currentSubscriptions.has(`s:${sub.id}`)}
                                                          on:change={(e) => handleSubDisciplineChange(sub.id, discipline.id, e.currentTarget.checked)}
                                                      />
                                                      <span class="text-sm text-gray-300 hover:text-gray-100">{sub.name}</span>
                                                  </label>
                                             {/each}
                                        </div>
                                    {/if}
                                </div>
                             {:else}
                                <p class="text-gray-500 italic">Aucune discipline disponible.</p>
                             {/each}
                        </div>
                         <p class="text-xs text-gray-400 mt-3">Cocher une spécialité sélectionne automatiquement toutes ses sous-spécialités.</p>
                    </div>
                </div>

				<!-- Save Button & Messages -->
				<div class="pt-5">
                     {#if saveSuccess}
                        <div role="alert" class="mb-4 flex items-center gap-2 rounded-md bg-green-800/30 border border-green-600 p-3 text-sm text-green-300">
                            <Check class="h-4 w-4 flex-shrink-0" />
                            Profil et abonnements mis à jour avec succès !
                        </div>
                     {/if}
                     {#if saveError}
                         <div role="alert" class="mb-4 flex items-center gap-2 rounded-md bg-red-900/30 border border-red-700 p-3 text-sm text-red-300">
                            <AlertCircle class="h-4 w-4 flex-shrink-0" />
                            {saveError}
                        </div>
                     {/if}
					<button
						type="submit"
						disabled={isLoading}
						class="flex w-full items-center justify-center rounded-lg bg-orange-600 px-8 py-3 font-semibold text-white shadow-md transition-all duration-300 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
					>
						{#if isLoading} <Loader2 class="mr-2 h-5 w-5 animate-spin" /> <span>Enregistrement...</span>
						{:else} Enregistrer les modifications {/if}
					</button>
				</div>
			</form>

            <hr class="my-10 border-gray-700" />

			<!-- Logout Section -->
			<div class="text-left">
				<h2 class="mb-4 text-xl md:text-2xl font-semibold text-white">Se déconnecter</h2>
				<button
					on:click={handleLogout}
                    disabled={isLoading}
					class="rounded-lg bg-gray-600 px-6 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
				>
					Déconnexion
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Custom scrollbar for the select dropdown & discipline list */
	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #0d9488 #374151; /* thumb(teal-600) track(gray-700) */
	}
	.scrollbar-thin::-webkit-scrollbar {
		width: 6px; height: 6px;
	}
	.scrollbar-thin::-webkit-scrollbar-track {
		background: #374151; /* gray-700 */ border-radius: 10px;
	}
	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #0d9488; /* teal-600 */ border-radius: 6px; border: 1px solid #374151; /* gray-700 */
	}
    .scrollbar-thin::-webkit-scrollbar-thumb:hover {
		background-color: #0f766e; /* teal-700 */
	}

    /* Ensure date input text is visible */
    input[type="date"] { color-scheme: dark; }
    input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(0.8); }

    /* Ensure checkbox is visible in dark mode */
    input[type="checkbox"] { color-scheme: dark; }

     /* Restore original input/select styles */
    label {
         /* Keep the existing label style */
         margin-bottom: 0.5rem; /* mb-2 */
         display: block;
         font-size: 0.875rem; /* text-sm */
         font-weight: 500; /* font-medium */
         color: #D1D5DB; /* text-gray-300 */
    }
     input[type="text"], input[type="date"], select {
        margin-top: 0.25rem; /* mt-1 */
        display: block;
        width: 100%;
        border-radius: 0.5rem; /* rounded-lg */
        border: 1px solid #4B5563; /* border-gray-700 */
        background-color: #374151; /* bg-gray-700 */
        padding: 0.75rem 1rem; /* px-4 py-3 */
        color: #FFFFFF; /* text-white */
        transition: all 0.2s ease-in-out; /* transition-all duration-200 */
        font-size: 0.875rem; /* text-sm */ /* Added to match Select component */
        line-height: 1.25rem; /* Added to match Select component */
        height: 3rem; /* Explicit height to match Select */
    }
     input[type="text"]:focus, input[type="date"]:focus, select:focus {
        border-color: #14B8A6; /* focus:border-teal-500 */
        outline: 2px solid transparent; /* Remove default outline */
        outline-offset: 2px;
        --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
        --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(1px + var(--tw-ring-offset-width)) var(--tw-ring-color); /* Simulating focus:ring */
        box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
        --tw-ring-color: rgba(20, 184, 166, 0.5); /* focus:ring-teal-600/50 */
    }

    /* Style select arrow */
    select {
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
        background-position: right 0.5rem center;
        background-repeat: no-repeat;
        background-size: 1.5em 1.5em;
        padding-right: 2.5rem;
        -webkit-appearance: none;
           -moz-appearance: none;
                appearance: none;
    }

     /* Revert the grid layout for profile fields */
    form > div:first-child > div:not(.space-y-6) { /* Target direct children divs containing profile info */
         display: block; /* Revert from grid */
    }
    form > div:first-child > div > div { /* Target the inner divs for each field */
        margin-bottom: 1.5rem; /* Re-add vertical spacing (space-y-6 equivalent) */
    }

</style>