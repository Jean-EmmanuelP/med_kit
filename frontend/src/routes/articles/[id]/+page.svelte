<!-- article/[id]/+page.svelte -->
<script lang="ts">
	import { i18n } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import userProfileStore from '$lib/stores/user';
	import { onMount } from 'svelte';
	import { supabase } from '$lib/supabase';

	export let data;

	// Définir les variables d'état
	let newComment = '';
	let comments = data.comments || [];
	let likesCount = data.likesCount || 0;
	let dislikesCount = data.dislikesCount || 0;
	let userHasLiked = data.userHasLiked || false;
	let userHasDisliked = data.userHasDisliked || false;
	let isSaved = data.isSaved || false;
	let isLoadingLike = false;
	let isLoadingDislike = false;
	let isLoadingSave = false;
	let isLoadingComment = false;
	// Utiliser un objet pour gérer l'état de chargement de suppression par commentaire
	let isLoadingDelete = {};

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
		'Médecine de la douleur'
	];

	// Fonction pour formater les titres : première lettre en majuscule, le reste en minuscule
	function formatTitle(title: string) {
		if (!title) return '';
		const words = title.toLowerCase().split(' ');
		if (words.length === 0) return '';
		words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
		return words.join(' ');
	}

	// Fonction pour parser le contenu Markdown ou structuré
	function parseContent(content) {
		if (!content) return [];

		const sections = [];
		let currentSection = { title: '', content: [] };
		const lines = content.split('\n');

		for (const line of lines) {
			if (line.startsWith('##')) {
				if (currentSection.title || currentSection.content.length > 0) {
					sections.push(currentSection);
				}
				currentSection = { title: line.replace(/^##\s+/, '').trim(), content: [] };
			} else if (line.trim()) {
				currentSection.content.push(line.trim());
			}
		}

		if (currentSection.title || currentSection.content.length > 0) {
			sections.push(currentSection);
		}

		return sections;
	}

	$: parsedContent = parseContent(data.article?.content);

	function goBack() {
		goto('/ma-veille');
	}

	async function handleToggleLike() {
		if (!$userProfileStore) {
			alert('Veuillez vous connecter pour liker cet article.');
			return;
		}

		if (isLoadingLike) return;
		isLoadingLike = true;

		try {
			if (userHasDisliked) {
				const { error: deleteError } = await supabase
					.from('article_dislikes')
					.delete()
					.eq('article_id', data.article.id)
					.eq('user_id', $userProfileStore.id);

				if (deleteError) throw deleteError;

				dislikesCount -= 1;
				userHasDisliked = false;
			}

			if (userHasLiked) {
				const { error: deleteError } = await supabase
					.from('article_likes')
					.delete()
					.eq('article_id', data.article.id)
					.eq('user_id', $userProfileStore.id);

				if (deleteError) throw deleteError;

				likesCount -= 1;
				userHasLiked = false;
			} else {
				const { error: insertError } = await supabase.from('article_likes').insert({
					article_id: data.article.id,
					user_id: $userProfileStore.id
				});

				if (insertError) throw insertError;

				likesCount += 1;
				userHasLiked = true;
			}
		} catch (error) {
			console.error('Error toggling like:', error);
			alert('Erreur lors de la mise à jour du like.');
		} finally {
			isLoadingLike = false;
		}
	}

	async function handleToggleDislike() {
		if (!$userProfileStore) {
			alert('Veuillez vous connecter pour disliker cet article.');
			return;
		}

		if (isLoadingDislike) return;
		isLoadingDislike = true;

		try {
			if (userHasLiked) {
				const { error: deleteError } = await supabase
					.from('article_likes')
					.delete()
					.eq('article_id', data.article.id)
					.eq('user_id', $userProfileStore.id);

				if (deleteError) throw deleteError;

				likesCount -= 1;
				userHasLiked = false;
			}

			if (userHasDisliked) {
				const { error: deleteError } = await supabase
					.from('article_dislikes')
					.delete()
					.eq('article_id', data.article.id)
					.eq('user_id', $userProfileStore.id);

				if (deleteError) throw deleteError;

				dislikesCount -= 1;
				userHasDisliked = false;
			} else {
				const { error: insertError } = await supabase.from('article_dislikes').insert({
					article_id: data.article.id,
					user_id: $userProfileStore.id
				});

				if (insertError) throw insertError;

				dislikesCount += 1;
				userHasDisliked = true;
			}
		} catch (error) {
			console.error('Error toggling dislike:', error);
			alert('Erreur lors de la mise à jour du dislike.');
		} finally {
			isLoadingDislike = false;
		}
	}

	async function handleToggleSave() {
		if (!$userProfileStore) {
			alert('Veuillez vous connecter pour enregistrer cet article.');
			return;
		}

		if (isLoadingSave) return;
		isLoadingSave = true;

		try {
			if (isSaved) {
				const { error } = await supabase
					.from('saved_articles')
					.delete()
					.eq('article_id', data.article.id)
					.eq('user_id', $userProfileStore.id);

				if (error) throw error;

				isSaved = false;
			} else {
				const { error } = await supabase.from('saved_articles').insert({
					article_id: data.article.id,
					user_id: $userProfileStore.id
				});

				if (error) throw error;

				isSaved = true;
			}
		} catch (error) {
			console.error('Error toggling save:', error);
			alert('Erreur lors de la mise à jour de l’enregistrement.');
		} finally {
			isLoadingSave = false;
		}
	}

	// Fonction corrigée pour ajouter un commentaire
	async function handleCommentSubmit() {
		if (!$userProfileStore) {
			alert('Veuillez vous connecter pour laisser un commentaire.');
			return;
		}

		if (newComment.trim() === '') {
			alert('Veuillez entrer un commentaire.');
			return;
		}

		if (isLoadingComment) return;
		isLoadingComment = true;

		try {
			const { data: commentData, error } = await supabase
				.from('comments')
				.insert({
					article_id: data.article.id,
					user_id: $userProfileStore.id,
					content: newComment
				})
				.select('id, user_id')
				.single();

			if (error) throw error;

			// Ajouter le commentaire à la liste avec user_id
			comments = [
				{
					id: commentData.id,
					content: newComment,
					created_at: new Date().toISOString(),
					user_id: $userProfileStore.id, // Ajouter user_id ici
					user: {
						first_name: $userProfileStore.first_name || 'Utilisateur',
						last_name: $userProfileStore.last_name || 'Inconnu',
						status: $userProfileStore.status,
						specialty: $userProfileStore.specialty
					}
				},
				...comments
			];
			newComment = '';
		} catch (error) {
			console.error('Error adding comment:', error);
			alert('Erreur lors de l’ajout du commentaire.');
		} finally {
			isLoadingComment = false;
		}
	}

	// Fonction pour supprimer un commentaire
	async function handleDeleteComment(commentId) {
		if (!$userProfileStore) {
			alert('Veuillez vous connecter pour supprimer un commentaire.');
			return;
		}

		if (!confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ?')) {
			return;
		}

		// Vérifier si une suppression est déjà en cours pour ce commentaire
		if (isLoadingDelete[commentId]) return;

		// Mettre à jour l'état de chargement pour ce commentaire
		isLoadingDelete = { ...isLoadingDelete, [commentId]: true };

		try {
			const { error } = await supabase
				.from('comments')
				.delete()
				.eq('id', commentId)
				.eq('user_id', $userProfileStore.id);

			if (error) throw error;

			// Supprimer le commentaire de la liste localement
			comments = comments.filter((comment) => comment.id !== commentId);
		} catch (error) {
			console.error('Error deleting comment:', error);
			alert('Erreur lors de la suppression du commentaire.');
		} finally {
			// Réinitialiser l'état de chargement pour ce commentaire
			isLoadingDelete = { ...isLoadingDelete, [commentId]: false };
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
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Retour
		</button>

		{#if data.error}
			<p class="text-black">Erreur : {data.error}</p>
		{:else if !data.article}
			<p class="text-black">Article non trouvé.</p>
		{:else}
			<!-- Titre, métadonnées et likes/dislikes de l’article -->
			<div class="mb-10 flex flex-col">
				<h1 class="mb-4 text-3xl font-bold text-black">{formatTitle(data.article.title)}</h1>
				<p class="mb-6 text-black">
					Publié le {new Date(data.article.published_at).toLocaleDateString()} par
					{data.article.journal}
					• Grade de recommandation
					<span class="inline-block py-1 text-black">{data.article.grade}</span>
					• {data.article.disciplines.join(' • ')}
				</p>
				<!-- Contenu de l’article -->
				<div class="prose mb-16 max-w-none">
					{#each parsedContent as section}
						{#if section.title}
							<h2 class="mt-6 mb-2 text-xl font-semibold text-black">{section.title}</h2>
						{/if}
						{#each section.content as paragraph}
							<p class="mb-4 text-black">{paragraph}</p>
						{/each}
					{/each}
				</div>

				<!-- Référence avec lien PubMed -->
				<div>
					{#if data.article.link}
						<div class="flex items-center text-sm text-gray-600">
							<svg
								class="mr-1 h-4 w-4"
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
								href={data.article.link}
								target="_blank"
								rel="noopener noreferrer"
								class="max-w-xs truncate text-blue-600 hover:underline"
							>
								{data.article.link}
							</a>
						</div>
					{/if}
				</div>
			</div>

			<!-- Séparation claire -->
			<hr class="border-t border-gray-400" />

			<!-- Section des interactions sociales -->
			<div class="mt-20 mb-16">
				<!-- Boutons Like, Dislike, et Enregistrer -->
				<h2 class="mb-4 text-xl font-semibold text-black">{$i18n.articles.feedbackPrompt}</h2>
				<div class="mb-10 flex items-center space-x-4">
					<!-- Bouton pouce vers le haut (Like) -->
					<button
						on:click={handleToggleLike}
						class="relative flex items-center text-black hover:text-gray-800"
					>
						{#if isLoadingLike}
							<svg class="absolute mr-2 h-5 w-5 animate-spin text-black" viewBox="0 0 24 24">
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
						{/if}
						<span class="mr-2 text-2xl {isLoadingLike ? 'opacity-0' : ''}">👍</span>
						<span class={isLoadingLike ? 'opacity-0' : ''}>{likesCount}</span>
					</button>

					<!-- Bouton pouce vers le bas (Dislike) -->
					<button
						on:click={handleToggleDislike}
						class="relative flex items-center text-black hover:text-gray-800"
					>
						{#if isLoadingDislike}
							<svg class="absolute mr-2 h-5 w-5 animate-spin text-black" viewBox="0 0 24 24">
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
						{/if}
						<span class="mr-2 text-2xl {isLoadingDislike ? 'opacity-0' : ''}">👎</span>
						<span class={isLoadingDislike ? 'opacity-0' : ''}>{dislikesCount}</span>
					</button>

					<!-- Bouton cœur (Enregistrer) -->
					<button
						on:click={handleToggleSave}
						class="relative flex items-center text-black hover:text-gray-800"
					>
						{#if isLoadingSave}
							<svg class="absolute mr-2 h-5 w-5 animate-spin text-black" viewBox="0 0 24 24">
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
						{/if}
						<span class="mr-2 text-2xl {isLoadingSave ? 'opacity-0' : ''}"
							>{isSaved ? '❤️' : '🤍'}</span
						>
						<span class={isLoadingSave ? 'opacity-0' : ''}
							>{isSaved ? 'Enregistré' : 'Enregistrer'}</span
						>
					</button>
				</div>

				<!-- Section des commentaires -->
				<div class="mt-12">
					{#if !$userProfileStore}
						<p class="mb-8 text-black">
							Veuillez <a href="/signup" class="text-black hover:underline">vous connecter</a> pour laisser
							un commentaire.
						</p>
					{:else}
						<!-- Formulaire pour ajouter un commentaire -->
						<div class="mb-10">
							<textarea
								name="content"
								bind:value={newComment}
								rows="4"
								class="mb-4 w-full rounded border border-gray-400 bg-white p-3 text-black transition-all duration-200 focus:border-black focus:ring focus:ring-gray-300"
								placeholder="Écrire un commentaire..."
							></textarea>
							<button
								on:click={handleCommentSubmit}
								disabled={isLoadingComment}
								class="relative rounded bg-black px-6 py-2 text-white transition-colors duration-200 hover:bg-gray-800 hover:text-white disabled:cursor-not-allowed disabled:bg-gray-600"
							>
								{#if isLoadingComment}
									<svg
										class="absolute top-1/2 left-4 mr-2 h-5 w-5 -translate-y-1/2 transform animate-spin text-white"
										viewBox="0 0 24 24"
									>
										<circle
											class="opacity-25"
											cx="12"
											cy="12"
											r="10"
											stroke="currentColor"
											stroke-width="4"
										/>
										<path
											class="opacity-75"
											fill="currentColor"
											d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
										/>
									</svg>
									<span class="opacity-0">Publier</span>
								{/if}
								<span class={isLoadingComment ? 'opacity-0' : ''}>Publier</span>
							</button>
						</div>
					{/if}

					<!-- Liste des commentaires -->
					{#if comments.length === 0}
						<p class="text-black">Aucun commentaire pour le moment.</p>
					{:else}
						<ul class="mt-10 space-y-8">
							{#each comments as comment (comment.id)}
								<li
									class="relative overflow-hidden rounded-lg border border-gray-400 bg-white p-6 shadow-sm"
								>
									<p class="mb-3">{comment.content}</p>
									<p class="text-sm text-black">
										Par {comment.user.status ? `${comment.user.status} ` : ''}{comment.user
											.first_name}
										{comment.user.last_name}{comment.user.specialty
											? `, ${comment.user.specialty}`
											: ''} •
										{new Date(comment.created_at).toLocaleDateString()}
									</p>
									{#if $userProfileStore && $userProfileStore.id === comment.user_id}
										<button
											on:click={() => handleDeleteComment(comment.id)}
											class="absolute top-4 right-4 text-black hover:text-gray-800"
											disabled={isLoadingDelete[comment.id]}
										>
											{#if isLoadingDelete[comment.id]}
												<svg class="h-5 w-5 animate-spin text-black" viewBox="0 0 24 24">
													<circle
														class="opacity-25"
														cx="12"
														cy="12"
														r="10"
														stroke="currentColor"
														stroke-width="4"
													/>
													<path
														class="opacity-75"
														fill="currentColor"
														d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
													/>
												</svg>
											{:else}
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
														d="M6 18L18 6M6 6l12 12"
													/>
												</svg>
											{/if}
										</button>
									{/if}
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.prose :where(h2):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
		font-size: 1.25rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
		color: black;
	}
	.prose :where(p):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
		margin-bottom: 1rem;
		color: black;
	}
</style>
