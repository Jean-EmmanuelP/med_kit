<!-- src/lib/components/articles/ArticleListView.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import * as Select from '$lib/components/ui/select';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';
	import { debounce } from '$lib/utils/debounce';
	import ArticleCard from './ArticleCard.svelte';
	import ArticleImmersiveModal from './ArticleImmersiveModal.svelte';

	// --- Component Props ---
	interface FilterOption {
		value: string;
		label: string;
	}
    interface SubDisciplineOption {
        id: number;
        name: string;
    }

	const {
		pageTitle = 'Articles',
		filters = [] as FilterOption[],
		initialFilterValue = null as string | null,
		filterSelectLabel = 'Filtrer par',
		showSignupPromptProp = false,
        enableSearch = false,
        searchDebounceMs = 300,
        searchPlaceholder = "Rechercher par mots-clés...",
		apiEndpoint = '/api/get_articles_my_veille',
		apiFilterParamName = 'specialty',
		userId = null as string | null,
		articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :',
		previousArticlesTitleTemplate = '📖 Articles précédents pour {filter} :',
		loadMoreButtonText = "Charger plus d'articles",
		allArticlesLoadedText = "Tous les articles ont été chargés",
        itemsPerPage = 10,
        subDisciplineSelectLabel = "Affiner par sous-spécialité",
        showAllSubDisciplinesOption = true,
        allSubDisciplinesLabel = "Toutes les sous-spécialités"
	} = $props<{
		pageTitle?: string;
		filters?: FilterOption[];
		initialFilterValue?: string | null;
		filterSelectLabel?: string;
		showSignupPromptProp?: boolean;
        enableSearch?: boolean;
        searchDebounceMs?: number;
        searchPlaceholder?: string;
		apiEndpoint?: string;
		apiFilterParamName?: string;
		userId?: string | null;
		articleOfTheDayTitleTemplate?: string;
		previousArticlesTitleTemplate?: string;
		loadMoreButtonText?: string;
		allArticlesLoadedText?: string;
        itemsPerPage?: number;
        subDisciplineSelectLabel?: string;
        showAllSubDisciplinesOption?: boolean;
        allSubDisciplinesLabel?: string;
	}>();

	// --- Internal State ---
	let selectedFilter = $state<string | null>(initialFilterValue ?? filters[0]?.value ?? null);
    let selectedSubDiscipline = $state<string | null>(null);
    let availableSubDisciplines = $state<SubDisciplineOption[]>([]);
    let isLoadingSubDisciplines = $state(false);
	let articles = $state<Article[]>([]);
	let articleOfTheDay = $state<Article | null>(null);
	let isLoading = $state(false);
    let isInitialLoading = $state(true);
	let hasMore = $state(true);
	let offset = $state(0);
	let immersiveArticle = $state<Article | null>(null);
	let searchQuery = $state('');
    let fetchError = $state<string | null>(null);
    let showSignupPrompt = $state(false);

	// --- Derived State ---
	const sortedFilters = $derived(
        [...filters].sort((a: FilterOption, b: FilterOption) =>
			a.label.localeCompare(b.label, 'fr', { sensitivity: 'base' })
		)
    );
	const triggerContent = $derived(
		filters.find((f: FilterOption) => f.value === selectedFilter)?.label ?? filterSelectLabel
	);
	const filterForTitle = $derived(
		filters.find((f: FilterOption) => f.value === selectedFilter)?.label ?? 'la sélection'
	);
	const formattedArticleOfTheDayTitle = $derived(
		articleOfTheDayTitleTemplate.replace('{filter}', filterForTitle)
	);
	const formattedPreviousArticlesTitle = $derived(
		previousArticlesTitleTemplate.replace('{filter}', filterForTitle)
	);
    const searchActive = $derived(enableSearch && searchQuery.trim().length > 0);
    const subDisciplineTriggerContent = $derived(
        selectedSubDiscipline === null ? subDisciplineSelectLabel :
        selectedSubDiscipline === allSubDisciplinesLabel ? allSubDisciplinesLabel : selectedSubDiscipline
    );
    const subDisciplineOptions = $derived(
        showAllSubDisciplinesOption
            ? [{ id: -1, name: allSubDisciplinesLabel }, ...availableSubDisciplines]
            : availableSubDisciplines
    );
    const isViewingSubDiscipline = $derived(selectedSubDiscipline !== null && selectedSubDiscipline !== allSubDisciplinesLabel);

	// --- Core Logic ---

    // Effect to fetch SUB-DISCIPLINES when main filter changes
    $effect(() => {
        const currentMainFilter = selectedFilter;
        console.log('Main filter changed to:', currentMainFilter);

        // Reset sub-discipline state
        selectedSubDiscipline = null;
        availableSubDisciplines = [];
        if (!currentMainFilter) {
             console.log('No main filter selected, skipping sub-discipline fetch.');
             return;
        }

        isLoadingSubDisciplines = true;
        console.log('Fetching sub-disciplines for:', currentMainFilter);

        fetch(`/api/get_sub_disciplines?disciplineName=${encodeURIComponent(currentMainFilter)}`)
            .then(async (res) => {
                if (!res.ok) {
                    const errorText = await res.text();
					throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);
                }
                return res.json();
            })
            .then((data: SubDisciplineOption[]) => {
                 console.log('Fetched sub-disciplines:', data);
                 availableSubDisciplines = data || [];
            })
            .catch(error => {
                console.error("Error fetching sub-disciplines:", error);
                availableSubDisciplines = [];
            })
            .finally(() => {
                isLoadingSubDisciplines = false;
                console.log('Finished fetching sub-disciplines.');
            });
    });

    // Create a debounced function for triggering the fetch
    const debouncedFetchArticles = debounce(fetchArticles, searchDebounceMs);

    // Reusable fetch function
    function fetchArticles(isLoadMore = false) {
        const currentFilter = selectedFilter;
        const currentSubFilter = selectedSubDiscipline;
        const currentSearch = searchQuery;
        const currentOffset = isLoadMore ? offset : 0;

        if (!currentFilter) {
            if (!isLoadMore) { // Only reset fully if not loading more
                articles = [];
                articleOfTheDay = null;
                hasMore = false;
                isLoading = false; // Ensure loading stops
                isInitialLoading = false; // Ensure initial loading stops
            }
            return;
        }

        // If it's an initial fetch (not loadMore), isInitialLoading should already be true
        // Mark general loading as true
        isLoading = true;
        if (!isLoadMore) {
            fetchError = null; // Clear previous errors only on initial load
        }

		console.log(`Fetching articles for filter: ${currentFilter}, subFilter: ${currentSubFilter}, search: ${currentSearch}, offset: ${currentOffset}`);

		const url = new URL(apiEndpoint, window.location.origin);
		url.searchParams.set(apiFilterParamName, currentFilter);
        if (currentSubFilter && currentSubFilter !== allSubDisciplinesLabel) {
             url.searchParams.set('subDiscipline', currentSubFilter);
        }
		url.searchParams.set('offset', currentOffset.toString());
        if (enableSearch && currentSearch.trim()) {
            url.searchParams.set('search', currentSearch.trim());
        }
		if (userId) { url.searchParams.set('userId', userId); }

		fetch(url.toString())
			.then(async (res) => {
                if (!res.ok) {
                    const errorText = await res.text();
					throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);
                }
                return res.json();
            })
			.then((data) => {
                console.log(`API Response (Offset: ${currentOffset}):`, data);
				if (data && Array.isArray(data.data)) {
                    const fetchedArticles: Article[] = data.data;

                    if (isLoadMore) {
                        if (fetchedArticles.length > 0) {
                            articles = [...articles, ...fetchedArticles];
                            offset += fetchedArticles.length;
                            hasMore = fetchedArticles.length >= itemsPerPage;
                        } else {
                            hasMore = false;
                        }
                    } else {
                        if (fetchedArticles.length > 0) {
                            articleOfTheDay = fetchedArticles[0];
                            articles = fetchedArticles.slice(1);
                            offset = fetchedArticles.length;
                            hasMore = fetchedArticles.length >= itemsPerPage;
                        } else {
                            articleOfTheDay = null;
                            articles = [];
                            offset = 0;
                            hasMore = false;
                        }
                    }
				} else {
                    console.warn('API response format unexpected or data.data is not an array:', data);
					throw new Error("Format de réponse invalide de l'API");
				}
            })
			.catch((error) => {
                console.error('Error fetching articles:', error);
                fetchError = error.message || "Une erreur est survenue lors du chargement des articles.";
                // Reset state on error
                articles = [];
                articleOfTheDay = null;
                hasMore = false;
            })
			.finally(() => {
                console.log(`Fetch finished (Offset: ${currentOffset})`);
                isLoading = false; // Stop general loading
                if (!isLoadMore) {
                    isInitialLoading = false; // Stop initial loading specifically
                }
            });
    }

    // Effect to trigger DEBOUNCED article fetch on filter/search changes
	$effect(() => {
        // Read the reactive values to establish dependency
        const currentFilter = selectedFilter;
        const currentSubFilter = selectedSubDiscipline;
        const currentSearch = searchQuery;

        // Mark as initial loading *synchronously* when dependencies change
        console.log("Filters changed, setting isInitialLoading = true");
        isInitialLoading = true;
        // Also reset previous articles immediately for better UX
        articles = [];
        articleOfTheDay = null;
        offset = 0;
        hasMore = true; // Assume there might be more until fetch confirms otherwise
        fetchError = null; // Clear any previous error message

        // Now call the debounced function
		console.log("Triggering debounced fetchArticles call");
        debouncedFetchArticles(false); // Call debounced function for initial fetch (isLoadMore = false)
	});

    function loadMore() {
        // Directly call fetchArticles with isLoadMore = true
        if (!isLoading && hasMore && selectedFilter) {
            fetchArticles(true);
        }
	}

    function openImmersive(event: CustomEvent<Article>) {
        const clickedArticle = event.detail;
        const articleIdToUpdate = getArticleId(clickedArticle);
        const currentUser = $userProfileStore; // Get current user state

        // --- Optimistic UI Update ---
        // Find and update the article in the local state BEFORE showing the modal
        // Update articleOfTheDay if it matches
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToUpdate) {
            console.log(`Optimistically updating AotD ${articleIdToUpdate} to read=true`);
            articleOfTheDay = { ...articleOfTheDay, is_read: true };
        }
        // Update the article in the main 'articles' list if it matches
        const articleIndex = articles.findIndex(a => getArticleId(a) === articleIdToUpdate);
        if (articleIndex > -1) {
             console.log(`Optimistically updating list article ${articleIdToUpdate} at index ${articleIndex} to read=true`);
             // Create a new object for the specific article to trigger reactivity
             const updatedArticle = { ...articles[articleIndex], is_read: true };
             // Create a new array to trigger reactivity for the list
             articles = [
                 ...articles.slice(0, articleIndex),
                 updatedArticle,
                 ...articles.slice(articleIndex + 1)
             ];
        }
        // --- End Optimistic Update ---


        // Set the article for the modal (use the potentially updated one if found, otherwise original)
        immersiveArticle = (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToUpdate)
                            ? articleOfTheDay
                            : (articleIndex > -1 ? articles[articleIndex] : clickedArticle);

        // --- Mark as read via API (fire and forget) ---
        if (currentUser?.id && typeof articleIdToUpdate === 'number' && !isNaN(articleIdToUpdate)) {
            console.log(`Modal opened for article ${articleIdToUpdate}. Firing API call to mark as read for user ${currentUser.id}...`);
             fetch('/api/mark-article-read', {
                 method: 'POST',
                 headers: { 'Content-Type': 'application/json' },
                 body: JSON.stringify({ articleId: articleIdToUpdate }),
             })
             .then(async (response) => {
                 if (!response.ok) {
                     const errorData = await response.json().catch(() => ({ message: 'Failed to parse error response' }));
                     console.error(`Failed to mark article ${articleIdToUpdate} as read via API:`, response.status, errorData.message || response.statusText);
                     // Optional: Revert optimistic update on error? (More complex)
                 } else {
                     console.log(`API confirmed article ${articleIdToUpdate} marked as read.`);
                 }
             })
             .catch((error) => {
                 console.error(`Network error marking article ${articleIdToUpdate} as read:`, error);
                 // Optional: Revert optimistic update on error?
             });
        } else if (!currentUser?.id) {
            console.log("Modal opened, but user not logged in. Skipping mark as read.");
        } else {
            console.warn("Modal opened, but article ID is not valid for API call:", articleIdToUpdate);
        }

        // Add class to body (do this last to avoid layout shift before modal renders)
		document.body.classList.add('overflow-hidden');
	}

	function closeImmersive() {
		immersiveArticle = null;
		document.body.classList.remove('overflow-hidden');
	}

    $effect(() => {
        if (showSignupPromptProp && !$userProfileStore) {
            const timer = setTimeout(() => {
                showSignupPrompt = true;
            }, 3000);
            return () => clearTimeout(timer);
        } else {
            showSignupPrompt = false;
        }
    });

	function handleSignup() {
		goto('/signup');
	}

    function handleSubDisciplineChange(value: string | null) {
        if (value === allSubDisciplinesLabel) {
            selectedSubDiscipline = null;
        } else {
            selectedSubDiscipline = value;
        }
    }
