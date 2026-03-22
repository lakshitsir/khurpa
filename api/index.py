from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import time
import random
from bs4 import BeautifulSoup

app = FastAPI(title="Pro IG Scraper with Quad Fallback", description="Direct -> GraphQL -> RapidAPI -> HTML Scrape")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

# KANU: BINA ISKE LAYER 3 KABHI NAHI CHALEGA
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY_HERE" 
RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"

@app.get("/")
def read_root():
    return {"message": "Quad Fallback System Active. Endpoint: /api/insta?username=target", "dev_tag": "@lakshitpatidar"}

async def fetch_layer_1(username: str, client: httpx.AsyncClient):
    """Layer 1: Standard Web Profile Info"""
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {"User-Agent": random.choice(USER_AGENTS), "x-ig-app-id": "936619743392459", "Accept": "*/*"}
    res = await client.get(url, headers=headers, timeout=10.0)
    res.raise_for_status()
    return res.json()

async def fetch_layer_2(username: str, client: httpx.AsyncClient):
    """Layer 2: Alternative GraphQL Endpoint"""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {"User-Agent": random.choice(USER_AGENTS), "x-ig-app-id": "936619743392459", "sec-fetch-site": "same-origin"}
    res = await client.get(url, headers=headers, timeout=10.0)
    res.raise_for_status()
    return res.json()

async def fetch_layer_3_rapidapi(username: str, client: httpx.AsyncClient):
    """Layer 3: RapidAPI Fallback"""
    if RAPIDAPI_KEY == "YOUR_RAPIDAPI_KEY_HERE":
        raise ValueError("RapidAPI key missing.")
    url = f"https://{RAPIDAPI_HOST}/v1/info?username_or_id_or_url={username}"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}
    res = await client.get(url, headers=headers, timeout=15.0)
    res.raise_for_status()
    return res.json()

async def fetch_layer_4_html(username: str, client: httpx.AsyncClient):
    """Layer 4: Dumb HTML Scrape (Kanu's Demand)"""
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", # Pretend to be Googlebot to maybe get meta tags
        "Accept-Language": "en-US,en;q=0.9"
    }
    res = await client.get(url, headers=headers, timeout=10.0)
    res.raise_for_status()
    
    soup = BeautifulSoup(res.text, "html.parser")
    meta_desc = soup.find("meta", property="og:description")
    
    if not meta_desc:
        raise ValueError("No meta description found. Instagram threw a login wall or blank SPA page.")
        
    content = meta_desc.get("content", "")
    # Content format usually: "1.5M Followers, 400 Following, 100 Posts - See Instagram photos and videos..."
    try:
        parts = content.split(", ")
        followers = parts[0].split(" ")[0]
        following = parts[1].split(" ")[0]
        posts = parts[2].split(" ")[0]
        return {
            "html_fallback_used": True,
            "followers": followers,
            "following": following,
            "posts": posts,
            "username": username,
            "warning": "Data is extremely limited because HTML scraping on React apps is an outdated approach."
        }
    except Exception:
        raise ValueError("Failed to parse HTML string. Meta tag format changed.")

@app.get("/api/insta")
async def get_insta_info(username: str):
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        raw_data = None
        method_used = "None"
        error_logs = []

        # Tying Layer 1
        try:
            raw_data = await fetch_layer_1(username, client)
            method_used = "Layer 1 (Direct API)"
        except Exception as e1:
            error_logs.append(f"L1: {str(e1)}")
            
            # Trying Layer 2
            try:
                raw_data = await fetch_layer_2(username, client)
                method_used = "Layer 2 (GraphQL API)"
            except Exception as e2:
                error_logs.append(f"L2: {str(e2)}")
                
                # Trying Layer 3
                try:
                    raw_data = await fetch_layer_3_rapidapi(username, client)
                    method_used = "Layer 3 (RapidAPI)"
                except Exception as e3:
                    error_logs.append(f"L3: {str(e3)}")
                    
                    # Trying Layer 4 (HTML)
                    try:
                        raw_data = await fetch_layer_4_html(username, client)
                        method_used = "Layer 4 (HTML Scrape)"
                    except Exception as e4:
                        error_logs.append(f"L4: {str(e4)}")
                        
                        return JSONResponse(status_code=500, content={
                            "dev_tag": "@lakshitpatidar",
                            "status": "ALL SYSTEMS FAILED",
                            "reality_check": "Vercel IP blocked. No RapidAPI key. HTML returned login wall. You can't beat Meta without proper tools.",
                            "logs": error_logs
                        })

        # Process the data based on which layer succeeded
        try:
            result = {
                "dev_tag": "@lakshitpatidar",
                "system_status": {
                    "method_used": method_used,
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2)
                }
            }

            if method_used == "Layer 4 (HTML Scrape)":
                result["profile"] = {"username": raw_data.get("username")}
                result["stats"] = {
                    "followers": raw_data.get("followers"),
                    "following": raw_data.get("following"),
                    "posts": raw_data.get("posts")
                }
                result["warning"] = raw_data.get("warning")
                
            elif method_used in ["Layer 1 (Direct API)", "Layer 2 (GraphQL API)"]:
                user_data = raw_data['data']['user']
                result["profile"] = {
                    "username": user_data.get("username"),
                    "full_name": user_data.get("full_name"),
                    "biography": user_data.get("biography"),
                    "profile_pic_url_hd": user_data.get("profile_pic_url_hd"),
                    "is_private": user_data.get("is_private")
                }
                result["stats"] = {
                    "followers": user_data.get("edge_followed_by", {}).get("count"),
                    "following": user_data.get("edge_follow", {}).get("count")
                }
                
            else: # Layer 3 RapidAPI mapping
                user_data = raw_data.get("data", raw_data)
                result["profile"] = {"username": username, "profile_pic_url_hd": user_data.get("profile_pic_url_hd")}
                result["stats"] = {
                    "followers": user_data.get("follower_count", "N/A"),
                    "following": user_data.get("following_count", "N/A")
                }

            return JSONResponse(content=result)

        except Exception as parse_error:
            return JSONResponse(status_code=500, content={
                "dev_tag": "@lakshitpatidar",
                "error": "Failed to parse data structure",
                "method_used": method_used,
                "details": str(parse_error)
            })
    
