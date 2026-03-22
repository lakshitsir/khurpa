from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import time
import random
from bs4 import BeautifulSoup

app = FastAPI(title="Frankenstein IG API", description="Old Scrapers + RapidAPI + Cache")

# TERA BEWAKOOFI BHARA HARDCODED KEY SETUP. (Nayi key daalna yahan, purani leak ho chuki hai)
RAPIDAPI_KEY = "59128d6552msh5031f4c0d3f221dp114026jsna5803a7f43c1" 
RAPIDAPI_HOST = "instagram-looter2.p.rapidapi.com"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

# THE REAL OPTIMIZER: IN-MEMORY CACHE
# Ye RapidAPI ki calls bachayega aur API ko instant fast banayega
cache = {}
CACHE_TTL = 1800  # Data 30 minutes (1800 seconds) tak memory me rahega

@app.get("/")
def read_root():
    return {"message": "System Active with Cache. Endpoint: /api/insta?username=target", "dev_tag": "@lakshitpatidar"}

async def fetch_layer_1(username: str, client: httpx.AsyncClient):
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {"User-Agent": random.choice(USER_AGENTS), "x-ig-app-id": "936619743392459"}
    res = await client.get(url, headers=headers, timeout=8.0)
    res.raise_for_status()
    return res.json()

async def fetch_layer_2(username: str, client: httpx.AsyncClient):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {"User-Agent": random.choice(USER_AGENTS), "x-ig-app-id": "936619743392459"}
    res = await client.get(url, headers=headers, timeout=8.0)
    res.raise_for_status()
    return res.json()

async def fetch_layer_3_rapidapi(username: str, client: httpx.AsyncClient):
    # Dhyan rakhna, endpoint /profile ya /search ho sakta hai teri API ke hisaab se
    url = f"https://{RAPIDAPI_HOST}/profile" 
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    querystring = {"username": username}
    res = await client.get(url, headers=headers, params=querystring, timeout=12.0)
    res.raise_for_status()
    return res.json()

async def fetch_layer_4_html(username: str, client: httpx.AsyncClient):
    url = f"https://www.instagram.com/{username}/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    res = await client.get(url, headers=headers, timeout=8.0)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    meta_desc = soup.find("meta", property="og:description")
    if not meta_desc:
        raise ValueError("Login wall hit.")
    return {"raw_html_meta": meta_desc.get("content", "")}

@app.get("/api/insta")
async def get_insta_info(username: str):
    start_time = time.time()
    
    # 1. CACHE CHECK: Agar data pehle se memory me hai, to return kardo instantly
    if username in cache:
        cached_data, timestamp = cache[username]
        if time.time() - timestamp < CACHE_TTL:
            return JSONResponse(content={
                "dev_tag": "@lakshitpatidar",
                "system_status": {
                    "method": "Served from CACHE (Ultra Fast, Zero API Cost)",
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2)
                },
                "data": cached_data
            })

    # 2. CACHE MISS: Ab jaake network calls marna shuru karo
    async with httpx.AsyncClient() as client:
        raw_data = None
        method_used = "None"
        logs = []

        # Teri zidd: Purane code ko time waste karne do
        try:
            raw_data = await fetch_layer_1(username, client)
            method_used = "Layer 1 (Direct)"
        except Exception as e1:
            logs.append(f"L1 failed: {str(e1)}")
            
            try:
                raw_data = await fetch_layer_2(username, client)
                method_used = "Layer 2 (GraphQL)"
            except Exception as e2:
                logs.append(f"L2 failed: {str(e2)}")
                
                # Actual reliable method (RapidAPI)
                try:
                    raw_data = await fetch_layer_3_rapidapi(username, client)
                    method_used = "Layer 3 (RapidAPI)"
                except Exception as e3:
                    logs.append(f"L3 failed: {str(e3)}")
                    
                    # Teri dusri zidd: Dumb HTML scrape
                    try:
                        raw_data = await fetch_layer_4_html(username, client)
                        method_used = "Layer 4 (HTML)"
                    except Exception as e4:
                        logs.append(f"L4 failed: {str(e4)}")
                        return JSONResponse(status_code=500, content={
                            "dev_tag": "@lakshitpatidar",
                            "error": "Sab kuch fail ho gaya.",
                            "logs": logs
                        })

        # 3. SAVE TO CACHE: Aage ke liye data save kar lo
        cache[username] = (raw_data, time.time())

        result = {
            "dev_tag": "@lakshitpatidar",
            "system_status": {
                "method": method_used,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "logs": logs if logs else "Clean hit"
            },
            "data": raw_data
        }
        
        return JSONResponse(content=result)

