<!--- File Path: frontend/src/routes/internal-stats-area/+page.svelte --->
<script lang="ts">
	import { AlertTriangle, Eye, EyeOff, Loader2 } from 'lucide-svelte';
	import { onMount } from 'svelte';
// Import Select components
	import { supabase } from '$lib/supabase'; // Import your configured Supabase client

	// --- Interfaces for fetched data ---
	interface Discipline {
		id: number;
		name: string;
	}
	interface SubDiscipline {
		id: number;
		name: string;
		discipline_id: number;
	}

	// --- Configuration (Password - Keep as is) ---
	const STORED_HASH = '93113621a41a0799762af6f34736347ede2a275cc35e70d6917fd5e38fd4e812';
	const SALT = 'pggts1DHI343haAXSNqR0mRnIiQ7Wm3e';

	// --- Authentication State (Keep as is) ---
	let isAuthenticated = $state(false);
	let passwordInput = $state('');
	let authErrorMessage = $state(''); // Renamed for clarity
	let showPassword = $state(false);
	let cryptoAvailable = $state(true);

	// --- Dashboard State ---
	let allDisciplines = $state<Discipline[]>([]);
	let selectedDisciplineId = $state<number | null>(null);
	let availableSubDisciplines = $state<SubDiscipline[]>([]);
	// Use a special string value for the "all subs" option, or null
	const ALL_SUBS_VALUE = '__ALL_SUBS__';
	let selectedSubDisciplineIdentifier = $state<number | string | null>(ALL_SUBS_VALUE); // Can be ID (number) or ALL_SUBS_VALUE (string)
	let subscriberCount = $state<number | null>(null);
	let isLoadingDisciplines = $state(false);
	let isLoadingSubDisciplines = $state(false);
	let isLoadingCount = $state(false);
	let fetchError = $state(''); // For data fetching errors

	// --- NEW: Daily Stats State ---
	const today = new Date().toISOString().split('T')[0]; // Get YYYY-MM-DD for today
	let selectedStatDate = $state<string>(today); // Default to today
	let dailyStats = $state<DailyStats | null>(null);
	let isLoadingStats = $state(false);
	let statsFetchError = $state('');

	// --- Crypto Check (Keep as is) ---
	onMount(() => {
		if (!window.crypto || !window.crypto.subtle) {
			console.error('SubtleCrypto API not available!');
			authErrorMessage = "Erreur: L'API de cryptographie n'est pas disponible.";
			cryptoAvailable = false;
		}
	});

	// --- Hashing Function (Keep as is) ---
	async function hashPasswordWithSalt(password: string, salt: string): Promise<string | null> {
		if (!cryptoAvailable) return null;
		try {
			const encoder = new TextEncoder();
			const data = encoder.encode(password + salt);
			const hashBuffer = await crypto.subtle.digest('SHA-256', data);
			const hashArray = Array.from(new Uint8Array(hashBuffer));
			const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
			return hashHex;
		} catch (error) {
			console.error('Hashing error:', error);
			authErrorMessage = 'Erreur lors du hachage du mot de passe.';
			return null;
		}
	}

	// --- Auth Submit Function (Keep as is) ---
	async function handlePasswordSubmit() {
		if (!cryptoAvailable) return;
		authErrorMessage = '';
		const inputHash = await hashPasswordWithSalt(passwordInput, SALT);
		if (inputHash === null) return;
		let difference = 0;
		const len = Math.max(inputHash.length, STORED_HASH.length);
		for (let i = 0; i < len; i++) {
			difference |= (inputHash.charCodeAt(i) || 0) ^ (STORED_HASH.charCodeAt(i) || 0);
		}
		if (difference === 0 && inputHash.length === STORED_HASH.length) {
			isAuthenticated = true;
		} else {
			authErrorMessage = 'Mot de passe incorrect.';
			passwordInput = '';
		}
	}

	// --- Toggle Password Visibility (Keep as is) ---
	function togglePasswordVisibility() {
		showPassword = !showPassword;
	}

	// --- Fetch All Disciplines once authenticated ---
	async function fetchDisciplines() {
		if (!isAuthenticated || allDisciplines.length > 0) return; // Fetch only once needed
		console.log('Fetching all disciplines...');
		isLoadingDisciplines = true;
		fetchError = '';
		try {
			const { data, error } = await supabase
				.from('disciplines')
				.select('id, name')
				.order('name', { ascending: true });
			if (error) throw error;
			allDisciplines = data || [];
			console.log('Disciplines fetched:', allDisciplines.length);
		} catch (err: any) {
			console.error('Error fetching disciplines:', err);
			fetchError = `Erreur chargement disciplines: ${err.message}`;
			allDisciplines = [];
		} finally {
			isLoadingDisciplines = false;
		}
	}
	$effect(() => {
		if (isAuthenticated) {
			fetchDisciplines();
		}
	});

	// --- Fetch Sub-Disciplines when Main Discipline changes ---
	async function fetchSubDisciplines(disciplineId: number | null) {
		availableSubDisciplines = []; // Reset
		selectedSubDisciplineIdentifier = null; // Reset to 'All'
		subscriberCount = null; // Reset count
		fetchError = '';
		if (!disciplineId) return; // Don't fetch if no main discipline selected

		console.log('Fetching sub-disciplines for ID:', disciplineId);
		isLoadingSubDisciplines = true;
		try {
			const { data, error } = await supabase
				.from('sub_disciplines')
				.select('id, name, discipline_id')
				.eq('discipline_id', disciplineId)
				.order('name', { ascending: true });
			if (error) throw error;
			availableSubDisciplines = data || [];
			console.log('Sub-disciplines fetched:', availableSubDisciplines.length);
		} catch (err: any) {
			console.error('Error fetching sub-disciplines:', err);
			fetchError = `Erreur chargement sous-disciplines: ${err.message}`;
		} finally {
			isLoadingSubDisciplines = false;
		}
	}
	$effect(() => {
		// Trigger fetch when selectedDisciplineId changes
		fetchSubDisciplines(selectedDisciplineId);
	});

	// --- Fetch Subscriber Count when selection changes ---
	async function fetchSubscriberCount() {
		// Reset count and error initially
		subscriberCount = null;
		fetchError = '';

		if (selectedDisciplineId === null) {
			console.log('Count Fetch: No main discipline selected.');
			isLoadingCount = false;
			return;
		}

		isLoadingCount = true;
		console.log(
			`Fetching count for Discipline ID: ${selectedDisciplineId}, Sub ID: ${selectedSubDisciplineIdentifier}`
		);

		try {
			// Case 1: Specific Sub-Discipline selected
			if (selectedSubDisciplineIdentifier !== null) {
				console.log(`Querying count for Specific Sub-Discipline ID: ${selectedSubDisciplineIdentifier}`);
				const { count, error } = await supabase
					.from('user_subscriptions')
					.select('id', { count: 'exact', head: true })
					.eq('sub_discipline_id', selectedSubDisciplineIdentifier);
				if (error) throw error;
				console.log('Count query result:', count);
				subscriberCount = count ?? 0;
				console.log('Subscriber count result:', subscriberCount);
			}
			// Case 2: "All" Sub-Disciplines selected (selectedSubDisciplineIdentifier is null)
			else {
				console.log(`Querying count for ALL users in Main Discipline ID: ${selectedDisciplineId}`);
				const { data, count, error } = await supabase
					.from('user_subscriptions')
					.select('*', { count: 'exact', head: true })
					.eq('discipline_id', selectedDisciplineId)
					.is('sub_discipline_id', null);
				if (error) throw error;
				console.log("DATA", data, "ERROR", error);
				console.log('Count query result:', count);
				subscriberCount = count ?? 0;
				console.log('Subscriber count result:', subscriberCount);
			}
		} catch (err: any) {
			console.error('Error fetching subscriber count:', err);
			fetchError = `Erreur chargement du nombre d'utilisateur: ${err.message}`;
			subscriberCount = null;
		} finally {
			isLoadingCount = false;
		}}
	$effect(() => {
		fetchSubscriberCount();
	});
	// --- Derived value for display ---
	const selectedDisciplineName = $derived(
		allDisciplines.find((d) => d.id === selectedDisciplineId)?.name ?? 'N/A'
	);
	const selectedSubDisciplineName = $derived(
		selectedSubDisciplineIdentifier === ALL_SUBS_VALUE
			? 'Toutes les sous-spécialités'
			: availableSubDisciplines.find((s) => s.id === selectedSubDisciplineIdentifier)?.name ??
				'N/A'
	);

	// --- NEW: Fetch Daily Stats ---
	async function fetchDailyStats() {
		if (!isAuthenticated || !selectedStatDate) {
			dailyStats = null;
			return;
		}

		console.log(`Fetching stats for date: ${selectedStatDate}`);
		isLoadingStats = true;
		statsFetchError = '';
		dailyStats = null;

		try {
			const { data, error } = await supabase.rpc('get_daily_read_stats', {
				 query_date: selectedStatDate
			});

			if (error) throw error;

			// RPC returns an array, potentially empty if no reads on that day
			if (data && data.length > 0) {
				dailyStats = data[0]; // Get the first (and only expected) row
				console.log('Daily stats received:', dailyStats);
			} else {
				// Set stats to zero if no data found for the date
				dailyStats = {
					read_day: selectedStatDate,
					total_reads_per_day: 0,
					unique_users_per_day: 0
				};
				console.log('No reads found for date, setting stats to zero.');
			}

		} catch (err: any) {
			console.error('Error fetching daily stats:', err);
			statsFetchError = `Erreur chargement des stats: ${err.message}`;
			dailyStats = null;
		} finally {
			isLoadingStats = false;
		}
	}
	// Trigger stats fetch when date changes or on auth
	$effect(() => {
		if (isAuthenticated && selectedStatDate) {
			 fetchDailyStats();
		}
	});
