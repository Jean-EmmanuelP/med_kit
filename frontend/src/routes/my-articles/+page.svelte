<!-- myArticles/+page.svelte -->
<script>
	import { i18n } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import userProfileStore from '$lib/stores/user';
	import { supabase } from '$lib/supabase';
	import { onMount } from 'svelte';
  
	export let data;
  
	let searchQuery = '';
	let selectedDiscipline = '';
	let filteredArticles = data.articles || [];
	let isLoadingRemove = false;
  
	// Populate userProfileStore with data from the server
	onMount(() => {
	  if (data.userProfile) {
		userProfileStore.set(data.userProfile);
	  }
	});
  
	// Liste des disciplines (doit correspondre à celles utilisées dans la DB)
	const disciplineOptions = [
	  'Médecine Générale',
	  'Urgences',
	  'Médecine du Travail',
	  'Santé Publique',
	  'Médecine Interne',
	  'Endocrinologie-Diabétologie-Nutrition',
	  'Cardiologie',
	  'Dermatologie',
	  'Hépato-Gastroentérologie',
	  'Génétique',
	  'Gériatrie',
	  'Hématologie',
	  'Maladies infectieuses',
	  'Néphrologie',
	  'Neurologie',
	  'Oncologie',
	  'Médecine physique et réadaptation',
	  'Pneumologie',
	  'Gynécologie-obstétrique',
	  'Pédiatrie',
	  'Psychiatrie',
	  'Anesthésie - Réanimation',
	  'Rhumatologie',
	  'Chirurgie cardiaque',
	  'Chirurgie digestive',
	  'Chirurgie ORL',
	  'Neurochirurgie',
	  'Ophtalmologie',
	  'Chirurgie orthopédique',
	  'Chirurgie thoracique',
	  'Urologie',
	  'Chirurgie vasculaire',
	  'Médecine de la douleur',
	];
  
	// Filtrer les articles selon la recherche et la discipline sélectionnée
	$: {
	  filteredArticles = data.articles || [];
	  if (searchQuery) {
		filteredArticles = filteredArticles.filter((article) =>
		  article.title.toLowerCase().includes(searchQuery.toLowerCase())
		);
	  }
	  if (selectedDiscipline) {
		filteredArticles = filteredArticles.filter((article) =>
		  article.disciplines.includes(selectedDiscipline)
		);
	  }
	}
  
	function goBack() {
	  goto('/ma-veille');
	}
  
	function resetFilters() {
	  searchQuery = '';
	  selectedDiscipline = '';
	}
  
	async function handleRemoveSavedArticle(articleId) {
	  if (isLoadingRemove) return;
	  isLoadingRemove = true;
  
	  try {
		const { error } = await supabase
		  .from('saved_articles')
		  .delete()
		  .eq('user_id', $userProfileStore.id)
		  .eq('article_id', articleId);
  
		if (error) throw error;
  
		filteredArticles = filteredArticles.filter((article) => article.id !== articleId);
	  } catch (error) {
		console.error('Error removing saved article:', error);
		alert('Erreur lors de la suppression de l’article.');
	  } finally {
		isLoadingRemove = false;
	  }
	}
  </script>
  
  <div class="min-h-screen bg-white px-4 py-12">
	<div class="mx-auto max-w-4xl">
	  <!-- Bouton de retour -->
	  <button on:click={goBack} class="mb-6 flex items-center text-black hover:text-gray-800">
		<svg
		  class="mr-2 h-6 w-6"
		  fill="none"
		  stroke="currentColor"
		  viewBox="0 0 24 24"
		  xmlns="http://www.w3.org/2000/svg"
		>
		  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
		</svg>
		Retour
	  </button>
  
	  <!-- Titre et barre de recherche -->
	  <div
		class="mb-8 flex flex-col items-start space-y-4 sm:flex-row sm:items-center sm:space-x-4 sm:space-y-0"
	  >
		<h1 class="text-3xl font-bold text-black">{$i18n.myArticles.title}</h1>
		<div class="flex w-full flex-col space-y-2 sm:w-auto sm:flex-row sm:space-x-2 sm:space-y-0">
		  <div class="relative w-full sm:w-64">
			<input
			  type="text"
			  bind:value={searchQuery}
			  placeholder={$i18n.header.searchPlaceholder}
			  class="w-full rounded-full border border-gray-400 bg-white px-4 py-2 pr-12 font-sans text-sm text-black transition-all duration-200 focus:border-black focus:ring focus:ring-gray-300"
			/>
			<svg
			  class="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 transform text-black"
			  fill="none"
			  stroke="currentColor"
			  viewBox="0 0 24 24"
			  xmlns="http://www.w3.org/2000/svg"
			>
			  <path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
			  />
			</svg>
		  </div>
		  <select
			bind:value={selectedDiscipline}
			class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-black transition-all duration-200 focus:border-black focus:ring focus:ring-gray-300 sm:w-48"
		  >
			<option value="">toutes les disciplines</option>
			{#each disciplineOptions as discipline}
			  <option value={discipline}>{discipline}</option>
			{/each}
		  </select>
		  <button
			on:click={resetFilters}
			class="text-black transition-colors duration-200 hover:text-gray-800"
		  >
			réinitialiser
		  </button>
		</div>
	  </div>
  
	  {#if data.error}
		<p class="text-black">Erreur : {data.error}</p>
	  {:else if filteredArticles.length === 0}
		<p class="text-black">
		  {searchQuery || selectedDiscipline
			? 'Aucun article ne correspond à votre recherche.'
			: 'Aucun article enregistré pour le moment.'}
		</p>
	  {:else}
		<ul class="space-y-4">
		  {#each filteredArticles as article}
			<li
			  class="flex items-center justify-between rounded border border-gray-400 bg-white p-4 shadow"
			>
			  <div>
				<h2 class="text-xl font-semibold text-black">
				  <a href={`/articles/${article.id}`} class="hover:underline">{article.title}</a>
				</h2>
				<p class="mt-2 text-sm text-black">
				  Publié le {new Date(article.published_at).toLocaleDateString()} •
				  Grade: <span class="inline-block border border-green-500 px-2 py-1 rounded text-black">{article.grade}</span> •
				  {article.disciplines.join(' • ')}
				</p>
			  </div>
			  <div class="flex space-x-2">
				<a href={`/articles/${article.id}`} class="text-black hover:text-gray-800">
				  <svg
					class="h-6 w-6"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				  >
					<path
					  stroke-linecap="round"
					  stroke-linejoin="round"
					  stroke-width="2"
					  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
					></path>
					<path
					  stroke-linecap="round"
					  stroke-linejoin="round"
					  stroke-width="2"
					  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
					></path>
				  </svg>
				</a>
				<button
				  on:click={() => handleRemoveSavedArticle(article.id)}
				  class="text-black hover:text-gray-800 relative"
				  disabled={isLoadingRemove}
				>
				  {#if isLoadingRemove}
					<svg class="animate-spin h-6 w-6 text-black absolute" viewBox="0 0 24 24">
					  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
					</svg>
				  {/if}
				  <svg
					class="h-6 w-6 {isLoadingRemove ? 'opacity-0' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				  >
					<path
					  stroke-linecap="round"
					  stroke-linejoin="round"
					  stroke-width="2"
					  d="M6 18L18 6M6 6l12 12"
					></path>
				  </svg>
				</button>
			  </div>
			</li>
		  {/each}
		</ul>
	  {/if}
	</div>
  </div>