<script lang="ts">
	import ArticleListView from '$lib/components/articles/ArticleListView.svelte';

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
</script>

<!-- Use the shared component, passing specific props for 'Tous les articles' -->
<ArticleListView
	pageTitle="Tous les articles"
	filters={filterOptions}
	initialFilterValue={initialFilter}
	filterSelectLabel="Spécialités"
	showSignupPromptProp={false}
	enableSearch={false}
    {articleOfTheDayTitleTemplate}
    {previousArticlesTitleTemplate}
/>