<!-- src/lib/components/articles/ArticleListDisplay.svelte -->
<script lang="ts">
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';
	import { createEventDispatcher } from 'svelte';
	import ArticleCard from './ArticleCard.svelte';

	// Define ListTitleInfo directly here or import if it becomes shared
    interface ListTitleInfo {
        text: string;
        iconType: 'heart' | 'book' | 'email' | null;
    }

	const {
		articleOfTheDay = null as Article | null,
		articles = [] as Article[],
		isInitialLoading = true,
		fetchError = null as string | null, // Error specific to loading this list section
		userId = null as string | null, // For "login to see liked" message
		isLikedArticlesView = false, // For "login to see liked" message
		emptyStateMessage = null as string | null,
		filterForTitle = 'la sélection',
		isViewingSubDiscipline = false,
		selectedSubDiscipline = null as string | null, // For empty state message
        searchActive = false, // For empty state message
		searchQuery = '', // For empty state message
		isLoading = false, // For load more button state / spinner
		hasMore = true,
		loadMoreButtonText = "Charger plus d'articles",
		allArticlesLoadedText = "Tous les articles ont été chargés",
        mainArticleListTitleInfo = { text: 'Articles', iconType: 'book' } as ListTitleInfo,
        ALL_CATEGORIES_VALUE = "__ALL__", // From parent, for AOTD title logic
        isSubscribed = false, // New prop for subscription status
        onEditClick = null as ((article: Article) => void) | null
	} = $props<{
		articleOfTheDay?: Article | null;
		articles?: Article[];
		isInitialLoading?: boolean;
		fetchError?: string | null;
		userId?: string | null;
		isLikedArticlesView?: boolean;
		emptyStateMessage?: string | null;
		filterForTitle?: string;
		isViewingSubDiscipline?: boolean;
		selectedSubDiscipline?: string | null;
        searchActive?: boolean;
		searchQuery?: string;
		isLoading?: boolean;
		hasMore?: boolean;
		loadMoreButtonText?: string;
		allArticlesLoadedText?: string;
        mainArticleListTitleInfo?: ListTitleInfo;
        ALL_CATEGORIES_VALUE?: string;
        isSubscribed?: boolean;
        onEditClick?: ((article: Article) => void) | null;
	}>();

	const dispatch = createEventDispatcher<{
		openArticle: Article;
		likeToggle: { articleId: number | string; currentlyLiked: boolean; currentLikeCount: number };
		toggleRead: Article;
		thumbsUpToggle: { articleId: number | string; currentlyThumbedUp: boolean; currentThumbsUpCount: number };
		loadMore: void;
		handleSignup: void; // For the "connectez-vous" button
	}>();

	function openImmersive(event: CustomEvent<Article>) {
		dispatch('openArticle', event.detail);
	}
	function handleLikeToggle(event: CustomEvent<{ articleId: number | string; currentlyLiked: boolean; currentLikeCount: number }>) {
		dispatch('likeToggle', event.detail);
	}
	function handleToggleRead(event: CustomEvent<Article>) {
		dispatch('toggleRead', event.detail);
	}
	function handleThumbsUpToggle(event: CustomEvent<{ articleId: number | string; currentlyThumbedUp: boolean; currentThumbsUpCount: number }>) {
		dispatch('thumbsUpToggle', event.detail);
	}
	function onLoadMoreClick() {
		dispatch('loadMore');
	}
	function onHandleSignupClick() {
		dispatch('handleSignup');
	}

    // Derive selectedFilter from filterForTitle for AOTD title conditional
    // This is a simplification; in practice, ArticleListView passes `selectedFilter` if needed for more complex logic here.
    // For now, we'll use filterForTitle and isViewingSubDiscipline for the AOTD title.
    const aotdTitleForFilter = $derived(filterForTitle === 'toutes les catégories' ? '' : filterForTitle);

</script>

