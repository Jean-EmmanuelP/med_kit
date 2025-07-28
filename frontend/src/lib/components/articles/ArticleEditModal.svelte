<!-- src/lib/components/articles/ArticleEditModal.svelte -->
<script lang="ts">
	import { supabase } from '$lib/supabase';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';
	import { getArticleId } from '$lib/utils/articleUtils';

	const {
		showModal = false,
		article = null as Article | null,
		onClose = null as (() => void) | null
	} = $props<{
		showModal?: boolean;
		article?: Article | null;
		onClose?: (() => void) | null;
	}>();

	// State for edit modal
	let editTitle = $state('');
	let editContent = $state('');
	let isUpdating = $state(false);
	let updateError: string | null = $state(null);

	// State for confirmation modal
	let showConfirmationModal = $state(false);
	let showDeleteConfirmationModal = $state(false);
	let showDisciplineWarningModal = $state(false);
	let isDeleting = $state(false);
	let disciplineToSelect = $state<{id: number, name: string} | null>(null);

	// State for categories management
	let allAvailableDisciplines = $state<{id: number, name: string, sub_disciplines: {id: number, name: string}[]}[]>([]);
	let selectedDisciplineIds = $state<number[]>([]);
	let selectedSubDisciplineIds = $state<number[]>([]);
	let currentArticleCategories = $state<{discipline_ids: number[], sub_discipline_ids: number[]}>({discipline_ids: [], sub_discipline_ids: []});
	let isLoadingCategories = $state(false);
	let categoryError = $state<string | null>(null);
	let isUpdatingCategories = $state(false);

	// Search functionality
	let searchTerm = $state('');
	let expandedDisciplines = $state<Set<number>>(new Set());
	let filteredDisciplines = $state<{id: number, name: string, sub_disciplines: {id: number, name: string}[]}[]>([]);

	// Simple array of all sub-disciplines
	let allSubDisciplines = $state<{id: number, name: string, parentDiscipline: string}[]>([]);

	// Check if user is admin
	const isAdmin = $derived($userProfileStore?.is_admin ?? false);

	// Function to update filtered disciplines
	function updateFilteredDisciplines() {
		if (!searchTerm.trim()) {
			filteredDisciplines = allAvailableDisciplines;
		} else {
			filteredDisciplines = allAvailableDisciplines.filter((discipline) => 
				discipline.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
				discipline.sub_disciplines?.some((sub) => 
					sub.name.toLowerCase().includes(searchTerm.toLowerCase())
				)
			);
		}
	}

	// Function to toggle discipline expansion
	function toggleDisciplineExpansion(disciplineId: number) {
		if (expandedDisciplines.has(disciplineId)) {
			expandedDisciplines.delete(disciplineId);
		} else {
			expandedDisciplines.add(disciplineId);
		}
		expandedDisciplines = new Set(expandedDisciplines);
	}

	// Function to select all sub-disciplines of a discipline
	function selectAllSubDisciplines(discipline: {id: number, name: string, sub_disciplines: {id: number, name: string}[]}) {
		if (!discipline.sub_disciplines) return;
		
		const subDisciplineIds = discipline.sub_disciplines.map(sub => sub.id);
		const allSelected = subDisciplineIds.every(id => selectedSubDisciplineIds.includes(id));
		
		if (allSelected) {
			// Deselect all
			selectedSubDisciplineIds = selectedSubDisciplineIds.filter(id => !subDisciplineIds.includes(id));
		} else {
			// Select all
			selectedSubDisciplineIds = [...new Set([...selectedSubDisciplineIds, ...subDisciplineIds])];
		}
	}

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
			filteredDisciplines = allAvailableDisciplines; // Initialize filtered disciplines
			
			// Create simple array of all sub-disciplines
			const subDisciplines: {id: number, name: string, parentDiscipline: string}[] = [];
			allAvailableDisciplines.forEach((discipline) => {
				if (discipline.sub_disciplines) {
					discipline.sub_disciplines.forEach((sub) => {
						subDisciplines.push({
							id: sub.id,
							name: sub.name,
							parentDiscipline: discipline.name
						});
					});
				}
			});
			allSubDisciplines = subDisciplines;
		} catch (error: any) {
			console.error('Error loading disciplines:', error);
			categoryError = 'Erreur lors du chargement des disciplines';
		}
	}

	// Effect to update filtered disciplines when search term changes
	$effect(() => {
		updateFilteredDisciplines();
	});

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

	// Function to handle category updates
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
		const discipline = allAvailableDisciplines.find((d) => d.id === disciplineId);
		if (!discipline) return;

		if (selectedDisciplineIds.includes(disciplineId)) {
			// Remove discipline and all its sub-disciplines
			selectedDisciplineIds = selectedDisciplineIds.filter((id: number) => id !== disciplineId);
			
			// Remove all sub-disciplines that belong to this discipline
			if (discipline.sub_disciplines) {
				const subDisciplineIdsToRemove = discipline.sub_disciplines.map((sub) => sub.id);
				selectedSubDisciplineIds = selectedSubDisciplineIds.filter((id: number) => !subDisciplineIdsToRemove.includes(id));
			}
		} else {
			// Check if discipline has sub-disciplines
			if (!discipline.sub_disciplines || discipline.sub_disciplines.length === 0) {
				// Show warning modal for discipline without sub-disciplines
				disciplineToSelect = { id: discipline.id, name: discipline.name };
				showDisciplineWarningModal = true;
				return;
			}
			
			// Add discipline
			selectedDisciplineIds = [...selectedDisciplineIds, disciplineId];
		}
	}

	// Function to toggle sub-discipline selection
	function toggleSubDiscipline(subDisciplineId: number) {
		if (selectedSubDisciplineIds.includes(subDisciplineId)) {
			selectedSubDisciplineIds = selectedSubDisciplineIds.filter((id: number) => id !== subDisciplineId);
			
			// Check if we need to uncheck the parent discipline
			const parentDiscipline = allAvailableDisciplines.find((d) => 
				d.sub_disciplines?.some((sub) => sub.id === subDisciplineId)
			);
			
			if (parentDiscipline) {
				const remainingSubDisciplines = parentDiscipline.sub_disciplines?.filter((sub) => 
					selectedSubDisciplineIds.includes(sub.id)
				) || [];
				
				// If no more sub-disciplines are selected for this discipline, uncheck the discipline
				if (remainingSubDisciplines.length === 0) {
					selectedDisciplineIds = selectedDisciplineIds.filter((id: number) => id !== parentDiscipline.id);
				}
			}
		} else {
			selectedSubDisciplineIds = [...selectedSubDisciplineIds, subDisciplineId];
			
			// Automatically check the parent discipline
			const parentDiscipline = allAvailableDisciplines.find((d) => 
				d.sub_disciplines?.some((sub) => sub.id === subDisciplineId)
			);
			
			if (parentDiscipline && !selectedDisciplineIds.includes(parentDiscipline.id)) {
				selectedDisciplineIds = [...selectedDisciplineIds, parentDiscipline.id];
			}
		}
	}

	// Function to remove category from current categories (direct deselection)
	function removeCategoryFromCurrent(categoryId: number, isSubDiscipline: boolean = false) {
		if (isSubDiscipline) {
			selectedSubDisciplineIds = selectedSubDisciplineIds.filter((id: number) => id !== categoryId);
		} else {
			// Remove discipline and all its sub-disciplines
			selectedDisciplineIds = selectedDisciplineIds.filter((id: number) => id !== categoryId);
			
			// Remove all sub-disciplines that belong to this discipline
			const discipline = allAvailableDisciplines.find((d) => d.id === categoryId);
			if (discipline && discipline.sub_disciplines) {
				const subDisciplineIdsToRemove = discipline.sub_disciplines.map((sub) => sub.id);
				selectedSubDisciplineIds = selectedSubDisciplineIds.filter((id: number) => !subDisciplineIdsToRemove.includes(id));
			}
		}
	}

	// Function to apply category changes
	async function applyCategoryChanges() {
		if (!article) return;
		
		const articleId = getArticleId(article);
		await handleUpdateCategories(articleId, selectedDisciplineIds, selectedSubDisciplineIds, 'replace');
	}

	// Function to delete article
	async function deleteArticle() {
		if (!article || !$userProfileStore) return;

		isDeleting = true;
		updateError = null;

		try {
			const articleId = article.article_id;
			
			// Delete from showed_articles table
			const { error: showedArticlesError } = await supabase
				.from('showed_articles')
				.delete()
				.eq('article_id', articleId);

			if (showedArticlesError) {
				console.error('Error deleting from showed_articles:', showedArticlesError);
				// Continue anyway as the article might not exist in showed_articles
			}

			// Close modal and refresh the page
			closeEditModal();
			window.location.reload();

		} catch (error: any) {
			console.error('Error deleting article:', error);
			updateError = error.message || 'Erreur lors de la suppression de l\'article';
		} finally {
			isDeleting = false;
			showDeleteConfirmationModal = false;
		}
	}

	// Function to open edit modal
	function openEditModal(articleToEdit: Article) {
		editTitle = articleToEdit.title;
		editContent = articleToEdit.content;
		updateError = null;
		categoryError = null;
		
		// Load categories for this article
		const articleId = getArticleId(articleToEdit);
		loadArticleCategories(articleId);
	}

	// Function to close edit modal
	function closeEditModal() {
		editTitle = '';
		editContent = '';
		updateError = null;
		categoryError = null;
		selectedDisciplineIds = [];
		selectedSubDisciplineIds = [];
		currentArticleCategories = {discipline_ids: [], sub_discipline_ids: []};
		if (onClose) onClose();
	}

	// Function to save article changes
	async function saveArticleChanges() {
		if (!article || !$userProfileStore) return;

		// Show confirmation modal instead of directly saving
		showConfirmationModal = true;
	}

	// Function to handle confirmation and actually save
	async function confirmSaveChanges() {
		if (!article || !$userProfileStore) return;

		showConfirmationModal = false;
		isUpdating = true;
		updateError = null;

		try {
			const articleId = getArticleId(article);
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

	// Function to show delete confirmation
	function showDeleteConfirmation() {
		showDeleteConfirmationModal = true;
	}

	// Function to cancel delete confirmation
	function cancelDeleteConfirmation() {
		showDeleteConfirmationModal = false;
	}

	// Function to cancel discipline warning
	function cancelDisciplineWarning() {
		showDisciplineWarningModal = false;
		disciplineToSelect = null;
	}

	// Function to confirm discipline selection despite warning
	function confirmDisciplineSelection() {
		if (disciplineToSelect) {
			selectedDisciplineIds = [...selectedDisciplineIds, disciplineToSelect.id];
		}
		showDisciplineWarningModal = false;
		disciplineToSelect = null;
	}

	// Effect to load disciplines on mount and when modal opens
	$effect(() => {
		if (showModal && article) {
			loadAllDisciplines();
			openEditModal(article);
		}
	});
</script>

<!-- Edit Modal -->
{#if showModal && article && isAdmin}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center bg-black bg-opacity-75 p-4">
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

							<!-- Search Bar -->
							<div class="mb-6">
								<div class="relative">
									<input
										type="text"
										bind:value={searchTerm}
										placeholder="Rechercher une discipline ou sous-discipline..."
										class="w-full px-4 py-3 pl-10 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-colors"
									/>
									<svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
									</svg>
								</div>
							</div>

							<!-- Disciplines and Sub-disciplines Tree -->
							<div class="space-y-2 max-h-96 overflow-y-auto border border-gray-700 rounded-lg p-4 bg-gray-900">
								{#each filteredDisciplines as discipline (discipline.id)}
									<div class="space-y-1">
										<!-- Discipline Header -->
										<div class="flex items-center justify-between p-2 hover:bg-gray-800 rounded-lg transition-colors">
											<div class="flex items-center gap-3 flex-1">
												<button
													onclick={() => toggleDisciplineExpansion(discipline.id)}
													class="flex items-center justify-center w-6 h-6 text-gray-400 hover:text-white transition-colors"
												>
													<svg class="w-4 h-4 transition-transform {expandedDisciplines.has(discipline.id) ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
													</svg>
												</button>
												
												<input
													type="checkbox"
													checked={selectedDisciplineIds.includes(discipline.id)}
													onchange={() => toggleDiscipline(discipline.id)}
													class="w-5 h-5 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 focus:ring-2"
												/>
												
												<span class="text-base font-medium text-gray-300">{discipline.name}</span>
												
												{#if discipline.sub_disciplines && discipline.sub_disciplines.length > 0}
													<span class="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded-full">
														{discipline.sub_disciplines.length} sous-discipline{discipline.sub_disciplines.length > 1 ? 's' : ''}
													</span>
												{/if}
											</div>
											
											{#if discipline.sub_disciplines && discipline.sub_disciplines.length > 0}
												<button
													onclick={() => selectAllSubDisciplines(discipline)}
													class="text-xs text-teal-400 hover:text-teal-300 px-2 py-1 rounded border border-teal-600 hover:bg-teal-600/20 transition-colors"
												>
													Tout sélectionner
												</button>
											{/if}
										</div>
										
										<!-- Sub-disciplines (when expanded) -->
										{#if expandedDisciplines.has(discipline.id) && discipline.sub_disciplines && discipline.sub_disciplines.length > 0}
											<div class="ml-8 space-y-1">
												{#each discipline.sub_disciplines as subDiscipline (subDiscipline.id)}
													<label class="flex items-center gap-3 p-2 hover:bg-gray-800 rounded-lg cursor-pointer transition-colors">
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
										{/if}
									</div>
								{/each}
								
								{#if filteredDisciplines.length === 0}
									<div class="text-center py-8">
										<p class="text-gray-500">Aucune discipline trouvée pour "{searchTerm}"</p>
									</div>
								{/if}
							</div>

							<!-- Current Categories Display - Clickable for deselection -->
							<div class="mt-6 p-4 bg-gray-700 rounded-lg">
								<div class="flex items-center justify-between mb-3">
									<div class="text-sm font-medium text-gray-400">Catégories sélectionnées :</div>
									<button
										onclick={() => {
											selectedDisciplineIds = [...currentArticleCategories.discipline_ids];
											selectedSubDisciplineIds = [...currentArticleCategories.sub_discipline_ids];
										}}
										class="text-xs text-blue-400 hover:text-blue-300 px-2 py-1 rounded border border-blue-600 hover:bg-blue-600/20 transition-colors"
									>
										Reset
									</button>
								</div>
								
								{#if selectedDisciplineIds.length > 0 || selectedSubDisciplineIds.length > 0}
									<div class="flex flex-wrap gap-2">
										{#each selectedDisciplineIds as disciplineId}
											{@const discipline = allAvailableDisciplines.find((d) => d.id === disciplineId)}
											{#if discipline}
												<button
													onclick={() => removeCategoryFromCurrent(disciplineId, false)}
													class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-900/50 text-blue-300 border border-blue-700 hover:bg-red-900/50 hover:text-red-300 hover:border-red-700 transition-colors cursor-pointer"
													title="Cliquer pour retirer cette catégorie"
												>
													{discipline.name}
													<svg class="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
													</svg>
												</button>
											{/if}
										{/each}
										{#each selectedSubDisciplineIds as subDisciplineId}
											{@const subDiscipline = allAvailableDisciplines.flatMap((d) => d.sub_disciplines || []).find((s) => s.id === subDisciplineId)}
											{#if subDiscipline}
												<button
													onclick={() => removeCategoryFromCurrent(subDisciplineId, true)}
													class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-900/50 text-green-300 border border-green-700 hover:bg-red-900/50 hover:text-red-300 hover:border-red-700 transition-colors cursor-pointer"
													title="Cliquer pour retirer cette catégorie"
												>
													{subDiscipline.name}
													<svg class="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
													</svg>
												</button>
											{/if}
										{/each}
									</div>
								{:else}
									<div class="text-center py-4 text-gray-500 text-sm">
										Aucune catégorie sélectionnée
									</div>
								{/if}
								
								<!-- Show changes indicator -->
								{#if selectedDisciplineIds.length !== currentArticleCategories.discipline_ids.length || selectedSubDisciplineIds.length !== currentArticleCategories.sub_discipline_ids.length}
									<div class="mt-3 p-2 bg-yellow-900/30 border border-yellow-700 rounded text-yellow-300 text-xs">
										⚠️ Modifications en cours - Cliquez sur "Appliquer les catégories" pour sauvegarder
									</div>
								{/if}
							</div>

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
									<span class="text-white font-mono">{getArticleId(article)}</span>
								</div>
								<div class="flex justify-between items-center py-2 border-b border-gray-700">
									<span class="text-gray-400 font-medium">Journal:</span>
									<span class="text-white">{article.journal || 'Non spécifié'}</span>
								</div>
								<div class="flex justify-between items-center py-2 border-b border-gray-700">
									<span class="text-gray-400 font-medium">Grade:</span>
									<span class="text-white">{article.grade || 'Non spécifié'}</span>
								</div>
								<div class="flex justify-between items-center py-2">
									<span class="text-gray-400 font-medium">Publié le:</span>
									<span class="text-white">{new Date(article.published_at).toLocaleDateString('fr-FR')}</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Modal Footer -->
			<div class="flex items-center justify-between bg-gray-800 px-8 py-6 border-t border-gray-700">
				<!-- Delete Button -->
				<button
					onclick={showDeleteConfirmation}
					disabled={isDeleting}
					class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-base font-medium"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
					</svg>
					{#if isDeleting}
						Suppression...
					{:else}
						Supprimer l'article
					{/if}
				</button>

				<!-- Action Buttons -->
				<div class="flex items-center gap-4">
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
	</div>
{/if}

<!-- Confirmation Modal -->
{#if showConfirmationModal}
	<div class="fixed inset-0 z-[10000] flex items-center justify-center bg-black bg-opacity-75">
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
					{#if article}
						<div class="mt-4 p-3 bg-gray-800 rounded border border-gray-700">
							<p class="text-xs text-gray-400 mb-1">Article à modifier :</p>
							<p class="text-sm text-white font-medium truncate">{editTitle || article.title}</p>
							<p class="text-xs text-gray-500">ID: {getArticleId(article)}</p>
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

<!-- Discipline Warning Modal -->
{#if showDisciplineWarningModal}
	<div class="fixed inset-0 z-[10000] flex items-center justify-center bg-black bg-opacity-75">
		<div class="w-full max-w-md bg-gray-900 rounded-lg shadow-xl">
			<div class="flex items-center justify-between bg-gray-800 px-6 py-4 rounded-t-lg">
				<h2 class="text-lg font-semibold text-white">Attention</h2>
				<button onclick={cancelDisciplineWarning} class="text-gray-400 hover:text-white transition-colors">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>
			<div class="p-6">
				<div class="mb-6">
					<div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-yellow-100 rounded-full">
						<svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
						</svg>
					</div>
					<h3 class="text-lg font-medium text-white text-center mb-2">Discipline sans sous-disciplines</h3>
					<p class="text-gray-400 text-center text-sm">
						La discipline <strong class="text-white">{disciplineToSelect?.name}</strong> n'a pas de sous-disciplines.
					</p>
					<p class="text-gray-400 text-center text-sm mt-2">
						Il est recommandé de sélectionner des sous-disciplines spécifiques pour une meilleure catégorisation.
					</p>
				</div>
				<div class="flex items-center justify-end gap-3">
					<button onclick={cancelDisciplineWarning} class="px-4 py-2 text-gray-400 hover:text-white transition-colors">
						Annuler
					</button>
					<button onclick={confirmDisciplineSelection} class="px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors flex items-center gap-2">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
						</svg>
						Sélectionner quand même
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteConfirmationModal}
	<div class="fixed inset-0 z-70 flex items-center justify-center bg-black bg-opacity-75">
		<div class="w-full max-w-md bg-gray-900 rounded-lg shadow-xl">
			<!-- Modal Header -->
			<div class="flex items-center justify-between bg-gray-800 px-6 py-4 rounded-t-lg">
				<h2 class="text-lg font-semibold text-white">Confirmer la suppression</h2>
				<button
					onclick={cancelDeleteConfirmation}
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
					<div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
						<svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
						</svg>
					</div>
					<h3 class="text-lg font-medium text-white text-center mb-2">Attention !</h3>
					<p class="text-gray-400 text-center text-sm">
						Vous êtes sur le point de supprimer cet article de la base de données. Cette action est irréversible.
					</p>
					{#if article}
						<div class="mt-4 p-3 bg-red-900/30 rounded border border-red-700">
							<p class="text-xs text-red-300 mb-1">Article à supprimer :</p>
							<p class="text-sm text-white font-medium truncate">{editTitle || article.title}</p>
							<p class="text-xs text-gray-500">ID: {getArticleId(article)}</p>
						</div>
					{/if}
				</div>

				<!-- Modal Actions -->
				<div class="flex items-center justify-end gap-3">
					<button
						onclick={cancelDeleteConfirmation}
						class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
						disabled={isDeleting}
					>
						Annuler
					</button>
					<button
						onclick={deleteArticle}
						disabled={isDeleting}
						class="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
					>
						{#if isDeleting}
							<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
							</svg>
							Suppression...
						{:else}
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
							</svg>
							Confirmer la suppression
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if} 