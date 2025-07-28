<!-- /src/routes/articles -->
<script lang="ts">
	import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
	import ArticleEditModal from '$lib/components/articles/ArticleEditModal.svelte';
	import userProfileStore from '$lib/stores/user';
	import type { Article } from '$lib/utils/articleUtils';

	// Get data loaded by +page.server.ts (list of all disciplines)
	const { data } = $props();

	// Prepare filters from all available disciplines
    const allDisciplines = $derived(data.disciplines || []);
	const filterOptions = $derived(
		[...allDisciplines]
			.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }))
			.map((discipline: { name: string }) => ({
				value: discipline.name,
				label: discipline.name
			}))
	);

	// Determine initial filter (first discipline in the sorted list)
	const initialFilter = $derived(filterOptions[0]?.value ?? null);

    // Define template strings with proper typing
    const articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :';
    const previousArticlesTitleTemplate = '📖 Articles pour {filter} :';

    // Edit modal state
    let showEditModal = $state(false);
    let editingArticle = $state<Article | null>(null);

    // Check if user is admin
    const isAdmin = $derived($userProfileStore?.is_admin ?? false);

    // Function to handle edit article
    function handleEditArticle(article: Article) {
        editingArticle = article;
        showEditModal = true;
    }

    // Function to close edit modal
    function closeEditModal() {
        showEditModal = false;
        editingArticle = null;
    }
</script>

<!-- Use the shared component, passing specific props for 'Tous les articles' -->
<ArticleListView
	pageTitle="Tous les articles"
	filters={filterOptions}
	initialFilterValue={null}
	filterSelectLabel="Spécialités"
	subDisciplineFetchMode="public"
	showSignupPromptProp={false}
	enableSearch={true}
	isSubscribed={data.isSubscribed}
	showAllCategoriesOption={true}
	enableRecommendationsToggle={true}
	onEditClick={handleEditArticle}
/>

<!-- Edit Article Modal -->
<ArticleEditModal 
	showModal={showEditModal} 
	article={editingArticle} 
	onClose={closeEditModal} 
/>