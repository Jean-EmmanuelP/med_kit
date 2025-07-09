<!-- src/lib/components/articles/ArticleCard.svelte -->
<script lang="ts">
	import userProfileStore from '$lib/stores/user';
	import {
		type Article,
		extractTitleEmoji,
		formatDate,
		formatTitle,
		getArticleId
	} from '$lib/utils/articleUtils';
	import { createEventDispatcher } from 'svelte';

	const {
		article,
		isSubscribed = false,
		onEditClick = null
	} = $props<{
		article: Article;
		isSubscribed?: boolean;
		onEditClick?: ((article: Article) => void) | null;
	}>();
	
	const dispatch = createEventDispatcher<{
		open: Article,
		likeToggle: { // Heart icon (Saved/Favorite)
			articleId: number | string;
			currentlyLiked: boolean;
			currentLikeCount: number;
		},
		toggleRead: Article, // Eye icon
		thumbsUpToggle: { // Thumbs up icon
			articleId: number | string;
			currentlyThumbedUp: boolean;
			currentThumbsUpCount: number;
		}
	}>();

	const emoji = $derived(article.is_recommandation ? '🌟' : extractTitleEmoji(article.content));
	const displayTitle = $derived(formatTitle(article.title));
	const displayDate = $derived(formatDate(article.published_at));
	const articleId = $derived(getArticleId(article));
	
	// Format counts
	const displayLikeCount = $derived(article.like_count != null ? article.like_count.toLocaleString() : '0');
	const displayReadCount = $derived(article.read_count != null ? article.read_count.toLocaleString() : '0');
	const displayThumbsUpCount = $derived(article.thumbs_up_count != null ? article.thumbs_up_count.toLocaleString() : '0');

	// Check if user is admin
	const isAdmin = $derived($userProfileStore?.is_admin ?? false);

	function handleCardClick() {
		dispatch('open', article);
	}

	function handleLikeClick() { // Heart toggle
		dispatch('likeToggle', {
			articleId: articleId,
			currentlyLiked: article.is_liked ?? false,
			currentLikeCount: article.like_count ?? 0
		});
	}

	function handleToggleReadClick() { // Eye toggle
		console.log(`Toggle Read button clicked for article: ${articleId}, current state: ${article.is_read}`);
		dispatch('toggleRead', article);
	}

	function handleThumbsUpClick() {
		dispatch('thumbsUpToggle', {
			articleId: articleId,
			currentlyThumbedUp: article.is_thumbed_up ?? false,
			currentThumbsUpCount: article.thumbs_up_count ?? 0
		});
	}

	// Handler for edit button
	function handleEditClick() {
		console.log('Edit button clicked for article:', articleId);
		console.log('onEditClick function:', onEditClick);
		if (onEditClick) {
			onEditClick(article);
		} else {
			console.warn('onEditClick function not provided');
		}
	}
</script>

<li
	onclick={handleCardClick}
	class="group relative rounded-lg border p-4 transition-all duration-300 {!isSubscribed ? 'cursor-pointer' : ''} {article.is_recommandation ? 'border-yellow-400/50 bg-yellow-50 hover:border-yellow-400 hover:bg-yellow-100/80' : 'border-gray-700 bg-gray-800 hover:border-teal-500/50 hover:bg-gray-700/50'}"
	data-article-id={articleId}
