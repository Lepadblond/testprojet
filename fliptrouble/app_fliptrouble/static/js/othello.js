let etatCases = [];
let tour = "red";
let nombreCoupJouable = 0;
let othelloSocket;
let couleurJoueur = ""
let tourPasse = false;

function InitialiserWebsocket() {
    const roomName = 'partie_1';
    othelloSocket = new WebSocket(`ws://${window.location.host}/ws/othello/${roomName}/`);

    othelloSocket.onopen = function() {
        console.log("Connexion à la salle WebSocket réussie");
    };

    othelloSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        if (data.type === 'chat') {
            const message = data.message;
            const otherUser = data.username || 'Inconnu';
            postMessage(otherUser, message);
        }
    
        if (data.type === 'start_game') {
            demarrerPartie();
        }
    
        if (data.type === 'move') {
            const row = data.row;
            const col = data.col;
            const color = data.color;
            etatCases[row][col] = color;
            choisirCouleurCase(row, col);
        }
    
        if (data.type === 'assign_color') {
            const color = data.color;
            console.log(`Vous êtes assigné au tour des ${color === 'blue' ? 'Bleus' : 'Rouges'}`);
            couleurJoueur = color;
        }

        if (data.type === 'change_turn') {

            tour = (tour === 'blue') ? 'red' : 'blue';
            document.getElementById("message").textContent = "";
            gererTour();
            gererMessageTour();
        }

        if (data.type === 'abandon'){
            for (let row = 0; row < 8; row++) {
                for (let col = 0; col < 8; col++) {
                    document.getElementById(`case-${row}${col}`).disabled = true;
                }
            }
        
            // desactiverBoutonNulle()
            desactiverBoutonAbandonner()
        
            const joueurGagnant = (tour === 'blue') ? "Rouge" : "Bleu";
            document.getElementById("message").textContent = `${joueurGagnant} a gagné !`;
        }
    };

    othelloSocket.onclose = function(e) {
        console.error('Connexion WebSocket fermée');
    };

    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatContainer = document.getElementById('chatMessages');

    const postMessage = (username, message) => {
        if (message.trim() === '') return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message';
        messageDiv.innerHTML = `<p><strong>${username} :</strong> ${message}</p>`;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value;

        if (message.trim() === '') return;

        othelloSocket.send(JSON.stringify({
            'message': message,
            'username': username,
            'type': 'chat'
        }));
        chatInput.value = '';
    });
}

function gererEtatCases() {
    for (let row = 0; row < 8; row++) {
        etatCases[row] = [];
        for (let col = 0; col < 8; col++) {
            etatCases[row][col] = 'empty';
        }
    }
}

function compterCases() {
    let bleues = 0;
    let rouges = 0;
    let casesVides = 0;

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            if (etatCases[row][col] === 'blue') {
                bleues++;
            } else if (etatCases[row][col] === 'red') {
                rouges++;
            } else if (etatCases[row][col] === 'empty') {
                casesVides++;
            }
        }
    }

    document.getElementById("compteurBleu").textContent = bleues;
    document.getElementById("compteurRouge").textContent = rouges;

    if (casesVides === 0 || bleues === 0 || rouges === 0) {
       
        let message = "";
        if (bleues > rouges) {
            message = "Les bleus gagnent !";
        } else if (rouges > bleues) {
            message = "Les rouges gagnent !";
        } else {
            message = "C'est une égalité !";
        }
        document.getElementById("message").textContent = message;
    }
}

function afficherCases() {
    const othelloContainer = document.getElementById("Othello");
    othelloContainer.innerHTML = '';

    const gridDiv = document.createElement("div");
    gridDiv.className = "d-flex flex-column align-items-center";
    for (let row = 0; row < 8; row++) {
        const rowDiv = document.createElement("div");
        rowDiv.className = "d-flex";
        for (let col = 0; col < 8; col++) {
            const button = document.createElement("button");
            button.className = "btn btn-outline-secondary m-1";
            button.style.width = "50px";
            button.style.height = "50px";
            button.id = `case-${row}${col}`;
            button.style.backgroundColor = "";

            if (etatCases[row][col] === 'blue') {
                button.style.backgroundColor = "blue";
            } else if (etatCases[row][col] === 'red') {
                button.style.backgroundColor = "red";c
            }

            button.addEventListener('click', function() {
                if (etatCases[row][col] == 'empty' && estMouvementValide(row, col) && tour === couleurJoueur) {
                    
                    othelloSocket.send(JSON.stringify({
                        'type': 'move',
                        'row': row,
                        'col': col,
                        'color': tour
                    }));
                }
            });
            rowDiv.appendChild(button);
        }
        gridDiv.appendChild(rowDiv);
    }
    othelloContainer.appendChild(gridDiv);
    
    marquerCasesJouables();
    compterCases();
}

