<!-- frontend/src/routes/comite/+page.svelte -->
<script lang="ts">
	import { AlertTriangle, CheckCircle, Loader2 } from 'lucide-svelte';

	// Get data loaded by +page.server.ts
	const { data } = $props<{ data: { referents: any[] } }>();

	// Use referents from database
	const referents = $derived(data.referents || []);

    // Define the missions
    const missions = [
        "Être référent(e) d\'une spécialité ou sous-spécialité",
        "Proposer des articles scientifiques pertinents à relayer",
        "Apporter des corrections aux synthèses générées par notre IA",
        "Valoriser votre engagement académique (mention sur le site, etc.)",
        "Rejoindre un réseau interdisciplinaire et engagé"
    ];

    let showForm = $state(false);
    let formData = $state({
        prenom: '', nom: '', statut: '', specialite: '', surSpecialite: '', centre: ''
    });
    let submissionStatus: 'idle' | 'loading' | 'success' | 'error' = $state('idle');
    let submissionMessage = $state('');

    function resetForm() {
        formData = {
            prenom: '', nom: '', statut: '', specialite: '', surSpecialite: '', centre: ''
        };
        submissionStatus = 'idle';
        submissionMessage = '';
    }

    function toggleForm() {
        showForm = !showForm;
        if (!showForm) resetForm();
    }

    async function handleSubmit() {
        submissionStatus = 'loading';
        submissionMessage = '';
        try {
            const response = await fetch('/api/committee-application', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.message || `Erreur ${response.status}`);
            submissionStatus = 'success';
            submissionMessage = result.message || 'Candidature envoyée !';
        } catch (err: any) {
            console.error("Application submission error:", err);
            submissionStatus = 'error';
            submissionMessage = err.message || "Une erreur est survenue.";
        }
    }

    function getSpecialtyEmoji(specialty: string): string {
        const emojiMap: Record<string, string> = {
            'Chirurgie orthopédique': '🦴', 'Chirurgie pédiatrique': '👶', 'Cardiologie': '❤️',
            'Endocrinologie – Diabétologie – Nutrition': '⚖️', 'Hématologie': '🩸',
            'Médecine physique et réadaptation': '🦿', 'Neurochirurgie': '🧠', 'Rhumatologie': '🦴', 'Urgences': '🚑', 'Urologie': '💧', 'Oncologie': '🎗️',
            'Médecine interne': '⚕️', 'Médecine vasculaire': '⚕️'
        };
        return emojiMap[specialty] || '⚕️';
    }

    $effect(() => {
        if (!showForm && submissionStatus !== 'idle') resetForm();
    });

</script>

