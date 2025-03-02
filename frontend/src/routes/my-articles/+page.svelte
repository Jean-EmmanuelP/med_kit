<script>
  import { i18n } from '$lib/i18n';
  import { goto } from '$app/navigation';
  import userProfileStore from '$lib/stores/user';

  export let data;
  export let form;

  function goBack() {
    goto('/articles');
  }
</script>

<div class="min-h-screen bg-gray-50 py-12 px-4">
  <div class="max-w-4xl mx-auto">
    <!-- Bouton de retour -->
    <button on:click={goBack} class="mb-4 flex items-center text-blue-600 hover:text-blue-800">
      <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
      </svg>
      Retour
    </button>

    <h1 class="text-3xl font-bold text-blue-600 mb-6">Mes Articles</h1>

    {#if !$userProfileStore}
      <p class="text-gray-600 mb-4">
        Veuillez <a href="/signup" class="text-blue-500 hover:underline">vous connecter</a> pour voir vos articles enregistrés.
      </p>
    {:else if data.error}
      <p class="text-red-500">Erreur : {data.error}</p>
    {:else if data.articles.length === 0}
      <p class="text-gray-600">Aucun article enregistré pour le moment.</p>
    {:else}
      <ul class="space-y-4">
        {#each data.articles as article}
          <li class="bg-white p-4 rounded shadow flex justify-between items-center">
            <div>
              <h2 class="text-xl font-semibold text-blue-600">{article.title}</h2>
              <p class="text-gray-500 text-sm mt-2">
                {article.disciplines.join(' • ')}
              </p>
            </div>
            <div class="flex space-x-2">
              <a href={`/articles/${article.id}`} class="text-blue-500 hover:text-blue-700">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                </svg>
              </a>
              <form action="?/removeSavedArticle" method="POST">
                <input type="hidden" name="articleId" value={article.id} />
                <button type="submit" class="text-red-500 hover:text-red-700">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </form>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>