<script lang="ts">
	// Correctly import 'page', not '$page'
	import { page } from '$app/stores';
	import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';

	// Get data loaded by +page.server.ts
	const { data } = $props();

	// Determine initial filter value from URL or default to FIRST user discipline
	let initialFilter: string | null = null;
	const urlParamDiscipline = $page.url.searchParams.get('discipline');
	const userDisciplines = data.userDisciplines || [];

	if (urlParamDiscipline && userDisciplines.includes(urlParamDiscipline)) {
		initialFilter = urlParamDiscipline;
	} else if (userDisciplines.length > 0) {
		initialFilter = userDisciplines[0]; // Default to first user discipline
	}

	// Prepare filters for the Select dropdown (NO "All" option needed here)
	const filterOptions = $derived(
		userDisciplines.map((discipline: string) => ({
			value: discipline,
			label: discipline
		})) || []
	);

	// Prepare savedArticleIds set
	const savedIdsSet = $derived(new Set<string | number>(data.savedArticleIds || []));

	// Get user ID for potential API use (e.g., for 'Favoris' filter)
	// Use $userProfileStore here to access the reactive store value
	const currentUserId = $derived($userProfileStore?.id ?? null);

	// Define template strings with proper typing
	const articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :';
	const previousArticlesTitleTemplate = '📖 Articles précédents pour {filter} :';
</script>

<!-- Use the shared component, passing specific props for 'Ma Veille' -->
<ArticleListView
	pageTitle={$i18n.header.myVeille || 'Ma Veille'}
	filters={filterOptions}
	initialFilterValue={initialFilter}
	filterSelectLabel="Mes spécialités"
	showSignupPromptProp={true}
	enableSearch={false}
	userId={currentUserId}
	savedArticleIds={savedIdsSet}
	articleOfTheDayTitleTemplate={articleOfTheDayTitleTemplate}
	previousArticlesTitleTemplate={previousArticlesTitleTemplate}
	showAllCategoriesOption={false}
/>

<style>
	/* Page-specific styles */
</style>