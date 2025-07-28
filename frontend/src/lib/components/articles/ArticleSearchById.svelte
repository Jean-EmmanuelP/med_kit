<!-- src/lib/components/articles/ArticleSearchById.svelte -->
<script lang="ts">
	import type { Article } from '$lib/utils/articleUtils';
	import userProfileStore from '$lib/stores/user';

	const {
		onArticleFound = null as ((article: Article) => void) | null
	} = $props<{
		onArticleFound?: ((article: Article) => void) | null;
	}>();

	// State for article search by ID
	let searchArticleId = $state('');
	let isSearching = $state(false);
	let searchError: string | null = $state(null);

	// Check if user is admin
	const isAdmin = $derived($userProfileStore?.is_admin ?? false);

	// Function to search and edit article by ID
	async function searchAndEditArticle() {
		if (!searchArticleId.trim()) return;

		isSearching = true;
		searchError = null;

		try {
			const response = await fetch(`/api/get-article/${searchArticleId.trim()}`);
			if (!response.ok) {
				throw new Error('Article non trouvé');
			}
			const articleData = await response.json();
			
			if (onArticleFound) {
				onArticleFound(articleData);
			}
			
			searchArticleId = '';
		} catch (error: any) {
			console.error('Error fetching article:', error);
			searchError = error.message || 'Erreur lors de la recherche de l\'article';
		} finally {
			isSearching = false;
		}
	}
</script>

{#if isAdmin}
	<div class="bg-gray-900 px-4 py-6 border-b border-gray-800">
		<div class="mx-auto max-w-4xl">
			<div class="mb-4">
				<h3 class="text-lg font-semibold text-white mb-2">Recherche d'article par ID</h3>
				<p class="text-sm text-gray-400">Entrez l'ID d'un article pour le modifier directement</p>
			</div>
			
			<div class="flex gap-3 items-center">
				<div class="flex-1">
					<input
						type="text"
						bind:value={searchArticleId}
						placeholder="Entrez l'ID de l'article à modifier..."
						class="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-teal-500 focus:border-transparent"
						onkeydown={(e) => e.key === 'Enter' && searchAndEditArticle()}
					/>
					{#if searchError}
						<p class="mt-1 text-xs text-red-400">{searchError}</p>
					{/if}
				</div>
				<button
					onclick={searchAndEditArticle}
					disabled={isSearching || !searchArticleId.trim()}
					class="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 text-sm"
				>
					{#if isSearching}
						<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
						</svg>
						Recherche...
					{:else}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
						</svg>
						Modifier
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if} 