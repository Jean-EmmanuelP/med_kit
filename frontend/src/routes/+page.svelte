<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';
	import Footer from '$lib/components/Footer.svelte';

	let showModal = false;
	let searchQuery = '';
	let isPlaying = false;
	let videoElement;

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
		'Médecine de la douleur'
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
	<div class="relative flex-auto overflow-hidden bg-black md:max-h-[60vh]">
		<!-- Fallback image behind the video -->
		<img
			src="/image/imagefromKaltura.png"
			alt="Fallback image for hero section"
			class="absolute inset-0 h-full w-full object-cover"
		/>
		<!-- Video -->
		<video
			bind:this={videoElement}
			class="absolute inset-0 h-full w-full object-cover"
			loop
			muted
			playsinline
		>
			<source src="/videos/VideofromKaltura.mp4" type="video/mp4" />
			Votre navigateur ne prend pas en charge la lecture de vidéos.
		</video>

		<!-- Overlay sombre -->
		<div class="absolute inset-0 bg-black opacity-25"></div>

		<!-- Bouton Play/Pause -->
		<button
			on:click={togglePlay}
			class="absolute top-[10%] right-[1%] z-20 transform text-white"
			aria-label={isPlaying ? 'Pause' : 'Play'}
		>
			{#if isPlaying}
				<!-- Icône Pause -->
				<svg
					class="h-12 w-12"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M10 9v6m4-6v6"
					></path>
				</svg>
			{:else}
				<!-- Icône Play -->
				<svg
					class="h-12 w-12"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="1"
						d="M9 5l10 7-10 7V5z"
					/>
				</svg>
			{/if}
		</button>

		<!-- Contenu -->
		<div
			class="absolute bottom-[10%] left-[4%] z-10 flex w-full transform flex-col space-y-6 md:left-[19%] md:flex-col"
		>
			<div class="flex max-w-[90%] flex-col gap-2 text-white md:gap-6">
				<h1
					class="font-display text-4xl font-thin tracking-tight drop-shadow-lg md:text-5xl lg:text-6xl"
				>
					{$i18n.home.hero.title}
				</h1>
				<p class="mt-2 font-serif text-lg font-light drop-shadow-md md:text-xl">
					{$i18n.home.hero.subtitle}
				</p>
			</div>

			<!-- Bouton -->
			<div>
				{#if !$userProfileStore}
					<a
						href="/signup"
						class="font-sans-bold inline-block w-[90%] rounded-full border-2 border-white py-3 text-center text-base font-medium text-white transition-colors duration-200 hover:bg-white hover:text-black md:w-fit md:px-6 md:text-lg"
					>
						{$i18n.home.hero.signup}
					</a>
				{:else}
					<a
						href="/articles"
						class="font-sans-bold inline-block w-[90%] rounded-full border-2 border-white py-3 text-center text-base font-medium text-white transition-colors duration-200 hover:bg-white hover:text-black md:w-fit md:px-6 md:text-lg"
					>
						{$i18n.home.hero.viewArticles}
					</a>
				{/if}
			</div>
		</div>
	</div>

	<!-- Section de recherche -->
	<div class="bg-white py-8">
		<div class="mx-auto flex max-w-7xl flex-col px-4 sm:px-6 md:flex-row md:space-x-8 lg:px-8">
			<!-- Liste des domaines -->
			<div class="mb-6 w-full md:mb-0 md:w-1/3">
				<h3 class="mb-4 font-sans text-sm font-medium text-gray-700 uppercase">
					Rechercher par domaine
				</h3>
				<div class="flex flex-wrap gap-2">
					{#each disciplineOptions as discipline}
						<a
							href={`/articles?discipline=${encodeURIComponent(discipline)}`}
							on:click={handleDisciplineClick}
							class="flex h-10 w-10 items-center justify-center rounded-full border border-gray-300 font-sans text-sm font-medium text-gray-700 transition-colors duration-200 hover:bg-blue-100"
						>
							{discipline.charAt(0)}
						</a>
					{/each}
				</div>
			</div>

			<!-- Barre de recherche -->
			<div class="flex w-full items-center md:w-2/3">
				<form on:submit={handleSearch} class="relative w-full">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Rechercher un article"
						class="w-full rounded-full border border-gray-300 px-4 py-2 pr-12 font-sans text-sm transition-all duration-200 focus:border-blue-500 focus:ring focus:ring-blue-200"
					/>
					<button
						type="submit"
						class="absolute top-1/2 right-3 -translate-y-1/2 transform text-gray-500 hover:text-blue-600"
						aria-label="Rechercher"
					>
						<svg
							class="h-5 w-5"
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
		<div class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black px-4">
			<div class="relative w-full max-w-md space-y-4 rounded-lg bg-white p-6">
				<button
					on:click={closeModal}
					class="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
					aria-label="Fermer la modale"
				>
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
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
				<h2 class="font-display text-xl font-bold text-gray-900">
					Créez un compte pour accéder aux articles
				</h2>
				<p class="font-sans text-sm text-gray-700">
					En créant un compte (ça prend <span class="font-sans-bold">1 minute</span>), vous aurez
					accès à tous les articles médicaux à jour dans vos domaines d’intérêt.
				</p>
				<button
					on:click={redirectToSignup}
					class="font-sans-bold w-full rounded-full bg-blue-600 py-3 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
				>
					Créer un compte
				</button>
			</div>
		</div>
	{/if}
</main>
