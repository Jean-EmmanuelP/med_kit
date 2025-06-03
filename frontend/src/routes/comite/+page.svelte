<!-- frontend/src/routes/comite/+page.svelte -->
<script lang="ts">
	import { AlertTriangle, CheckCircle, Loader2 } from 'lucide-svelte';

	// Define the referent data directly in the script
	// Ensure the initial array is sorted by specialty, then maybe by name for consistency
	const referents = [
        {
            specialty: 'Chirurgie orthopédique',
            name: 'Dr Félix Barbier',
            title: 'Docteur Junior en chirurgie orthopédique',
            affiliation: 'AP-HP',
            focus: 'Spécialiste en chirurgie de la main'
        },
		{
			specialty: 'Chirurgie pédiatrique',
			name: 'Dr Camille Girardin',
			title: 'Docteur Junior en chirurgie pédiatrique',
            affiliation: 'CHU de Lille',
			focus: 'Spécialiste en chirurgie ortho-pédiatrique'
		},
		{
			specialty: 'Endocrinologie – Diabétologie – Nutrition',
			name: 'Dr Baptiste Mazas',
			title: 'Interne en Endocrinologie-Diabétologie-Nutrition',
            affiliation: 'AP-HP',
			focus: 'Diabétologie, Nutrition, Prévention Cardiovasculaire, Médecine du Sport'
		},
        {
			specialty: 'Endocrinologie – Diabétologie – Nutrition',
			name: 'Dr Flora Lambert',
			title: 'Interne en Endocrinologie-Diabétologie-Nutrition',
            affiliation: 'AP-HP',
			focus: null // No specific focus listed
		},
        {
			specialty: 'Hématologie',
			name: 'Dr Alexis Talbot',
			title: 'MCU-PH, service d\'Immuno-Hématologie',
            affiliation: 'Hôpital Saint-Louis (AP-HP)',
			focus: 'Spécialiste en myélome multiple, immunothérapie, CAR-T cells'
		},
		{
			specialty: 'Neurochirurgie',
			name: 'Dr Gonzague Defrance',
			title: 'Docteur Junior en neurochirurgie',
            affiliation: 'AP-HP',
			focus: 'Spécialiste en chirurgie fonctionnelle'
		},
		{
			specialty: 'Rhumatologie',
			name: 'Dr Elisabetta Lanciano',
			title: 'Rhumatologie',
            affiliation: 'CH d\'Angoulême',
			focus: null // No specific focus listed
		},
		{
			specialty: 'Urgences',
			name: 'Dr Benjamin Chevallier',
			title: 'Médecine d\'urgence',
            affiliation: 'SAMU de Paris – SMUR Necker – Urgences adultes Paris Saint-Joseph, AP-HP',
			focus: null // No specific focus listed
		},
        {
            specialty: 'Cardiologie',
            name: 'Léo Azria',
            title: 'Interne de Cardiologie',
            affiliation: 'AP-HP',
            focus: null // No specific focus listed
        },
        {
            specialty: 'Urologie',
            name: 'Dr Maxime Pattou',
            title: 'Docteur Junior en urologie',
            affiliation: 'AP-HP',
            focus: 'Spécialiste en uro-oncologie'
        },
        {
            specialty: 'Rhumatologie',
            name: 'Félix Laborie',
            title: 'Interne de Rhumatologie',
            affiliation: 'AP-HP',
            focus: null // No specific focus listed
        },
        {
            specialty: 'Chirurgie pédiatrique',
            name: 'Maxence de Lanversin',
            title: 'Interne en chirurgie pédiatrique',
            affiliation: 'CHU de Poitiers',
            focus: 'Chirurgie plastique pédiatrique '
        },
        {
            specialty: 'Urologie',
            name: 'Dr Alexandra Clerget',
            title: 'Docteur en Urologie',
            affiliation: 'Hopital Paris Saint Joseph (ESPIC)',
            focus: 'Andrologie et médecine de la reproduction',
        },
        {
            specialty: 'Oncologie',
            name: 'Jean-Baptiste Demigné',
            title: 'Interne en oncologie médicale',
            affiliation: 'AP-HM Timone',
            focus: null,
        },
        {
            specialty: 'Médecine interne',
            name: 'Dr Romain Bollart',
            title: 'Chef de clinique dans le service de médecine interne',
            affiliation: 'CHU de Lariboisière, AP-HP',
            focus: null,
        },
        {
            specialty: 'Médecine vasculaire',
            name: 'Dr Benjamin Pariente',
            title: 'Chef de clinique dans le service d’Excellence en Hypertension Artérielle',
            affiliation: 'Hôpital Européen Georges-Pompidou, AP-HP',
            focus: 'Spécialiste en Hypertension Artérielle',
        }
	].sort((a, b) => { // Ensure sorting is done definitively here
        const specialtyCompare = a.specialty.localeCompare(b.specialty, 'fr', { sensitivity: 'base' });
        if (specialtyCompare !== 0) {
            return specialtyCompare;
        }
        // Optional: Sort by name within the same specialty
        return a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' });
    });

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
            'Neurochirurgie': '🧠', 'Rhumatologie': '🦴', 'Urgences': '🚑', 'Urologie': '💧', 'Oncologie': '🎗️'
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
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
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
                        {getSpecialtyEmoji(referent.specialty)} {referent.specialty}
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