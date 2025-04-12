<!-- src/lib/components/articles/ArticleImmersiveModal.svelte -->
<script lang="ts">
	import userProfileStore from '$lib/stores/user';
	import {
		type Article,
		extractTitleEmoji,
		formatDate,
		formatTitle,
		getArticleId,
		parseContent
	} from '$lib/utils/articleUtils';
	import { createEventDispatcher } from 'svelte';

	const { article } = $props<{ article: Article | null }>();
	const dispatch = createEventDispatcher<{ close: void }>();

	// Use $derived for computed values based on the 'article' prop
	const emoji = $derived(article ? extractTitleEmoji(article.content) : '📝');
	const displayTitle = $derived(article ? formatTitle(article.title) : '');
	const displayDate = $derived(article ? formatDate(article.published_at) : '');
	const contentSections = $derived(article ? parseContent(article.content) : []);

	// --- Effect to mark article as read when modal opens ---
	$effect(() => {
		const currentArticle = article; // Capture prop value
		const currentUser = $userProfileStore; // Capture store value

		if (currentArticle && currentUser) {
			// Get the numeric article ID
			const articleIdNumber = getArticleId(currentArticle);

			// Ensure ID is a number before proceeding
			if (typeof articleIdNumber === 'number' && !isNaN(articleIdNumber)) {
				console.log(`Modal opened for article ${articleIdNumber}. Marking as read for user ${currentUser.id}...`);

				// Call the API endpoint asynchronously - no need to wait for response usually
				fetch('/api/mark-article-read', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({ articleId: articleIdNumber }),
				})
				.then(async (response) => {
					if (!response.ok) {
						// Log error but don't necessarily block UI
						const errorData = await response.json().catch(() => ({ message: 'Failed to parse error response' }));
						console.error(`Failed to mark article ${articleIdNumber} as read:`, response.status, errorData.message || response.statusText);
					} else {
						console.log(`Article ${articleIdNumber} marked as read successfully.`);
						// Optionally: Update local state immediately if needed for UI feedback
						// (e.g., update a 'isRead' flag on the article object if passed back)
					}
				})
				.catch((error) => {
					// Handle network errors
					console.error(`Network error marking article ${articleIdNumber} as read:`, error);
				});
			} else {
				console.warn('Cannot mark article as read: Invalid article ID.', articleIdNumber);
			}
		}
	});

	function handleClose() {
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			handleClose();
		}
	}
</script>

{#if article}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm"
		on:click|self={handleClose}
		on:keydown={handleKeydown}
		role="dialog"
        aria-modal="true"
        aria-labelledby="immersive-title"
	>
		<div
			class="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-gray-900 p-6 md:p-8 shadow-2xl scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800"
		>
			<button
				class="absolute top-3 right-3 text-3xl text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 rounded-full p-1 leading-none"
				on:click={handleClose}
                aria-label="Fermer la vue détaillée de l'article"
			>
				× <!-- Use HTML entity for '×' -->
			</button>

			<h2 id="immersive-title" class="mb-4 pr-8 text-2xl md:text-3xl font-bold text-white">
				<span class="mr-2">{emoji}</span>{displayTitle}
			</h2>

			{#if article.grade}
				<p class="mb-2 text-sm text-green-400">
					Grade de recommandation : {article.grade}
				</p>
			{/if}

			<div class="mb-4 flex flex-wrap items-center gap-x-4 text-sm text-gray-400">
				{#if article.journal}
				    <span>{article.journal}</span>
                {/if}
				{#if article.journal && displayDate !== 'Non spécifiée' && displayDate !== 'Date invalide'} <span class="text-gray-600">•</span> {/if}
                {#if displayDate !== 'Non spécifiée' && displayDate !== 'Date invalide'}
				    <span>Publié le : {displayDate}</span>
                {/if}
			</div>


			{#each contentSections as section (section.title)}
				<div class="mb-6">
					<h3 class="mb-2 flex items-center text-lg font-semibold text-teal-400">
						<span class="mr-2 text-xl">{section.emoji}</span>
						{section.title}
					</h3>
					<ul class="ml-4 list-disc space-y-1.5 pl-4 text-gray-300 marker:text-teal-500">
						{#each section.content as paragraph (paragraph)}
							<li>{paragraph}</li>
						{/each}
					</ul>
				</div>
			{:else}
                <p class="text-gray-400">{article.content || "Contenu non disponible."}</p>
            {/each}

			{#if article.link}
                <div class="mt-6 border-t border-gray-700 pt-4">
				    <a href={article.link} target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 text-teal-400 underline hover:text-teal-300 transition-colors duration-200">
					    Accéder à l'article original
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                        </svg>
				    </a>
                </div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #1f2937; /* thumb track */
	}

	.scrollbar-thin::-webkit-scrollbar {
		width: 8px;
		height: 8px;
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