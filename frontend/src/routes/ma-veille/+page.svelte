<script lang="ts">
	// Correctly import 'page', not '$page'
	import { page } from '$app/stores';
	import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';

	// --- Type for the structure from server ---
	interface SubDisciplineInfo { id: number; name: string; }
	interface DisciplineStructure {
		id: number;
		name: string;
		subscribed_sub_disciplines: SubDisciplineInfo[];
	}

	// Get data loaded by +page.server.ts
	const { data } = $props<{
		data: {
			initialMainFilterValue: string | null; // Provided by server
			initialSubFilterValue: string | null;  // Provided by server
			userSubscriptionStructure: DisciplineStructure[];
			savedArticleIds: (string | number)[];
			error: string | null;
		}
	}>();

	const userStructure = data.userSubscriptionStructure || [];
	const hasSubscriptions = userStructure.length > 0;

	// Prepare filters for the *first* dropdown using the structure
	const filterOptions = $derived(
		userStructure.map((discipline: DisciplineStructure) => ({
			value: discipline.name,
			label: discipline.name
		}))
	);

	const savedIdsSet = $derived(new Set<string | number>(data.savedArticleIds || []));
	const currentUserId = $derived($userProfileStore?.id ?? null);
	const articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :';
	const previousArticlesTitleTemplate = '📖 Articles précédents pour {filter} :';

	// Pass the server-determined initial values directly
	const initialMainFilterFromData = data.initialMainFilterValue;
	const initialSubFilterFromData = data.initialSubFilterValue;
</script>

{#if !hasSubscriptions && !data.error}
	<!-- Empty State (No Subscriptions) -->
	<div class="flex min-h-[60vh] items-center justify-center text-center text-white p-6">
		<div class="empty-state">
			<p>Vous n'avez pas encore configuré les disciplines que vous souhaitez suivre.</p>
			<p>Veuillez <a href="/account">configurer vos disciplines</a> pour commencer à recevoir des articles pertinents.</p>
		</div>
	</div>
{:else if data.error}
	<!-- Error State -->
	<div class="flex min-h-[60vh] items-center justify-center text-center text-red-300 p-6">
		<p>Une erreur est survenue lors du chargement de vos données. Veuillez réessayer plus tard.</p>
	</div>
{:else}
	<!-- Pass the CORRECT initial values from server data to ArticleListView -->
	<ArticleListView
		pageTitle={$i18n.header.myVeille || 'Ma Veille'}
		filters={filterOptions}
		initialFilterValue={initialMainFilterFromData}
		initialSubFilterValue={initialSubFilterFromData}
		filterSelectLabel="Mes spécialités"
		showSignupPromptProp={true}
		enableSearch={true}
		subDisciplineFetchMode="user"
		userId={currentUserId}
		savedArticleIds={savedIdsSet}
		{articleOfTheDayTitleTemplate}
		{previousArticlesTitleTemplate}
		showAllCategoriesOption={false}
		showAllSubDisciplinesOption={true}
		allSubDisciplinesLabel="Toutes mes sous-spécialités"
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