function choisirCouleurCase(row, col) {

    etatCases[row][col] = tour;
    verifierCasesAdjacentes(row, col);
    tour = (tour === 'blue') ? 'red' : 'blue';

    afficherCases();
    gererTour();
}

function estMouvementValide(row, col) {
    const directions = [
        [-1, 0], [1, 0], [0, -1], [0, 1],
        [-1, -1], [-1, 1], [1, -1], [1, 1]
    ];

    const couleurActuelle = tour;
    const couleurAdverse = couleurActuelle === 'blue' ? 'red' : 'blue';

    for (let direction of directions) {
        let currentRow = row + direction[0];
        let currentCol = col + direction[1];
        let foundAdversaryPiece = false;

        while (currentRow >= 0 && currentRow < 8 && currentCol >= 0 && currentCol < 8) {
            const piece = etatCases[currentRow][currentCol];
            
            if (piece === 'empty') break;
            if (piece === couleurActuelle) {
                if (foundAdversaryPiece) return true;
                else break;
            }
            if (piece === couleurAdverse) foundAdversaryPiece = true;

            currentRow += direction[0];
            currentCol += direction[1];
        }
    }
    return false;
}

function verifierCasesAdjacentes(row, col) {
    const directions = [
        [-1, 0], [1, 0], [0, -1], [0, 1],
        [-1, -1], [-1, 1], [1, -1], [1, 1]
    ];

    const couleurActuelle = etatCases[row][col];
    const couleurAdverse = couleurActuelle === 'blue' ? 'red' : 'blue';

    directions.forEach(direction => {
        let currentRow = row + direction[0];
        let currentCol = col + direction[1];
        let piecesToFlip = [];

        while (currentRow >= 0 && currentRow < 8 && currentCol >= 0 && currentCol < 8) {
            const piece = etatCases[currentRow][currentCol];
            
            if (piece === 'empty') {
                break;
            }

            if (piece === couleurActuelle) {
                piecesToFlip.forEach(([r, c]) => {
                    etatCases[r][c] = couleurActuelle;
                    document.getElementById(`case-${r}${c}`).style.backgroundColor = couleurActuelle;
                });
                break;
            }

            if (piece === couleurAdverse) {
                piecesToFlip.push([currentRow, currentCol]);
            }

            currentRow += direction[0];
            currentCol += direction[1];
        }
    });
}

function marquerCasesJouables() {
    if (tour == couleurJoueur){
        nombreCoupJouable = 0;
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                if (etatCases[row][col] === 'empty' && estMouvementValide(row, col)) {
                    nombreCoupJouable++;
                    document.getElementById(`case-${row}${col}`).style.backgroundColor = "rgba(211, 211, 211, 0.35)";
                }
            }
        }
    }
}

function verifierMouvementsDisponibles() {
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            if (etatCases[row][col] === 'empty' && estMouvementValide(row, col)) {
                return true;
            }
        }
    }
    return false;
}

function passerTour() {
    othelloSocket.send(JSON.stringify({
        'type': 'pass_turn',
        'username': username,
    }));
}

function afficherMessagePasserTour() {
    const messageContainer = document.getElementById("message");
    messageContainer.textContent = `${tour === 'blue' ? "Bleus" : "Rouges"} n'ont pas de coup possible.`;

    const passerTourButton = document.createElement("button");
    passerTourButton.className = "bg-bleu btn btn-primary mt-3";
    passerTourButton.textContent = "Passer le tour";
    passerTourButton.addEventListener("click", function() {
        passerTour();
    });

    console.log(passerTourButton)

    messageContainer.appendChild(passerTourButton);

    console.log(messageContainer)
}

function gererMessageTour(){
    if(tour === couleurJoueur){
        if(tourPasse){
            afficherMessagePasserTour()
            tourPasse = false;
        } else{
            document.getElementById("message").textContent = `C'est à vous de jouer!`;
        }
    } 
    else{
        document.getElementById("message").textContent = `C'est au tour de l'adversaire!`;
    }
}

function gererTour() {
    if (verifierMouvementsDisponibles()) {
        marquerCasesJouables();
    } else {
       tourPasse = true;
    }
    gererMessageTour();
    compterCases();    
}

