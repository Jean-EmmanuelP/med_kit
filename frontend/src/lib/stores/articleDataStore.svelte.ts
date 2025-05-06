// src/lib/stores/articleDataStore.ts
import type { Article } from '../utils/articleUtils.ts';
import { getArticleId } from '../utils/articleUtils.ts';
import userProfileStore from './user.ts';
// Debounce is not used inside the store directly anymore, but in the component calling setSearchQuery

export interface ArticleDataStoreConfig {
	apiEndpoint: string;
	apiFilterParamName: string;
	itemsPerPage: number;
	filterByUserSubs: boolean;
	initialSelectedFilter: string | null;
	initialSelectedSubFilter: string | null;
	mainFiltersAvailable: boolean; // True if the 'filters' prop in ArticleListView has items
	allSubDisciplinesLabel: string; // Constant label for "all sub-disciplines"
	ALL_CATEGORIES_VALUE: string; // Constant value for "all categories"
	enableSearch: boolean;
}

export function createArticleDataStore(config: ArticleDataStoreConfig) {
	const {
		apiEndpoint,
		apiFilterParamName,
		itemsPerPage,
		filterByUserSubs,
		initialSelectedFilter,
		initialSelectedSubFilter,
		mainFiltersAvailable,
		allSubDisciplinesLabel,
		ALL_CATEGORIES_VALUE,
		enableSearch
	} = config;

	// --- Internal State ---
	let articles = $state<Article[]>([]);
	let articleOfTheDay = $state<Article | null>(null);
	let isLoading = $state(false);
	let isInitialLoading = $state(true); // True until first fetch attempt completes
	let hasMore = $state(true);
	let offset = $state(0);
	let fetchError = $state<string | null>(null);

	// Store's current understanding of filter/search parameters
	let currentSelectedFilter = $state<string | null>(initialSelectedFilter);
	let currentSelectedSubDiscipline = $state<string | null>(initialSelectedSubFilter);
	let currentSearchQuery = $state(''); // Store's search query, set by component

	// --- Derived State ---
	const isLikedArticlesView = $derived(apiEndpoint === '/api/get-liked-articles');
	const searchActive = $derived(enableSearch && currentSearchQuery.trim().length > 0);

	// --- Core Fetch Logic ---
	const _fetchArticles = (isLoadMore = false) => {
		const effectiveFilter = currentSelectedFilter;
		// Ensure subFilter is null if main filter is "All" or null
		const effectiveSubFilter =
			effectiveFilter && effectiveFilter !== ALL_CATEGORIES_VALUE
				? currentSelectedSubDiscipline
				: null;
		const effectiveSearch = currentSearchQuery; // Use store's knowledge
		const currentOffset = isLoadMore ? offset : 0;
		const currentUserId = userProfileStore?.id ?? null;

		// Re-check dependency on user ID for liked articles
		if (isLikedArticlesView && !currentUserId) {
			if (!isLoadMore) {
				articles = [];
				articleOfTheDay = null;
				hasMore = false;
			}
			isLoading = false;
			isInitialLoading = false; // Blocked, so initial load considered "done"
			return;
		}

		// Re-check filter requirement
		if (effectiveFilter === null && mainFiltersAvailable) {
			if (!isLoadMore) {
				articles = [];
				articleOfTheDay = null;
				hasMore = false;
			}
			isLoading = false;
			isInitialLoading = false; // Blocked, so initial load considered "done"
			return;
		}

		isLoading = true;
		if (!isLoadMore) {
			fetchError = null;
		}

		const url = new URL(apiEndpoint, window.location.origin);
		url.searchParams.set('offset', currentOffset.toString());
		url.searchParams.set('limit', itemsPerPage.toString());

		if (effectiveFilter && effectiveFilter !== ALL_CATEGORIES_VALUE) {
			url.searchParams.set(apiFilterParamName, effectiveFilter);
			if (effectiveSubFilter && effectiveSubFilter !== allSubDisciplinesLabel) {
				url.searchParams.set('subDiscipline', effectiveSubFilter);
			}
		}
		if (searchActive) {
			// Use store's searchActive and currentSearchQuery
			url.searchParams.set('search', currentSearchQuery.trim());
		}
		url.searchParams.set('filterByUserSubs', filterByUserSubs.toString());
		// Optionally pass user_id if backend needs it for general queries too
		if (currentUserId) {
			url.searchParams.set('user_id', currentUserId);
		}

		fetch(url.toString())
			.then(async (res) => {
				if (!res.ok) {
					const errorText = await res.text().catch(() => `Erreur HTTP ${res.status}`);
					throw new Error(`Erreur réseau ${res.status}: ${errorText}`);
				}
				return res.json();
			})
			.then((data) => {
				if (data && Array.isArray(data.data)) {
					const fetchedArticles: Article[] = data.data.map((item: any) => ({
						...item, // Spread existing fields
						id: item.article_id, // Make sure ID mapping is correct
						is_article_of_the_day: item.is_article_of_the_day
					}));

					if (isLoadMore) {
						articles = [...articles, ...fetchedArticles];
					} else {
						let potentialAotd: Article | null = null;
						let remainingArticles = [...fetchedArticles];
						const isAotdContext = !searchActive && !isLikedArticlesView;

						if (isAotdContext && fetchedArticles.length > 0) {
							const firstArticle = fetchedArticles[0];
							if (firstArticle?.is_article_of_the_day === true) {
								potentialAotd = firstArticle;
								remainingArticles = fetchedArticles.slice(1);
							}
						}
						articleOfTheDay = potentialAotd;
						articles = remainingArticles;
					}
					offset = currentOffset + fetchedArticles.length;
					hasMore = fetchedArticles.length >= itemsPerPage;
				} else {
					console.warn('API response format unexpected or data.data is not an array:', data);
					throw new Error("Format de réponse invalide de l'API");
				}
			})
			.catch((error) => {
				console.error('Error fetching articles in store:', error);
				fetchError = error.message || "Une erreur est survenue lors du chargement des articles.";
				if (!isLoadMore) {
					articles = [];
					articleOfTheDay = null;
				}
				hasMore = false; // Stop further loading on error
			})
			.finally(() => {
				isLoading = false;
				if (!isLoadMore) {
					isInitialLoading = false; //^ Mark initial load as finished
				}
			});
	};

	// Effect to trigger article fetch when store's understanding of filters/search changes
	$effect(() => {
		// Capture reactive dependencies for the effect
		const filterVal = currentSelectedFilter;
		const subFilterVal = currentSelectedSubDiscipline; // unused but KEEP (state)
		const searchVal = currentSearchQuery; // unused but KEEP (state)
		const userId = userProfileStore?.id ?? null; // React to user changes

		// Block fetch if conditions not met (these checks are also in _fetchArticles,
		// but having them here prevents unnecessary state resets if conditions flip before fetch)
		if (isLikedArticlesView && !userId) {
			articles = []; articleOfTheDay = null; hasMore = false; isInitialLoading = false;
			return;
		}
		if (filterVal === null && mainFiltersAvailable) {
			articles = []; articleOfTheDay = null; hasMore = false; isInitialLoading = false;
			return;
		}

		// Reset state and fetch for new parameters
		// console.log("ArticleDataStore $effect: Inputs changed, resetting and fetching.", {filterVal, subFilterVal, searchVal, userId});
		isInitialLoading = true; // Set to true before new fetch sequence starts
		articles = [];
		articleOfTheDay = null;
		offset = 0;
		hasMore = true;
		fetchError = null; // Clear previous errors

		_fetchArticles(false); // Call directly (not debounced within the store)
	});

	// --- Public API for the store ---
	const setFilter = (newFilter: string | null) => {
		if (currentSelectedFilter !== newFilter) {
			currentSelectedFilter = newFilter;
			// The component (ArticleListView) will be responsible for clearing its own
			// UI searchQuery state and then calling store.setSearchQuery('') if needed.
		}
	};

	const setSubFilter = (newSubFilter: string | null) => {
		if (currentSelectedSubDiscipline !== newSubFilter) {
			currentSelectedSubDiscipline = newSubFilter;
		}
	};

	const setSearchQuery = (newQuery: string) => {
		// This is called by ArticleListView, potentially after debouncing.
		// If newQuery is different, the store's $effect will trigger a fetch.
		const trimmedQuery = newQuery.trim();
        if (currentSearchQuery !== trimmedQuery) {
		    currentSearchQuery = trimmedQuery;
        }
	};

	const loadMore = () => {
		if (!isLoading && hasMore) {
			_fetchArticles(true);
		}
	};

	const updateArticleInState = (articleIdToUpdate: string | number, updates: Partial<Article>) => {
		if (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToUpdate) {
			articleOfTheDay = { ...articleOfTheDay, ...updates };
		}
		articles = articles.map((a) =>
			getArticleId(a) === articleIdToUpdate ? { ...a, ...updates } : a
		);
	};

	const removeArticleFromState = (articleIdToRemove: string | number) => {
		if (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToRemove) {
			articleOfTheDay = null;
		}
		articles = articles.filter((a) => getArticleId(a) !== articleIdToRemove);
	};

	// Expose reactive state and methods
	return {
		// Readable state
		get articles() { return articles; },
		get articleOfTheDay() { return articleOfTheDay; },
		get isLoading() { return isLoading; },
		get isInitialLoading() { return isInitialLoading; },
		get hasMore() { return hasMore; },
		get fetchError() { return fetchError; },
        get searchActive() { return searchActive; },
        get isLikedArticlesView() { return isLikedArticlesView; },

		// Methods to change state
		setFilter,
		setSubFilter,
		setSearchQuery,
		loadMore,
		updateArticleInState,
		removeArticleFromState,
	};
}