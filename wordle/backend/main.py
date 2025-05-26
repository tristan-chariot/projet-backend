from fastapi import FastAPI, Cookie, Request, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost", "http://127.0.0.1", "null",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Secret_Word = "AINSI"

games = {}

class GameState:
    def __init__(self, secret_word):
        self.secret_word = secret_word
        self.attempts = []
        self.max_attempts = 6
        self.won = False


class Guess(BaseModel):
    guess: str        



@app.get("/start")
async def start_game():
    user_id = str(uuid4())
    games[user_id] = GameState(Secret_Word)
    res = JSONResponse({"message": "Nouvelle partie créée.", "max_attempts": 6})
    res.set_cookie("user_id", user_id)
    return res



@app.post("/guess")
async def make_guess(guess_data: Guess = Body(...), user_id: str = Cookie(None)):
    if user_id is None or user_id not in games:
        return {"error": "La partie n'a pas été trouvée. Démarre une nouvelle partie (/start)."}

    guess = guess_data.guess.upper()

    game = games[user_id]

    if game.won:
        return {
            "message": "Tu as gagné la partie. Bravo !",
            "attempts": game.attempts
            }

    if len(game.attempts) >= game.max_attempts:
        return {
            "message": "Le nombre maximal d'essais a été atteint. Tu as perdu la partie",
            "attempts": game.attempts, "secret_word": game.secret_word
            }


    feedback = []

    for ind, let in enumerate(guess):
        if let == game.secret_word[ind]:
            feedback.append("correct")  
        elif let in game.secret_word:
            feedback.append("present")  
        else:
            feedback.append("absent")

    game.attempts.append({"guess": guess, "feedback": feedback})

    if guess == game.secret_word:
        game.won = True
        return {"message": "Tu as gagné la partie. Bravo !",
                "attempts": game.attempts,
                "status": "win",
                "feedback": feedback
                }

    elif len(game.attempts) == game.max_attempts:
        return {"message": "Le nombre maximal d'essais a été atteint. Tu as perdu la partie.",
                "attempts": game.attempts, "secret_word": game.secret_word,
                "status": "lose",
                "feedback": feedback
                }

    return {"attempt": len(game.attempts),
            "feedback": feedback,
            "attempts_left": game.max_attempts - len(game.attempts)
            }