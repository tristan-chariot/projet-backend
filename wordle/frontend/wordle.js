const guessTry = document.getElementById('guessTry');
const submitButton = document.getElementById('submitButton');
const guessesContainer = document.getElementById('guesses');
const message = document.getElementById('message');
const Backend_URL = "http://localhost:8000" 



async function startGame() {
    try {
        const res = await fetch(`${Backend_URL}/start`, {
        credentials: "include"
        });
        const data = await res.json();
        console.log("Partie démarrée :", data);
    }
    catch (error) {
        message.textContent = "Erreur réseau, il est impossible de démarrer la partie";
    }
}



async function sendGuess(guess) {
    try {
        const res = await fetch(`${Backend_URL}/guess`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guess })
        });
        return await res.json();
    }
    catch (error) {
        message.textContent = "Erreur réseau pendant l'envoi du mot.";
        return null;
    }
}



function renderGuess(guess, feedback) {
    const row = document.createElement('div');
    for (let i = 0; i < guess.length; i++) {
        const span = document.createElement('span');
        span.textContent = guess[i].toUpperCase();
        span.classList.add('letter', feedback[i]);
        row.appendChild(span);
    }
    guessesContainer.appendChild(row);
}



submitButton.addEventListener('click', async () => {
    const guess = guessTry.value.trim().toLowerCase();
    if (guess.length !== 5) {
        message.textContent = "Le mot doit contenir 5 lettres.";
        return;
    }

    guessTry.value = '';
    message.textContent = '';

    const result = await sendGuess(guess);
    if (!result || !result.feedback) return;

    renderGuess(guess, result.feedback);

    if (result.status === 'win') {
        message.textContent = "Bravo ! Tu as gagné";
        guessTry.disabled = true;
        submitButton.disabled = true;
        return;
    }

    if (result.status === 'lose') {
        message.textContent = `Perdu ! Tu as utilisé toutes tes tentatives. Le mot était : ${result.secret_word.toUpperCase()}`;
        guessTry.disabled = true;
        submitButton.disabled = true;
    }
});



guessTry.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') submitButton.click();
});




startGame();