<svelte:head>
	<title>Comité Scientifique - Veille Médicale</title>
	<meta
		name="description"
		content="Découvrez les médecins référents par spécialité du comité scientifique de Veille Médicale."
	/>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="min-h-screen bg-black px-4 py-12 pt-20 text-white font-sans">
	<div class="mx-auto max-w-4xl">
		<!-- En-tête -->
		<header class="mb-12 text-center">
			<h1 class="mb-4 text-4xl font-bold text-white sm:text-5xl">
                🏥 Référents par spécialité
            </h1>
		</header>

        <!-- Section Missions -->
        <section class="mb-16 rounded-lg bg-gray-800 p-6 shadow-lg">
            <h2 class="mb-6 text-center text-2xl font-semibold text-white sm:text-3xl">
                📋 Les missions des membres
            </h2>
            <ul class="list-disc space-y-3 pl-6 text-gray-300">
                {#each missions as mission}
                    <li>{mission}</li>
                {/each}
            </ul>
            <div class="mt-6 text-center">
                <button
                    on:click={toggleForm}
                    class="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                    {showForm ? 'Masquer le formulaire' : 'Rejoindre le comité'}
                </button>
            </div>
        </section>

        {#if showForm}
            <!-- Section Formulaire -->
            <section class="mb-16 rounded-lg bg-gray-800 p-6 shadow-lg transition-all duration-300 ease-in-out">
                <h2 class="mb-6 text-center text-2xl font-semibold text-white sm:text-3xl">
                    ✍️ Postuler au comité scientifique
                </h2>
                {#if submissionStatus === 'success'}
                    <div class="flex flex-col items-center justify-center text-center py-8 px-4 bg-gray-700 rounded-lg">
                        <CheckCircle class="h-12 w-12 text-green-400 mb-4" />
                        <h3 class="text-xl font-semibold mb-2 text-white">Candidature Envoyée !</h3>
                        <p class="text-gray-300 mb-6">{submissionMessage}</p>
                        <button on:click={toggleForm} class="bg-gray-600 hover:bg-gray-500 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm">
                            Fermer
                        </button>
                    </div>
                {:else}
                    <form on:submit|preventDefault={handleSubmit} class="space-y-4">
                         <div>
                            <label for="prenom" class="block text-gray-300 mb-1 text-sm">Prénom</label>
                            <input type="text" id="prenom" bind:value={formData.prenom} class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" required disabled={submissionStatus === 'loading'} />
                        </div>
                        <div>
                            <label for="nom" class="block text-gray-300 mb-1 text-sm">Nom</label>
                            <input type="text" id="nom" bind:value={formData.nom} class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" required disabled={submissionStatus === 'loading'} />
                        </div>
                        <div>
                            <label for="statut" class="block text-gray-300 mb-1 text-sm">Statut</label>
                            <input type="text" id="statut" bind:value={formData.statut} placeholder="Interne, Docteur, Professeur…" class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" required disabled={submissionStatus === 'loading'} />
                        </div>
                        <div>
                            <label for="specialite" class="block text-gray-300 mb-1 text-sm">Spécialité</label>
                            <input type="text" id="specialite" bind:value={formData.specialite} class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" required disabled={submissionStatus === 'loading'} />
                        </div>
                        <div>
                            <label for="surSpecialite" class="block text-gray-300 mb-1 text-sm">Sur-spécialité (optionnelle)</label>
                            <input type="text" id="surSpecialite" bind:value={formData.surSpecialite} class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" disabled={submissionStatus === 'loading'} />
                        </div>
                        <div>
                            <label for="centre" class="block text-gray-300 mb-1 text-sm">Centre d'exercice</label>
                            <input type="text" id="centre" bind:value={formData.centre} placeholder="CHU, hôpital, clinique, cabinet…" class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 border border-gray-600 text-sm" required disabled={submissionStatus === 'loading'} />
                        </div>
                        <div class="bg-gray-700/50 p-3 rounded-lg border border-gray-600">
                            <p class="text-gray-400 text-xs mb-1">📝 Exemple :</p>
                            <p class="text-gray-400 text-xs italic">Dr Xavier Montjou, Chirurgie orthopédique, Spécialiste en chirurgie de la main, AP-HP</p>
                        </div>
                        <div class="pt-2 space-y-3">
                            {#if submissionStatus === 'error'}
                                <p class="text-sm text-red-400 flex items-center gap-1.5 p-3 bg-red-900/30 border border-red-700 rounded-md" role="alert">
                                    <AlertTriangle class="h-4 w-4 flex-shrink-0"/> {submissionMessage}
                                </p>
                            {/if}
                            <button type="submit" class="w-full inline-flex items-center justify-center bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed" disabled={submissionStatus === 'loading'}>
                                {#if submissionStatus === 'loading'}
                                    <Loader2 class="mr-2 h-5 w-5 animate-spin" /> Envoi en cours...
                                {:else}
                                    Envoyer ma candidature
                                {/if}
                            </button>
                        </div>
                    </form>
                {/if}
            </section>
        {/if}

        <!-- Liste des Référents - Robust Loop with Index Check -->
        <section>
            {#each referents as referent, index (referent.name)}
                <!-- Show heading if it's the first item OR if specialty differs from the previous item -->
                {#if index === 0 || referent.specialty !== referents[index - 1].specialty}
                    <h2 class="mt-10 mb-6 border-b border-gray-700 pb-2 text-2xl font-semibold text-teal-400 sm:text-3xl">
                        {referent.emoji || getSpecialtyEmoji(referent.specialty)} {referent.specialty}
                        <span class="text-sm text-gray-500 ml-2">
                            ({referents.filter((r: any) => r.specialty === referent.specialty).length} référent{referents.filter((r: any) => r.specialty === referent.specialty).length > 1 ? 's' : ''})
                        </span>
                    </h2>
                {/if}

                <!-- Referent Card -->
                <div class="mb-6 rounded-lg bg-gray-800 p-5 shadow-md transition-shadow hover:shadow-lg">
                    <h3 class="text-xl font-bold text-white">{referent.name}</h3>
                    <p class="text-md text-gray-300">{referent.title}</p>
                    {#if referent.affiliation}
                        <p class="text-sm text-gray-400">{referent.affiliation}</p>
                    {/if}
                    {#if referent.focus}
                        <p class="mt-1 text-sm text-gray-400 italic">{referent.focus}</p>
                    {/if}
                </div>
            {/each}
        </section>
	</div>
</div>

<style>
/* Styles remain the same */
</style>