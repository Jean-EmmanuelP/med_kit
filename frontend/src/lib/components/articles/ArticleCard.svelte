<!-- src/lib/components/articles/ArticleCard.svelte -->
<script lang="ts">
	import {
		type Article,
		extractTitleEmoji,
		formatDate,
		formatTitle,
		getArticleId
	} from '$lib/utils/articleUtils';
	import { createEventDispatcher } from 'svelte';
		
	const { article } = $props<{ article: Article }>();
	const dispatch = createEventDispatcher<{ open: Article }>();

	const emoji = $derived(extractTitleEmoji(article.content));
	const displayTitle = $derived(formatTitle(article.title));
	const displayDate = $derived(formatDate(article.published_at));
	const articleId = $derived(getArticleId(article)); // Use helper for consistent ID

	function handleClick() {
		dispatch('open', article);
	}
</script>

<li
	on:click={handleClick}
	class="relative cursor-pointer list-none rounded-lg bg-gray-800 p-4 shadow-md transition-all duration-200 hover:bg-gray-700 hover:shadow-xl"
	data-article-id={articleId}
>
	<h3 class="text-left text-lg font-bold text-white">
		<span class="mr-2">{emoji}</span>{displayTitle}
	</h3>
	{#if article.grade}
		<p class="mt-1 text-sm text-green-400">Grade de recommandation : {article.grade}</p>
	{/if}
	<div class="mt-2 flex items-center text-sm text-gray-400">
		{#if article.journal}
		    <span class="mr-1">{article.journal}</span>
        {/if}
		<!-- Optionally add other info like disciplines here -->
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
		<span class="mr-1">Date :</span>
		<span>{displayDate}</span>
	</div>
    <!-- Example: Add a saved icon if needed -->
    <!-- {#if isSaved}
        <span class="absolute top-2 right-2 text-yellow-400">⭐</span>
    {/if} -->
</li>