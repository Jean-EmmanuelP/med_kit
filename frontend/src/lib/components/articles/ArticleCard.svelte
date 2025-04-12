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
	const dispatch = createEventDispatcher<{
		open: Article,
		likeToggle: {
			articleId: number | string;
			currentlyLiked: boolean;
			currentLikeCount: number;
		}
	}>();

	const emoji = $derived(extractTitleEmoji(article.content));
	const displayTitle = $derived(formatTitle(article.title));
	const displayDate = $derived(formatDate(article.published_at));
	const articleId = $derived(getArticleId(article));
	const displayLikeCount = $derived(article.like_count != null ? article.like_count.toLocaleString() : '0');

	function handleCardClick() {
		dispatch('open', article);
	}

	function handleLikeClick(event: MouseEvent) {
		event.stopPropagation();
		dispatch('likeToggle', {
			articleId: articleId,
			currentlyLiked: article.is_liked ?? false,
			currentLikeCount: article.like_count ?? 0
		});
	}
</script>

<li
	on:click={handleCardClick}
	class="relative cursor-pointer list-none rounded-lg bg-gray-800 p-4 pb-8 shadow-md transition-all duration-200 hover:bg-gray-700 hover:shadow-xl"
	data-article-id={articleId}
>
	<!-- Status Icons Container -->
	<div class="absolute top-2 right-2 flex items-center space-x-2">
		<!-- Read Status Eye Icon -->
		<div title={article.is_read ? "Marqué comme lu" : "Non lu"}>
			{#if article.is_read}
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-teal-400">
					<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
					<path fill-rule="evenodd" d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 0 1 0-1.113ZM17.25 12a5.25 5.25 0 1 1-10.5 0 5.25 5.25 0 0 1 10.5 0Z" clip-rule="evenodd" />
				</svg>
			{:else}
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-500">
					<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
					<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
				</svg>
			{/if}
		</div>

		<!-- Like Button/Icon -->
		<button
			type="button"
			aria-label={article.is_liked ? "Retirer des favoris" : "Ajouter aux favoris"}
			title={article.is_liked ? "Retirer des favoris" : "Ajouter aux favoris"}
			on:click={handleLikeClick}
			class="focus:outline-none rounded-full p-0.5 transition-transform duration-100 ease-in-out hover:scale-110 active:scale-95"
		>
			<!-- Single SVG for Heart -->
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class:w-5={true}
				class:h-5={true}
				class:fill-pink-500={article.is_liked}
				class:text-pink-500={article.is_liked}
				class:fill-none={!article.is_liked}
				class:text-gray-500={!article.is_liked}
				class:hover:text-pink-400={!article.is_liked}
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
			</svg>
		</button>
	</div>

	<h3 class="text-left text-lg font-bold text-white pr-16">
		<span class="mr-2">{emoji}</span>{displayTitle}
	</h3>
	{#if article.grade}
		<p class="mt-1 text-sm text-green-400">Grade de recommandation : {article.grade}</p>
	{/if}
	<div class="mt-2 flex items-center text-sm text-gray-400">
		{#if article.journal}
			<span class="mr-1">{article.journal}</span>
		{/if}
	</div>
	<div class="mt-2 flex items-center text-sm text-gray-400">
		<svg class="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
		</svg>
		<span class="mr-1">Date :</span>
		<span>{displayDate}</span>
	</div>

	<!-- Like Count Display -->
	{#if article.like_count != null}
		<div class="absolute bottom-2 right-3 flex items-center space-x-1 text-xs text-gray-400" title="Nombre total de favoris">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="w-3.5 h-3.5 fill-pink-500 text-pink-500"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
			</svg>
			<span>{displayLikeCount}</span>
		</div>
	{/if}
</li>