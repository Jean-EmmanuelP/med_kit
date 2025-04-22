<!-- src/lib/components/articles/ArticleImmersiveModal.svelte -->
<script lang="ts">
	import userProfileStore from '$lib/stores/user';
	import {
		type Article,
		extractTitleEmoji,
		formatDate,
		formatTitle,
		getArticleId,
		parseContent,
        type ContentSection // Make sure ContentSection is exported or defined here
	} from '$lib/utils/articleUtils';
	import { createEventDispatcher, tick } from 'svelte';
    import { Copy, Check } from 'lucide-svelte'; // Import icons

	const { article } = $props<{ article: Article | null }>();
	const dispatch = createEventDispatcher<{ close: void }>();

	// State for copy button feedback
	let copyStatus = $state<'idle' | 'copied' | 'error'>('idle');
	let copyTimeoutId: ReturnType<typeof setTimeout> | null = null;

	// Use $derived for computed values based on the 'article' prop
	const emoji = $derived(article ? extractTitleEmoji(article.content) : '📝');
	const displayTitle = $derived(article ? formatTitle(article.title) : '');
	const displayDate = $derived(article ? formatDate(article.published_at) : '');
	const contentSections = $derived(article ? parseContent(article.content) : []);
	const articleId = $derived(article ? getArticleId(article) : null);

	// --- Effect to mark article as read ---
	$effect(() => {
		const currentArticle = article;
		const currentUser = $userProfileStore;

		if (currentArticle && currentUser && articleId) {
			const articleIdNumber = typeof articleId === 'string' ? parseInt(articleId, 10) : articleId;

			if (!isNaN(articleIdNumber)) {
				console.log(`Modal opened for article ${articleIdNumber}. Marking as read for user ${currentUser.id}...`);
				// Fire-and-forget API call
				fetch('/api/mark-article-read', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ articleId: articleIdNumber }),
				})
				.then(async (response) => {
					if (!response.ok) {
						const errorData = await response.json().catch(() => ({ message: 'Failed to parse error response' }));
						console.error(`Failed to mark article ${articleIdNumber} as read:`, response.status, errorData.message || response.statusText);
					} else {
						console.log(`Article ${articleIdNumber} marked as read successfully.`);
					}
				})
				.catch((error) => {
					console.error(`Network error marking article ${articleIdNumber} as read:`, error);
				});
			} else {
				console.warn('Cannot mark article as read: Invalid article ID.', articleId);
			}
		}

        // Cleanup previous timeout if article changes or modal closes
		return () => {
			if (copyTimeoutId) {
				clearTimeout(copyTimeoutId);
                copyStatus = 'idle';
			}
		};
	});

	function handleClose() {
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			handleClose();
		}
	}

    // --- Function to copy content ---
    async function handleCopyContent() {
        if (!article || copyStatus === 'copied') return; // Don't do anything if already copied recently

        // 1. Assemble the text content
        let textToCopy = '';
        textToCopy += `${emoji} ${displayTitle}\n\n`; // Title

        // Metadata
        if (article.journal) textToCopy += `Journal: ${article.journal}\n`;
        if (displayDate !== 'Non spécifiée' && displayDate !== 'Date invalide') textToCopy += `Publié le: ${displayDate}\n`;
        if (article.grade) textToCopy += `Grade: ${article.grade}\n`;
        textToCopy += `\n---\n\n`;

        // Content Sections
        contentSections.forEach(section => {
            textToCopy += `${section.emoji} ${section.title}\n`;
            section.content.forEach(paragraph => {
                textToCopy += `- ${paragraph}\n`;
            });
            textToCopy += '\n';
        });

        // Fallback for non-sectioned content
        if (contentSections.length === 0 && article.content) {
             textToCopy += `${article.content}\n\n`;
        }

        // Original Link
        if (article.link) {
            textToCopy += `---\nLien original: ${article.link}\n`;
        }

        // 2. Use Clipboard API
        try {
            await navigator.clipboard.writeText(textToCopy.trim());
            copyStatus = 'copied';
            console.log('Article content copied to clipboard');

            // Reset status after a delay
            if (copyTimeoutId) clearTimeout(copyTimeoutId); // Clear previous timeout if any
            copyTimeoutId = setTimeout(() => {
                copyStatus = 'idle';
                copyTimeoutId = null;
            }, 2000); // Reset after 2 seconds

        } catch (err) {
            copyStatus = 'error';
            console.error('Failed to copy article content:', err);
            // Optionally show an error message to the user
             if (copyTimeoutId) clearTimeout(copyTimeoutId);
             copyTimeoutId = setTimeout(() => {
                copyStatus = 'idle';
                copyTimeoutId = null;
            }, 3000); // Show error longer
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
			class="modal-content relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-gray-900 p-6 md:p-8 shadow-2xl scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800"
		>
            <!-- Action Buttons Container -->
            <div class="absolute top-3 right-3 flex items-center space-x-2">
                <!-- Copy Button -->
                <button
                    type="button"
                    class="text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 rounded-full p-1.5 transition-colors duration-150"
                    on:click={handleCopyContent}
                    aria-label="Copier le contenu de l'article"
                    title="Copier le contenu"
                    disabled={copyStatus === 'copied'}
                >
                    {#if copyStatus === 'copied'}
                        <Check class="w-5 h-5 text-green-500" />
                    {:else if copyStatus === 'error'}
                         <Copy class="w-5 h-5 text-red-500" /> <!-- Or an error icon -->
                    {:else}
                        <Copy class="w-5 h-5" />
                    {/if}
                </button>

                <!-- Close Button -->
                <button
                    type="button"
                    class="text-3xl text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 rounded-full p-1 leading-none"
                    on:click={handleClose}
                    aria-label="Fermer la vue détaillée de l'article"
                >
                    ×
                </button>
            </div>


			<h2 id="immersive-title" class="mb-4 pr-16 text-2xl md:text-3xl font-bold text-white"> <!-- Increased pr for buttons -->
				<span class="mr-2">{emoji}</span>{displayTitle}
			</h2>

			{#if article.grade}
				<p class="mb-2 text-sm {article.grade == 'A' ? 'text-green-500' : article.grade == 'B' ? 'text-yellow-400' : article.grade == 'C' ? 'text-orange-400' : 'text-red-400'}">
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
                <!-- Metadata Icons -->
                {#if article.read_count != null || article.thumbs_up_count != null || article.like_count != null}
                    <span class="text-gray-600">•</span>
                    <div class="flex items-center space-x-3">
                        {#if article.read_count != null}
                            <div class="flex items-center space-x-1" title="Nombre total de lectures">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 text-teal-400">
                                    <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
                                    <path fill-rule="evenodd" d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 0 1 0-1.113ZM17.25 12a5.25 5.25 0 1 1-10.5 0 5.25 5.25 0 0 1 10.5 0Z" clip-rule="evenodd" />
                                </svg>
                                <span>{article.read_count.toLocaleString()}</span>
                            </div>
                        {/if}
                        {#if article.thumbs_up_count != null}
                            <div class="flex items-center space-x-1" title="Nombre total de pouces levés">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3.5 h-3.5 text-blue-500">
                                    <path d="M7.493 19.5c-.425 0-.82-.236-.975-.632A7.48 7.48 0 0 1 6 15.125c0-1.75.599-3.358 1.602-4.634.151-.192.373-.309.6-.397.473-.183.89-.514 1.212-.924a9.042 9.042 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23h-.777ZM2.331 10.727a11.969 11.969 0 0 0-.831 4.398 12 12 0 0 0 .52 3.507C2.28 19.482 3.105 20 3.994 20H4.9c.445 0 .72-.498.523-.898a8.963 8.963 0 0 1-.924-3.977c0-1.708.476-3.305 1.302-4.666.245-.403-.028-.959-.5-.959H4.25c-.832 0-1.612.453-1.918 1.227Z" />
                                </svg>
                                <span>{article.thumbs_up_count.toLocaleString()}</span>
                            </div>
                        {/if}
                        {#if article.like_count != null}
                            <div class="flex items-center space-x-1" title="Nombre total de favoris">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5 fill-pink-500 text-pink-500">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
                                </svg>
                                <span>{article.like_count.toLocaleString()}</span>
                            </div>
                        {/if}
                    </div>
                {/if}
			</div>

			{#each contentSections as section (section.title)}
				<div class="mb-6">
					<h3 class="mb-2 flex items-center text-lg font-semibold text-teal-400">
						<span class="mr-2 text-xl">{section.emoji}</span>
						{section.title}
					</h3>
					<ul class="section-content ml-4 list-disc space-y-1.5 pl-4 text-gray-300 marker:text-teal-500">
						{#each section.content as paragraph (paragraph)}
							<li class="selectable-text">{paragraph}</li>
						{/each}
					</ul>
				</div>
			{:else}
                <p class="selectable-text text-gray-400">{article.content || "Contenu non disponible."}</p>
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
    /* Apply selection styles to specific elements */
    .modal-content h2,
    .modal-content h3,
    .modal-content p,
    .modal-content li,
    .modal-content span:not(.mr-2):not(.text-gray-600), /* Avoid selecting separators */
    .modal-content a
    {
        user-select: text !important;
        -webkit-user-select: text !important;
        cursor: text;
    }
    /* Or using the added class */
     .selectable-text {
        user-select: text !important;
        -webkit-user-select: text !important;
        cursor: text;
    }

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