</script>

<svelte:head>
	<title>Dashboard Interne</title>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-black px-4 py-12 text-white">
	{#if !isAuthenticated}
		<!-- Password Entry Form (Keep as is) -->
		<div class="w-full max-w-md rounded-xl bg-gray-800 p-8 shadow-xl">
			<h1 class="mb-6 text-center text-2xl font-bold text-white">Accès Dashboard</h1>
			{#if !cryptoAvailable}
				<div
					role="alert"
					class="mb-6 flex items-center gap-2 rounded-md border border-red-700 bg-red-900/40 p-3 text-sm text-red-300"
				>
					<AlertTriangle class="h-4 w-4 flex-shrink-0" />
					{authErrorMessage || 'API Crypto non disponible.'}
				</div>
			{:else}
				<p class="mb-6 text-center text-sm text-gray-400">
					Veuillez entrer le mot de passe pour accéder aux statistiques.
				</p>
				<form on:submit|preventDefault={handlePasswordSubmit} class="space-y-6">
					<div>
						<label for="password" class="block text-sm font-medium text-gray-300">Mot de passe</label
						>
						<div class="relative mt-1">
							<input
								id="password"
								name="password"
								type={showPassword ? 'text' : 'password'}
								bind:value={passwordInput}
								required
								class="block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-3 text-white placeholder-gray-400 shadow-sm transition-colors duration-200 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800"
								placeholder="••••••••"
								disabled={!cryptoAvailable}
							/>
							<button
								type="button"
								on:click={togglePasswordVisibility}
								class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-200 focus:outline-none focus:ring-1 focus:ring-teal-500 rounded-r-lg"
								aria-label={showPassword ? 'Cacher le mot de passe' : 'Montrer le mot de passe'}
								disabled={!cryptoAvailable}
							>
								{#if showPassword} <EyeOff class="h-5 w-5" /> {:else} <Eye class="h-5 w-5" /> {/if}
							</button>
						</div>
					</div>

					{#if authErrorMessage && cryptoAvailable}
						<div
							role="alert"
							class="flex items-center gap-2 rounded-md border border-red-700 bg-red-900/40 p-3 text-sm text-red-300"
						>
							<AlertTriangle class="h-4 w-4 flex-shrink-0" />
							{authErrorMessage}
						</div>
					{/if}

					<button
						type="submit"
						class="w-full rounded-lg bg-teal-600 px-5 py-3 text-base font-semibold text-white shadow-md transition-colors duration-300 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={!cryptoAvailable}
					>
						Accéder
					</button>
				</form>
			{/if}
		</div>
	{:else}
		<!-- Actual Dashboard Content -->
		<div class="w-full max-w-4xl rounded-xl bg-gray-800 p-8 shadow-xl">
			<h1 class="mb-8 border-b border-gray-700 pb-4 text-3xl font-bold text-white">
				Dashboard Statistique
			</h1>

			<!-- Subscription Count Section -->
			<section class="mb-10 rounded-lg bg-gray-700 p-6">
				<h2 class="mb-5 text-xl font-semibold text-white">Nombre d'utilisateur par Spécialité</h2>

				{#if fetchError}
					<div
						role="alert"
						class="mb-4 flex items-center gap-2 rounded-md border border-red-700 bg-red-900/40 p-3 text-sm text-red-300"
					>
						<AlertTriangle class="h-4 w-4 flex-shrink-0" />
						{fetchError}
					</div>
				{/if}

				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<!-- Discipline Dropdown (Native HTML Select) -->
					<div>
						<label for="discipline-select" class="mb-1 block text-sm font-medium text-gray-300">Spécialité Principale</label>
						{#if isLoadingDisciplines}
							<div class="h-10 animate-pulse rounded-lg bg-gray-600"></div>
						{:else}
							<div class="relative">
								<select
									id="discipline-select"
									class="block w-full appearance-none rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 pr-8 text-sm text-white focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
									bind:value={selectedDisciplineId}
									aria-label="Sélectionner une spécialité principale"
									disabled={isLoadingDisciplines}
								>
									<option value={null} selected={selectedDisciplineId === null}>-- Choisir une spécialité --</option>
									{#each allDisciplines as discipline (discipline.id)}
										<option value={discipline.id}>{discipline.name}</option>
									{/each}
								</select>
								<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
									<svg class="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>
								</div>
							</div>
						{/if}
					</div>

					<!-- Sub-Discipline Dropdown (Native HTML Select) -->
					<div>
						<label for="subdiscipline-select" class="mb-1 block text-sm font-medium text-gray-300">Sous-spécialité (Optionnel)</label>
						{#if isLoadingSubDisciplines && selectedDisciplineId}
							<div class="h-10 animate-pulse rounded-lg bg-gray-600"></div>
						{:else}
							<div class="relative">
								<select
									id="subdiscipline-select"
									class="block w-full appearance-none rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 pr-8 text-sm text-white focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:opacity-50 disabled:cursor-not-allowed"
									bind:value={selectedSubDisciplineIdentifier}
									aria-label="Sélectionner une sous-spécialité"
									disabled={isLoadingSubDisciplines || !selectedDisciplineId}
								>
									<option value={null} selected={selectedSubDisciplineIdentifier === null}>-- Toutes les sous-spécialités --</option>
									{#if availableSubDisciplines.length === 0 && selectedDisciplineId && !isLoadingSubDisciplines}
										 <option value={null} disabled>Aucune sous-spécialité</option>
									{:else}
										{#each availableSubDisciplines as sub (sub.id)}
											<option value={sub.id}>{sub.name}</option>
										{/each}
									{/if}
								</select>
								<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
									<svg class="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>
								</div>
							</div>
						{/if}
					</div>
				</div>

				<!-- Display Count Result -->
				<div class="mt-6 rounded-lg bg-gray-800 p-4 text-center">
					{#if isLoadingCount}
						<div class="flex items-center justify-center gap-2 text-gray-400">
							<Loader2 class="h-5 w-5 animate-spin" />
							Chargement du nombre...
						</div>
					{:else if subscriberCount !== null}
						<p class="text-sm text-gray-300">Nombre d'abonnés pour la sélection :</p>
						<p class="mt-1 text-4xl font-bold text-teal-400">
							{subscriberCount.toLocaleString('fr-FR')}
						</p>
					{:else if selectedDisciplineId}
						<p class="text-sm text-gray-500 italic">Veuillez patienter ou sélectionner une sous-spécialité.</p>
					{:else}
						<p class="text-sm text-gray-500 italic">Sélectionnez une spécialité principale.</p>
					{/if}
				</div>
			</section>

			<!-- NEW: Daily Stats Section -->
			<section class="rounded-lg bg-gray-700 p-6">
				<h2 class="mb-5 text-xl font-semibold text-white">Statistiques de Lecture Journalières</h2>

				{#if statsFetchError}
					<div role="alert" class="mb-4 flex items-center gap-2 rounded-md border border-red-700 bg-red-900/40 p-3 text-sm text-red-300">
						<AlertTriangle class="h-4 w-4 flex-shrink-0" />
						{statsFetchError}
					</div>
				{/if}

				<!-- Date Picker -->
				<div class="mb-6 max-w-xs">
					<label for="stats-date" class="mb-1 block text-sm font-medium text-gray-300">Choisir une date</label>
					<input
						type="date"
						id="stats-date"
						bind:value={selectedStatDate}
						max={today}
						class="block w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-white focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
						aria-label="Sélectionner une date pour les statistiques"
						disabled={isLoadingStats}
					/>
				</div>

				<!-- Display Stats Result -->
				<div class="rounded-lg bg-gray-800 p-4">
					{#if isLoadingStats}
						<div class="flex items-center justify-center gap-2 text-gray-400">
							<Loader2 class="h-5 w-5 animate-spin" />
							Chargement des statistiques...
						</div>
					{:else if dailyStats}
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-center">
							<div>
								<p class="text-sm text-gray-300">Articles lus le {new Date(dailyStats.read_day + 'T00:00:00Z').toLocaleDateString('fr-FR', { timeZone: 'UTC' })} :</p>
						        <p class="mt-1 text-3xl font-bold text-teal-400"> {dailyStats.total_reads_per_day.toLocaleString('fr-FR')} </p>
							</div>
							<div>
								<p class="text-sm text-gray-300">Utilisateurs uniques :</p>
						        <p class="mt-1 text-3xl font-bold text-teal-400"> {dailyStats.unique_users_per_day.toLocaleString('fr-FR')} </p>
							</div>
						</div>
					{:else if !statsFetchError}
						<p class="text-center text-sm text-gray-500 italic">Aucune donnée pour la date sélectionnée.</p>
					{/if}
				</div>
			</section>

			<!-- Placeholder for other stats (Keep as is) -->
			<!-- <div class="grid grid-cols-1 md:grid-cols-2 gap-6"> ... -->
		</div>
	{/if}
</div>

<style>
	/* Basic appearance none for select */
	select {
		-webkit-appearance: none;
		-moz-appearance: none;
		appearance: none;
		background-image: none; /* Override default if necessary */
	}
	/* Add scrollbar styling if Select component doesn't handle it */
	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #374151; /* thumb track */
	}
	.scrollbar-thin::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	.scrollbar-thin::-webkit-scrollbar-track {
		background: #374151; /* gray-700 */
		border-radius: 3px;
	}
	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6; /* teal-500 */
		border-radius: 3px;
	}
	.scrollbar-thin::-webkit-scrollbar-thumb:hover {
		background-color: #0f766e; /* teal-600 */
	}
</style>