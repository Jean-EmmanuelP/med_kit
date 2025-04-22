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

{#if userDisciplines.length === 0}
	<div class="empty-state">
		<p>Vous n'avez pas encore configuré les disciplines que vous souhaitez suivre.</p>
		<p>Veuillez <a href="/account">configurer vos disciplines</a> pour commencer à recevoir des articles pertinents.</p>
	</div>
{:else}
	<!-- Use the shared component, passing specific props for 'Ma Veille' -->
	<ArticleListView
		pageTitle={$i18n.header.myVeille || 'Ma Veille'}
		filters={filterOptions}
		initialFilterValue={initialFilter}
		filterSelectLabel="Mes spécialités"
		showSignupPromptProp={true}
		enableSearch={true}
		subDisciplineFetchMode="user"
		userId={currentUserId}
		savedArticleIds={savedIdsSet}
		articleOfTheDayTitleTemplate={articleOfTheDayTitleTemplate}
		previousArticlesTitleTemplate={previousArticlesTitleTemplate}
		showAllCategoriesOption={false}
	/>
{/if}

<style>
	/* Page-specific styles */
	.empty-state {
		text-align: center;
		padding: 2rem;
		margin: 2rem auto;
		max-width: 600px;
		background-color: #374151; /* gray-700 to match other components */
		border-radius: 8px;
		color: #f3f4f6; /* gray-100 for text */
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.empty-state p {
		margin: 1rem 0;
		font-size: 1.1rem;
		color: inherit;
	}

	.empty-state a {
		color: var(--color-primary, #0d9488); /* teal-600 */
		text-decoration: underline;
	}
</style>