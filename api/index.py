from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import time
import random

app = FastAPI(title="Ultimate IG Scraper API", description="Max Features with Media Links")

# Rotating User-Agents as a primary backup strategy against basic blocks
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
]

@app.get("/")
def read_root():
    return {"message": "System Active. Endpoint: /api/insta?username=target", "dev_tag": "@lakshitpatidar"}

async def fetch_ig_data(username: str, client: httpx.AsyncClient, retries=2):
    """Fetches data with a built-in backup retry mechanism"""
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    for attempt in range(retries):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "x-ig-app-id": "936619743392459",
            "Accept": "*/*",
        }
        try:
            response = await client.get(url, headers=headers, timeout=15.0)
            if response.status_code == 200:
                return response.json(), "success"
            elif response.status_code == 404:
                return None, "user_not_found"
        except Exception as e:
            if attempt == retries - 1:
                return None, f"failed_after_retries: {str(e)}"
            time.sleep(1) # Small delay before backup attempt
            
    return None, "blocked_by_instagram"

@app.get("/api/insta")
async def get_insta_info(username: str):
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        raw_data, status_msg = await fetch_ig_data(username, client)
        
        if status_msg != "success" or not raw_data:
            return JSONResponse(status_code=400, content={
                "dev_tag": "@lakshitpatidar",
                "error": "Failed to fetch data.",
                "reason": status_msg,
                "reality_check": "If this says blocked, Instagram detected Vercel. You need proxies."
            })

        try:
            user_data = raw_data['data']['user']
            
            # Extracting Posts with Max Quality Download Links
            media_downloads = []
            timeline = user_data.get("edge_owner_to_timeline_media", {})
            for edge in timeline.get("edges", [])[:12]: # Gets up to 12 recent posts
                node = edge.get("node", {})
                
                # Handling Sidecar (Carousel / Multiple images in one post)
                children = []
                if "edge_sidecar_to_children" in node:
                    for child_edge in node["edge_sidecar_to_children"].get("edges", []):
                        child_node = child_edge.get("node", {})
                        children.append({
                            "type": child_node.get("__typename"),
                            "image_hd_url": child_node.get("display_url"),
                            "video_url": child_node.get("video_url") if child_node.get("is_video") else None
                        })

                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                
                media_downloads.append({
                    "post_id": node.get("id"),
                    "shortcode": node.get("shortcode"),
                    "type": node.get("__typename"),
                    "caption": caption_edges[0].get("node", {}).get("text", "") if caption_edges else "",
                    "likes": node.get("edge_liked_by", {}).get("count", 0),
                    "comments": node.get("edge_media_to_comment", {}).get("count", 0),
                    "is_video": node.get("is_video"),
                    "views": node.get("video_view_count") if node.get("is_video") else None,
                    "download_links": {
                        "main_image_hd": node.get("display_url"),
                        "main_video_hd": node.get("video_url") if node.get("is_video") else None,
                        "carousel_media": children if children else None
                    }
                })

            # Building the Fully Advanced Payload
            result = {
                "dev_tag": "@lakshitpatidar",
                "system_status": {
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                    "backup_engine": "Active (Auto-Retries Enabled)"
                },
                "profile": {
                    "username": user_data.get("username"),
                    "full_name": user_data.get("full_name"),
                    "bio": user_data.get("biography"),
                    "profile_pic_hd_download": user_data.get("profile_pic_url_hd"),
                    "is_private": user_data.get("is_private"),
                    "is_verified": user_data.get("is_verified")
                },
                "network_stats": {
                    "followers_count": user_data.get("edge_followed_by", {}).get("count"),
                    "following_count": user_data.get("edge_follow", {}).get("count"),
                    "note": "To get exact list of followers/following, Instagram requires login cookies. Impossible anonymously."
                },
                "story_data": {
                    "status": "Unavailable",
                    "reason": "Story extraction strictly requires an authenticated sessionid cookie. Unauthenticated access is blocked by Meta."
                },
                "recent_media_with_downloads": media_downloads
            }
            return JSONResponse(content=result)

        except Exception as e:
            return JSONResponse(status_code=500, content={"dev_tag": "@lakshitpatidar", "error": "Parsing error", "details": str(e)})
  
