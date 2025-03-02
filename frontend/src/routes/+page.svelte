<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';
  
	let showModal = false;
	let searchQuery = '';
	let isPlaying = false;
	let videoElement;
  
	const disciplineOptions = [
	  'Médecine Générale', 'Urgences', 'Médecine du Travail', 'Santé Publique', 'Médecine Interne',
	  'Endocrinologie-Diabétologie-Nutrition', 'Cardiologie', 'Dermatologie', 'Hépato-Gastroentérologie',
	  'Génétique', 'Gériatrie', 'Hématologie', 'Maladies infectieuses', 'Néphrologie', 'Neurologie',
	  'Oncologie', 'Médecine physique et réadaptation', 'Pneumologie', 'Gynécologie-obstétrique',
	  'Pédiatrie', 'Psychiatrie', 'Anesthésie - Réanimation', 'Rhumatologie', 'Chirurgie cardiaque',
	  'Chirurgie digestive', 'Chirurgie ORL', 'Neurochirurgie', 'Ophtalmologie', 'Chirurgie orthopédique',
	  'Chirurgie thoracique', 'Urologie', 'Chirurgie vasculaire', 'Médecine de la douleur'
	];
  
	function handleSearch(event) {
	  event.preventDefault();
	  showModal = true; // Affiche la modale si l'utilisateur recherche
	}
  
	function handleDisciplineClick(event) {
	  event.preventDefault();
	  showModal = true; // Affiche la modale si l'utilisateur clique sur un domaine
	}
  
	function closeModal() {
	  showModal = false;
	}
  
	function redirectToSignup() {
	  goto('/signup');
	}
  
	function togglePlay() {
	  if (isPlaying) {
		videoElement.pause();
	  } else {
		videoElement.play();
	  }
	  isPlaying = !isPlaying;
	}
  </script>
  
  <main class="relative flex min-h-screen flex-col">
	<!-- Hero Section avec vidéo -->
	<div class="relative flex-auto">
	  <video
		bind:this={videoElement}
		class="absolute inset-0 w-full h-full object-cover"
		loop
		muted
		playsinline
	  >
		<source src="/videos/VideofromKaltura.mp4" type="video/mp4" />
		Votre navigateur ne prend pas en charge la lecture de vidéos.
	  </video>
  
	  <!-- Overlay sombre -->
	  <div class="absolute inset-0 bg-black opacity-50"></div>
  
	  <!-- Bouton Play/Pause -->
	  <button
		on:click={togglePlay}
		class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 text-white"
		aria-label={isPlaying ? 'Pause' : 'Play'}
	  >
		{#if isPlaying}
		  <!-- Icône Pause -->
		  <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6"></path>
		  </svg>
		{:else}
		  <!-- Icône Play -->
		  <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l10 7-10 7V5z"></path>
		  </svg>
		{/if}
	  </button>
  
	  <!-- Contenu -->
	  <div class="absolute bottom-8 right-8 z-10 text-right text-white">
		<h1 class="text-4xl md:text-5xl lg:text-6xl font-bold font-display tracking-tight drop-shadow-lg">
		  Transforming your care
		</h1>
		<p class="text-lg md:text-xl font-light font-serif drop-shadow-md pl-4 mt-2">
		  Learn how we drive innovation
		</p>
		<div class="mt-4 pl-4">
		  {#if !$userProfileStore}
			<a
			  href="/signup"
			  class="inline-block rounded-full border-2 border-white px-6 py-3 text-base md:text-lg font-medium font-sans-bold text-white hover:bg-white hover:text-black transition-colors duration-200"
			>
			  Créer un compte
			</a>
		  {:else}
			<a
			  href="/articles"
			  class="inline-block rounded-full border-2 border-white px-6 py-3 text-base md:text-lg font-medium font-sans-bold text-white hover:bg-white hover:text-black transition-colors duration-200"
			>
			  Voir les récents articles
			</a>
		  {/if}
		</div>
	  </div>
	</div>
  
	<!-- Section de recherche -->
	<div class="bg-white py-8">
	  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row md:space-x-8">
		<!-- Liste des domaines -->
		<div class="w-full md:w-1/3 mb-6 md:mb-0">
		  <h3 class="text-sm font-medium font-sans text-gray-700 mb-4 uppercase">
			Rechercher par domaine
		  </h3>
		  <div class="flex flex-wrap gap-2">
			{#each disciplineOptions as discipline}
			  <a
				href={`/articles?discipline=${encodeURIComponent(discipline)}`}
				on:click={handleDisciplineClick}
				class="w-10 h-10 flex items-center justify-center rounded-full border border-gray-300 text-sm font-medium font-sans text-gray-700 hover:bg-blue-100 transition-colors duration-200"
			  >
				{discipline.charAt(0)}
			  </a>
			{/each}
		  </div>
		</div>
  
		<!-- Barre de recherche -->
		<div class="w-full md:w-2/3 flex items-center">
		  <form on:submit={handleSearch} class="relative w-full">
			<input
			  type="text"
			  bind:value={searchQuery}
			  placeholder="Rechercher un article"
			  class="w-full py-2 px-4 pr-12 rounded-full border border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all duration-200 text-sm font-sans"
			/>
			<button
			  type="submit"
			  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-blue-600"
			  aria-label="Rechercher"
			>
			  <svg
				class="w-5 h-5"
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
			</button>
		  </form>
		</div>
	  </div>
	</div>
  
	<!-- Modale -->
	{#if showModal}
	  <div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center px-4">
		<div class="bg-white rounded-lg p-6 max-w-md w-full space-y-4 relative">
		  <button
			on:click={closeModal}
			class="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
			aria-label="Fermer la modale"
		  >
			<svg
			  class="w-6 h-6"
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
			  />
			</svg>
		  </button>
		  <h2 class="text-xl font-bold font-display text-gray-900">
			Créez un compte pour accéder aux articles
		  </h2>
		  <p class="text-sm font-sans text-gray-700">
			En créant un compte (ça prend <span class="font-sans-bold">1 minute</span>), vous aurez accès à tous les articles médicaux à jour dans vos domaines d’intérêt.
		  </p>
		  <button
			on:click={redirectToSignup}
			class="w-full rounded-full bg-blue-600 py-3 text-white font-medium font-sans-bold hover:bg-blue-700 transition-colors duration-200"
		  >
			Créer un compte
		  </button>
		</div>
	  </div>
	{/if}
  </main>