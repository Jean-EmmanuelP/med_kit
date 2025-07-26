<!-- Dashboard page with article editing functionality -->
<script lang="ts">
	import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
	import { supabase } from '$lib/supabase';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';

	// Get data loaded by +page.server.ts (list of all disciplines)
	const { data } = $props<{ data: any }>();

	// Prepare filters from all available disciplines
	const allDisciplines = $derived(data.disciplines || []);
	const filterOptions = $derived([...allDisciplines]
		.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }))
		.map((discipline: { name: string }) => ({
			value: discipline.name,
			label: discipline.name
		})));

	// Determine initial filter (first discipline in the sorted list)
	const initialFilter = $derived(filterOptions[0]?.value ?? null);

	// State for edit modal
	let showEditModal = $state(false);
	let editingArticle: Article | null = $state(null);
	let editTitle = $state('');
	let editContent = $state('');
	let isUpdating = $state(false);
	let updateError: string | null = $state(null);

	// State for confirmation modal
	let showConfirmationModal = $state(false);

	// State for categories management
	let allAvailableDisciplines = $state<{id: number, name: string, sub_disciplines: {id: number, name: string}[]}[]>([]);
	let selectedDisciplineIds = $state<number[]>([]);
	let selectedSubDisciplineIds = $state<number[]>([]);
	let currentArticleCategories = $state<{discipline_ids: number[], sub_discipline_ids: number[]}>({discipline_ids: [], sub_discipline_ids: []});
	let isLoadingCategories = $state(false);
	let categoryError = $state<string | null>(null);
	let isUpdatingCategories = $state(false);

	// State for article search by ID
	let searchArticleId = $state('');
	let isSearching = $state(false);
	let searchError: string | null = $state(null);

	// Function to load all available disciplines with sub-disciplines
	async function loadAllDisciplines() {
		try {
			const { data: disciplinesData, error } = await supabase
				.from('disciplines')
				.select(`
					id,
					name,
					sub_disciplines (
						id,
						name
					)
				`)
				.order('name');

			if (error) throw error;
			allAvailableDisciplines = disciplinesData || [];
		} catch (error: any) {
			console.error('Error loading disciplines:', error);
			categoryError = 'Erreur lors du chargement des disciplines';
		}
	}

	// Function to load current article categories
	async function loadArticleCategories(articleId: string | number) {
		if (!articleId) return;
		
		isLoadingCategories = true;
		categoryError = null;

		try {
			const response = await fetch(`/api/get-article-categories/${articleId}`);
			if (!response.ok) {
				throw new Error('Erreur lors du chargement des catégories');
			}
			
			const data = await response.json();
			currentArticleCategories = {
				discipline_ids: data.discipline_ids || [],
				sub_discipline_ids: data.sub_discipline_ids || []
			};
			
			// Set selected categories
			selectedDisciplineIds = [...data.discipline_ids];
			selectedSubDisciplineIds = [...data.sub_discipline_ids];
			
		} catch (error: any) {
			console.error('Error loading article categories:', error);
			categoryError = error.message || 'Erreur lors du chargement des catégories';
		} finally {
			isLoadingCategories = false;
		}
	}

	// Function to handle category updates (Svelte 5 runes version)
	async function handleUpdateCategories(articleId: string | number, disciplineIds: number[], subDisciplineIds: number[], mode: 'add' | 'replace' = 'replace') {
		try {
			isUpdatingCategories = true;
			categoryError = null;

			// If mode is "add", merge with existing categories
			let finalDisciplineIds = disciplineIds;
			let finalSubDisciplineIds = subDisciplineIds;
			
			if (mode === 'add' && currentArticleCategories) {
				// Merge with existing categories
				finalDisciplineIds = [...new Set([...currentArticleCategories.discipline_ids, ...disciplineIds])];
				finalSubDisciplineIds = [...new Set([...currentArticleCategories.sub_discipline_ids, ...subDisciplineIds])];
			}
			
			const response = await fetch('/api/update-article-categories', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					article_id: articleId,
					discipline_ids: finalDisciplineIds,
					sub_discipline_ids: finalSubDisciplineIds,
					mode
				})
			});
			
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.error || 'Erreur lors de la mise à jour');
			}

			const data = await response.json();
			
			// Update local state
			currentArticleCategories = {
				discipline_ids: data.discipline_ids,
				sub_discipline_ids: data.sub_discipline_ids
			};
			
			selectedDisciplineIds = [...data.discipline_ids];
			selectedSubDisciplineIds = [...data.sub_discipline_ids];
			
			console.log('Categories updated successfully');
			
		} catch (error: any) {
			console.error('Error updating categories:', error);
			categoryError = error.message || 'Échec de la mise à jour des catégories';
		} finally {
			isUpdatingCategories = false;
		}
	}

	// Function to toggle discipline selection
	function toggleDiscipline(disciplineId: number) {
		if (selectedDisciplineIds.includes(disciplineId)) {
			selectedDisciplineIds = selectedDisciplineIds.filter(id => id !== disciplineId);
		} else {
			selectedDisciplineIds = [...selectedDisciplineIds, disciplineId];
		}
	}

	// Function to toggle sub-discipline selection
	function toggleSubDiscipline(subDisciplineId: number) {
		if (selectedSubDisciplineIds.includes(subDisciplineId)) {
			selectedSubDisciplineIds = selectedSubDisciplineIds.filter(id => id !== subDisciplineId);
		} else {
			selectedSubDisciplineIds = [...selectedSubDisciplineIds, subDisciplineId];
		}
	}

	// Function to apply category changes
	async function applyCategoryChanges() {
		if (!editingArticle) return;
		
		const articleId = getArticleId(editingArticle);
		await handleUpdateCategories(articleId, selectedDisciplineIds, selectedSubDisciplineIds, 'replace');
	}

	// Function to open edit modal
	function openEditModal(article: Article) {
		editingArticle = article;
		editTitle = article.title;
		editContent = article.content;
		showEditModal = true;
		updateError = null;
		categoryError = null;
		
		// Load categories for this article
		const articleId = getArticleId(article);
		loadArticleCategories(articleId);
	}

	// Function to close edit modal
	function closeEditModal() {
		showEditModal = false;
		editingArticle = null;
		editTitle = '';
		editContent = '';
		updateError = null;
		categoryError = null;
		selectedDisciplineIds = [];
		selectedSubDisciplineIds = [];
		currentArticleCategories = {discipline_ids: [], sub_discipline_ids: []};
	}

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
			openEditModal(articleData);
			searchArticleId = '';
		} catch (error: any) {
			console.error('Error fetching article:', error);
			searchError = error.message || 'Erreur lors de la recherche de l\'article';
		} finally {
			isSearching = false;
		}
	}

	// Function to save article changes
	async function saveArticleChanges() {
		if (!editingArticle || !$userProfileStore) return;

		// Show confirmation modal instead of directly saving
		showConfirmationModal = true;
	}

	// Function to handle confirmation and actually save
	async function confirmSaveChanges() {
		if (!editingArticle || !$userProfileStore) return;

		showConfirmationModal = false;
		isUpdating = true;
		updateError = null;

		try {
			const articleId = getArticleId(editingArticle);
			const { error } = await supabase
				.from('articles')
				.update({
					title: editTitle.trim(),
					content: editContent.trim(),
					updated_at: new Date().toISOString()
				})
				.eq('id', articleId);

			if (error) {
				throw error;
			}

			// Close modal and refresh the page to show updated content
			closeEditModal();
			window.location.reload();

		} catch (error: any) {
			console.error('Error updating article:', error);
			updateError = error.message || 'Erreur lors de la mise à jour de l\'article';
		} finally {
			isUpdating = false;
		}
	}

	// Function to cancel confirmation
	function cancelSaveChanges() {
		showConfirmationModal = false;
	}

	// Effect to load disciplines on mount
	$effect(() => {
		loadAllDisciplines();
	});
