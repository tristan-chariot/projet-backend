import time
from copy import deepcopy
from uuid import uuid4
from fastapi import Cookie, FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


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
        self.last_edited_time_nanos = round(time.time()) * 1000000000



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

@app.get("/api/v1/{nom_carte}/preinit")
async def preinit(nom_carte: str):
    carte = cartes[nom_carte]
    if not carte:
        return{"error": "Je nai pas trouvé la carte."}
    
    key = carte.create_new_key()
    res = JSONResponse({"key": key})
    res.set_cookie("key", key, secure=True, maxe_age=360, samesite="none")
    return res

@app.get("/api/v1/{carte}/init")
async def init(nom_carte: str,
                query_key: str = Query(alias="key"),
                cookie_key: str = Cookie(alias="key")):
    carte = cartes[nom_carte]
    if carte is None:
        return{"error": "Je nai pas trouvé la carte."}
    if query_key != cookie_key:
        return {"error": "Les clés ne correspondent pas"}
    if not carte.is_valid_key(cookie_key):
        return{"error": "La clé n'est pas valide"}
    
    user_id = carte.create_new_user_id()
    res = JSONResponse({
        "id": "user id",
        "nx": carte.nx,
        "ny": carte.ny,
        "data": carte.data,
        #"timeout":carte.timeout_nanos,
    })
    res.set_cookie("id", user_id, secure=True, samesite="none", max_ahe=3600)
    return res


@app.get("/api/v1/{carte}/deltas")
async def init(nom_carte: str,
                query_user_id: str = Query(alias="id"),
                cookie_key: str = Cookie(alias="key"),
                cookie_user_id: str = Cookie(alias="id")):
    carte = cartes[nom_carte]
    if carte is None:
        return{"error": "Je nai pas trouvé la carte."}
    if carte.is_valid_key(cookie_key):
        return{"error": "La clé n'est pas valide"}
    if query_user_id != cookie_user_id:
        return{"error": "Les identifiants des utilisateurs ne correspondent pas"}
    if not carte.is_valid_user_id(query_user_id):
        return{"error": "La clé n'est pas valide"}

    user_info = carte.users[query_user_id]
    user_carte = user_info.last_seen_map

    deltas: list[tuple[int, int, int, int, int]] = []
    for y in range(carte.ny):
        for x in range(carte.nx):
            if carte.data[x][y] != user_carte[x][y]:
                deltas.append((y, x, *carte.data[x][y]))
    
    return {
        "id": "user id",
        "nx": carte.nx,
        "ny": carte.ny,
        "data": carte.data,
        "deltas": deltas
        }