{#if isInitialLoading}
	<div class="flex justify-center items-center py-20" aria-live="polite" aria-busy="true"><div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500"></div></div>
{:else if fetchError && articles.length === 0 && !articleOfTheDay}
	<!-- This specific error message was for initial load errors that prevented any display -->
	<div class="my-10 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-center" role="alert"><p><strong>Erreur chargement initial :</strong> {fetchError}</p><p class="mt-2 text-sm">Veuillez réessayer.</p></div>
{:else if !userId && isLikedArticlesView}
	<div class="my-10 p-4 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-400 text-center"><p>Connectez-vous pour voir vos favoris.</p><button onclick={onHandleSignupClick} class="mt-4 rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-700">Se connecter</button></div>
{:else if !articleOfTheDay && articles.length === 0 && !isLoading}
	<div class="my-10 p-4 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-400 text-center">
		{#if emptyStateMessage}<p>{@html emptyStateMessage}</p>
		{:else}
			<p>{#if searchActive}Aucun article pour "{filterForTitle}"{#if isViewingSubDiscipline} dans "{selectedSubDiscipline}"{/if} avec "{searchQuery}".{:else}Aucun article pour "{filterForTitle}"{#if isViewingSubDiscipline} dans "{selectedSubDiscipline}"{/if}.{/if}</p>
			{#if isViewingSubDiscipline && !articleOfTheDay && !isLoading}<p class="mt-3 text-sm text-gray-500 italic">(Aucun article du jour spécifique à cette sous-spécialité.)</p>{/if}
			<p class="mt-2 text-sm">{#if searchActive}Essayez de modifier recherche/filtres.{:else}Revenez plus tard ou autre filtre.{/if}</p>
		{/if}
	</div>
{:else}
	{#if articleOfTheDay}
		<div class="mb-8">
            <!-- Simplified AOTD title. Parent `ArticleListView` could pass a more specific `aotdTitle` prop if complex logic is needed -->
			<h2 class="text-2xl font-bold text-teal-500">🔥 Article du jour {#if isViewingSubDiscipline && selectedSubDiscipline}{selectedSubDiscipline}{:else if aotdTitleForFilter}{aotdTitleForFilter}{/if}</h2>
			<ul class="mt-4 space-y-4"><ArticleCard article={articleOfTheDay} {isSubscribed} {onEditClick} on:open={openImmersive} on:likeToggle={handleLikeToggle} on:toggleRead={handleToggleRead} on:thumbsUpToggle={handleThumbsUpToggle}/>
			</ul>
		</div>
	{:else if isViewingSubDiscipline && !isLoading && articles.length > 0} <!-- Show this only if there are previous articles -->
		 <p class="mb-6 text-sm text-gray-500 italic">Aucun article du jour pour "{selectedSubDiscipline}". Voici les articles précédents :</p>
	{/if}

	<div class="mb-6">
		{#if articles.length > 0}
			<h2 class="text-2xl font-bold text-white flex items-center gap-2">
				{#if mainArticleListTitleInfo.iconType == 'heart'}
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 fill-pink-500 text-pink-500"> <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" /> </svg>
				{:else if mainArticleListTitleInfo.iconType == 'book'}
					📖
				{:else if mainArticleListTitleInfo.iconType == 'email'}
					<svg class="w-6 h-6 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 7.89a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
					</svg>
				{/if}
				{mainArticleListTitleInfo.text}
			</h2>
			<ul class="mt-4 space-y-4">
				 {#each articles as article (getArticleId(article))}
					<ArticleCard {article} {isSubscribed} {onEditClick} on:open={openImmersive} on:likeToggle={handleLikeToggle} on:toggleRead={handleToggleRead} on:thumbsUpToggle={handleThumbsUpToggle}/>
				 {/each}
			</ul>
		{/if}
	</div>

	{#if hasMore || isLoading}
		<div class="mt-8 text-center">
			{#if isLoading && !isInitialLoading}<div class="flex justify-center items-center py-4"><div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-teal-500"></div></div>
			{:else if hasMore}<button onclick={onLoadMoreClick} disabled={isLoading} class="rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed">{loadMoreButtonText}</button>{/if}
		</div>
	{:else if !isInitialLoading && (articles.length > 0 || articleOfTheDay)} <!-- Show "all loaded" only if some articles were ever loaded -->
		<div class="mt-8 text-center text-gray-500"><span class="inline-flex items-center gap-2 rounded-full bg-gray-800 px-4 py-2 text-sm"><svg class="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>{allArticlesLoadedText}</span></div>
	{/if}
{/if}