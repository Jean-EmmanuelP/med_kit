<!-- src/lib/components/articles/ArticleListView.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import ConfirmationModal from '$lib/components/ui/ConfirmationModal.svelte';
	import * as Select from '$lib/components/ui/select';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';
	import { debounce } from '$lib/utils/debounce';
	import { tick } from 'svelte';
// Import tick
	import ArticleCard from './ArticleCard.svelte';
	import ArticleImmersiveModal from './ArticleImmersiveModal.svelte';


	// --- Constants ---
    const ALL_CATEGORIES_VALUE = "__ALL__"; // Special value for "All"
    const ALL_CATEGORIES_LABEL = "Toutes les catégories"; // Display label

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
		initialFilterValue = null,
		filterSelectLabel = 'Filtrer par',
		showSignupPromptProp = false,
        enableSearch = false,
        searchDebounceMs = 300,
        searchPlaceholder = "Rechercher par mots-clés...",
		apiEndpoint = '/api/get_articles_my_veille',
		apiFilterParamName = 'specialty',
		userId = null as string | null, // Keep userId prop if needed elsewhere, but rely on store for actions
		articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :',
		previousArticlesTitleTemplate = '📖 Articles précédents pour {filter} :',
		loadMoreButtonText = "Charger plus d'articles",
		allArticlesLoadedText = "Tous les articles ont été chargés",
        emptyStateMessage = null as string | null,
        itemsPerPage = 10,
        subDisciplineSelectLabel = "Affiner par sous-spécialité",
        showAllSubDisciplinesOption = true,
        allSubDisciplinesLabel = "Toutes les sous-spécialités",
        showAllCategoriesOption = true
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
		userId?: string | null; // Keep prop
		articleOfTheDayTitleTemplate?: string;
		previousArticlesTitleTemplate?: string;
		loadMoreButtonText?: string;
		allArticlesLoadedText?: string;
        emptyStateMessage?: string | null;
        itemsPerPage?: number;
        subDisciplineSelectLabel?: string;
        showAllSubDisciplinesOption?: boolean;
        allSubDisciplinesLabel?: string;
        showAllCategoriesOption?: boolean;
	}>();

    // Update initial filter default logic slightly to handle empty filters AND showAll option
    const defaultInitialFilter = filters.length > 0 ? (filters[0]?.value ?? null) : (showAllCategoriesOption ? ALL_CATEGORIES_VALUE : null);

	// --- Internal State ---
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
    let articleToUnlike = $state<{
        articleId: number | string;
        currentlyLiked: boolean;
        currentLikeCount: number;
    } | null>(null);

	// --- Derived State ---
	const sortedFilters = $derived(
        [...filters].sort((a: FilterOption, b: FilterOption) =>
			a.label.localeCompare(b.label, 'fr', { sensitivity: 'base' })
		)
    );
	const triggerContent = $derived(
        selectedFilter === ALL_CATEGORIES_VALUE
            ? ALL_CATEGORIES_LABEL
            : (filters.find((f: FilterOption) => f.value === selectedFilter)?.label ?? filterSelectLabel)
    );
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
    const isLikedArticlesView = $derived(apiEndpoint === '/api/get-liked-articles');

    // --- Core Logic ---

    // Effect to fetch SUB-DISCIPLINES when main filter changes
    $effect(() => {
        const currentMainFilter = selectedFilter;
        // console.log('Main filter changed to:', currentMainFilter);

        selectedSubDiscipline = null;
        availableSubDisciplines = [];
        if (!currentMainFilter || currentMainFilter === ALL_CATEGORIES_VALUE) {
            //  console.log('Skipping sub-discipline fetch (All or None selected).');
             isLoadingSubDisciplines = false;
             return;
        }

        isLoadingSubDisciplines = true;
        // console.log('Fetching sub-disciplines for:', currentMainFilter);

        fetch(`/api/get_sub_disciplines?disciplineName=${encodeURIComponent(currentMainFilter)}`)
            .then(async (res) => {
                if (!res.ok) {
                    const errorText = await res.text();
					throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);
                }
                return res.json();
            })
            .then((data: SubDisciplineOption[]) => {
                //  console.log('Fetched sub-disciplines:', data);
                 availableSubDisciplines = data || [];
            })
            .catch(error => {
                console.error("Error fetching sub-disciplines:", error);
                availableSubDisciplines = [];
            })
            .finally(() => {
                isLoadingSubDisciplines = false;
                // console.log('Finished fetching sub-disciplines.');
            });
    });

    // Create a debounced function for triggering the fetch
    const debouncedFetchArticles = debounce(fetchArticles, searchDebounceMs);

    // Effect to trigger DEBOUNCED article fetch on filter/search/user changes
	$effect(() => {
        const _filter = selectedFilter;
        const _subFilter = selectedSubDiscipline;
        const _search = searchQuery;
        const _userId = $userProfileStore?.id ?? null; // Use store here

        // Check if API needs user ID and if it's available
        if (apiEndpoint === '/api/get-liked-articles' && !_userId) {
            // console.log("$effect: Blocking fetch - waiting for userId for liked articles.");
            if (!isInitialLoading) { // Only clear if not the very first load
                articles = [];
                articleOfTheDay = null;
                hasMore = false;
            }
            // Keep isInitialLoading true until user ID is available or handled
            return;
        }

        // Check if a filter is required and if it's selected
        if (_filter === null && filters.length > 0) { // Only block if filters ARE available but none is selected
            // console.log("$effect: Blocking fetch - selectedFilter is null but filters exist.");
             if (!isInitialLoading) {
                articles = [];
                articleOfTheDay = null;
                hasMore = false;
            }
            return;
        }

        // console.log("$effect: Conditions met, resetting state and triggering fetch");
        isInitialLoading = true; // Set to true before fetch starts
        articles = [];
        articleOfTheDay = null;
        offset = 0;
        hasMore = true;
        fetchError = null;

		// console.log("$effect: Triggering debounced fetchArticles call");
        debouncedFetchArticles(false); // Call fetch directly or debounced
	});

    // Reusable fetch function
    function fetchArticles(isLoadMore = false) {
        const currentFilter = selectedFilter;
        const currentSubFilter = (currentFilter !== ALL_CATEGORIES_VALUE) ? selectedSubDiscipline : null;
        const currentSearch = searchQuery;
        const currentOffset = isLoadMore ? offset : 0;
        const currentUserId = $userProfileStore?.id ?? null; // Use store

        // Re-check dependency on user ID
        if (apiEndpoint === '/api/get-liked-articles' && !currentUserId) {
            // console.log("fetchArticles exit: Waiting for user ID for liked articles.");
            if (!isLoadMore) {
                 articles = [];
                 articleOfTheDay = null;
                 hasMore = false;
                 isLoading = false;
                 isInitialLoading = false; // Mark initial load as done (even though failed)
            }
            return;
        }

        // Re-check filter requirement
        if (currentFilter === null && filters.length > 0) {
            // console.log("fetchArticles exit: selectedFilter is null but filters exist.");
            if (!isLoadMore) {
                articles = [];
                articleOfTheDay = null;
                hasMore = false;
                isLoading = false;
                isInitialLoading = false; // Mark initial load as done
            }
            return;
        }


        isLoading = true;
        if (!isLoadMore) {
            fetchError = null;
            // isInitialLoading is already true here due to the $effect logic
        } else {
            // Don't reset initial loading flag when loading more
        }

		// console.log(`FETCHING articles -> Endpoint: ${apiEndpoint}, Filter: ${currentFilter}, SubFilter: ${currentSubFilter}, Search: ${currentSearch}, Offset: ${currentOffset}, UserID: ${currentUserId}`);

		const url = new URL(apiEndpoint, window.location.origin);

        // Append parameters
        if (currentFilter && currentFilter !== ALL_CATEGORIES_VALUE) {
		    url.searchParams.set(apiFilterParamName, currentFilter);
            if (currentSubFilter && currentSubFilter !== allSubDisciplinesLabel) {
                 url.searchParams.set('subDiscipline', currentSubFilter);
            }
        }
		url.searchParams.set('offset', currentOffset.toString());
		url.searchParams.set('limit', itemsPerPage.toString()); // <<< ADD LIMIT
        if (enableSearch && currentSearch.trim()) {
            url.searchParams.set('search', currentSearch.trim());
        }
        // Add user ID if needed by the endpoint (handled by RPC now mostly)
        // if (userId) { url.searchParams.set('userId', userId); }

		fetch(url.toString())
			.then(async (res) => {
                if (!res.ok) {
                    const errorText = await res.text();
					throw new Error(`Erreur réseau ${res.status}: ${errorText || res.statusText}`);
                }
                return res.json();
            })
			.then((data) => {
                // console.log(`API Response (Offset: ${currentOffset}):`, data);
				if (data && Array.isArray(data.data)) {
                    const fetchedArticles: Article[] = data.data;

                    if (isLoadMore) {
                        articles = [...articles, ...fetchedArticles];
                    } else {
                        // Split AotD only if NOT searching, NOT liked view, and NOT sub-discipline view
                         if (!searchActive && !isLikedArticlesView && !isViewingSubDiscipline && fetchedArticles.length > 0) {
                            articleOfTheDay = fetchedArticles[0];
                            articles = fetchedArticles.slice(1);
                        } else {
                            // Otherwise, all fetched articles go into the main list
                            articleOfTheDay = null;
                            articles = fetchedArticles;
                        }
                    }

                    // Update offset and hasMore based on fetched count vs limit
                    offset = currentOffset + fetchedArticles.length;
                    hasMore = fetchedArticles.length >= itemsPerPage;

				} else {
                    console.warn('API response format unexpected or data.data is not an array:', data);
					throw new Error("Format de réponse invalide de l'API");
				}
            })
			.catch((error) => {
                console.error('Error fetching articles:', error);
                fetchError = error.message || "Une erreur est survenue lors du chargement des articles.";
                // Clear articles on error unless loading more
                if (!isLoadMore) {
                    articles = [];
                    articleOfTheDay = null;
                }
                hasMore = false; // Stop loading more on error
            })
			.finally(() => {
                // console.log(`Fetch finished (Offset: ${currentOffset})`);
                isLoading = false;
                // Set initial loading false only after the *first* fetch completes (success or error)
                if (!isLoadMore) {
                    isInitialLoading = false;
                }
            });
    }

    function loadMore() {
         if (!isLoading && hasMore) {
             fetchArticles(true);
         }
	}

    function openImmersive(event: CustomEvent<Article>) {
        const clickedArticle = event.detail;
        const articleIdToUpdate = getArticleId(clickedArticle);
        const currentUser = $userProfileStore; // Get current user state

        // Optimistically mark as read in UI *before* showing modal
        markArticleAsReadUI(articleIdToUpdate);

        // Set the article for the modal
        immersiveArticle = getArticleFromState(articleIdToUpdate) ?? clickedArticle;

        // Call API to mark as read (fire and forget)
        markArticleAsReadAPI(articleIdToUpdate, currentUser?.id);

        // Add class to body
		document.body.classList.add('overflow-hidden');
	}

	function closeImmersive() {
		immersiveArticle = null;
		document.body.classList.remove('overflow-hidden');
	}

    // --- Separate UI update function ---
    function markArticleAsReadUI(articleId: string | number) {
        console.log(`Optimistic UI: Marking article ${articleId} as read.`);
         if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) {
            articleOfTheDay = { ...articleOfTheDay, is_read: true };
        }
        articles = articles.map(a =>
            getArticleId(a) === articleId ? { ...a, is_read: true } : a
        );
    }

    // --- Separate API call function ---
    function markArticleAsReadAPI(articleId: string | number, userId: string | null | undefined) {
         if (userId && typeof articleId === 'number' && !isNaN(articleId)) {
            // console.log(`Calling API to mark article ${articleId} as read for user ${userId}...`);
             fetch('/api/mark-article-read', { // Use the single mark-read endpoint
                 method: 'POST',
                 headers: { 'Content-Type': 'application/json' },
                 body: JSON.stringify({ articleId: articleId }),
             })
             .then(async (response) => {
                 if (!response.ok) {
                     const errorData = await response.json().catch(() => ({ message: 'Failed to parse error response' }));
                     console.error(`API failed to mark article ${articleId} as read:`, response.status, errorData.message || response.statusText);
                     // Optionally revert UI? Might be complex if user navigates away.
                 } else {
                    //  console.log(`API confirmed article ${articleId} marked as read.`);
                 }
             })
             .catch((error) => {
                 console.error(`Network error marking article ${articleId} as read:`, error);
             });
        } else if (!userId) {
            // console.log("User not logged in, skipping mark as read API call.");
        } else {
            console.warn("Cannot mark article as read via API: Invalid article ID.", articleId);
        }
    }

     // Helper to get the current state of an article
    function getArticleFromState(articleId: string | number): Article | null {
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) {
            return articleOfTheDay;
        }
        return articles.find(a => getArticleId(a) === articleId) || null;
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
        const newValue = value === allSubDisciplinesLabel ? null : value;
        if (selectedSubDiscipline !== newValue) {
            selectedSubDiscipline = newValue;
            // Fetch will be triggered by the $effect watching selectedSubDiscipline
        }
    }

    // --- Handle Like Toggle ---
    function handleLikeToggle(event: CustomEvent<{ articleId: number | string; currentlyLiked: boolean; currentLikeCount: number; }>) {
		const { articleId, currentlyLiked, currentLikeCount } = event.detail;
		const currentUser = $userProfileStore; if (!currentUser) { console.warn("User not logged in, cannot toggle like."); return; }
		if (isLikedArticlesView && currentlyLiked) { articleToUnlike = { articleId, currentlyLiked, currentLikeCount }; showUnlikeConfirmModal = true; return; }
		const newStateIsLiked = !currentlyLiked; const newLikeCount = currentlyLiked ? Math.max(0, currentLikeCount - 1) : currentLikeCount + 1;
		performOptimisticLikeUpdate(articleId, newStateIsLiked, newLikeCount); triggerLikeApiCall(articleId, currentlyLiked, currentLikeCount);
        if (isLikedArticlesView && newStateIsLiked === false) { removeArticleFromUI(articleId); }
	}

    // --- Handle Thumbs Up Toggle ---
    function handleThumbsUpToggle(event: CustomEvent<{ articleId: number | string; currentlyThumbedUp: boolean; currentThumbsUpCount: number; }>) {
        const { articleId, currentlyThumbedUp, currentThumbsUpCount } = event.detail;
        const currentUser = $userProfileStore;
        if (!currentUser) { console.warn("User not logged in, cannot toggle thumbs-up."); return; }
        const newStateIsThumbedUp = !currentlyThumbedUp;
        const newThumbsUpCount = currentlyThumbedUp ? Math.max(0, currentThumbsUpCount - 1) : currentThumbsUpCount + 1;
        performOptimisticThumbsUpUpdate(articleId, newStateIsThumbedUp, newThumbsUpCount);
        triggerThumbsUpApiCall(articleId, currentlyThumbedUp, currentThumbsUpCount);
    }
    function performOptimisticThumbsUpUpdate(articleId: number | string, newStateIsThumbedUp: boolean, newThumbsUpCount: number) {
        // console.log(`Optimistic ThumbsUp Update: Setting thumbed_up=${newStateIsThumbedUp}, count=${newThumbsUpCount} for article ${articleId}`);
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) {
            articleOfTheDay = { ...articleOfTheDay, is_thumbed_up: newStateIsThumbedUp, thumbs_up_count: newThumbsUpCount };
        }
        articles = articles.map(a =>
            getArticleId(a) === articleId ? { ...a, is_thumbed_up: newStateIsThumbedUp, thumbs_up_count: newThumbsUpCount } : a
        );
    }
    function triggerThumbsUpApiCall(articleId: number | string, originalIsThumbedUp: boolean, originalThumbsUpCount: number) {
        if (typeof articleId !== 'number' || isNaN(articleId)) { console.warn("Cannot toggle thumbs-up: Invalid article ID.", articleId); return; }
        const revertThumbsUpUpdate = () => {
            // console.log(`Reverting thumbs-up status for article ${articleId} to thumbed_up=${originalIsThumbedUp}, count=${originalThumbsUpCount}`);
            performOptimisticThumbsUpUpdate(articleId, originalIsThumbedUp, originalThumbsUpCount);
        };
        fetch('/api/toggle-article-thumbs-up', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ articleId: articleId }), })
        .then(async (response) => {
            const responseData = await response.json().catch(() => ({}));
            if (!response.ok) { console.error(`API error toggling thumbs-up for article ${articleId}:`, response.status, responseData.message || response.statusText); revertThumbsUpUpdate(); }
            else {
                const currentOptimisticState = getArticleFromState(articleId);
                if (currentOptimisticState && currentOptimisticState.is_thumbed_up !== responseData.thumbed_up) { console.warn(`Optimistic thumbs-up state mismatch for ${articleId}. Reverting.`); revertThumbsUpUpdate(); }
            }
        })
        .catch((error) => { console.error(`Network error toggling thumbs-up for article ${articleId}:`, error); revertThumbsUpUpdate(); });
    }

	// --- Modal Event Handlers ---
	function handleConfirmUnlike() {
		if (!articleToUnlike) return;

		// console.log("User confirmed unlike via modal for article:", articleToUnlike.articleId);
		const { articleId, currentlyLiked, currentLikeCount } = articleToUnlike;

        // Mark as unliked and update count optimistically
		performOptimisticLikeUpdate(articleId, false, Math.max(0, currentLikeCount - 1));
        // Trigger the API call
		triggerLikeApiCall(articleId, currentlyLiked, currentLikeCount);
        // Remove from UI specifically for the liked articles view
        removeArticleFromUI(articleId);

		// Reset modal state
		showUnlikeConfirmModal = false;
		articleToUnlike = null;
	}

	function handleCancelUnlike() {
		// console.log("Unlike cancelled via modal.");
		showUnlikeConfirmModal = false;
		articleToUnlike = null;
	}

    // --- Helper to remove article visually ---
    function removeArticleFromUI(articleIdToRemove: number | string) {
        if (articleOfTheDay && getArticleId(articleOfTheDay) === articleIdToRemove) {
            articleOfTheDay = null;
        }
        articles = articles.filter(a => getArticleId(a) !== articleIdToRemove);
    }


	// --- Extracted Helper Functions ---
	function performOptimisticLikeUpdate(articleId: number | string, newStateIsLiked: boolean, newLikeCount: number) {
		// console.log(`Optimistic Like Update: Setting liked=${newStateIsLiked}, count=${newLikeCount} for article ${articleId}`);
		if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) {
			articleOfTheDay = { ...articleOfTheDay, is_liked: newStateIsLiked, like_count: newLikeCount };
		}
		articles = articles.map(a =>
			getArticleId(a) === articleId ? { ...a, is_liked: newStateIsLiked, like_count: newLikeCount } : a
		);
	}

    // --- Trigger Like API Call (with revert logic passed in) ---
	function triggerLikeApiCall(articleId: number | string, originalIsLiked: boolean, originalLikeCount: number) {
		if (typeof articleId !== 'number' || isNaN(articleId)) {
            console.warn("Cannot toggle like: Invalid article ID.", articleId);
			return; // Exit if ID is invalid
		}

        // Define the revert function specific to this action
        const revertLikeUpdate = () => {
            console.log(`Reverting like status for article ${articleId} to liked=${originalIsLiked}, count=${originalLikeCount}`);
            performOptimisticLikeUpdate(articleId, originalIsLiked, originalLikeCount);
            // If unliking on liked view was reverted, potentially add item back (more complex UI logic)
            if (isLikedArticlesView && !originalIsLiked) {
                 console.warn("Reverting an unlike on /favoris. Re-fetching might be needed to add the item back correctly if it was removed.");
                 // Consider re-fetching or more complex state management here if needed
            }
        };

		fetch('/api/toggle-article-like', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ articleId: articleId }),
		})
		.then(async (response) => {
			const responseData = await response.json().catch(() => ({}));
			if (!response.ok) {
				console.error(`API error toggling like for article ${articleId}:`, response.status, responseData.message || response.statusText);
                revertLikeUpdate(); // Revert on API error
			} else {
				// console.log(`API confirmed like status for ${articleId} is now: ${responseData.liked}`);
                // Optional: Verify API state vs optimistic state
                const currentOptimisticState = getArticleFromState(articleId);
                if (currentOptimisticState && currentOptimisticState.is_liked !== responseData.liked) {
                    console.warn(`Optimistic like state mismatch for ${articleId}. Reverting.`);
                    revertLikeUpdate();
                }
			}
		})
		.catch((error) => {
			console.error(`Network error toggling like for article ${articleId}:`, error);
            revertLikeUpdate(); // Revert on network error
		});
	}

	// --- CORRECTED: Handler for Toggling Read Status ---
	async function handleToggleRead(event: CustomEvent<Article>) {
		const articleToToggle = event.detail;
		const articleId = getArticleId(articleToToggle);
		const currentUser = $userProfileStore;

		if (!currentUser?.id || typeof articleId !== 'number' || isNaN(articleId)) {
			console.warn("Cannot toggle read: User not logged in or invalid article ID.", { userId: currentUser?.id, articleId });
			return;
		}

		// console.log(`UI: handleToggleRead triggered for article ${articleId}`);

		// --- Find original state for potential revert ---
        const originalState = getArticleFromState(articleId);
        if (!originalState) {
             console.error(`Cannot find article ${articleId} in state to toggle read status.`);
             return;
        }
        const originalIsRead = originalState.is_read ?? false;
		const newReadState = !originalIsRead;

		// --- 1. Optimistic UI Update (Update in place, never remove) ---
		// console.log(`Optimistic UI: Setting article ${articleId} is_read to ${newReadState}`);
		if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) {
			articleOfTheDay = { ...articleOfTheDay, is_read: newReadState };
		}
		articles = articles.map(a =>
			getArticleId(a) === articleId ? { ...a, is_read: newReadState } : a
		);
		await tick(); // Wait for DOM update

		// --- 2. API Call ---
		try {
			// console.log(`API Call: Toggling read status for article ${articleId}`);
			const response = await fetch('/api/toggle-article-read', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ articleId: articleId }),
			});
			const responseData = await response.json().catch(() => ({}));

			if (!response.ok) {
				throw new Error(responseData.message || `API Error: ${response.status}`);
			}
			// console.log(`API Success: Article ${articleId} read status is now ${responseData.read}`);

            // Optional: Verify API response matches optimistic state
            if (responseData.read !== newReadState) {
                console.warn(`Optimistic/API read state mismatch for ${articleId}. Reverting UI.`);
                performReadRevert(originalState);
            }

		} catch (error: any) {
			console.error(`Error toggling read status API for article ${articleId}:`, error);
			// --- 3. Revert Optimistic UI on Error ---
			console.log(`Reverting optimistic UI read status change for article ${articleId}`);
			performReadRevert(originalState);
            fetchError = `Erreur lors de la mise à jour du statut 'lu' pour l'article ${articleId}.`; // Show user-facing error
		}
	}

	// --- Helper to Revert Read Status UI Change ---
    function performReadRevert(originalArticleState: Article) {
         const articleId = getArticleId(originalArticleState);
         // console.log(`Reverting UI: Setting article ${articleId} is_read back to ${originalArticleState.is_read}`);
          if (articleOfTheDay && getArticleId(articleOfTheDay) === articleId) {
            articleOfTheDay = originalArticleState; // Restore original object
        }
        articles = articles.map(a =>
            getArticleId(a) === articleId ? originalArticleState : a // Restore original object
        );
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

		{#if fetchError && !isLoading}
             <div class="my-6 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-center" role="alert">
                <p><strong>Erreur :</strong> {fetchError}</p>
                <button on:click={() => fetchError = null} class="mt-2 text-xs underline hover:text-red-100">Ignorer</button>
             </div>
        {/if}


		<h1 class="mb-4 text-3xl font-bold text-white">{pageTitle}</h1>

		<div class="mb-6 flex flex-col gap-4">
            <div class="flex flex-col md:flex-row flex-wrap gap-4">
                {#if filters.length > 0 || showAllCategoriesOption}
                    <div class="relative w-full md:max-w-xs shrink-0">
                        <Select.Root type="single" name="selectedFilter" value={selectedFilter ?? undefined} onValueChange={(detail) => selectedFilter = detail}>
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
                                    {#if showAllCategoriesOption}
                                        <Select.Item
                                            value={ALL_CATEGORIES_VALUE}
                                            label={ALL_CATEGORIES_LABEL}
                                            class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600/80 hover:text-white data-[selected]:bg-teal-700"
                                        >
                                            {ALL_CATEGORIES_LABEL}
                                        </Select.Item>
                                    {/if}
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

                {#if showSubDisciplineFilter}
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
        {:else if fetchError && articles.length === 0 && !articleOfTheDay}
             <div class="my-10 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-center" role="alert">
                 <p><strong>Erreur lors du chargement initial :</strong> {fetchError}</p>
                 <p class="mt-2 text-sm">Veuillez réessayer ou vérifier votre connexion.</p>
             </div>
        {:else if !userId && isLikedArticlesView}
            <div class="my-10 p-4 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-400 text-center">
                <p>Connectez-vous pour voir vos articles favoris.</p>
                <button
                    on:click={handleSignup}
                    class="mt-4 rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors duration-200 hover:bg-teal-700"
                >
                    Se connecter
                </button>
            </div>
		{:else if !articleOfTheDay && articles.length === 0}
            <div class="my-10 p-4 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-400 text-center">
                {#if emptyStateMessage}
                    <p>{@html emptyStateMessage}</p>
                {:else}
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
                {/if}
            </div>
        {:else}
            <!-- Article of the Day Section (Conditional Display Logic) -->
			{#if articleOfTheDay}
                <div class="mb-8">
                    <h2 class="text-2xl font-bold text-teal-500">🔥 Article du jour</h2>
                    <p class="mt-2 mb-4 text-gray-400">Article selectionné aujourd'hui pour {filterForTitle} :</p>
                    <ul class="space-y-4">
                        <ArticleCard article={articleOfTheDay} on:open={openImmersive} on:likeToggle={handleLikeToggle} on:toggleRead={handleToggleRead} on:thumbsUpToggle={handleThumbsUpToggle}/>
                    </ul>
                </div>
            {/if}

            <!-- Main Article List Section -->
			<div class="mb-6">
                {#if articles.length > 0}
                    <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                        {#if isLikedArticlesView}
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 fill-pink-500 text-pink-500"> <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" /> </svg>
                            Favoris {#if selectedFilter !== ALL_CATEGORIES_VALUE && selectedFilter}: {filterForTitle}{/if} {#if isViewingSubDiscipline} - {selectedSubDiscipline}{/if}
                        {:else if searchActive}
                            Résultats de recherche
                        {:else if isViewingSubDiscipline}
                            📖 Articles pour {selectedSubDiscipline}
                        {:else}
                            📖 Articles précédents
                        {/if}
                    </h2>
                     <p class="mt-2 mb-4 text-gray-400">
                        {#if isLikedArticlesView}
                            {#if isViewingSubDiscipline}
                                Vos favoris pour {selectedSubDiscipline} ({filterForTitle}) :
                            {:else if searchActive}
                                 Résultats pour "{searchQuery}" dans vos favoris {#if selectedFilter !== ALL_CATEGORIES_VALUE}pour {filterForTitle}{/if} :
                            {:else if selectedFilter !== ALL_CATEGORIES_VALUE}
                                 Vos favoris pour {filterForTitle} :
                            {:else}
                                 Tous vos articles favoris :
                            {/if}
                        {:else if searchActive}
                            Résultats pour "{searchQuery}" dans "{filterForTitle}"{#if isViewingSubDiscipline} - {selectedSubDiscipline}{/if} :
                        {:else if isViewingSubDiscipline}
                            Articles selectionnés pour {selectedSubDiscipline} ({filterForTitle}) :
                        {:else}
                            Articles précédemment selectionnés pour {filterForTitle} :
                        {/if}
                    </p>
                {/if}

                <ul class="space-y-4">
                    {#each articles as article (getArticleId(article))}
                        <ArticleCard {article} on:open={openImmersive} on:likeToggle={handleLikeToggle} on:toggleRead={handleToggleRead} on:thumbsUpToggle={handleThumbsUpToggle}/>
                    {/each}
				</ul>

                {#if !isLoading && articles.length === 0 && articleOfTheDay && !isViewingSubDiscipline}
                    <p class="text-gray-500 italic text-sm ml-1 mt-4">Aucun article précédent trouvé pour cette sélection.</p>
				{/if}
			</div>

            <!-- Load More / All Loaded Section -->
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
            {:else if !isInitialLoading}
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

<ConfirmationModal
    isOpen={showUnlikeConfirmModal}
    on:confirm={handleConfirmUnlike}
    on:cancel={handleCancelUnlike}
    title="Confirmer le retrait"
    message="Êtes-vous sûr de vouloir retirer cet article de vos favoris ?"
    confirmText="Retirer"
    cancelText="Annuler"
/>


<style>
	button:focus-visible, input:focus-visible {
		outline: 2px solid #14b8a6; /* Teal-500 */
        outline-offset: 2px;
	}
    [data-radix-select-trigger]:focus-visible {
        outline: 2px solid #14b8a6; /* Teal-500 */
        outline-offset: 2px;
    }

	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #1f2937; /* thumb track - Teal-500, Gray-800 */
	}

	.scrollbar-thin::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: #1f2937; /* Gray-800 */
        border-radius: 10px;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6; /* Teal-500 */
		border-radius: 6px;
		border: 2px solid #1f2937; /* Gray-800 */
	}
</style>