>
	<!-- Status Icons Container (Top Right) -->
	<div class="absolute top-2 right-2 flex items-center space-x-2">
		<!-- Edit Button (show only if user is admin AND onEditClick function is provided) -->
		{#if isAdmin && onEditClick}
			<button
				type="button"
				aria-label="Modifier l'article"
				title="Modifier l'article"
				onclick={(e) => {
					e.stopPropagation();
					handleEditClick();
				}}
				class="focus:outline-none rounded-full p-0.5 transition-colors duration-150 hover:bg-gray-600 focus-visible:ring-2 focus-visible:ring-yellow-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
			>
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-yellow-400 hover:text-yellow-300 pointer-events-none">
					<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
				</svg>
			</button>
		{/if}

		<!-- Read Status Eye Icon / Button -->
		<button
			type="button"
			aria-label={article.is_read ? "Marquer comme non lu" : "Marquer comme lu"}
			title={article.is_read ? "Marquer comme non lu" : "Marquer comme lu"}
			onclick={(e) => {
				e.stopPropagation();
				handleToggleReadClick();
			}}
			class="focus:outline-none rounded-full p-0.5 transition-colors duration-150 hover:bg-gray-600 focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
		>
			{#if article.is_read}
				<!-- Read Icon -->
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-teal-400 pointer-events-none">
					<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
					<path fill-rule="evenodd" d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 0 1 0-1.113ZM17.25 12a5.25 5.25 0 1 1-10.5 0 5.25 5.25 0 0 1 10.5 0Z" clip-rule="evenodd" />
				</svg>
			{:else}
				<!-- Unread Icon -->
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-500 pointer-events-none">
					<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
					<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
				</svg>
			{/if}
		</button>

        <!-- Thumbs Up Button/Icon -->
		<button
			type="button"
			aria-label={article.is_thumbed_up ? "Retirer le pouce levé" : "Mettre un pouce levé"}
			title={article.is_thumbed_up ? "Retirer le pouce levé" : "Mettre un pouce levé"}
			onclick={(e) => {
				e.stopPropagation();
				handleThumbsUpClick();
			}}
			class="focus:outline-none rounded-full p-0.5 transition-transform duration-100 ease-in-out hover:scale-110 active:scale-95 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
		>
			<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"
                 class="w-5 h-5 pointer-events-none {article.is_thumbed_up ? 'fill-blue-500 text-blue-500' : 'fill-gray-500 text-gray-500 hover:fill-blue-400 hover:text-blue-400'}">
                <path d="M7.493 19.5c-.425 0-.82-.236-.975-.632A7.48 7.48 0 0 1 6 15.125c0-1.75.599-3.358 1.602-4.634.151-.192.373-.309.6-.397.473-.183.89-.514 1.212-.924a9.042 9.042 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23h-.777ZM2.331 10.727a11.969 11.969 0 0 0-.831 4.398 12 12 0 0 0 .52 3.507C2.28 19.482 3.105 20 3.994 20H4.9c.445 0 .72-.498.523-.898a8.963 8.963 0 0 1-.924-3.977c0-1.708.476-3.305 1.302-4.666.245-.403-.028-.959-.5-.959H4.25c-.832 0-1.612.453-1.918 1.227Z" />
            </svg>
		</button>

		<!-- Like (Heart) Button/Icon -->
		<button
			type="button"
			aria-label={article.is_liked ? "Retirer des favoris" : "Ajouter aux favoris"}
			title={article.is_liked ? "Retirer des favoris" : "Ajouter aux favoris"}
			onclick={(e) => {
				e.stopPropagation();
				handleLikeClick();
			}}
			class="focus:outline-none rounded-full p-0.5 transition-transform duration-100 ease-in-out hover:scale-110 active:scale-95 focus-visible:ring-2 focus-visible:ring-pink-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
		>
			<!-- Single SVG for Heart -->
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="w-5 h-5 pointer-events-none {article.is_liked ? 'fill-pink-500 text-pink-500' : 'fill-none text-gray-500 hover:text-pink-400'}"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
			</svg>
		</button>
	</div>

	<h3 class="text-left text-lg font-bold pr-32 {article.is_recommandation ? 'text-gray-900' : 'text-white'}"> <!-- Increased pr to avoid overlap with edit button -->
		<span class="mr-2">{emoji}</span>{displayTitle}
	</h3>
	{#if article.is_recommandation}
		<p class="mt-1 text-sm font-semibold text-green-500">Recommandation scientifique</p>
	{:else if article.grade}
		<p class="mt-1 text-sm {article.grade == 'A' ? 'text-green-500' : article.grade == 'B' ? 'text-yellow-400' : article.grade == 'C' ? 'text-orange-400' : 'text-red-400'}">Grade de recommandation : {article.grade}</p>
	{/if}
	<div class="mt-2 flex items-center text-sm {article.is_recommandation ? 'text-gray-600' : 'text-gray-400'}">
		{#if article.journal}
			<span class="mr-1">{article.journal}</span>
		{/if}
	</div>
	<div class="mt-2 flex items-center text-sm {article.is_recommandation ? 'text-gray-600' : 'text-gray-400'}">
		<svg class="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
		</svg>
		<span class="mr-1">Date :</span>
		<span>{displayDate}</span>
	</div>

	<!-- Counts Display (Bottom Right) -->
	<div class="absolute bottom-2 right-3 flex items-center space-x-3 text-xs {article.is_recommandation ? 'text-gray-600' : 'text-gray-400'}">
		{#if article.read_count != null}
			<div class="flex items-center space-x-1" title="Nombre total de lectures">
				<!-- Use the filled eye icon (teal color) -->
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 text-teal-400">
					<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
					<path fill-rule="evenodd" d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 0 1 0-1.113ZM17.25 12a5.25 5.25 0 1 1-10.5 0 5.25 5.25 0 0 1 10.5 0Z" clip-rule="evenodd" />
				</svg>
				<span>{displayReadCount}</span>
			</div>
		{/if}

        <!-- Thumbs Up Count Display -->
		{#if article.thumbs_up_count != null}
			<div class="flex items-center space-x-1" title="Nombre total de pouces levés">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3.5 h-3.5 text-blue-500">
                    <path d="M7.493 19.5c-.425 0-.82-.236-.975-.632A7.48 7.48 0 0 1 6 15.125c0-1.75.599-3.358 1.602-4.634.151-.192.373-.309.6-.397.473-.183.89-.514 1.212-.924a9.042 9.042 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23h-.777ZM2.331 10.727a11.969 11.969 0 0 0-.831 4.398 12 12 0 0 0 .52 3.507C2.28 19.482 3.105 20 3.994 20H4.9c.445 0 .72-.498.523-.898a8.963 8.963 0 0 1-.924-3.977c0-1.708.476-3.305 1.302-4.666.245-.403-.028-.959-.5-.959H4.25c-.832 0-1.612.453-1.918 1.227Z" />
                </svg>
				<span>{displayThumbsUpCount}</span>
			</div>
		{/if}

		{#if article.like_count != null}
			<div class="flex items-center space-x-1" title="Nombre total de favoris">
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
	</div>
</li>