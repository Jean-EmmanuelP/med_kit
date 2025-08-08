<!-- Dashboard page for managing committee referents -->
<script lang="ts">
	import { supabase } from '$lib/supabase';
	import userProfileStore from '$lib/stores/user';
	import { AlertTriangle, CheckCircle, Loader2, Plus, Trash2, Edit, Save, X, Eye, EyeOff } from 'lucide-svelte';

	// Get data loaded by +page.server.ts
	const { data } = $props<{ data: any }>();

	// State for referents management
	let referents = $state<any[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let isSaving = $state(false);
	let saveMessage = $state<string | null>(null);

	// State for adding/editing referent
	let showForm = $state(false);
	let editingIndex = $state<number | null>(null);
	let formData = $state({
		specialty: '',
		name: '',
		title: '',
		affiliation: '',
		focus: '',
		emoji: ''
	});

	// State for preview
	let showPreview = $state(true);

	// Predefined emojis for common specialties
	const specialtyEmojis = [
		{ specialty: 'Chirurgie orthopédique', emoji: '🦴' },
		{ specialty: 'Chirurgie pédiatrique', emoji: '👶' },
		{ specialty: 'Cardiologie', emoji: '❤️' },
		{ specialty: 'Endocrinologie – Diabétologie – Nutrition', emoji: '⚖️' },
		{ specialty: 'Hématologie', emoji: '🩸' },
		{ specialty: 'Médecine physique et réadaptation', emoji: '🦿' },
		{ specialty: 'Neurochirurgie', emoji: '🧠' },
		{ specialty: 'Rhumatologie', emoji: '🦴' },
		{ specialty: 'Urgences', emoji: '🚑' },
		{ specialty: 'Urologie', emoji: '💧' },
		{ specialty: 'Oncologie', emoji: '🎗️' },
		{ specialty: 'Médecine interne', emoji: '⚕️' },
		{ specialty: 'Médecine vasculaire', emoji: '⚕️' },
		{ specialty: 'Dermatologie', emoji: '🩹' },
		{ specialty: 'Gastroentérologie', emoji: '🍽️' },
		{ specialty: 'Gynécologie', emoji: '👩‍⚕️' },
		{ specialty: 'Pneumologie', emoji: '🫁' },
		{ specialty: 'Psychiatrie', emoji: '🧠' },
		{ specialty: 'Radiologie', emoji: '📷' },
		{ specialty: 'Anesthésie', emoji: '💉' }
	];

	// Common emojis for new specialties
	const commonEmojis = ['⚕️', '🏥', '👨‍⚕️', '👩‍⚕️', '🩺', '💊', '🔬', '🧬', '🫀', '🫁', '🧠', '🦴', '🩸', '💉', '🩹', '🚑', '❤️', '💧', '🎗️', '⚖️', '🦿', '👶', '🧠', '🩺'];

	// Get existing specialties from current referents
	const existingSpecialties = $derived([...new Set(referents.map(r => r.specialty))].sort());

	// Function to get emoji for specialty
	function getEmojiForSpecialty(specialty: string): string {
		const predefined = specialtyEmojis.find(s => s.specialty === specialty);
		return predefined?.emoji || '⚕️';
	}

	// Load referents from database
	async function loadReferents() {
		try {
			isLoading = true;
			error = null;

			const { data: referentsData, error: fetchError } = await supabase
				.from('committee_referents')
				.select('*')
				.order('specialty')
				.order('name');

			if (fetchError) throw fetchError;

			referents = referentsData || [];
		} catch (err: any) {
			console.error('Error loading referents:', err);
			error = 'Erreur lors du chargement des référents';
		} finally {
			isLoading = false;
		}
	}

	// Save referents to database
	async function saveReferents() {
		try {
			isSaving = true;
			saveMessage = null;

			// Delete all existing referents
			const { error: deleteError } = await supabase
				.from('committee_referents')
				.delete()
				.neq('id', 0); // Delete all records

			if (deleteError) throw deleteError;

			// Insert new referents (sans l'id)
			if (referents.length > 0) {
				const referentsToInsert = referents.map(({ id, created_at, updated_at, ...referent }) => referent);
				
				const { error: insertError } = await supabase
					.from('committee_referents')
					.insert(referentsToInsert);

				if (insertError) throw insertError;
			}

			saveMessage = 'Référents sauvegardés avec succès !';
			setTimeout(() => { saveMessage = null; }, 3000);
		} catch (err: any) {
			console.error('Error saving referents:', err);
			error = 'Erreur lors de la sauvegarde';
		} finally {
			isSaving = false;
		}
	}

	// Add new referent
	function addReferent() {
		editingIndex = null;
		formData = {
			specialty: '',
			name: '',
			title: '',
			affiliation: '',
			focus: '',
			emoji: ''
		};
		showForm = true;
	}

	// Edit existing referent
	function editReferent(index: number) {
		editingIndex = index;
		formData = { ...referents[index] };
		showForm = true;
	}

	// Save referent from form
	function saveReferent() {
		if (!formData.specialty.trim() || !formData.name.trim()) {
			error = 'La spécialité et le nom sont obligatoires';
			return;
		}

		// Prepare referent data (without id for new referents)
		const referentData = {
			specialty: formData.specialty.trim(),
			name: formData.name.trim(),
			title: formData.title.trim() || null,
			affiliation: formData.affiliation.trim() || null,
			focus: formData.focus.trim() || null,
			emoji: formData.emoji || getEmojiForSpecialty(formData.specialty)
		};

		if (editingIndex !== null) {
			// Update existing referent - keep the id
			referents[editingIndex] = { 
				...referents[editingIndex], // Keep existing id and other fields
				...referentData 
			};
		} else {
			// Add new referent - don't include id, let database generate it
			referents = [...referents, referentData];
		}

		// Sort referents by specialty, then by name
		referents.sort((a, b) => {
			const specialtyCompare = a.specialty.localeCompare(b.specialty, 'fr', { sensitivity: 'base' });
			if (specialtyCompare !== 0) {
				return specialtyCompare;
			}
			return a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' });
		});

		showForm = false;
		error = null;
	}

	// Delete referent
	function deleteReferent(index: number) {
		if (confirm('Êtes-vous sûr de vouloir supprimer ce référent ?')) {
			referents = referents.filter((_, i) => i !== index);
		}
	}

	// Cancel form
	function cancelForm() {
		showForm = false;
		editingIndex = null;
		error = null;
	}

	// Auto-select emoji when specialty changes
	$effect(() => {
		if (formData.specialty && !formData.emoji) {
			const predefined = specialtyEmojis.find(s => s.specialty === formData.specialty);
			if (predefined) {
				formData.emoji = predefined.emoji;
			} else {
				formData.emoji = getEmojiForSpecialty(formData.specialty);
			}
		}
	});

	// Load referents on mount
	$effect(() => {
		loadReferents();
	});
</script>

<div class="min-h-screen bg-black text-white">
	<!-- Header -->
	<div class="bg-gray-900 px-4 py-8 border-b border-gray-800">
		<div class="mx-auto max-w-6xl">
			<div class="flex items-center justify-between mb-4">
				<div>
					<h1 class="text-xl font-bold text-white">Gestion des Référents</h1>
					<p class="text-sm text-gray-400">Gérez les membres du comité scientifique</p>
				</div>
				<div class="flex items-center gap-3">
					<a 
						href="/dashboard" 
						class="inline-flex items-center px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors text-sm font-medium"
					>
						← Retour au Dashboard
					</a>
					<div class="text-xs text-gray-400">
						{$userProfileStore?.first_name}
						{#if $userProfileStore?.has_all_power}
							<span class="ml-1 text-red-400 font-medium">(Super Admin)</span>
						{:else if $userProfileStore?.is_admin}
							<span class="ml-1 text-green-400 font-medium">(Admin)</span>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="px-4 py-8">
		<div class="mx-auto max-w-6xl">
			<!-- Actions Bar -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-4">
					<button
						onclick={addReferent}
						class="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-md transition-colors text-sm font-medium"
					>
						<Plus class="w-4 h-4 mr-2" />
						Ajouter un référent
					</button>
					<button
						onclick={saveReferents}
						disabled={isSaving}
						class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{#if isSaving}
							<Loader2 class="w-4 h-4 mr-2 animate-spin" />
							Sauvegarde...
						{:else}
							<Save class="w-4 h-4 mr-2" />
							Sauvegarder
						{/if}
					</button>
				</div>
				<div class="text-sm text-gray-400">
					{referents.length} référent(s)
				</div>
			</div>

			<!-- Messages -->
			{#if error}
				<div class="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-md text-red-400 flex items-center gap-2">
					<AlertTriangle class="w-4 h-4" />
					{error}
				</div>
			{/if}

			{#if saveMessage}
				<div class="mb-4 p-3 bg-green-900/30 border border-green-700 rounded-md text-green-400 flex items-center gap-2">
					<CheckCircle class="w-4 h-4" />
					{saveMessage}
				</div>
			{/if}

			<!-- Loading State -->
			{#if isLoading}
				<div class="flex items-center justify-center py-12">
					<Loader2 class="w-8 h-8 animate-spin text-teal-400" />
					<span class="ml-3 text-gray-400">Chargement des référents...</span>
				</div>
			{:else}
				<!-- Referents List -->
				<div class="space-y-6">
					{#each referents as referent, index (referent.name)}
						<!-- Show heading if it's the first item OR if specialty differs from the previous item -->
						{#if index === 0 || referent.specialty !== referents[index - 1].specialty}
							<h2 class="mt-8 mb-4 border-b border-gray-700 pb-2 text-xl font-semibold text-teal-400">
								{referent.emoji || getEmojiForSpecialty(referent.specialty)} {referent.specialty}
								<span class="text-sm text-gray-500 ml-2">
									({referents.filter(r => r.specialty === referent.specialty).length} référent{referents.filter(r => r.specialty === referent.specialty).length > 1 ? 's' : ''})
								</span>
							</h2>
						{/if}

						<!-- Referent Card -->
						<div class="bg-gray-800 rounded-lg p-4 shadow-md">
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<h3 class="text-lg font-bold text-white">{referent.name}</h3>
									<p class="text-md text-gray-300">{referent.title}</p>
									{#if referent.affiliation}
										<p class="text-sm text-gray-400">{referent.affiliation}</p>
									{/if}
									{#if referent.focus}
										<p class="mt-1 text-sm text-gray-400 italic">{referent.focus}</p>
									{/if}
								</div>
								<div class="flex items-center gap-2 ml-4">
									<button
										onclick={() => editReferent(index)}
										class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
										title="Modifier"
									>
										<Edit class="w-4 h-4" />
									</button>
									<button
										onclick={() => deleteReferent(index)}
										class="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded-md transition-colors"
										title="Supprimer"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								</div>
							</div>
						</div>
					{/each}

					{#if referents.length === 0}
						<div class="text-center py-12 text-gray-400">
							<p>Aucun référent pour le moment.</p>
							<p class="text-sm mt-2">Cliquez sur "Ajouter un référent" pour commencer.</p>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- Add/Edit Modal -->
{#if showForm}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
		<div class="w-full max-w-4xl bg-gray-900 rounded-lg shadow-xl">
			<!-- Modal Header -->
			<div class="flex items-center justify-between bg-gray-800 px-6 py-4 rounded-t-lg">
				<h2 class="text-xl font-semibold text-white">
					{editingIndex !== null ? 'Modifier le référent' : 'Ajouter un référent'}
				</h2>
				<div class="flex items-center gap-3">
					<button
						onclick={() => showPreview = !showPreview}
						class="inline-flex items-center px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
						title={showPreview ? 'Masquer l\'aperçu' : 'Afficher l\'aperçu'}
					>
						{#if showPreview}
							<EyeOff class="w-4 h-4 mr-1" />
							Masquer l'aperçu
						{:else}
							<Eye class="w-4 h-4 mr-1" />
							Afficher l'aperçu
						{/if}
					</button>
					<button
						onclick={cancelForm}
						class="text-gray-400 hover:text-white transition-colors p-1 rounded-md hover:bg-gray-700"
					>
						<X class="w-5 h-5" />
					</button>
				</div>
			</div>

			<!-- Modal Content -->
			<div class="p-6">
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<!-- Form Section -->
					<div class="space-y-4">
						<form onsubmit={saveReferent} class="space-y-4">
							<div>
								<label for="specialty" class="block text-gray-300 mb-1 text-sm">Spécialité *</label>
								<div class="space-y-2">
									<input 
										type="text" 
										id="specialty" 
										bind:value={formData.specialty} 
										class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" 
										required 
									/>
									<!-- Existing Specialties Toggle -->
									{#if existingSpecialties.length > 0}
										<div class="bg-gray-800 rounded-lg p-3">
											<p class="text-xs text-gray-400 mb-2">Spécialités existantes :</p>
											<div class="flex flex-wrap gap-1">
												{#each existingSpecialties as specialty}
													<button
														type="button"
														onclick={() => {
															formData.specialty = specialty;
															formData.emoji = getEmojiForSpecialty(specialty);
														}}
														class="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors flex items-center gap-1"
														title="Cliquer pour sélectionner"
													>
														<span>{getEmojiForSpecialty(specialty)}</span>
														<span>{specialty}</span>
													</button>
												{/each}
											</div>
										</div>
									{/if}
								</div>
							</div>
							<div>
								<label for="name" class="block text-gray-300 mb-1 text-sm">Nom *</label>
								<input 
									type="text" 
									id="name" 
									bind:value={formData.name} 
									class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" 
									required 
								/>
							</div>
							<div>
								<label for="title" class="block text-gray-300 mb-1 text-sm">Titre</label>
								<input 
									type="text" 
									id="title" 
									bind:value={formData.title} 
									class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" 
								/>
							</div>
							<div>
								<label for="affiliation" class="block text-gray-300 mb-1 text-sm">Affiliation</label>
								<input 
									type="text" 
									id="affiliation" 
									bind:value={formData.affiliation} 
									class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" 
								/>
							</div>
							<div>
								<label for="focus" class="block text-gray-300 mb-1 text-sm">Spécialisation</label>
								<input 
									type="text" 
									id="focus" 
									bind:value={formData.focus} 
									class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" 
								/>
							</div>
							<div>
								<label for="emoji" class="block text-gray-300 mb-1 text-sm">Emoji</label>
								<div class="flex items-center gap-2">
									<input 
										type="text" 
										id="emoji" 
										bind:value={formData.emoji} 
										class="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" 
										placeholder="⚕️"
									/>
									<div class="text-2xl">{formData.emoji || '⚕️'}</div>
								</div>
								<!-- Emoji Picker -->
								<div class="mt-2">
									<p class="text-xs text-gray-400 mb-2">Emojis populaires :</p>
									<div class="flex flex-wrap gap-1">
										{#each commonEmojis as emoji}
											<button
												type="button"
												onclick={() => formData.emoji = emoji}
												class="text-xl p-1 hover:bg-gray-700 rounded transition-colors"
												title="Cliquer pour sélectionner"
											>
												{emoji}
											</button>
										{/each}
									</div>
								</div>
							</div>
							<div class="flex gap-3 pt-4">
								<button 
									type="submit" 
									class="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm"
								>
									{editingIndex !== null ? 'Modifier' : 'Ajouter'}
								</button>
								<button 
									type="button" 
									onclick={cancelForm}
									class="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm"
								>
									Annuler
								</button>
							</div>
						</form>
					</div>

					<!-- Preview Section -->
					{#if showPreview}
						<div class="bg-gray-800 rounded-lg p-4">
							<h3 class="text-lg font-semibold text-white mb-4">Aperçu du rendu</h3>
							{#if formData.specialty && formData.name}
								<div class="space-y-4">
									<!-- Specialty Header -->
									<h2 class="border-b border-gray-700 pb-2 text-xl font-semibold text-teal-400">
										{formData.emoji || getEmojiForSpecialty(formData.specialty)} {formData.specialty}
									</h2>
									
									<!-- Referent Card Preview -->
									<div class="bg-gray-700 rounded-lg p-4 shadow-md">
										<h3 class="text-lg font-bold text-white">{formData.name}</h3>
										{#if formData.title}
											<p class="text-md text-gray-300">{formData.title}</p>
										{/if}
										{#if formData.affiliation}
											<p class="text-sm text-gray-400">{formData.affiliation}</p>
										{/if}
										{#if formData.focus}
											<p class="mt-1 text-sm text-gray-400 italic">{formData.focus}</p>
										{/if}
									</div>
								</div>
							{:else}
								<div class="text-center py-8 text-gray-400">
									<p>Remplissez au moins la spécialité et le nom pour voir l'aperçu</p>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if} 