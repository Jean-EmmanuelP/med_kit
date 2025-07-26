<!-- /routes/account/+page.svelte -->
<script lang="ts">
	import SubscriptionStatus from '$lib/components/SubscriptionStatus.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase';
	import { AlertCircle, Check, ChevronDown, ChevronUp, Loader2 } from 'lucide-svelte';

	let { data } = $props();

    // --- Reactive State ---
    // Profile fields
	let firstName = $state(data.userProfile?.first_name || '');
	let lastName = $state(data.userProfile?.last_name || '');
	let status = $state(data.userProfile?.status || '');
	let specialty = $state(data.userProfile?.specialty || '');
	let dateOfBirth = $state(data.userProfile?.date_of_birth || '');
    let activeSubscription = $state(data.activeSubscription || null);

    // Subscription state
    let currentSubscriptions = $state(new Set<string>(data.userSubscriptions || []));
    let selectedGrades = $state(new Set<string>(data.userGradePreferences && data.userGradePreferences.length > 0 ? data.userGradePreferences : ['A', 'B', 'C'])); // Fix: Only default if no grades are saved

    // Debug logs for data loading
    console.log('=== ACCOUNT PAGE DATA LOADING ===');
    console.log('data.userGradePreferences:', data.userGradePreferences);
    console.log('data.userSubscriptions:', data.userSubscriptions);
    console.log('Initial selectedGrades:', Array.from(selectedGrades));
    console.log('Initial currentSubscriptions:', Array.from(currentSubscriptions));

    // UI State
	let isLoading = $state(false);
    let saveSuccess = $state(false);
    let saveError = $state('');
    let openDisciplines = $state(new Set<number>());
    let showGradeInfo = $state(false); // Keep grade info panel logic

    // Auto-open discipline sections that have selected sub-disciplines
    $effect(() => {
        if (allDisciplines.length > 0 && currentSubscriptions.size > 0) {
            const disciplinesToOpen = new Set<number>();
            allDisciplines.forEach(discipline => {
                // Check if this discipline has any selected sub-disciplines
                const hasSelectedSubs = discipline.sub_disciplines?.some(sub => 
                    currentSubscriptions.has(`s:${sub.id}`)
                );
                if (hasSelectedSubs) {
                    disciplinesToOpen.add(discipline.id);
                }
            });
            openDisciplines = disciplinesToOpen;
            console.log('Auto-opened disciplines:', Array.from(disciplinesToOpen));
        }
    });

    // Data from load function
    const allDisciplines = $derived(data.allDisciplines || []);
    const statusOptions = $derived(data.statusOptions || []);
    const notificationOptions = $derived(data.notificationOptions || []);
    // REMOVED minimumGradeOptions = $derived(...)

    // Update the trigger content to always show the selected option's label
    const triggerNotificationContent = $derived(
        notificationOptions.find(o => o.value === selectedNotificationFreq)?.label || 'Choisir une fréquence'
    );

    let selectedNotificationFreq = $state(
        notificationOptions.some(opt => opt.value === data.userProfile?.notification_frequency)
            ? data.userProfile?.notification_frequency
            : 'tous_les_jours'
    );

	const triggerStatusContent = $derived(
		statusOptions.find(o => o === status) ?? 'Choisissez un statut'
	);

    // --- Grade Info Data (unchanged) ---
    const gradeInfo = [
      { grade: 'A', label: 'Preuve scientifique établie', niveau: 'Niveau 1', details: ['essais comparatifs randomisés de forte puissance', 'méta-analyse d\'essais comparatifs randomisés', 'analyse de décision fondée sur des études bien menées.'] },
      { grade: 'B', label: 'Présomption scientifique', niveau: 'Niveau 2', details: ['essais comparatifs randomisés de faible puissance', 'études comparatives non randomisées bien menées', 'études de cohortes.'] },
      { grade: 'C', label: 'Faible niveau de preuve scientifique', niveau: 'Niveau 3 et 4', details: ['études cas-témoins', 'études comparatives comportant des biais importants', 'études rétrospectives', 'séries de cas', 'études épidémiologiques descriptives (transversale, longitudinale).'] }
    ];

    // --- Effects (unchanged, except for initial openDisciplines which is now empty as it's handled by toggles) ---
    $effect(() => {
        if (saveSuccess || saveError) {
            const timer = setTimeout(() => {
                saveSuccess = false;
                saveError = '';
            }, 4000);
            return () => clearTimeout(timer);
        }
    });

    // --- Functions ---
    function toggleDisciplineSection(disciplineId: number) {
        // Logic remains the same
        const newSet = new Set(openDisciplines);
        if (newSet.has(disciplineId)) { newSet.delete(disciplineId); } else { newSet.add(disciplineId); }
        openDisciplines = newSet;
    }
    function handleMainDisciplineChange(disciplineId: number, isChecked: boolean) {
        // Logic remains the same
        const key = `d:${disciplineId}`;
        const newSubs = new Set(currentSubscriptions);
        const newOpen = new Set(openDisciplines);
        const discipline = allDisciplines.find(d => d.id === disciplineId);
        if (isChecked) {
            newSubs.add(key);
            discipline?.sub_disciplines.forEach(sub => { newSubs.add(`s:${sub.id}`); });
            newOpen.add(disciplineId);
        } else {
            newSubs.delete(key);
            discipline?.sub_disciplines.forEach(sub => { newSubs.delete(`s:${sub.id}`); });
            newOpen.delete(disciplineId);
        }
        currentSubscriptions = newSubs;
        openDisciplines = newOpen;
    }
    function handleSubDisciplineChange(subDisciplineId: number, disciplineId: number, isChecked: boolean) {
        // Logic remains the same
        const key = `s:${subDisciplineId}`;
        const mainKey = `d:${disciplineId}`;
        const newSubs = new Set(currentSubscriptions);
        if (isChecked) {
            newSubs.add(key);
            if (!newSubs.has(mainKey)) { newSubs.add(mainKey); }
        } else {
            newSubs.delete(key);
        }
        currentSubscriptions = newSubs;
    }

    // **** NEW: Handle grade checkbox changes ****
    function handleGradeChange(grade: 'A' | 'B' | 'C', isChecked: boolean) {
        const newGrades = new Set(selectedGrades);
        if (isChecked) {
            newGrades.add(grade);
        } else {
            newGrades.delete(grade); // Allow unchecking all for now
        }
        selectedGrades = newGrades;
        console.log("Selected grades:", Array.from(selectedGrades));
    }
    // **** END NEW ****


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
            // REMOVED minimum_grade_notification
        };

        // Discipline subscription payload logic remains the same
        const subscriptionsPayload: { discipline_id: number; sub_discipline_id: number | null }[] = [];
        const disciplineIds = new Set();
        currentSubscriptions.forEach(key => {
            if (key.startsWith('d:')) { disciplineIds.add(parseInt(key.split(':')[1], 10)); }
            else if (key.startsWith('s:')) {
                const subId = parseInt(key.split(':')[1], 10);
                for (const disc of allDisciplines) {
                    if (disc.sub_disciplines?.some(s => s.id === subId)) {
                        subscriptionsPayload.push({ discipline_id: disc.id, sub_discipline_id: subId });
                        disciplineIds.add(disc.id); // Ensure parent is tracked
                        break;
                    }
                }
            }
        });
        // Add main discipline entries ONLY if no subs are selected for that main discipline
        disciplineIds.forEach(discId => {
            if (!isNaN(discId)) {
                 const hasSelectedSub = subscriptionsPayload.some(p => p.discipline_id === discId && p.sub_discipline_id !== null);
                 if (!hasSelectedSub) {
                     subscriptionsPayload.push({ discipline_id: discId, sub_discipline_id: null });
                 }
            }
        });


        // **** NEW: Prepare grade preferences payload ****
        const gradePreferencesPayload = Array.from(selectedGrades);
        // **** END NEW ****

        // Debug logs for submission
        console.log('=== SUBMITTING DATA ===');
        console.log('profileUpdates:', profileUpdates);
        console.log('subscriptionsPayload:', subscriptionsPayload);
        console.log('gradePreferencesPayload:', gradePreferencesPayload);
        console.log('currentSubscriptions before submit:', Array.from(currentSubscriptions));
        console.log('selectedGrades before submit:', Array.from(selectedGrades));

        try {
            // IMPORTANT: Update the API endpoint to accept gradePreferencesPayload
            const response = await fetch('/api/update-profile-and-subscriptions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile: profileUpdates,
                    subscriptions: subscriptionsPayload,
                    gradePreferences: gradePreferencesPayload // **** NEW ****
                })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || `HTTP Error ${response.status}`);

            console.log("Update successful:", result);
            userProfileStore.update(current => {
                if (current) {
                    return { ...current, ...profileUpdates };
                }
                return null;
            });
            saveSuccess = true;
        } catch (err: any) {
            console.error('Error updating profile/subscriptions/grades:', err);
            saveError = err.message || 'Erreur lors de la mise à jour.';
        } finally {
            isLoading = false;
        }
	}

	async function handleLogout() {
		// Logic remains the same
		try {
			isLoading = true; saveError = '';
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
        <SubscriptionStatus subscription={activeSubscription} />
		<h1 class="mb-8 text-3xl md:text-4xl font-bold text-white">Mon compte</h1>

		{#if data.error}
			<p class="mb-6 rounded border border-red-700 bg-red-900/30 p-4 text-red-300">{data.error}</p>
		{:else if !data.userProfile}
            <p class="mb-6 rounded border border-yellow-700 bg-yellow-900/30 p-4 text-yellow-300">Chargement du profil...</p>
        {:else}
			<form on:submit|preventDefault={handleSubmit} class="space-y-8 rounded-lg bg-gray-800 p-6 md:p-8 shadow-lg">

				<!-- Vos Informations Section (No changes needed here) -->
				<div>
                    <h2 class="text-xl md:text-2xl font-semibold text-white border-b border-gray-700 pb-3 mb-6">Vos informations</h2>
                    <div class="space-y-6">
                        <!-- Fields for firstName, lastName, status, specialty, dateOfBirth remain the same -->
                        <div>
                            <label for="firstName" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.login.firstName}</label>
                            <input id="firstName" type="text" bind:value={firstName} class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50" required />
                        </div>
                        <div>
                            <label for="lastName" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.login.lastName}</label>
                            <input id="lastName" type="text" bind:value={lastName} class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50" required />
                        </div>
                        <div>
                            <label for="status" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.account.status}</label>
                            <select id="status" bind:value={status} class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-sm text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50 appearance-none">
                                <option value="">-- Choisir --</option>
                                {#each statusOptions as option}<option value={option}>{option}</option>{/each}
                            </select>
                        </div>
                        <div>
                            <label for="specialty" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.account.specialty}</label>
                            <input id="specialty" type="text" bind:value={specialty} class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50" placeholder="Ex: Médecine Générale" />
                        </div>
                        <div>
                            <label for="dateOfBirth" class="mb-2 block text-sm font-medium text-gray-300">{$i18n.login.dateOfBirth}</label>
                            <input id="dateOfBirth" type="date" bind:value={dateOfBirth} class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50" />
                        </div>
                    </div>
                </div>

				<hr class="border-gray-700" />

                <!-- Vos Préférences Section -->
				<div>
                    <h2 class="text-xl md:text-2xl font-semibold text-white border-b border-gray-700 pb-3 mb-6">Vos préférences de veille</h2>

                    <!-- Notification Frequency (remains the same) -->
                    <div class="mb-8">
                        <label for="notificationFrequency" class="mb-2 block text-sm font-medium text-gray-300">Fréquence des notifications</label>
                        <select id="notificationFrequency" bind:value={selectedNotificationFreq} class="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-700 px-4 py-3 text-sm text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-600/50 appearance-none">
                            {#each notificationOptions as option}<option value={option.value}>{option.label}</option>{/each}
                        </select>
                    </div>

                    <!-- **** NEW: Minimum Grade Checkboxes **** -->
                    <div class="mb-8 relative">
                        <label class="mb-2 block text-sm font-medium text-gray-300 flex items-center gap-2">
                            Grades de recommandation souhaités
                             <span class="relative cursor-pointer" on:click={() => showGradeInfo = !showGradeInfo} tabindex="0">
                                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-600 text-white text-xs font-bold border border-gray-400 select-none">i</span>
                            </span>
                        </label>
                        <div class="mt-1 space-y-2">
                            {#each ['A', 'B', 'C'] as grade}
                                <label class="flex items-center cursor-pointer select-none text-sm text-gray-200">
                                    <input
                                        type="checkbox"
                                        value={grade}
                                        class="h-4 w-4 rounded border-gray-500 bg-gray-600 text-teal-500 focus:ring-teal-600 focus:ring-offset-gray-800 mr-3 shrink-0"
                                        checked={selectedGrades.has(grade)}
                                        on:change={(e) => handleGradeChange(grade, e.currentTarget.checked)}
                                    />
                                    Grade {grade}
                                </label>
                            {/each}
                        </div>
                         {#if showGradeInfo}
                            <!-- Grade info panel (remains the same) -->
                             <div class="mt-4 w-full overflow-x-auto">
                                <div class="text-center font-bold text-base text-gray-100 mb-3">Niveaux de preuve scientifique</div>
                                <table class="min-w-full text-xs text-left text-gray-200 border border-gray-700 bg-gray-900 rounded-lg">
                                    <thead>
                                        <tr class="bg-gray-800">
                                            <th class="px-4 py-2 border-b border-gray-700 w-1/3 text-center">Grade des recommandations</th>
                                            <th class="px-4 py-2 border-b border-gray-700 text-center">Niveau de preuve scientifique fourni par la littérature</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each gradeInfo as info (info.grade)}
                                            <tr class="align-top">
                                                <td class="px-4 py-2 border-b border-gray-700 border-r border-gray-700 {info.grade === 'C' ? 'rowspan-2' : ''}">
                                                    <span class="font-bold">{info.grade}</span><br />
                                                    <span class="italic">{info.label}</span>
                                                </td>
                                                <td class="px-4 py-2 {info.grade === 'C' ? 'border-b border-gray-700' : 'border-b-0'}">
                                                    <span class="font-bold">{info.niveau}</span><br />
                                                    <ul class="list-disc list-inside ml-4">
                                                        {#each info.details as detail}<li>{detail}</li>{/each}
                                                    </ul>
                                                </td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>
                        {/if}
                    </div>
                    <!-- **** END NEW **** -->

                    <!-- Discipline/Sub-discipline Subscriptions (No UI changes needed here, logic handled in handlers) -->
                    <div>
                         <label class="mb-4 block text-sm font-medium text-gray-300">Spécialités et sous-spécialités suivies</label>
                        <div class="space-y-4 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-teal-600 scrollbar-track-gray-700 rounded-md border border-gray-600 p-4 bg-gray-700/50">
                             {#each allDisciplines as discipline (discipline.id)}
                                <div class="discipline-group">
                                    <div class="flex items-center justify-between">
                                        <label class="flex items-center cursor-pointer select-none py-1 flex-grow">
                                            <input type="checkbox" class="h-4 w-4 rounded border-gray-500 bg-gray-600 text-teal-500 focus:ring-teal-600 focus:ring-offset-gray-800 mr-3 shrink-0"
                                                checked={currentSubscriptions.has(`d:${discipline.id}`)}
                                                on:change={(e) => handleMainDisciplineChange(discipline.id, e.currentTarget.checked)} />
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
                                                      <input type="checkbox" class="h-4 w-4 rounded border-gray-500 bg-gray-600 text-teal-500 focus:ring-teal-600 focus:ring-offset-gray-800 mr-3 shrink-0"
                                                          checked={currentSubscriptions.has(`s:${sub.id}`)}
                                                          on:change={(e) => handleSubDisciplineChange(sub.id, discipline.id, e.currentTarget.checked)} />
                                                      <span class="text-sm text-gray-300 hover:text-gray-100">{sub.name}</span>
                                                  </label>
                                             {/each}
                                        </div>
                                    {/if}
                                </div>
                             {:else} <p class="text-gray-500 italic">Aucune discipline disponible.</p> {/each}
                        </div>
                         <p class="text-xs text-gray-400 mt-3">Cocher une spécialité sélectionne automatiquement toutes ses sous-spécialités.</p>
                    </div>
                </div>

				<!-- Save Button & Messages (remains the same) -->
				<div class="pt-5">
                     {#if saveSuccess}
                        <div role="alert" class="mb-4 flex items-center gap-2 rounded-md bg-green-800/30 border border-green-600 p-3 text-sm text-green-300">
                            <Check class="h-4 w-4 flex-shrink-0" />
                            Mise à jour réussie !
                        </div>
                     {/if}
                     {#if saveError}
                         <div role="alert" class="mb-4 flex items-center gap-2 rounded-md bg-red-900/30 border border-red-700 p-3 text-sm text-red-300">
                            <AlertCircle class="h-4 w-4 flex-shrink-0" />
                            {saveError}
                        </div>
                     {/if}
					<button type="submit" disabled={isLoading} class="flex w-full items-center justify-center rounded-lg bg-orange-600 px-8 py-3 font-semibold text-white shadow-md transition-all duration-300 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:cursor-not-allowed disabled:opacity-60">
						{#if isLoading} <Loader2 class="mr-2 h-5 w-5 animate-spin" /> <span>Enregistrement...</span>
						{:else} Enregistrer les modifications {/if}
					</button>
				</div>
			</form>

            <hr class="my-10 border-gray-700" />

            <div class="text-center mb-10">
                <a href="/update-password" class="text-blue-400 hover:underline text-sm">Modifier mon mot de passe</a>
            </div>

			<!-- Logout Section (remains the same) -->
			<div class="text-left">
				<h2 class="mb-4 text-xl md:text-2xl font-semibold text-white">Se déconnecter</h2>
				<button on:click={handleLogout} disabled={isLoading} class="rounded-lg bg-gray-600 px-6 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:cursor-not-allowed disabled:opacity-60">
					Déconnexion
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Styles remain the same */
	.scrollbar-thin { scrollbar-width: thin; scrollbar-color: #0d9488 #374151; }
	.scrollbar-thin::-webkit-scrollbar { width: 6px; height: 6px; }
	.scrollbar-thin::-webkit-scrollbar-track { background: #374151; border-radius: 10px; }
	.scrollbar-thin::-webkit-scrollbar-thumb { background-color: #0d9488; border-radius: 6px; border: 1px solid #374151; }
    .scrollbar-thin::-webkit-scrollbar-thumb:hover { background-color: #0f766e; }
    input[type="date"] { color-scheme: dark; }
    input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(0.8); }
    input[type="checkbox"] { color-scheme: dark; }
    label { margin-bottom: 0.5rem; display: block; font-size: 0.875rem; font-weight: 500; color: #D1D5DB; }
     input[type="text"], input[type="date"], select { margin-top: 0.25rem; display: block; width: 100%; border-radius: 0.5rem; border: 1px solid #4B5563; background-color: #374151; padding: 0.75rem 1rem; color: #FFFFFF; transition: all 0.2s ease-in-out; font-size: 0.875rem; line-height: 1.25rem; height: 3rem; }
     input[type="text"]:focus, input[type="date"]:focus, select:focus { border-color: #14B8A6; outline: 2px solid transparent; outline-offset: 2px; --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color); --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(1px + var(--tw-ring-offset-width)) var(--tw-ring-color); box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000); --tw-ring-color: rgba(20, 184, 166, 0.5); }
    select { background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e"); background-position: right 0.5rem center; background-repeat: no-repeat; background-size: 1.5em 1.5em; padding-right: 2.5rem; -webkit-appearance: none; -moz-appearance: none; appearance: none; }
    form > div:first-child > div:not(.space-y-6) { display: block; }
    form > div:first-child > div > div { margin-bottom: 1.5rem; }
</style>