<!-- src/routes/favoris/+page.svelte -->
<script lang="ts">
    import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
    import userProfileStore from '$lib/stores/user';

    // Get data from +page.server.ts
    const { data } = $props();

    const currentUserId = $derived($userProfileStore?.id ?? null);

    // Define the custom empty state message for this page
    const noLikedArticlesMessage = `Vous n'avez pas encore ajouté d'articles à vos favoris.<br>Cliquez sur ❤️ sur un article pour le retrouver ici !`;

    // Use the filters loaded from the server
    const filtersForView = $derived(data.likedFilters || []);

    // Define the special value for clarity
    const ALL_CATEGORIES_VALUE = "__ALL__";
</script>

{#if currentUserId}
    <ArticleListView
        pageTitle="Mes articles favoris"
        filters={filtersForView}
        initialFilterValue={ALL_CATEGORIES_VALUE}
        filterSelectLabel="Filtrer par discipline"
        showAllCategoriesOption={true}
        apiEndpoint="/api/get-liked-articles"
        userId={currentUserId}
        subDisciplineFetchMode="public"
        enableSearch={true}
        searchPlaceholder="Rechercher dans mes favoris..."
        showAllSubDisciplinesOption={true}
        subDisciplineSelectLabel="Affiner par sous-spécialité"
        allArticlesLoadedText="Tous vos articles favoris sont chargés"
        itemsPerPage={10}
        emptyStateMessage={noLikedArticlesMessage}
        isSubscribed={data.isSubscribed}
    />
{:else}
     <!-- Optional: Show message or loader while user store initializes -->
     <div class="flex justify-center items-center min-h-screen text-white">
         <p>Chargement des favoris...</p>
     </div>
{/if}

<style>
    /* Page-specific styles if needed */
</style>