function ConfigurerPositionDepart() {
    const positionBleue = [
        { row: 3, col: 3 },
        { row: 4, col: 4 }
    ];

    const positionRouge = [
        { row: 3, col: 4 },
        { row: 4, col: 3 }
    ];

    positionBleue.forEach(pos => {
        etatCases[pos.row][pos.col] = 'blue';
        document.getElementById(`case-${pos.row}${pos.col}`).style.backgroundColor = "blue";
    });

    positionRouge.forEach(pos => {
        etatCases[pos.row][pos.col] = 'red';
        document.getElementById(`case-${pos.row}${pos.col}`).style.backgroundColor = "red";
    });
}

// function desactiverBoutonNulle() {
//     const boutonDemanderNulle = document.getElementById('boutonDemanderNulle');
//     boutonDemanderNulle.disabled = true;
//     boutonDemanderNulle.classList.add('disabled'); 
//     boutonDemanderNulle.style.pointerEvents = 'none';
//     boutonDemanderNulle.style.opacity = '0.5';
// }

function desactiverBoutonAbandonner() {
    const boutonAbandonner = document.getElementById('boutonAbandonner');
    boutonAbandonner.disabled = true;
    boutonAbandonner.classList.add('disabled'); 
    boutonAbandonner.style.pointerEvents = 'none';
    boutonAbandonner.style.opacity = '0.5';
}

function demarrerPartie() {
    gererEtatCases();
    afficherCases();
    ConfigurerPositionDepart();
    marquerCasesJouables();

    document.getElementById("compteurCard").classList.remove("d-none");
    gererMessageTour();
    compterCases();

    $("#boutonAbandonner").removeClass("d-none");
    // $("#boutonDemanderNulle").removeClass("d-none");
    $("#messageAvant").addClass("d-none");
    $("#boutonRegleAvant").addClass("d-none");
    $("#boutonReglePendant").removeClass("d-none");
}

function abandonnerPartie() {
    othelloSocket.send(JSON.stringify({
        'type': 'abandon',
        'username': username,
    }));
}

// function demanderNulle() {
//     document.getElementById("messageNulle").textContent = `${tour === 'blue' ? "Bleu" : "Rouge"} a demandé une partie nulle.`;
// }

$(document).ready(function () {
    // Création et ajout des boutons dynamiques
    const startButton = $('<button class="btn btn-primary mb-3 bg-bleu" id="demarrerPartie">Démarrer</button>');
    $("#boutonDemarrer").append(startButton);

    const abandonButton = $('<button class="btn btn-danger mb-3 w-100" id="abandonnerPartie">Abandonner</button>');
    $("#boutonAbandonner").append(abandonButton);

    // const nulleButton = $('<button class="bg-bleu btn btn-secondary mb-3 w-100" id="demanderNulle">Demander une nulle</button>');
    // $("#boutonDemanderNulle").append(nulleButton);

    const regleButtonPendant = $('<button>', {
        id: 'openOverlay',
        class: 'btn btn-primary bg-bleu',
        text: 'Voir les règlements'
    });

    // Gestion de l'overlay
    const overlay = $("#overlay");
    const openButtonAvant = $("#boutonRegleAvant");
    const openButtonPendant= $("#boutonReglePendant");
    const closeButton = $("#closeOverlay");

    openButtonAvant.on("click", function () {
        overlay.removeClass("d-none");
    });

    openButtonPendant.on("click", function () {
        overlay.removeClass("d-none");
    });

    closeButton.on("click", function () {
        overlay.addClass("d-none");
    });

    // Ferme l'overlay si l'on clique en dehors du contenu
    overlay.on("click", function (e) {
        if ($(e.target).is(overlay)) {
            overlay.addClass("d-none");
        }
    });

    // Ajout du bouton dans le conteneur
    $("#boutonReglePendant").append(regleButtonPendant);

    // Actions des boutons
    $("#demarrerPartie").on("click", function() {
        $(this).hide();  // Cache le bouton "Démarrer"
        $("#messageAvant").text("À l'attente d'un 2e joueur...");
        InitialiserWebsocket();  // Initialise le websocket
    });

    $("#abandonnerPartie").on("click", function() {
        abandonnerPartie();  // Appel de la fonction d'abandon
    });

    // $("#demanderNulle").on("click", function() {
    //     demanderNulle();  // Appel de la fonction de demande de nulle
    // });
});
