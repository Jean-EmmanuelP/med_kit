<script lang="ts">
	import { goto } from '$app/navigation';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';
	import * as Select from '$lib/components/ui/select/index.js';

	const { articles, userDisciplines, error } = $props<{
		articles: {
			id: number;
			article_id: number;
			title: string;
			journal: string;
			published_at: string;
			link: string;
			grade: string | null;
			discipline: string;
			added_at: string;
			is_article_of_the_day: boolean;
		}[];
		userDisciplines: string[];
		error: string | null;
	}>();

	let searchQuery = $state('');
	let selectedDiscipline = $state(userDisciplines[0] || '');
	let filteredArticles = $state<any[]>([]);
	let showSignupPrompt = $state(false);
	let loading = $state(false);
	let displayedArticles = $state<any[]>([]);
	let articlesPerPage = $state(20);
	let currentPage = $state(1);
	let specialties = $state<string[]>(userDisciplines);
	let allArticlesByDiscipline = $state(new Map<string, any[]>());
	let searchSuggestions = $state<any[]>([]);
	let errorMessage = $state<string | null>(error);

	// Débouncer pour la recherche
	let searchTimeout: NodeJS.Timeout | null = null;
	let debouncedSearchQuery = $state('');

	$effect(() => {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			debouncedSearchQuery = searchQuery;
		}, 300);
		return () => clearTimeout(searchTimeout);
	});

	// Initialiser les données au montage
	$effect(() => {
		if (error) {
			errorMessage = error;
			return;
		}

		if (!articles || articles.length === 0) {
			errorMessage = "Aucun article trouvé pour les disciplines de l'utilisateur.";
			return;
		}

		// Vérifier si l'utilisateur est connecté
		if (!$userProfileStore?.id) {
			errorMessage = 'Utilisateur non connecté.';
			showSignupPrompt = true;
			return;
		}

		specialties = userDisciplines;
		selectedDiscipline = specialties[0] || '';

		if (specialties.length === 0) {
			errorMessage = 'Aucune discipline choisie.';
			return;
		}

		// Organiser les articles par discipline
		articles.forEach((article) => {
			const lowerTitle = article.title.toLowerCase();
			const publishedDate = article.published_at
				? new Date(article.published_at).toLocaleDateString('fr-FR', {
						day: '2-digit',
						month: '2-digit',
						year: 'numeric'
					})
				: '';

			if (!allArticlesByDiscipline.has(article.discipline)) {
				allArticlesByDiscipline.set(article.discipline, []);
			}
			allArticlesByDiscipline.get(article.discipline)!.push({
				id: article.article_id,
				title: article.title,
				lowerTitle,
				journal: article.journal,
				published_at: article.published_at,
				publishedDate,
				link: article.link,
				grade: article.grade,
				discipline: article.discipline,
				added_at: article.added_at,
				is_article_of_the_day: article.is_article_of_the_day
			});
		});

		// Charger les articles pour la discipline sélectionnée
		if (selectedDiscipline) {
			fetchArticlesForDiscipline(selectedDiscipline, debouncedSearchQuery);
		}
	});

	// Filtrer les articles pour une discipline donnée
	async function fetchArticlesForDiscipline(discipline: string, query: string) {
		loading = true;
		try {
			let updatedArticles = allArticlesByDiscipline.get(discipline) || [];

			if (query) {
				updatedArticles = await new Promise((resolve) => {
					setTimeout(() => {
						const filtered = updatedArticles.filter(
							(article) =>
								article.lowerTitle.includes(query.toLowerCase()) ||
								article.publishedDate.includes(query.toLowerCase())
						);
						resolve(filtered);
					}, 0);
				});
			}

			filteredArticles = updatedArticles;
			currentPage = 1;
			displayedArticles = filteredArticles.slice(0, currentPage * articlesPerPage);
		} catch (err) {
			console.error(`Erreur lors du filtrage des articles pour ${discipline}:`, err);
			filteredArticles = [];
			displayedArticles = [];
			errorMessage = 'Erreur lors du filtrage des articles.';
		} finally {
			loading = false;
		}
	}

	// Suggestions de recherche
	$effect(() => {
		if (searchQuery) {
			const allArticles = Array.from(allArticlesByDiscipline.values()).flat();
			searchSuggestions = allArticles
				.filter((article) => article.lowerTitle.includes(searchQuery.toLowerCase()))
				.slice(0, 5);
		} else {
			searchSuggestions = [];
		}
	});

	// Réagir aux changements de discipline ou de recherche
	$effect(() => {
		if (selectedDiscipline) {
			fetchArticlesForDiscipline(selectedDiscipline, debouncedSearchQuery);
		}
	});

	function loadMore() {
		currentPage += 1;
		displayedArticles = filteredArticles.slice(0, currentPage * articlesPerPage);
	}

	function formatTitle(title: string) {
		if (!title) return '';
		const words = title.toLowerCase().split(' ');
		if (words.length === 0) return '';
		words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
		return words.join(' ');
	}

	function formatDate(publishedAt: string) {
		if (!publishedAt) return 'Non spécifiée';
		const date = new Date(publishedAt);
		return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}`;
	}

	function handleArticleClick(articleId: number) {
		goto(`/articles/${articleId}`);
	}

	$effect(() => {
		const timer = setTimeout(() => {
			if (!$userProfileStore?.id) {
				showSignupPrompt = true;
			}
		}, 2000);
		return () => clearTimeout(timer);
	});

	$effect(() => {
		if ($userProfileStore?.id) {
			showSignupPrompt = false;
		}
	});

	$effect(() => {
		if (selectedFilter != "Tout" && selectedFilter != "Favoris") {
			let articles;
			fetch(`/api/get_articles_my_veille?specialty=${selectedFilter}`)
				.then((res) => res.json())
				.then((data) => {
					console.log(data.data)
				});
		}
	});

	function toggleSummary(articleId) {
		expandedArticleId = expandedArticleId === String(articleId) ? null : String(articleId);
	}

	function handleSignup() {
		goto('/signup');
	}

	let triggerContent = $derived(selectedDiscipline || '');
</script>

<div class="min-h-screen bg-black px-4 py-12 text-white">
	<div class="mx-auto max-w-4xl">
		{#if loading}
			<div class="flex h-screen items-center justify-center">
				<p class="text-white">Chargement en cours...</p>
			</div>
		{/if}

		{#if showSignupPrompt && !$userProfileStore?.id}
			<div
				class="mb-6 flex items-center justify-between rounded-lg bg-teal-600/20 p-4 shadow-md transition-all duration-300 hover:bg-teal-600/30"
			>
				<p class="text-sm font-medium">S’inscrire maintenant pour plus de fonctionnalités !</p>
				<button
					on:click={handleSignup}
					class="group inline-block flex items-center justify-center gap-2 rounded-full bg-teal-500 px-4 py-2 text-xs font-semibold text-white transition-all duration-200 hover:bg-teal-600"
				>
					<span>S’inscrire</span>
					<svg
						class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 5l7 7m0 0l-7 7m7-7H3"
						/>
					</svg>
				</button>
			</div>
		{/if}

		<h1 class="mb-4 text-3xl font-bold">{$i18n.header.myVeille}</h1>

		{#if errorMessage}
			<p class="mb-4 text-red-500">{errorMessage}</p>
		{/if}

		{#if specialties.length > 0}
			<div class="relative mb-8 w-full max-w-sm">
				<Select.Root type="single" name="selectedDiscipline" bind:value={selectedDiscipline}>
					<Select.Trigger
						class="w-full rounded-lg border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
					>
						{triggerContent}
					</Select.Trigger>
					<Select.Content
						class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
					>
						<Select.Group>
							<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400"
								>Spécialités</Select.GroupHeading
							>
							{#each specialties as specialty (specialty)}
								<Select.Item
									value={specialty}
									label={specialty}
									class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
								/>
							{/each}
						</Select.Group>
					</Select.Content>
				</Select.Root>
			</div>

			<div
				class="mb-8 flex flex-col items-start space-y-4 sm:flex-row sm:items-center sm:space-x-4 sm:space-y-0"
			>
				<div class="relative w-full sm:w-64">
					<form>
						<input
							type="text"
							bind:value={searchQuery}
							placeholder={$i18n.header.searchPlaceholder}
							class="w-full rounded-full border border-gray-700 bg-gray-800 px-4 py-2 pr-12 text-sm text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-700"
						/>
						<svg
							class="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 transform text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							/>
						</svg>
					</form>
					{#if searchSuggestions.length > 0}
						<ul
							class="absolute z-10 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg"
						>
							{#each searchSuggestions as suggestion (suggestion.id)}
								<li
									on:click={() => handleArticleClick(suggestion.id)}
									class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600"
								>
									<span class="font-medium">{formatTitle(suggestion.title)}</span>
									<span class="block text-sm text-gray-400"
										>{formatDate(suggestion.published_at)}</span
									>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</div>

			{#if !loading}
				<div class="mt-12">
					<h2 class="text-2xl font-bold text-teal-500">🔥 Articles du jour</h2>
					{#if displayedArticles.some((article) => article.is_article_of_the_day)}
						<ul class="space-y-4">
							{#each displayedArticles.filter((article) => article.is_article_of_the_day) as article (article.id)}
								<li
									on:click={() => handleArticleClick(article.id)}
									class="relative mt-2 cursor-pointer list-none rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-lg"
								>
									<h2 class="text-left text-lg font-bold text-white">
										{formatTitle(article.title)}
									</h2>
									{#if article.grade}
										<p class="mt-1 text-sm text-green-400">
											Grade de recommandation : {article.grade}
										</p>
									{/if}
									<div class="mt-2 flex items-center text-sm text-gray-400">
										<span class="mr-1">{article.journal || 'Inconnu'}</span>
									</div>
									<div class="mt-2 flex items-center text-sm text-gray-400">
										<svg
											class="mr-1 h-4 w-4"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
											/>
										</svg>
										<span class="mr-1">Date de publication :</span>
										<span>{formatDate(article.published_at)}</span>
									</div>
								</li>
							{/each}
						</ul>
					{:else}
						<p class="mt-2 text-gray-400">Aucun article du jour pour {selectedDiscipline}.</p>
					{/if}
				</div>

				<div class="mb-6">
					<h2 class="text-2xl font-bold text-teal-500">📚 Articles de base</h2>
					{#if displayedArticles.every((article) => article.is_article_of_the_day)}
						<p class="mt-2 text-gray-400">
							Aucun article de base disponible pour {selectedDiscipline}.
						</p>
					{:else}
						<ul class="space-y-4">
							{#each displayedArticles.filter((article) => !article.is_article_of_the_day) as article (article.id)}
								<li
									on:click={() => handleArticleClick(article.id)}
									class="relative cursor-pointer rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-lg"
								>
									<h2 class="text-left text-lg font-bold text-white">
										{formatTitle(article.title)}
									</h2>
									{#if article.grade}
										<p class="mt-1 text-sm text-green-400">
											Grade de recommandation : {article.grade}
										</p>
									{/if}
									<div class="mt-2 flex items-center text-sm text-gray-400">
										<span class="mr-1">{article.journal || 'Inconnu'}</span>
									</div>
									<div class="mt-2 flex items-center text-sm text-gray-400">
										<svg
											class="mr-1 h-4 w-4"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
											/>
										</svg>
										<span class="mr-1">Date de publication :</span>
										<span>{formatDate(article.published_at)}</span>
									</div>
								</li>
							{/each}
						</ul>
					{/if}
				</div>

				{#if displayedArticles.length < filteredArticles.length}
					<div class="my-4 flex justify-center">
						<button
							on:click={loadMore}
							class="rounded-full bg-teal-500 px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600"
						>
							Charger plus
						</button>
					</div>
				{/if}
			{/if}
		{/if}
	</div>
</div>

<style>
	/* Style général */
	button:focus {
		outline: none;
	}
	.animate-bounce {
		animation: bounce 2s infinite;
	}

	@keyframes bounce {
		0%,
		20%,
		50%,
		80%,
		100% {
			transform: translateY(0);
		}
		40% {
			transform: translateY(-10px);
		}
		60% {
			transform: translateY(-5px);
		}
	}

	.modal-enter-active {
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		0% {
			opacity: 0;
			transform: scale(0.95);
		}
		100% {
			opacity: 1;
			transform: scale(1);
		}
	}

	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #1f2937;
	}

	.scrollbar-thin::-webkit-scrollbar {
		width: 8px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: #1f2937;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6;
		border-radius: 6px;
		border: 2px solid #1f2937;
	}
</style>
