// trouble.js
// Identique ou très similaire à l’exemple précédent.
// Le code front-end n’a pas besoin de savoir qui est bot ou humain.
// Il reçoit juste les updates et les affiche.

let troubleSocket;
let myColor = null;
let currentTurn = null;
let lastDice = null;

const totalCases = 28;
let board = [];
let players = {};

document.addEventListener('DOMContentLoaded', function() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const roomName = 'trouble_room1';
    troubleSocket = new WebSocket(protocol + "//" + window.location.host + "/ws/trouble/" + roomName + "/");

    troubleSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'assign_color') {
            myColor = data.color;
            afficherMessage(`Vous êtes la couleur ${myColor}`);
        }
        if (data.type === 'update_state') {
            board = data.board;
            players = data.players;
            currentTurn = data.currentTurn;
            lastDice = data.lastDice;
            afficherMessage(data.message || "");
            renderAll();
        }
        if (data.type === 'dice_result') {
            lastDice = data.value;
            document.getElementById('diceResult').textContent = lastDice;
            afficherMessage(`Résultat du dé : ${lastDice}. Si c'est votre tour, choisissez un pion à déplacer.`);
        }
    };

    troubleSocket.onclose = function(e) {
        console.error("WebSocket fermé");
    };

    initBoard();
    document.getElementById('rollDiceBtn').addEventListener('click', function(){
        if (myColor === currentTurn) {
            troubleSocket.send(JSON.stringify({'type':'roll_dice'}));
        } else {
            afficherMessage("Ce n'est pas votre tour.");
        }
    });
});

function afficherMessage(msg) {
    document.getElementById('message').textContent = msg;
}

function initBoard() {
    const boardDiv = document.getElementById('board');
    boardDiv.innerHTML = '';
    for (let i = 0; i < totalCases; i++) {
        const cell = document.createElement('div');
        cell.className = 'case m-1';
        cell.style.width = '50px';
        cell.style.height = '50px';
        cell.style.border = '1px solid #fff';
        cell.style.textAlign = 'center';
        cell.style.lineHeight = '50px';
        cell.style.color = '#fff';
        cell.id = 'case-'+i;
        boardDiv.appendChild(cell);
    }
}

function renderAll() {
    renderBoard();
    renderPions();
}

function renderBoard() {
    for (let i = 0; i < totalCases; i++) {
        const cell = document.getElementById('case-'+i);
        cell.style.backgroundColor = '#333';
        cell.textContent = '';
        if (board[i]) {
            const col = board[i].color;
            cell.style.backgroundColor = col;
            cell.textContent = col.charAt(0).toUpperCase();
        }
    }
}

function renderPions() {
    const colors = ['blue','red','green','yellow'];
    colors.forEach(color => {
        const homeDiv = document.getElementById(color+'Home');
        if (homeDiv) homeDiv.innerHTML = '';
        players[color].pions.forEach((p, idx) => {
            if (p.pos === 'home') {
                const pion = createPion(color, idx);
                if (homeDiv) homeDiv.appendChild(pion);
            }
        });
    });
}

function createPion(color, index) {
    const pion = document.createElement('div');
    pion.style.width = '30px';
    pion.style.height = '30px';
    pion.style.borderRadius = '50%';
    pion.style.backgroundColor = color;
    pion.style.margin = '5px';
    pion.style.cursor = 'pointer';

    pion.addEventListener('click', function() {
        if (myColor === currentTurn && lastDice !== null) {
            troubleSocket.send(JSON.stringify({
                'type': 'move_pion',
                'color': color,
                'pionIndex': index,
                'steps': lastDice
            }));
        } else {
            afficherMessage("Vous ne pouvez pas bouger ce pion maintenant.");
        }
    });

    return pion;
}