</script>

<div class="min-h-screen bg-black text-white">
	<!-- Simplified Dashboard Header -->
	<div class="bg-gray-900 px-4 py-8 border-b border-gray-800">
		<div class="mx-auto max-w-4xl">
			<div class="flex items-center justify-between mb-4">
				<div>
					<h1 class="text-xl font-bold text-white">Dashboard Admin</h1>
				</div>
				<div class="flex items-center gap-3">
					<!-- User Management Link - Only for super admins -->
					{#if $userProfileStore?.has_all_power}
						<a 
							href="/dashboard/users" 
							class="inline-flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors text-sm font-medium"
						>
							<svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
							</svg>
							Utilisateurs
						</a>
					{/if}
					<div class="text-xs text-gray-400">
						{$userProfileStore?.first_name}
						{#if $userProfileStore?.has_all_power}
							<span class="ml-1 text-red-400 font-medium">(Super Admin)</span>
						{:else if $userProfileStore?.is_admin}
							<span class="ml-1 text-green-400 font-medium">(Admin)</span>
						{/if}
					</div>
				</div>
			</div>
			
			<!-- Compact Article Search -->
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

	<!-- Article List with Browse Functionality -->
	<div class="px-4 pb-6">
		<div class="mx-auto max-w-4xl">
			<div class="mb-4 mt-6">
				<h2 class="text-lg font-semibold text-white mb-1">Articles disponibles</h2>
				<p class="text-sm text-gray-400">Parcourez et gérez vos articles ci-dessous</p>
			</div>
			
			<!-- Use existing ArticleListView component -->
			<ArticleListView
				pageTitle="Articles disponibles"
				filters={filterOptions}
				initialFilterValue={null}
				filterSelectLabel="Spécialités"
				subDisciplineFetchMode="public"
				showSignupPromptProp={false}
				enableSearch={true}
				isSubscribed={data.isSubscribed}
				onEditClick={openEditModal}
				showAllCategoriesOption={true}
				enableRecommendationsToggle={true}
			/>
		</div>
	</div>
</div>

<!-- Edit Modal -->
{#if showEditModal && editingArticle}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
		<div class="w-full max-w-[80vw] max-h-[90vh] bg-gray-900 rounded-lg shadow-xl overflow-hidden">
			<!-- Modal Header -->
			<div class="flex items-center justify-between bg-gray-800 px-8 py-5">
				<h2 class="text-2xl font-semibold text-white">Modifier l'article</h2>
				<button
					onclick={closeEditModal}
					class="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-700"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			<!-- Modal Content -->
			<div class="p-8 overflow-y-auto max-h-[calc(90vh-180px)]">
				{#if updateError}
					<div class="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300">
						<p><strong>Erreur :</strong> {updateError}</p>
					</div>
				{/if}

				<div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
					<!-- Left Column: Article Content -->
					<div class="space-y-6">
						<!-- Title Field -->
						<div>
							<label for="edit-title" class="block text-lg font-medium text-gray-300 mb-3">
								Titre de l'article
							</label>
							<input
								id="edit-title"
								type="text"
								bind:value={editTitle}
								class="w-full px-5 py-4 text-lg bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-colors"
								placeholder="Titre de l'article..."
							/>
						</div>

						<!-- Content Field -->
						<div class="flex-1">
							<label for="edit-content" class="block text-lg font-medium text-gray-300 mb-3">
								Contenu de l'article
							</label>
							<textarea
								id="edit-content"
								bind:value={editContent}
								rows="25"
								class="w-full px-5 py-4 text-base bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none font-mono leading-relaxed"
								placeholder="Contenu de l'article..."
							></textarea>
						</div>
					</div>

					<!-- Right Column: Categories and Info -->
					<div class="space-y-6">
						<!-- Categories Management Section -->
						<div class="bg-gray-800 rounded-lg p-6">
							<div class="flex items-center justify-between mb-6">
								<h3 class="text-xl font-medium text-white">Catégories de l'article</h3>
								{#if isLoadingCategories}
									<div class="flex items-center gap-2 text-gray-400">
										<svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
										</svg>
										<span class="text-sm">Chargement...</span>
									</div>
								{/if}
							</div>

							{#if categoryError}
								<div class="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
									{categoryError}
								</div>
							{/if}

							<div class="space-y-6">
								<!-- Disciplines Selection -->
								<div>
									<h4 class="text-base font-medium text-gray-300 mb-4">Disciplines principales</h4>
									<div class="max-h-56 overflow-y-auto space-y-2 border border-gray-700 rounded-lg p-4 bg-gray-900">
										{#each allAvailableDisciplines as discipline (discipline.id)}
											<label class="flex items-center gap-3 hover:bg-gray-800 p-3 rounded-lg cursor-pointer transition-colors">
												<input
													type="checkbox"
													checked={selectedDisciplineIds.includes(discipline.id)}
													onchange={() => toggleDiscipline(discipline.id)}
													class="w-5 h-5 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 focus:ring-2"
												/>
												<span class="text-base text-gray-300">{discipline.name}</span>
											</label>
										{/each}
									</div>
								</div>

								<!-- Sub-disciplines Selection -->
								<div>
									<h4 class="text-base font-medium text-gray-300 mb-4">Sous-disciplines</h4>
									<div class="max-h-56 overflow-y-auto space-y-4 border border-gray-700 rounded-lg p-4 bg-gray-900">
										{#each allAvailableDisciplines as discipline (discipline.id)}
											{#if discipline.sub_disciplines && discipline.sub_disciplines.length > 0}
												<div class="mb-4">
													<div class="text-sm font-medium text-gray-400 mb-3 px-2">{discipline.name}</div>
													<div class="space-y-2 pl-4 border-l-2 border-gray-700">
														{#each discipline.sub_disciplines as subDiscipline (subDiscipline.id)}
															<label class="flex items-center gap-3 hover:bg-gray-800 p-2 rounded cursor-pointer transition-colors">
																<input
																	type="checkbox"
																	checked={selectedSubDisciplineIds.includes(subDiscipline.id)}
																	onchange={() => toggleSubDiscipline(subDiscipline.id)}
																	class="w-4 h-4 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 focus:ring-2"
																/>
																<span class="text-sm text-gray-300">{subDiscipline.name}</span>
															</label>
														{/each}
													</div>
												</div>
											{/if}
										{/each}
									</div>
								</div>
							</div>

							<!-- Current Categories Display -->
							{#if currentArticleCategories.discipline_ids.length > 0 || currentArticleCategories.sub_discipline_ids.length > 0}
								<div class="mt-6 p-4 bg-gray-700 rounded-lg">
									<div class="text-sm font-medium text-gray-400 mb-3">Catégories actuelles de l'article :</div>
									<div class="flex flex-wrap gap-2">
										{#each currentArticleCategories.discipline_ids as disciplineId}
											{@const discipline = allAvailableDisciplines.find(d => d.id === disciplineId)}
											{#if discipline}
												<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-900/50 text-blue-300 border border-blue-700">
													{discipline.name}
												</span>
											{/if}
										{/each}
										{#each currentArticleCategories.sub_discipline_ids as subDisciplineId}
											{@const subDiscipline = allAvailableDisciplines.flatMap(d => d.sub_disciplines || []).find(s => s.id === subDisciplineId)}
											{#if subDiscipline}
												<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-900/50 text-green-300 border border-green-700">
													{subDiscipline.name}
												</span>
											{/if}
										{/each}
									</div>
								</div>
							{/if}

							<!-- Apply Categories Button -->
							<div class="mt-6 flex justify-end">
								<button
									onclick={applyCategoryChanges}
									disabled={isUpdatingCategories}
									class="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-base font-medium"
								>
									{#if isUpdatingCategories}
										<svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
										</svg>
										Mise à jour...
									{:else}
										Appliquer les catégories
									{/if}
								</button>
							</div>
						</div>

						<!-- Article Info -->
						<div class="bg-gray-800 rounded-lg p-6">
							<h3 class="text-xl font-medium text-white mb-4">Informations de l'article</h3>
							<div class="grid grid-cols-1 gap-4 text-base">
								<div class="flex justify-between items-center py-2 border-b border-gray-700">
									<span class="text-gray-400 font-medium">ID:</span>
									<span class="text-white font-mono">{getArticleId(editingArticle)}</span>
								</div>
								<div class="flex justify-between items-center py-2 border-b border-gray-700">
									<span class="text-gray-400 font-medium">Journal:</span>
									<span class="text-white">{editingArticle.journal || 'Non spécifié'}</span>
								</div>
								<div class="flex justify-between items-center py-2 border-b border-gray-700">
									<span class="text-gray-400 font-medium">Grade:</span>
									<span class="text-white">{editingArticle.grade || 'Non spécifié'}</span>
								</div>
								<div class="flex justify-between items-center py-2">
									<span class="text-gray-400 font-medium">Publié le:</span>
									<span class="text-white">{new Date(editingArticle.published_at).toLocaleDateString('fr-FR')}</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Modal Footer -->
			<div class="flex items-center justify-end gap-4 bg-gray-800 px-8 py-6 border-t border-gray-700">
				<button
					onclick={closeEditModal}
					class="px-6 py-3 text-gray-400 hover:text-white transition-colors text-base font-medium"
					disabled={isUpdating}
				>
					Annuler
				</button>
				<button
					onclick={saveArticleChanges}
					disabled={isUpdating || !editTitle.trim() || !editContent.trim()}
					class="px-8 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-base font-medium"
				>
					{#if isUpdating}
						<svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
						</svg>
						Mise à jour...
					{:else}
						Sauvegarder
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Confirmation Modal -->
{#if showConfirmationModal}
	<div class="fixed inset-0 z-60 flex items-center justify-center bg-black bg-opacity-75">
		<div class="w-full max-w-md bg-gray-900 rounded-lg shadow-xl">
			<!-- Modal Header -->
			<div class="flex items-center justify-between bg-gray-800 px-6 py-4 rounded-t-lg">
				<h2 class="text-lg font-semibold text-white">Confirmer les modifications</h2>
				<button
					onclick={cancelSaveChanges}
					class="text-gray-400 hover:text-white transition-colors"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			<!-- Modal Content -->
			<div class="p-6">
				<div class="mb-6">
					<div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-yellow-100 rounded-full">
						<svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
						</svg>
					</div>
					<h3 class="text-lg font-medium text-white text-center mb-2">Êtes-vous sûr ?</h3>
					<p class="text-gray-400 text-center text-sm">
						Vous êtes sur le point de modifier cet article. Cette action est irréversible.
					</p>
					{#if editingArticle}
						<div class="mt-4 p-3 bg-gray-800 rounded border border-gray-700">
							<p class="text-xs text-gray-400 mb-1">Article à modifier :</p>
							<p class="text-sm text-white font-medium truncate">{editTitle || editingArticle.title}</p>
							<p class="text-xs text-gray-500">ID: {getArticleId(editingArticle)}</p>
						</div>
					{/if}
				</div>

				<!-- Modal Actions -->
				<div class="flex items-center justify-end gap-3">
					<button
						onclick={cancelSaveChanges}
						class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
						disabled={isUpdating}
					>
						Annuler
					</button>
					<button
						onclick={confirmSaveChanges}
						disabled={isUpdating}
						class="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
					>
						{#if isUpdating}
							<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
							</svg>
							Modification...
						{:else}
							Confirmer la modification
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Style for edit buttons */
	:global(.edit-button) {
		z-index: 10;
	}
	
	:global(.edit-button:hover) {
		transform: scale(1.05);
	}
</style> 