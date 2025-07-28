<!-- src/routes/favoris/+page.svelte -->
<script lang="ts">
    import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
    import ArticleEditModal from '$lib/components/articles/ArticleEditModal.svelte';
    import userProfileStore from '$lib/stores/user';
    import type { Article } from '$lib/utils/articleUtils';

    // Get data from +page.server.ts
    const { data } = $props();

    const currentUserId = $derived($userProfileStore?.id ?? null);

    // Define the custom empty state message for this page
    const noLikedArticlesMessage = `Vous n'avez pas encore ajouté d'articles à vos favoris.<br>Cliquez sur ❤️ sur un article pour le retrouver ici !`;

    // Use the filters loaded from the server
    const filtersForView = $derived(data.likedFilters || []);

    // Define the special value for clarity
    const ALL_CATEGORIES_VALUE = "__ALL__";

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

{#if currentUserId}
    <ArticleListView
        pageTitle="Mes favoris"
        filters={[]}
        apiEndpoint="/api/get-liked-articles"
        showAllCategoriesOption={true}
        emptyStateMessage="Vous n'avez pas encore ajouté d'articles à vos favoris.<br>Parcourez les articles et cliquez sur le cœur pour les sauvegarder ici."
        userId={data.userId}
        itemsPerPage={15}
        loadMoreButtonText="Charger plus de favoris"
        allArticlesLoadedText="Tous vos favoris ont été chargés"
        isSubscribed={data.isSubscribed}
        showRecommendationsOnly={false}
        enableRecommendationsToggle={true}
        onEditClick={handleEditArticle}
    />
{:else}
     <!-- Optional: Show message or loader while user store initializes -->
     <div class="flex justify-center items-center min-h-screen text-white">
         <p>Chargement des favoris...</p>
     </div>
{/if}

<!-- Edit Article Modal -->
<ArticleEditModal 
    showModal={showEditModal} 
    article={editingArticle} 
    onClose={closeEditModal} 
/>

<style>
    /* Page-specific styles if needed */
</style>