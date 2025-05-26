import time
from copy import deepcopy
from uuid import uuid4
from fastapi import Cookie, FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(CORSMiddleware,
    allow_origins=["*", "http://localhost:8000"],
    allow_credentials=True
    )

class UserInfo:
    last_edited_time_nanos : int
    last_seen_map: list[list[tuple[int, int, int]]]

    def __init__(self, carte):
        self.last_seen_map = deepcopy(carte)
        self.last_edited_time_nanos = round(time.time() * 1000000000)



class Carte:
    keys : set[str]
    users: dict[str, ]
    nx: int
    ny: int
    data: list[list[tuple[int,int,int]]]

    def __init__(self, nx: int, ny: int, timeout_nanos: int = 1000000000):
        self.keys = set()
        self.nx = nx
        self.ny = ny
        self.data = [
            [ (0,0,0) for _ in range(ny)]
            for _ in range(nx)
            ]
        self.timeout_nanos = timeout_nanos
        self.users = {}
        self.user_ids = set()

    def create_new_key(self):
        key = str(uuid4())
        self.keys.add(key)
        return key
    
    def is_valid_key(self, key: str):
        return key in self.keys
    
    def create_new_user_id(self):
        user_id = str(uuid4())
        self.user_ids.add(user_id)
        return user_id
    
    def is_valid_user_id(self, user_id:str):
        return user_id in self.user_ids

cartes : dict[str, Carte] = {
    "0000": Carte(nx=10, ny=10),
}


class PixelUpdate(BaseModel):
    x: int
    y: int
    color: list[int]




@app.get("/api/v1/{nom_carte}/preinit")
async def preinit(nom_carte: str):
    carte = cartes[nom_carte]
    if not carte:
        return{"error": "Je n'ai pas trouvé la carte."}
    
    key = carte.create_new_key()
    res = JSONResponse({"key": key})
    res.set_cookie("key", key, secure=True, max_age=360, samesite="none")
    return res

@app.get("/api/v1/{nom_carte}/init")
async def init(nom_carte: str,
                query_key: str = Query(alias="key"),
                cookie_key: str = Cookie(alias="key")):
    carte = cartes[nom_carte]
    if carte is None:
        return{"error": "Je n'ai pas trouvé la carte."}
    if query_key != cookie_key:
        return {"error": "Les clés ne correspondent pas"}
    if not carte.is_valid_key(cookie_key):
        return{"error": "La clé n'est pas valide"}
    
    user_id = carte.create_new_user_id()
    user_info = UserInfo(carte.data)
    carte.users[user_id] = user_info
    res = JSONResponse({
        "id": user_id,
        "nx": carte.nx,
        "ny": carte.ny,
        "data": carte.data,
        #"timeout":carte.timeout_nanos,
    })
    res.set_cookie("id", user_id, secure=True, samesite="none", max_age=3600)
    return res


@app.get("/api/v1/{nom_carte}/deltas")
async def get_deltas(nom_carte: str,
                        query_user_id: str = Query(alias="id"),
                        cookie_key: str = Cookie(alias="key"),
                        cookie_user_id: str = Cookie(alias="id")):
    carte = cartes[nom_carte]
    if carte is None:
        return{"error": "Je n'ai pas trouvé la carte."}
    if not carte.is_valid_key(cookie_key):
        return{"error": "La clé n'est pas valide"}
    if query_user_id != cookie_user_id:
        return{"error": "Les identifiants des utilisateurs ne correspondent pas"}
    if not carte.is_valid_user_id(query_user_id):
        return{"error": "L'utilisateur n'est pas valide"}

    user_info = carte.users[query_user_id]
    user_carte = user_info.last_seen_map

    deltas: list[tuple[int, int, int, int, int]] = []
    for x in range(carte.nx):
        for y in range(carte.ny):
            if carte.data[x][y] != user_carte[x][y]:
                deltas.append((x, y, *carte.data[x][y]))
    
    user_info.last_seen_map = deepcopy(carte.data)
    user_info.last_edited_time_nanos = round(time.time() * 1000000000)

    return {
        "id": query_user_id,
        "nx": carte.nx,
        "ny": carte.ny,
        "data": carte.data,
        "deltas": deltas
        }



@app.post("/api/v1/{nom_carte}/update_pixel")
async def update_pixel(nom_carte: str,
                        pixel: PixelUpdate,
                        cookie_key: str = Cookie(alias="key"),
                        cookie_user_id: str = Cookie(alias="id")):
    carte = cartes[nom_carte]
    if carte is None:
        return{"error": "Je n'ai pas trouvé la carte."}
    if not carte.is_valid_key(cookie_key):
        return{"error": "La clé n'est pas valide"}
    if not carte.is_valid_user_id(cookie_user_id):
        return{"error": "L'utilisateur n'est pas valide"}
    
    now = time.time()
    cooldown = 10
    last_edit = carte.users[cookie_user_id].last_edited_time_nanos / 1000000000
    if now - last_edit < cooldown:
        time_left = round(cooldown - (now - last_edit))
        return {"error": f"Tu es trop impatient ! Attends encore {time_left} secondes avant de pouvoir rejouer."}

    x = pixel.x
    y = pixel.y
    color = pixel.color

    if not (0 <= x < carte.nx and 0 <= y < carte.ny):
        return{"error": "Les coordonnées sont en dehors des limites de la carte"}
    if len(color) != 3 or any(not (0 <= col <= 255) for col in color):
        return{"error": "La couleur n'est pas valide"}   
    
    carte.data[x][y] = tuple(color)
    carte.users[cookie_user_id].last_edited_time_nanos = round(now * 1000000000)

    return {"x": x,
            "y": y,
            "color": color,
            "timestamp": now
            }
