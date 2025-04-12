<!-- src/lib/components/articles/ArticleListView.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import * as Select from '$lib/components/ui/select';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';
	import ArticleCard from './ArticleCard.svelte';
	import ArticleImmersiveModal from './ArticleImmersiveModal.svelte';

	// --- Component Props ---
	interface FilterOption {
		value: string;
		label: string;
	}

	const {
		pageTitle = 'Articles',
		filters = [] as FilterOption[],
		initialFilterValue = null as string | null,
		filterSelectLabel = 'Filtrer par',
		showSignupPromptProp = false, // Renamed to avoid conflict with internal state
        enableSearch = false,
		apiEndpoint = '/api/get_articles_my_veille',
		apiFilterParamName = 'specialty',
		userId = null as string | null,
		// savedArticleIds = new Set<string | number>(), // Keep if needed for UI hints later
		articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :',
		previousArticlesTitleTemplate = '📖 Articles précédents pour {filter} :',
		loadMoreButtonText = "Charger plus d'articles",
		allArticlesLoadedText = "Tous les articles ont été chargés",
        itemsPerPage = 10 // Define how many items are expected per page for hasMore logic
	} = $props<{
		pageTitle?: string;
		filters?: FilterOption[];
		initialFilterValue?: string | null;
		filterSelectLabel?: string;
		showSignupPromptProp?: boolean;
        enableSearch?: boolean;
		apiEndpoint?: string;
		apiFilterParamName?: string;
		userId?: string | null;
		// savedArticleIds?: Set<string | number>;
		articleOfTheDayTitleTemplate?: string;
		previousArticlesTitleTemplate?: string;
		loadMoreButtonText?: string;
		allArticlesLoadedText?: string;
        itemsPerPage?: number;
	}>();

	// --- Internal State ---
	let selectedFilter = $state<string | null>(initialFilterValue ?? filters[0]?.value ?? null);
	let articles = $state<Article[]>([]); // List of previous articles
	let articleOfTheDay = $state<Article | null>(null);
	let isLoading = $state(false);
    let isInitialLoading = $state(true); // To show main spinner only initially
	let hasMore = $state(true);
	let offset = $state(0);
	let immersiveArticle = $state<Article | null>(null);
	let searchQuery = $state('');
    let fetchError = $state<string | null>(null);
    let showSignupPrompt = $state(false); // Internal state for signup prompt visibility timer

	// --- Derived State ---
	const triggerContent = $derived(
		filters.find((f) => f.value === selectedFilter)?.label ?? filterSelectLabel
	);
	const filterForTitle = $derived(
		filters.find((f) => f.value === selectedFilter)?.label ?? 'la sélection'
	);
	const formattedArticleOfTheDayTitle = $derived(
		articleOfTheDayTitleTemplate.replace('{filter}', filterForTitle)
	);
	const formattedPreviousArticlesTitle = $derived(
		previousArticlesTitleTemplate.replace('{filter}', filterForTitle)
	);
    const searchActive = $derived(enableSearch && searchQuery.trim().length > 0);

	// --- Core Logic ---

    // Effect to fetch articles when filter or search changes
	$effect(() => {
        // Capture state for the async operation
        const currentFilter = selectedFilter;
        const currentSearch = searchQuery;

		if (!currentFilter) {
            articles = [];
            articleOfTheDay = null;
            hasMore = false;
            isInitialLoading = false;
            isLoading = false;
			return; // Don't fetch if no filter is selected
		}

		// Reset state for new fetch
		articles = [];
		articleOfTheDay = null;
		offset = 0;
		hasMore = true;
		fetchError = null;
        isLoading = true;
        isInitialLoading = true; // Mark as initial load for this filter

		console.log(`Fetching articles for filter: ${currentFilter}, search: ${currentSearch}, offset: 0`);

		const url = new URL(apiEndpoint, window.location.origin);
		url.searchParams.set(apiFilterParamName, currentFilter);
		url.searchParams.set('offset', '0');
        if (searchActive) {
            url.searchParams.set('search', currentSearch.trim()); // Add search param if active
        }
		if (userId) {
			url.searchParams.set('userId', userId); // Add userId if provided (e.g., for 'Favoris' filter)
		}

		fetch(url.toString())
			.then(async (res) => {
				if (!res.ok) {
                    const errorText = await res.text();
					throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);
				}
				return res.json();
			})
			.then((data) => {
                console.log('API Response:', data);
				if (data && Array.isArray(data.data)) {
                    const fetchedArticles: Article[] = data.data;
                    if (fetchedArticles.length > 0) {
                        articleOfTheDay = fetchedArticles[0];
                        articles = fetchedArticles.slice(1);
                        offset = fetchedArticles.length;
                        hasMore = fetchedArticles.length >= itemsPerPage; // Check if a full page was returned
                    } else {
                        // No articles found for this filter
                        articleOfTheDay = null;
                        articles = [];
                        offset = 0;
                        hasMore = false;
                    }
				} else {
                    console.warn('API response format unexpected or data.data is not an array:', data);
					throw new Error("Format de réponse invalide de l'API");
				}
			})
			.catch((error) => {
				console.error('Error fetching articles:', error);
                fetchError = error.message || "Une erreur est survenue lors du chargement des articles.";
                articleOfTheDay = null;
                articles = [];
                hasMore = false;
			})
			.finally(() => {
				isLoading = false;
                isInitialLoading = false;
			});
	});

    // Function to load more articles
	function loadMore() {
		if (isLoading || !hasMore || !selectedFilter) return;

		isLoading = true;
        fetchError = null; // Clear previous errors
        const currentOffset = offset; // Use current offset for this fetch

        console.log(`Loading more articles for filter: ${selectedFilter}, search: ${searchQuery}, offset: ${currentOffset}`);

		const url = new URL(apiEndpoint, window.location.origin);
		url.searchParams.set(apiFilterParamName, selectedFilter);
		url.searchParams.set('offset', currentOffset.toString());
        if (searchActive) {
            url.searchParams.set('search', searchQuery.trim());
        }
		if (userId) {
			url.searchParams.set('userId', userId);
		}

		fetch(url.toString())
			.then(async (res) => {
				if (!res.ok) {
					const errorText = await res.text();
					throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);
				}
				return res.json();
			})
			.then((data) => {
                console.log('Load More API Response:', data);
				if (data && Array.isArray(data.data)) {
                    const newArticles: Article[] = data.data;
					if (newArticles.length > 0) {
						articles = [...articles, ...newArticles];
						offset += newArticles.length;
						hasMore = newArticles.length >= itemsPerPage; // Update hasMore based on this fetch
					} else {
						hasMore = false; // No more articles returned
					}
				} else {
                    console.warn('API response format unexpected or data.data is not an array:', data);
                    // Decide if this is an error or just end of data
                    hasMore = false; // Assume end of data if format is weird
                }
			})
			.catch((error) => {
				console.error('Error loading more articles:', error);
                fetchError = error.message || "Une erreur est survenue lors du chargement.";
                // Optionally stop trying to load more on error:
                // hasMore = false;
			})
			.finally(() => {
				isLoading = false;
			});
	}

    // Modal handling
	function openImmersive(event: CustomEvent<Article>) {
		immersiveArticle = event.detail;
		document.body.classList.add('overflow-hidden');
	}

	function closeImmersive() {
		immersiveArticle = null;
		document.body.classList.remove('overflow-hidden');
	}

    // Signup prompt logic
    $effect(() => {
        // Only show prompt if prop is enabled and user is not logged in
        if (showSignupPromptProp && !$userProfileStore) {
            const timer = setTimeout(() => {
                showSignupPrompt = true;
            }, 3000); // Delay showing the prompt
            return () => clearTimeout(timer);
        } else {
            showSignupPrompt = false; // Hide if prop is false or user logs in
        }
    });

	function handleSignup() {
		goto('/signup');
	}

