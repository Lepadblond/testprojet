document.addEventListener("DOMContentLoaded", function() {
    const jeuStatsSelect = document.getElementById("JeuStats");
    const gameCardContainer = document.getElementById("Statistique");

    if (!jeuStatsSelect || !gameCardContainer) {
        console.error("Elements not found in the DOM.");
        return; 
    }

    jeuStatsSelect.addEventListener("change", function() {
        const selectedGame = this.value;
        gameCardContainer.innerHTML = ''; 

        let gameCard = '';

        if (selectedGame === 'othello') {
            gameCard = `
                <div class="card bg-white shadow-lg border-primary mt-2 mb-3">
                    <div class="bg-brunpale card-header">
                        <h3 class="font-weight-bold card-text text-center">Othello</h3>
                    </div>
                    <div class="card-body">
                        <p class="card-text">Nombre de parties jouées : 0</p>
                        <p class="card-text">Victoire : 0</p>
                        <p class="card-text">Nulle : 0</p>
                        <p class="card-text">Défaite : 0</p>
                    </div>
                </div>`;
        } else if (selectedGame === 'trouble') {
            gameCard = `
                <div class="card shadow-lg border-primary mt-2 mb-3">
                    <div class="bg-brunpale card-header">
                        <h3 class="font-weight-bold card-text text-center">Trouble</h3>
                    </div>
                    <div class="card-body">
                        <p class="card-text">Nombre de parties jouées : 0</p>
                        <p class="card-text">Victoire : 0</p>
                        <p class="card-text">Nulle : 0</p>
                        <p class="card-text">Défaite : 0</p>
                    </div>
                </div>`;
        }

        gameCardContainer.innerHTML = gameCard;
    });
});

