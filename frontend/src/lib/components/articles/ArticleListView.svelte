<!-- src/lib/components/articles/ArticleListView.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import SubscriptionRequired from '$lib/components/SubscriptionRequired.svelte';
	import ConfirmationModal from '$lib/components/ui/ConfirmationModal.svelte';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';
	import { debounce } from '$lib/utils/debounce';
	import { tick } from 'svelte';
	import ArticleImmersiveModal from './ArticleImmersiveModal.svelte';
	import ArticleListDisplay from './ArticleListDisplay.svelte';
	import ArticleListHeader from './ArticleListHeader.svelte';
	import ArticleEditModal from './ArticleEditModal.svelte';

    const ALL_CATEGORIES_VALUE = "__ALL__";
    const ALL_CATEGORIES_LABEL = "Toutes les catégories";

	interface FilterOption { value: string; label: string; }
    interface SubDisciplineOption { id: number; name: string; }

	// Types for sent articles
	interface SentArticle {
		id: number;
		article_id: number;
		sent_at: string;
		discipline: string;
		sub_discipline: string | null;
		is_article_of_the_day: boolean;
		title: string;
		content: string;
		journal: string;
		published_at: string;
		grade: number | null;
		link: string;
		is_read: boolean;
		read_at: string | null;
		is_saved: boolean;
	}

	interface SentArticlesResponse {
		success: boolean;
		data: SentArticle[];
		pagination: {
			page: number;
			pageSize: number;
			totalPages: number;
			totalCount: number;
		};
		statistics: {
			totalArticles: number;
			readArticles: number;
			unreadArticles: number;
			readPercentage: number;
		};
	}

	const {
        articleId = 0,
        articleTitle = "",
		pageTitle = 'Articles',
		filters = [] as FilterOption[],
		initialFilterValue = null,
		initialSubFilterValue = null,
		filterSelectLabel = 'Filtrer par',
		showSignupPromptProp = false,
        enableSearch = false,
        searchDebounceMs = 300,
        searchPlaceholder = "Rechercher par mots-clés...",
		apiEndpoint = '/api/get_articles_my_veille',
		apiFilterParamName = 'specialty',
		userId: propUserId = null as string | null,
		loadMoreButtonText = "Charger plus d'articles",
		allArticlesLoadedText = "Tous les articles ont été chargés",
        emptyStateMessage = null as string | null,
        itemsPerPage = 10,
        subDisciplineSelectLabel = "Affiner par sous-spécialité",
        showAllSubDisciplinesOption = true,
        allSubDisciplinesLabel = "Toutes les sous-spécialités",
        showAllCategoriesOption = true,
        subDisciplineFetchMode = 'user' as 'user' | 'public',
        filterByUserSubs = false,
        isSubscribed = false,
        onEditClick = null as ((article: Article) => void) | null,
        // Add progress data from parent
        progressData = null as any,
        // New prop for recommendations filter
        showRecommendationsOnly = false,
        // New prop to control recommendations toggle visibility
        enableRecommendationsToggle = true,
        // New prop to control read articles toggle visibility
        enableReadArticlesToggle = true
	} = $props<{
        articleId?: number;
        articleTitle?: string;
		pageTitle?: string;
		filters?: FilterOption[];
		initialFilterValue?: string | null;
		initialSubFilterValue?: string | null;
		filterSelectLabel?: string;
		showSignupPromptProp?: boolean;
        enableSearch?: boolean;
        searchDebounceMs?: number;
        searchPlaceholder?: string;
		apiEndpoint?: string;
		apiFilterParamName?: string;
		userId?: string | null;
		loadMoreButtonText?: string;
		allArticlesLoadedText?: string;
        emptyStateMessage?: string | null;
        itemsPerPage?: number;
        subDisciplineSelectLabel?: string;
        showAllSubDisciplinesOption?: boolean;
        allSubDisciplinesLabel?: string;
        showAllCategoriesOption?: boolean;
        subDisciplineFetchMode?: 'user' | 'public';
        filterByUserSubs?: boolean;
        isSubscribed?: boolean;
        onEditClick?: ((article: Article) => void) | null;
        // Add progress data from parent
        progressData?: any;
        showRecommendationsOnly?: boolean;
        // New prop to control recommendations toggle visibility
        enableRecommendationsToggle?: boolean;
        // New prop to control read articles toggle visibility
        enableReadArticlesToggle?: boolean;
	}>();

    const defaultInitialFilter = filters.length > 0 ? (showAllCategoriesOption ? ALL_CATEGORIES_VALUE : (filters[0]?.value ?? null)) : (showAllCategoriesOption ? ALL_CATEGORIES_VALUE : null);

	    let selectedFilter = $state<string | null>(initialFilterValue ?? defaultInitialFilter);
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
    let showUnlikeConfirmModal = $state(false);
    let showSubscriptionRequired = $state(false);
    let articleToUnlike = $state<{ articleId: number | string; currentlyLiked: boolean; currentLikeCount: number; } | null>(null);
    let hasInitialized = $state(false);
    let initialSearchSet = $state(false);
    
    // Recommendations filter state
    let showRecommendationsFilter = $state(showRecommendationsOnly);

    // Read articles filter state
    let showReadArticlesFilter = $state(false);

    // Edit modal state
    let showEditModal = $state(false);
    let editingArticle = $state<Article | null>(null);

	const filterForTitle = $derived(
        selectedFilter === ALL_CATEGORIES_VALUE
            ? 'toutes les catégories'
            : (filters.find((f: FilterOption) => f.value === selectedFilter)?.label ?? 'la sélection')
    );
    const searchActive = $derived(enableSearch && searchQuery.trim().length > 0);
    const showSubDisciplineFilter = $derived(
        (availableSubDisciplines.length > 0 || isLoadingSubDisciplines) &&
        selectedFilter !== ALL_CATEGORIES_VALUE &&
        selectedFilter !== null
    );
    const isViewingSubDiscipline = $derived(selectedSubDiscipline !== null && selectedSubDiscipline !== allSubDisciplinesLabel);
    const isLikedArticlesView = $derived(apiEndpoint === '/api/get-liked-articles');
    const isEmailArticlesView = $derived(false); // Removed email articles view state
	const currentUserIdFromStore = $derived($userProfileStore?.id ?? null);

    interface ListTitleInfo { text: string; iconType: 'heart' | 'book' | 'email' | null; }
    let mainArticleListTitleInfo: ListTitleInfo = $state({ text: '', iconType: null });

    $effect(() => {
        if (articleOfTheDay) {
            if (isLikedArticlesView) {
                let titleText = "Favoris";
                if (selectedFilter !== ALL_CATEGORIES_VALUE && selectedFilter) { titleText += `: ${filterForTitle}`; }
                if (isViewingSubDiscipline) { titleText += ` - ${selectedSubDiscipline}`; }
                mainArticleListTitleInfo = { text: titleText, iconType: 'heart' };
            } else if (isEmailArticlesView) {
                let titleText = "Articles reçus par email";
                if (selectedFilter !== ALL_CATEGORIES_VALUE && selectedFilter) { titleText += `: ${filterForTitle}`; }
                if (isViewingSubDiscipline) { titleText += ` - ${selectedSubDiscipline}`; }
                mainArticleListTitleInfo = { text: titleText, iconType: 'email' };
            } else if (searchActive) {
                mainArticleListTitleInfo = { text: "Résultats de recherche", iconType: 'book' };
            } else if (isViewingSubDiscipline) {
                mainArticleListTitleInfo = { text: `Articles pour ${selectedSubDiscipline}`, iconType: 'book' };
            } else {
                mainArticleListTitleInfo = { text: `Articles précédents`, iconType: 'book' };
            }
        } else {
             if (isLikedArticlesView) {
                 let titleText = "Favoris";
                 if (selectedFilter !== ALL_CATEGORIES_VALUE && selectedFilter) { titleText += `: ${filterForTitle}`; }
                 if (isViewingSubDiscipline) { titleText += ` - ${selectedSubDiscipline}`; }
                 mainArticleListTitleInfo = { text: titleText, iconType: 'heart' };
             } else if (isEmailArticlesView) {
                 let titleText = "Articles reçus par email";
                 if (selectedFilter !== ALL_CATEGORIES_VALUE && selectedFilter) { titleText += `: ${filterForTitle}`; }
                 if (isViewingSubDiscipline) { titleText += ` - ${selectedSubDiscipline}`; }
                 mainArticleListTitleInfo = { text: titleText, iconType: 'email' };
             } else if (searchActive) {
                 mainArticleListTitleInfo = { text: "Résultats de recherche", iconType: 'book' };
             } else if (isViewingSubDiscipline) {
                 mainArticleListTitleInfo = { text: `Articles pour ${selectedSubDiscipline}`, iconType: 'book' };
             } else {
                 mainArticleListTitleInfo = { text: `Articles pour ${filterForTitle}`, iconType: 'book' };
             }
        }
    });

    $effect(() => {
        const currentMainFilter = selectedFilter;
        
        // Don't reset subdiscipline if we're on the initial filter and have an initial subdiscipline value
        const shouldKeepInitialSubdiscipline = currentMainFilter === initialFilterValue && 
                                               initialSubFilterValue && 
                                               selectedSubDiscipline === initialSubFilterValue;
        
        if (!shouldKeepInitialSubdiscipline) {
            selectedSubDiscipline = null;
        }
        availableSubDisciplines = [];

        if (!currentMainFilter || currentMainFilter === ALL_CATEGORIES_VALUE) {
             isLoadingSubDisciplines = false;
             return;
        }
        isLoadingSubDisciplines = true;
        const apiUrl = `/api/get_sub_disciplines?disciplineName=${encodeURIComponent(currentMainFilter)}&mode=${subDisciplineFetchMode}`;
        fetch(apiUrl)
            .then(async (res) => { if (!res.ok) { const errorText = await res.text().catch(() => `HTTP error ${res.status}`); throw new Error(`Erreur réseau ${res.status}: ${errorText}`); } return res.json();})
            .then((data: SubDisciplineOption[]) => {
                 availableSubDisciplines = data || [];
                 // Only set initial subdiscipline if it wasn't already set and it exists in the fetched data
                 if (initialSubFilterValue && 
                     data.some(sub => sub.name === initialSubFilterValue) && 
                     selectedFilter === initialFilterValue &&
                     selectedSubDiscipline !== initialSubFilterValue) {
                     selectedSubDiscipline = initialSubFilterValue;
                 }
            })
            .catch(error => { console.error("Error fetching sub-disciplines:", error); availableSubDisciplines = []; fetchError = `Erreur chargement sous-spécialités.`; })
            .finally(() => { isLoadingSubDisciplines = false; });
    });

    const debouncedFetchArticles = debounce(fetchArticles, searchDebounceMs);

    // Initialize search query with articleTitle if provided - handle both SSR and client scenarios
    $effect(() => {
        // Set initial search query immediately if we have articleTitle, regardless of user store
        if (!initialSearchSet && articleId && articleTitle) {
            searchQuery = articleTitle;
            initialSearchSet = true;
        }
        
        // Set initial subdiscipline if provided, to avoid second fetch
        if (!hasInitialized && initialSubFilterValue && selectedFilter === initialFilterValue) {
            selectedSubDiscipline = initialSubFilterValue;
        }
        
        // Mark as initialized when user store is available
        if (!hasInitialized && currentUserIdFromStore) {
            hasInitialized = true;
        }
    });

	$effect(() => {
        // Skip if not initialized yet to avoid multiple calls
        if (!hasInitialized) {
            return;
        }
        
        const _filter = selectedFilter;
        const _subFilter = selectedSubDiscipline;
        const _search = searchQuery;
        const _userId = currentUserIdFromStore;
        const _showEmailArticles = false; // Removed email articles view state
        const _emailReadFilter = 'all'; // Removed email articles read filter state
        const _showRecommendations = showRecommendationsFilter;
        const _showReadArticles = showReadArticlesFilter;

        if (!_userId) { 
            return; 
        }
        if (apiEndpoint === '/api/get-liked-articles' && !_userId) {
            if (!isInitialLoading) { articles = []; articleOfTheDay = null; hasMore = false; }
            return;
        }
        if (_filter === null && filters.length > 0 && !showAllCategoriesOption) {
             if (!isInitialLoading) { articles = []; articleOfTheDay = null; hasMore = false;}
            return;
        }
        isInitialLoading = true; articles = []; articleOfTheDay = null; offset = 0; hasMore = true; fetchError = null;
        debouncedFetchArticles(false);
	});

    // Removed email articles view toggle function

    // Function to toggle recommendations filter
    function toggleRecommendationsFilter() {
        showRecommendationsFilter = !showRecommendationsFilter;
        // Reset and fetch articles
        articles = [];
        articleOfTheDay = null;
        offset = 0;
        hasMore = true;
        fetchError = null;
        isInitialLoading = true;
        debouncedFetchArticles(false);
    }

    // Function to toggle read articles filter
    function toggleReadArticlesFilter() {
        showReadArticlesFilter = !showReadArticlesFilter;
        // Reset and fetch articles
        articles = [];
        articleOfTheDay = null;
        offset = 0;
        hasMore = true;
        fetchError = null;
        isInitialLoading = true;
        debouncedFetchArticles(false);
    }

    function processFetchedArticlesForAotD(newlyFetchedArticles: Article[], isSearchCurrentlyActive: boolean, isLikedArticlesPage: boolean): { aotd: Article | null; regularArticles: Article[] } {
        let potentialAotd: Article | null = null;
        let remainingArticles = [...newlyFetchedArticles];
        const isAotdContext = !isSearchCurrentlyActive && !isLikedArticlesPage;
        if (isAotdContext && newlyFetchedArticles.length > 0) {
            const firstArticle = newlyFetchedArticles[0];
            if (firstArticle?.is_article_of_the_day === true) {
                potentialAotd = firstArticle;
                remainingArticles = newlyFetchedArticles.slice(1);
            }
        }
        return { aotd: potentialAotd, regularArticles: remainingArticles };
    }

    function fetchArticles(isLoadMore = false) {
        const currentFilter = selectedFilter;
        const currentSubFilter = (currentFilter && currentFilter !== ALL_CATEGORIES_VALUE) ? selectedSubDiscipline : null;
        const currentSearch = searchQuery;
        const currentOffset = isLoadMore ? offset : 0;
        const userIdForFetch = currentUserIdFromStore;
        const currentPage = isLoadMore ? 1 : 1; // No email articles pagination

        if (apiEndpoint === '/api/get-liked-articles' && !userIdForFetch) {
            if (!isLoadMore) { articles = []; articleOfTheDay = null; hasMore = false; isLoading = false; isInitialLoading = false; }
            return;
        }
         if (currentFilter === null && filters.length > 0 && !showAllCategoriesOption) {
            if (!isLoadMore) { articles = []; articleOfTheDay = null; hasMore = false; isLoading = false; isInitialLoading = false; }
            return;
        }

        isLoading = true;
        if (!isLoadMore) { fetchError = null; }

        // Handle email articles vs regular articles
        // Removed email articles fetch logic

        // Regular articles fetch logic
		const url = new URL(apiEndpoint, window.location.origin);
		url.searchParams.set('offset', currentOffset.toString());
		url.searchParams.set('limit', itemsPerPage.toString());
        if (currentFilter && currentFilter !== ALL_CATEGORIES_VALUE) {
		    url.searchParams.set(apiFilterParamName, currentFilter);
            if (currentSubFilter && currentSubFilter !== allSubDisciplinesLabel) {
                 url.searchParams.set('subDiscipline', currentSubFilter);
            }
        }
        if (enableSearch && currentSearch.trim()) {
            url.searchParams.set('search', currentSearch.trim());
        }
        if (filterByUserSubs) {
            url.searchParams.set('filterByUserSubs', filterByUserSubs.toString());
        }
        if (apiEndpoint === '/api/get-liked-articles' && userIdForFetch) {
            url.searchParams.set('userId', userIdForFetch);
        }
        // Add recommendations filter
        if (showRecommendationsFilter) {
            url.searchParams.set('isRecommandation', 'true');
        }
        // Add read articles filter
        if (showReadArticlesFilter) {
            url.searchParams.set('p_only_read_articles', 'true');
        }

		fetch(url.toString())
			.then(async (res) => {  if (!res.ok) { const errorText = await res.text(); throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);} return res.json(); })
			.then((data) => {
                if (data && Array.isArray(data.data)) {
                    const fetchedArticles: Article[] = data.data.map((item: any) => ({
                        ...item, id: item.article_id, is_article_of_the_day: item.is_article_of_the_day
                    }));

                    if (isLoadMore) {
                        articles = [...articles, ...fetchedArticles];
                    } else {
                        const { aotd, regularArticles } = processFetchedArticlesForAotD(
                            fetchedArticles,
                            searchActive,
                            isLikedArticlesView
                        );
                        articleOfTheDay = aotd;
                        articles = regularArticles;
                    }
                    offset = currentOffset + fetchedArticles.length;
                    hasMore = fetchedArticles.length >= itemsPerPage;
				} else {
                    console.warn('API response format unexpected:', data); throw new Error("Format de réponse invalide");
				}
            })
			.catch((error) => {  console.error('Error fetching articles:', error); fetchError = error.message || "Erreur chargement articles."; if (!isLoadMore) { articles = []; articleOfTheDay = null; } hasMore = false; })
			.finally(() => { isLoading = false; if (!isLoadMore) { isInitialLoading = false; } });
    }

    function loadMore() { if (!isLoading && hasMore) { fetchArticles(true); } }

    function openImmersive(clickedArticle: Article) {
        if (!isSubscribed) {
            showSubscriptionRequired = true;
            return;
        }
        const articleIdToUpdate = getArticleId(clickedArticle);
        markArticleAsReadUI(articleIdToUpdate);
        immersiveArticle = getArticleFromState(articleIdToUpdate) ?? clickedArticle;
        markArticleAsReadAPI(articleIdToUpdate, currentUserIdFromStore);
		document.body.classList.add('overflow-hidden');
	}
	function closeImmersive() { immersiveArticle = null; document.body.classList.remove('overflow-hidden');}
    function markArticleAsReadUI(articleId: string | number) { performOptimisticArticleUpdate(articleId, { is_read: true }); }
    function markArticleAsReadAPI(articleId: string | number, userIdToUse: string | null | undefined) {
         if (userIdToUse && typeof articleId === 'number' && !isNaN(articleId)) {
             fetch('/api/mark-article-read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ articleId: articleId }), })
             .then(async (response) => { if (!response.ok) { const errorData = await response.json().catch(() => ({})); console.error(`API fail mark read ${articleId}:`, response.status, errorData.message);}})
             .catch((error) => { console.error(`Network error mark read ${articleId}:`, error); });
        }
    }
    function getArticleFromState(articleId: string | number): Article | null {
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) return articleOfTheDay;
        return articles.find(a => getArticleId(a) === articleId) || null;
    }

    $effect(() => {
        if (showSignupPromptProp && !currentUserIdFromStore) {
            const timer = setTimeout(() => { showSignupPrompt = true; }, 3000);
            return () => clearTimeout(timer);
        } else { showSignupPrompt = false; }
    });
	function handleSignup() { goto('/signup'); }

    function onSubDisciplineChangedByHeader(_newValue: string | null) {
        searchQuery = '';
    }

    let initialFilterSetForSearchClear = false;
    $effect(() => {
        const currentFilterValue = selectedFilter;
        
        // Only clear search if this isn't the initial load and we don't have a specific article to search for
        if (initialFilterSetForSearchClear && !articleId && !initialSearchSet) {
             searchQuery = '';
        }
        initialFilterSetForSearchClear = true;

		// This is to re-apply the initialSubFilterValue if the main filter changes back to initialFilterValue
        // and initialSubFilterValue was indeed set.
		if (currentFilterValue === initialFilterValue && initialSubFilterValue && availableSubDisciplines.some(sub => sub.name === initialSubFilterValue)) {
			if (selectedSubDiscipline !== initialSubFilterValue) {
				selectedSubDiscipline = initialSubFilterValue;
			}
		}
    });

    function performOptimisticArticleUpdate(
        articleIdToUpdate: number | string,
        updates: Partial<Pick<Article, 'is_liked' | 'like_count' | 'is_thumbed_up' | 'thumbs_up_count' | 'is_read'>>
    ) {
        const updateLogic = (article: Article): Article => (getArticleId(article) === articleIdToUpdate) ? { ...article, ...updates } : article;
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToUpdate) articleOfTheDay = updateLogic(articleOfTheDay);
        articles = articles.map(updateLogic);
    }
    function handleLikeToggle(eventDetail: { articleId: number | string; currentlyLiked: boolean; currentLikeCount: number; }) {
		const { articleId, currentlyLiked, currentLikeCount } = eventDetail;
		if (!currentUserIdFromStore) return;
		if (isLikedArticlesView && currentlyLiked) { articleToUnlike = { articleId, currentlyLiked, currentLikeCount }; showUnlikeConfirmModal = true; return; }
		const newStateIsLiked = !currentlyLiked; const newLikeCount = currentlyLiked ? Math.max(0, currentLikeCount - 1) : currentLikeCount + 1;
		performOptimisticLikeUpdate(articleId, newStateIsLiked, newLikeCount); triggerLikeApiCall(articleId, currentlyLiked, currentLikeCount);
        if (isLikedArticlesView && !newStateIsLiked) removeArticleFromUI(articleId);
	}
    function handleThumbsUpToggle(eventDetail: { articleId: number | string; currentlyThumbedUp: boolean; currentThumbsUpCount: number; }) {
        const { articleId, currentlyThumbedUp, currentThumbsUpCount } = eventDetail;
        if (!currentUserIdFromStore) return;
        const newStateIsThumbedUp = !currentlyThumbedUp; const newThumbsUpCount = currentlyThumbedUp ? Math.max(0, currentThumbsUpCount - 1) : currentThumbsUpCount + 1;
        performOptimisticThumbsUpUpdate(articleId, newStateIsThumbedUp, newThumbsUpCount);
        triggerThumbsUpApiCall(articleId, currentlyThumbedUp, currentThumbsUpCount);
    }
    function performOptimisticThumbsUpUpdate(articleId: number | string, newStateIsThumbedUp: boolean, newThumbsUpCount: number) {
        performOptimisticArticleUpdate(articleId, { is_thumbed_up: newStateIsThumbedUp, thumbs_up_count: newThumbsUpCount });
    }
    function triggerThumbsUpApiCall(articleIdNum: number | string, originalIsThumbedUp: boolean, originalThumbsUpCount: number) {
        if (typeof articleIdNum !== 'number' || isNaN(articleIdNum)) return;
        const revert = () => performOptimisticThumbsUpUpdate(articleIdNum, originalIsThumbedUp, originalThumbsUpCount);
        fetch('/api/toggle-article-thumbs-up', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ articleId: articleIdNum }), })
        .then(async (res) => { const data = await res.json().catch(() => ({})); if (!res.ok) { console.error(`API err thumbsup ${articleIdNum}:`, res.status, data.message); revert(); } else { const optimState = getArticleFromState(articleIdNum); if (optimState && optimState.is_thumbed_up !== data.thumbed_up) revert(); }})
        .catch((err) => { console.error(`Net err thumbsup ${articleIdNum}:`, err); revert(); });
    }
	function handleConfirmUnlike() {
		if (!articleToUnlike) return; const { articleId, currentlyLiked, currentLikeCount } = articleToUnlike;
		performOptimisticLikeUpdate(articleId, false, Math.max(0, currentLikeCount - 1));
		triggerLikeApiCall(articleId, currentlyLiked, currentLikeCount);
        removeArticleFromUI(articleId);
		showUnlikeConfirmModal = false; articleToUnlike = null;
	}
	function handleCancelUnlike() { showUnlikeConfirmModal = false; articleToUnlike = null; }
    function removeArticleFromUI(articleIdToRemove: number | string) {
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToRemove) articleOfTheDay = null;
        articles = articles.filter(a => getArticleId(a) !== articleIdToRemove);
    }
	function performOptimisticLikeUpdate(articleId: number | string, newStateIsLiked: boolean, newLikeCount: number) {
        performOptimisticArticleUpdate(articleId, { is_liked: newStateIsLiked, like_count: newLikeCount });
	}
	function triggerLikeApiCall(articleIdNum: number | string, originalIsLiked: boolean, originalLikeCount: number) {
		if (typeof articleIdNum !== 'number' || isNaN(articleIdNum)) return;
        const revert = () => { performOptimisticLikeUpdate(articleIdNum, originalIsLiked, originalLikeCount); if (isLikedArticlesView && !originalIsLiked) console.warn("Reverting unlike on /favoris. Re-fetch might be needed."); };
		fetch('/api/toggle-article-like', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ articleId: articleIdNum }), })
		.then(async (res) => { const data = await res.json().catch(() => ({})); if (!res.ok) { console.error(`API err like ${articleIdNum}:`, res.status, data.message); revert(); } else { const optimState = getArticleFromState(articleIdNum); if (optimState && optimState.is_liked !== data.liked) revert(); }})
		.catch((err) => { console.error(`Net err like ${articleIdNum}:`, err); revert(); });
	}
	async function handleToggleRead(articleToToggle: Article) {
		const articleId = getArticleId(articleToToggle);
		if (!currentUserIdFromStore || typeof articleId !== 'number' || isNaN(articleId)) return;
        const originalState = getArticleFromState(articleId); if (!originalState) return;
        const newReadState = !(originalState.is_read ?? false);
        performOptimisticArticleUpdate(articleId, { is_read: newReadState }); await tick();
		try {
			const response = await fetch('/api/toggle-article-read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ articleId: articleId }), });
			const responseData = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(responseData.message || `API Error: ${response.status}`);
            if (responseData.read !== newReadState) performReadRevert(originalState);
		} catch (error: any) {
			console.error(`Error toggle read API for ${articleId}:`, error);
			performReadRevert(originalState);
            fetchError = `Erreur MàJ statut 'lu' pour article ${getArticleId(originalState)}.`;
		}
	}
    function performReadRevert(originalArticleState: Article) {
         performOptimisticArticleUpdate(getArticleId(originalArticleState), { is_read: originalArticleState.is_read ?? false });
    }

    // Function to handle edit article
    function handleEditArticle(article: Article) {
        editingArticle = article;
        showEditModal = true;
    }

    // Function to close edit modal
    function closeEditModal() {
        showEditModal = false;
        editingArticle = null;
    }
</script>

<div class="min-h-screen bg-black px-4 py-8 md:py-12 text-white">
	<div class="mx-auto max-w-4xl">
		{#if showSignupPrompt}
			<div class="mb-6 flex flex-col sm:flex-row items-center justify-between gap-3 rounded-lg bg-teal-600/20 p-4 shadow-md transition-all duration-300 hover:bg-teal-600/30">
				<p class="text-sm font-medium text-center sm:text-left">Débloquez tout le potentiel ! Inscrivez-vous pour sauvegarder vos articles favoris et personnaliser votre veille.</p>
				<button onclick={handleSignup} class="group flex shrink-0 inline-block items-center justify-center gap-2 rounded-full bg-teal-500 px-4 py-2 text-xs font-semibold text-white transition-all duration-200 hover:bg-teal-600 whitespace-nowrap">
					<span>S'inscrire gratuitement</span>
					<svg class="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"> <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7m0 0l-7 7m7-7H3"/> </svg>
				</button>
			</div>
		{/if}

		{#if fetchError && !isLoading && (articles.length === 0 && !articleOfTheDay)}
             <div class="my-6 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-center" role="alert">
                <p><strong>Erreur :</strong> {fetchError}</p>
                <button onclick={() => fetchError = null} class="mt-2 text-xs underline hover:text-red-100">Ignorer</button>
             </div>
        {/if}

		<h1 class="mb-4 text-3xl font-bold text-white">{pageTitle}</h1>

		<!-- Toggles Section -->
		<div class="mb-6 flex items-center justify-between">
			<div class="flex items-center space-x-4">
				<!-- Recommendations Toggle -->
				{#if enableRecommendationsToggle}
					<button
						onclick={toggleRecommendationsFilter}
						class="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-300 {showRecommendationsFilter ? 'bg-yellow-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
					>
						<span class="text-lg">🌟</span>
						<span>
							{showRecommendationsFilter ? 'Voir tous les articles' : 'Recommandations uniquement'}
						</span>
					</button>
				{/if}

				<!-- Read Articles Toggle -->
				{#if enableReadArticlesToggle}
					<button
						onclick={toggleReadArticlesFilter}
						class="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-300 {showReadArticlesFilter ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
					>
						<span class="text-lg">📖</span>
						<span>
							{showReadArticlesFilter ? 'Voir tous les articles' : 'Articles non lus uniquement'}
						</span>
					</button>
				{/if}
			</div>
		</div>

		<ArticleListHeader
            {filters}
            bind:selectedFilter
            {filterSelectLabel}
            {showAllCategoriesOption}
            {ALL_CATEGORIES_VALUE}
            {ALL_CATEGORIES_LABEL}
            isContentLoading={isLoading && isInitialLoading}
            {showSubDisciplineFilter}
            {availableSubDisciplines}
            bind:selectedSubDiscipline
            {isLoadingSubDisciplines}
            {subDisciplineSelectLabel}
            {allSubDisciplinesLabel}
            {showAllSubDisciplinesOption}
            on:subdisciplinechanged={(e) => onSubDisciplineChangedByHeader(e.detail)}
            {enableSearch}
            bind:searchQuery
            {searchPlaceholder}
            isSearchDisabled={isLoading && isInitialLoading && !searchActive}
        />

        <ArticleListDisplay
            {articleOfTheDay}
            {articles}
            {isInitialLoading}
            fetchError={fetchError}
            userId={currentUserIdFromStore}
            {isLikedArticlesView}
            {emptyStateMessage}
            {filterForTitle}
            {isViewingSubDiscipline}
            {selectedSubDiscipline}
            {searchActive}
            {searchQuery}
            isLoading={isLoading}
            {hasMore}
            {loadMoreButtonText}
            {allArticlesLoadedText}
            {mainArticleListTitleInfo}
            {ALL_CATEGORIES_VALUE}
            {isSubscribed}
            onEditClick={handleEditArticle}
            on:openArticle={(e) => openImmersive(e.detail)}
            on:likeToggle={(e) => handleLikeToggle(e.detail)}
            on:toggleRead={(e) => handleToggleRead(e.detail)}
            on:thumbsUpToggle={(e) => handleThumbsUpToggle(e.detail)}
            on:loadMore={loadMore}
            on:handleSignup={handleSignup}
        />
	</div>
</div>
<ArticleImmersiveModal article={immersiveArticle} on:close={closeImmersive} />
<ArticleEditModal 
    showModal={showEditModal} 
    article={editingArticle} 
    onClose={closeEditModal} 
/>
<ConfirmationModal isOpen={showUnlikeConfirmModal} on:confirm={handleConfirmUnlike} on:cancel={handleCancelUnlike} title="Confirmer le retrait" message="Retirer cet article de vos favoris ?" confirmText="Retirer" cancelText="Annuler"/>
{#if showSubscriptionRequired}
    <SubscriptionRequired on:close={() => showSubscriptionRequired = false} />
{/if}

<style>
	button:focus-visible, input:focus-visible, [data-radix-select-trigger]:focus-visible { outline: 2px solid #14b8a6; outline-offset: 2px; }
	.scrollbar-thin { scrollbar-width: thin; scrollbar-color: #14b8a6 #1f2937; }
	.scrollbar-thin::-webkit-scrollbar { width: 8px; height: 8px; }
	.scrollbar-thin::-webkit-scrollbar-track { background: #1f2937; border-radius: 10px; }
	.scrollbar-thin::-webkit-scrollbar-thumb { background-color: #14b8a6; border-radius: 6px; border: 2px solid #1f2937; }
</style>