</script>

<div class="min-h-screen bg-black px-4 py-8 md:py-12 text-white">
	<div class="mx-auto max-w-4xl">
		<!-- Signup Prompt -->
		{#if showSignupPrompt}
			<div
				class="mb-6 flex flex-col sm:flex-row items-center justify-between gap-3 rounded-lg bg-teal-600/20 p-4 shadow-md transition-all duration-300 hover:bg-teal-600/30"
			>
				<p class="text-sm font-medium text-center sm:text-left">
                    Débloquez tout le potentiel ! Inscrivez-vous pour sauvegarder vos articles favoris et personnaliser votre veille.
                </p>
				<button
					on:click={handleSignup}
					class="group flex shrink-0 inline-block items-center justify-center gap-2 rounded-full bg-teal-500 px-4 py-2 text-xs font-semibold text-white transition-all duration-200 hover:bg-teal-600 whitespace-nowrap"
				>
					<span>S'inscrire gratuitement</span>
					<svg
						class="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1"
						fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"
					> <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7m0 0l-7 7m7-7H3"/> </svg>
				</button>
			</div>
		{/if}

		<h1 class="mb-4 text-3xl font-bold text-white">{pageTitle}</h1>

        <!-- Filters Row -->
		<div class="mb-6 flex flex-col md:flex-row gap-4">
            <!-- Filter Select -->
			{#if filters.length > 0}
				<div class="relative w-full md:max-w-xs">
					<Select.Root type="single" name="selectedFilter" bind:value={selectedFilter}>
						<Select.Trigger
							class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-sm transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                            disabled={isLoading && isInitialLoading}
						>
							{triggerContent}
						</Select.Trigger>
						<Select.Content
							class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 z-10 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg"
						>
							<Select.Group>
								<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400 text-xs uppercase tracking-wider">
									{filterSelectLabel}
								</Select.GroupHeading>
								{#each filters as filter (filter.value)}
									<Select.Item
										value={filter.value}
										label={filter.label}
										class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600/80 hover:text-white data-[selected]:bg-teal-700"
									>
                                        {filter.label}
                                    </Select.Item>
								{/each}
							</Select.Group>
						</Select.Content>
					</Select.Root>
				</div>
            {:else}
                 <p class="text-gray-500">Aucun filtre disponible.</p>
            {/if}

            <!-- Search Input -->
            {#if enableSearch}
                <div class="relative w-full md:flex-1">
                    <input
                        type="search"
                        bind:value={searchQuery}
                        placeholder="Rechercher par titre..."
                        class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 pl-10 text-sm font-medium text-white shadow-sm transition-all duration-300 placeholder-gray-500 focus:ring-2 focus:ring-teal-500 focus:outline-none focus:border-teal-500"
                        disabled={isLoading && isInitialLoading}
                    />
                    <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                    </svg>
                </div>
            {/if}
		</div>

        <!-- Loading / Error / Content Area -->
		{#if isLoading && isInitialLoading}
			<div class="flex justify-center items-center py-20">
				<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500"></div>
			</div>
        {:else if fetchError}
            <div class="my-10 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-center">
                <p><strong>Erreur :</strong> {fetchError}</p>
                <p class="mt-2 text-sm">Veuillez réessayer ou vérifier votre connexion.</p>
            </div>
		{:else if !articleOfTheDay && articles.length === 0}
            <div class="my-10 p-4 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-400 text-center">
                <p>Aucun article trouvé pour "{filterForTitle}"{searchActive ? ` correspondant à votre recherche "${searchQuery}"` : ''}.</p>
                {#if searchActive}
                    <p class="mt-2 text-sm">Essayez de modifier votre recherche.</p>
                {:else}
                    <p class="mt-2 text-sm">Revenez plus tard ou essayez un autre filtre.</p>
                {/if}
            </div>
        {:else}
			<!-- Article du jour Section -->
			<div class="mb-8">
                {#if articleOfTheDay || articles.length > 0}
				    <h2 class="text-2xl font-bold text-teal-500">🔥 Article du jour</h2>
                    <p class="mt-2 mb-4 text-gray-400">Article selectionné aujourd'hui pour {filterForTitle} :</p>
                {/if}
				{#if articleOfTheDay}
					<ul class="space-y-4">
						<ArticleCard article={articleOfTheDay} on:open={openImmersive} />
					</ul>
                {:else if !isLoading}
                    <p class="text-gray-500 italic text-sm ml-1">Aucun article spécifique pour aujourd'hui.</p>
				{/if}
			</div>

			<!-- Articles précédents Section -->
			<div class="mb-6">
                {#if articleOfTheDay || articles.length > 0}
				    <h2 class="text-2xl font-bold text-teal-500">📖 Articles précédents</h2>
                    <p class="mt-2 mb-4 text-gray-400">Articles précédemment selectionnés pour {filterForTitle} :</p>
                {/if}
				{#if articles.length > 0}
					<ul class="space-y-4">
						{#each articles as article (getArticleId(article))}
							<ArticleCard {article} on:open={openImmersive} />
						{/each}
					</ul>
                {:else if !isLoading && articleOfTheDay}
                    <p class="text-gray-500 italic text-sm ml-1">Aucun article précédent trouvé pour cette sélection.</p>
				{/if}
			</div>

            <!-- Pagination Controls -->
            {#if hasMore || isLoading}
                <div class="mt-8 text-center">
                    {#if isLoading}
                         <div class="flex justify-center items-center py-4">
                            <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-teal-500"></div>
                         </div>
                    {:else if hasMore}
                        <button
                            on:click={loadMore}
                            disabled={isLoading}
                            class="rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors duration-200 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loadMoreButtonText}
                        </button>
                    {/if}
                </div>
            {:else if !isInitialLoading && (articles.length > 0 || articleOfTheDay)}
                <div class="mt-8 text-center text-gray-500">
                    <span class="inline-flex items-center gap-2 rounded-full bg-gray-800 px-4 py-2 text-sm">
                        <svg class="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        {allArticlesLoadedText}
                    </span>
                </div>
            {/if}
		{/if}

	</div> <!-- End max-w-4xl -->
</div> <!-- End container -->

<!-- Modal -->
<ArticleImmersiveModal article={immersiveArticle} on:close={closeImmersive} />

<style>
	button:focus-visible, input:focus-visible {
		outline: 2px solid #14b8a6; /* Teal-500 */
        outline-offset: 2px;
	}
    /* Ensure Select component focus rings are consistent if needed */
    [data-radix-select-trigger]:focus-visible {
        outline: 2px solid #14b8a6;
        outline-offset: 2px;
    }

	/* Scrollbar styles */
	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #1f2937; /* thumb track */
	}

	.scrollbar-thin::-webkit-scrollbar {
		width: 8px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: #1f2937;
        border-radius: 10px;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6;
		border-radius: 6px;
		border: 2px solid #1f2937;
	}
</style>