</script>

<div class="min-h-screen bg-black px-4 py-8 md:py-12 text-white">
	<div class="mx-auto max-w-4xl">
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

		<div class="mb-6 flex flex-col gap-4">
            <div class="flex flex-col md:flex-row flex-wrap gap-4">
                {#if filters.length > 0}
                    <div class="relative w-full md:max-w-xs shrink-0">
                        <Select.Root type="single" name="selectedFilter" bind:value={selectedFilter}>
                            <Select.Trigger
                                class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-sm transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                                disabled={isLoading && isInitialLoading}
                            >
                                {triggerContent}
                            </Select.Trigger>
                            <Select.Content
                                class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 z-20 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg"
                            >
                                <Select.Group>
                                    <Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400 text-xs uppercase tracking-wider">
                                        {filterSelectLabel}
                                    </Select.GroupHeading>
                                    {#each sortedFilters as filter (filter.value)}
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
                {/if}

                {#if (availableSubDisciplines.length > 0 || isLoadingSubDisciplines) && selectedFilter}
                    <div class="relative w-full md:max-w-xs shrink-0">
                        <Select.Root
                            type="single"
                            name="selectedSubDiscipline"
                            value={selectedSubDiscipline ?? allSubDisciplinesLabel}
                            onValueChange={(detail) => handleSubDisciplineChange(detail)}
                        >
                            <Select.Trigger
                                class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-sm transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                                disabled={isLoadingSubDisciplines || (isLoading && isInitialLoading)}
                            >
                                {#if isLoadingSubDisciplines}
                                    <span class="flex items-center gap-2 opacity-70">
                                        <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>
                                        Chargement...
                                    </span>
                                {:else}
                                    {subDisciplineTriggerContent}
                                {/if}
                            </Select.Trigger>
                            <Select.Content class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 z-10 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg">
                                <Select.Group>
                                    <Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400 text-xs uppercase tracking-wider">
                                        {subDisciplineSelectLabel}
                                    </Select.GroupHeading>
                                    {#if showAllSubDisciplinesOption}
                                        <Select.Item value={allSubDisciplinesLabel} label={allSubDisciplinesLabel} class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600/80 hover:text-white data-[selected]:bg-teal-700">
                                            {allSubDisciplinesLabel}
                                        </Select.Item>
                                    {/if}
                                    {#each availableSubDisciplines as sub (sub.name)}
                                        <Select.Item value={sub.name} label={sub.name} class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600/80 hover:text-white data-[selected]:bg-teal-700">
                                            {sub.name}
                                        </Select.Item>
                                    {/each}
                                </Select.Group>
                            </Select.Content>
                        </Select.Root>
                    </div>
                {/if}
            </div>

            {#if enableSearch}
                <div class="relative w-full">
                    <input
                        type="search"
                        bind:value={searchQuery}
                        placeholder={searchPlaceholder}
                        class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 pl-10 text-sm font-medium text-white shadow-sm transition-all duration-300 placeholder-gray-500 focus:ring-2 focus:ring-teal-500 focus:outline-none focus:border-teal-500"
                        disabled={isLoading && isInitialLoading && !searchActive}
                    />
                    <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500 pointer-events-none" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                    </svg>
                    {#if searchQuery}
                        <button
                            aria-label="Effacer la recherche"
                            on:click={() => searchQuery = ''}
                            class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-white focus:outline-none focus:ring-1 focus:ring-teal-500 rounded-full p-0.5"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                            </svg>
                        </button>
                    {/if}
                </div>
            {/if}
		</div>

		{#if isInitialLoading}
			<div class="flex justify-center items-center py-20" aria-live="polite" aria-busy="true">
				<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500"></div>
			</div>
        {:else if fetchError}
            <div class="my-10 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-center" role="alert">
                <p><strong>Erreur :</strong> {fetchError}</p>
                <p class="mt-2 text-sm">Veuillez réessayer ou vérifier votre connexion.</p>
            </div>
		{:else if !articleOfTheDay && articles.length === 0}
            <div class="my-10 p-4 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-400 text-center">
                <p>
                    {#if searchActive}
                        Aucun article trouvé pour "{filterForTitle}"
                        {#if isViewingSubDiscipline} dans "{selectedSubDiscipline}"{/if}
                        correspondant à votre recherche "{searchQuery}".
                    {:else}
                        Aucun article trouvé pour "{filterForTitle}"
                        {#if isViewingSubDiscipline} dans "{selectedSubDiscipline}"{/if}.
                    {/if}
                </p>
                <p class="mt-2 text-sm">
                    {#if searchActive}
                        Essayez de modifier votre recherche ou les filtres.
                    {:else}
                         Revenez plus tard ou essayez un autre filtre.
                    {/if}
                </p>
            </div>
        {:else}
			{#if !isViewingSubDiscipline && !searchActive}
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
            {/if}

			<div class="mb-6">
                {#if articleOfTheDay || articles.length > 0}
                    <h2 class="text-2xl font-bold text-teal-500">
                        {#if searchActive}
                            Résultats de recherche
                        {:else if isViewingSubDiscipline}
                            📖 Articles pour {selectedSubDiscipline}
                        {:else}
                            📖 Articles précédents
                        {/if}
                    </h2>
                     <p class="mt-2 mb-4 text-gray-400">
                         {#if searchActive}
                             Résultats pour "{searchQuery}" dans "{filterForTitle}"{#if isViewingSubDiscipline} - {selectedSubDiscipline}{/if} :
                         {:else if isViewingSubDiscipline}
                             Articles selectionnés pour {selectedSubDiscipline} ({filterForTitle}) :
                          {:else}
                             Articles précédemment selectionnés pour {filterForTitle} :
                          {/if}
                     </p>
                {/if}

                <ul class="space-y-4">
                    {#if (isViewingSubDiscipline || searchActive) && articleOfTheDay}
                        <ArticleCard article={articleOfTheDay} on:open={openImmersive} />
                    {/if}
                    {#each articles as article (getArticleId(article))}
                        <ArticleCard {article} on:open={openImmersive} />
                    {/each}
				</ul>

                {#if !isLoading && !articleOfTheDay && articles.length === 0 && isViewingSubDiscipline}
                     <p class="text-gray-500 italic text-sm ml-1">Aucun article trouvé pour cette sous-spécialité.</p>
                {:else if !isLoading && articleOfTheDay && articles.length === 0 && !isViewingSubDiscipline}
                    <p class="text-gray-500 italic text-sm ml-1">Aucun article précédent trouvé pour cette sélection.</p>
				{/if}
			</div>

            {#if hasMore || isLoading}
                <div class="mt-8 text-center">
                    {#if isLoading && !isInitialLoading}
                         <div class="flex justify-center items-center py-4" aria-live="polite" aria-busy="true">
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

	</div>
</div>

<ArticleImmersiveModal article={immersiveArticle} on:close={closeImmersive} />

<style>
	button:focus-visible, input:focus-visible {
		outline: 2px solid #14b8a6;
        outline-offset: 2px;
	}
    [data-radix-select-trigger]:focus-visible {
        outline: 2px solid #14b8a6;
        outline-offset: 2px;
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
        border-radius: 10px;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6;
		border-radius: 6px;
		border: 2px solid #1f2937;
	}
</style>