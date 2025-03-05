<!-- /ma-veille/+page.svelte -->
<script>
    import { i18n } from '$lib/i18n';
  
    let { data } = $props();
    let showOlderArticles = $state(false);
    let expandedArticleId = $state(null); // Pour gérer l'affichage du résumé
  
    // Date d'aujourd'hui
    const today = new Date();
    const formattedDate = `${today.getDate().toString().padStart(2, '0')}/${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getFullYear()}`;
  
    // Fonction pour parser le contenu structuré des articles
    function parseContent(content) {
      if (!content) return [];
  
      const sections = [];
      let currentSection = { emoji: '', title: '', content: [] };
      const lines = content.split('\n');
      let inSection = false;
  
      for (const line of lines) {
        if (
          line.trim().startsWith('## 📝') ||
          line.trim().startsWith('## 📌') ||
          line.trim().startsWith('## 🧪') ||
          line.trim().startsWith('## 📊') ||
          line.trim().startsWith('## 🩺') ||
          line.trim().startsWith('## 📖')
        ) {
          if (inSection && (currentSection.title || currentSection.content.length > 0)) {
            sections.push(currentSection);
          }
          inSection = true;
          const [emoji, ...titleParts] = line
            .trim()
            .replace(/^##\s*/, '')
            .split(' ');
          currentSection = {
            emoji: emoji,
            title: titleParts.join(' ').trim(),
            content: [],
          };
        } else if (line.trim() && inSection) {
          currentSection.content.push(line.trim());
        }
      }
  
      if (inSection && (currentSection.title || currentSection.content.length > 0)) {
        sections.push(currentSection);
      }
  
      return sections;
    }
  
    // Fonction pour basculer l'affichage du résumé
    function toggleSummary(articleId) {
      articleId = String(articleId);
      expandedArticleId = expandedArticleId === articleId ? null : articleId;
    }
  </script>
  
  <div class="min-h-screen bg-gray-50 px-4 py-12">
    <div class="mx-auto max-w-4xl">
      <!-- Date et titre -->
      <div class="flex items-center mb-4">
        <svg
          class="h-6 w-6 mr-2 text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <span class="text-lg text-gray-600">Date / {formattedDate}</span>
      </div>
      <h1 class="text-3xl font-bold text-gray-800 mb-8">{$i18n.header.myVeille}</h1>
  
      {#if data.error}
        <p class="text-red-500">Erreur : {data.error}</p>
      {:else if data.recentArticles.length === 0}
        <p class="text-gray-600">Aucun article disponible pour le moment.</p>
      {:else}
        <!-- Articles récents -->
        <ul class="space-y-4">
          {#each data.recentArticles as article}
            <li class="rounded bg-white p-4 shadow transition-shadow hover:shadow-md">
              <!-- Titre de l'article -->
              <h2 class="text-lg font-semibold text-gray-800">{article.title}</h2>
              <!-- Grade de recommandation -->
              {#if article.grade}
                <p class="text-sm text-green-600 mt-1">
                  Grade de recommandation : {article.grade}
                </p>
              {/if}
  
              <!-- Résumé cliquable -->
              <button
                on:click={() => toggleSummary(article.id)}
                class="text-sm text-gray-600 hover:underline mt-2 flex items-center"
              >
                <span class="mr-1">Résumé</span>
                {#if expandedArticleId === String(article.id)}
                  <svg
                    class="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 15l7-7 7 7"
                    />
                  </svg>
                {:else}
                  <svg
                    class="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                {/if}
              </button>
  
              <!-- Contenu du résumé (si ouvert) -->
              {#if expandedArticleId === String(article.id)}
                <div class="prose mt-2 max-w-none text-gray-700">
                  {#each parseContent(article.content) as section}
                    <div class="mb-2">
                      <h3 class="flex items-center text-md font-semibold text-gray-800">
                        <span class="mr-2">{section.emoji}</span>
                        {section.title}
                      </h3>
                      {#each section.content as paragraph}
                        <p class="mt-1 text-sm">{paragraph}</p>
                      {/each}
                    </div>
                  {/each}
                </div>
                <!-- Bouton "Voir l'article" -->
                <a
                  href={`/articles/${article.id}`}
                  class="mt-3 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors duration-200"
                >
                  Voir l'article
                </a>
              {/if}
  
              <!-- Lien PubMed -->
              {#if article.link}
                <div class="mt-2 flex items-center text-sm text-gray-600">
                  <svg
                    class="h-4 w-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                    />
                  </svg>
                  <span class="mr-1">Lien :</span>
                  <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-blue-600 hover:underline truncate max-w-xs"
                  >
                    {article.link}
                  </a>
                </div>
              {/if}
            </li>
          {/each}
  
          <!-- Articles plus anciens (si showOlderArticles est vrai) -->
          {#if showOlderArticles}
            {#each data.olderArticles as article}
              <li class="rounded bg-white p-4 shadow transition-shadow hover:shadow-md">
                <!-- Titre de l'article -->
                <h2 class="text-lg font-semibold text-gray-800">{article.title}</h2>
                <!-- Grade de recommandation -->
                {#if article.grade}
                  <p class="text-sm text-green-600 mt-1">
                    Grade de recommandation : {article.grade}
                  </p>
                {/if}
  
                <!-- Résumé cliquable -->
                <button
                  on:click={() => toggleSummary(article.id)}
                  class="text-sm text-gray-600 hover:underline mt-2 flex items-center"
                >
                  <span class="mr-1">Résumé</span>
                  {#if expandedArticleId === String(article.id)}
                    <svg
                      class="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M5 15l7-7 7 7"
                      />
                    </svg>
                  {:else}
                    <svg
                      class="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  {/if}
                </button>
  
                <!-- Contenu du résumé (si ouvert) -->
                {#if expandedArticleId === String(article.id)}
                  <div class="prose mt-2 max-w-none text-gray-700">
                    {#each parseContent(article.content) as section}
                      <div class="mb-2">
                        <h3 class="flex items-center text-md font-semibold text-gray-800">
                          <span class="mr-2">{section.emoji}</span>
                          {section.title}
                        </h3>
                        {#each section.content as paragraph}
                          <p class="mt-1 text-sm">{paragraph}</p>
                        {/each}
                      </div>
                    {/each}
                  </div>
                  <!-- Bouton "Voir l'article" -->
                  <a
                    href={`/articles/${article.id}`}
                    class="mt-3 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors duration-200"
                  >
                    Voir l'article
                  </a>
                {/if}
  
                <!-- Lien PubMed -->
                {#if article.link}
                  <div class="mt-2 flex items-center text-sm text-gray-600">
                    <svg
                      class="h-4 w-4 mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                      />
                    </svg>
                    <span class="mr-1">Lien :</span>
                    <a
                      href={article.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-blue-600 hover:underline truncate max-w-xs"
                    >
                      {article.link}
                    </a>
                  </div>
                {/if}
              </li>
            {/each}
          {/if}
        </ul>
  
        <!-- Bouton "Faites défiler pour voir les articles précédents" ou "Voir moins" -->
        {#if data.olderArticles.length > 0}
          {#if showOlderArticles}
            <button
              on:click={() => (showOlderArticles = false)}
              class="mt-6 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors duration-200"
            >
              Voir moins
            </button>
          {:else}
            <button
              on:click={() => (showOlderArticles = true)}
              class="mt-6 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors duration-200"
            >
              Faites défiler pour voir les articles précédents
            </button>
          {/if}
        {/if}
      {/if}
    </div>
  </div>