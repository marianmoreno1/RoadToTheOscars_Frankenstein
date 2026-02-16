
import os
import time
import requests
import pandas as pd
from urllib.parse import urlparse, parse_qs

# ========= CONFIG =========
API_KEY = "AIzaSyAi3WIZheX9j_9widqinpbI6drnp6mBQjc"
YOUTUBE_URL = "https://www.youtube.com/watch?v=EnN6DL2Z7vA"

OUTPUT_DIR = "/Users/allende/Desktop/5 ICAI /Segundo cuatri/Analítica Social y de la Web /Trabajo Práctico /IMDB Y ROTTENTOMATOES"
OUTPUT_FILENAME = "youtube_comments_EnN6DL2Z7vA.xlsx"
# ==========================

def extract_video_id(url: str) -> str:
    """Extrae el videoId de URLs tipo watch?v=... o youtu.be/..."""
    parsed = urlparse(url)
    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        return parsed.path.strip("/")
    qs = parse_qs(parsed.query)
    if "v" in qs and qs["v"]:
        return qs["v"][0]
    raise ValueError(f"No pude extraer el video ID de la URL: {url}")

def fetch_all_comments(api_key: str, video_id: str) -> list[dict]:
    """
    Descarga comentarios con YouTube Data API v3 (commentThreads.list).
    Incluye top-level comments y respuestas incluidas en el snippet (si las hay).
    Nota: La API NO devuelve todas las respuestas si hay muchas; para eso habría que llamar también a comments.list.
    """
    all_rows = []
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet,replies",
        "videoId": video_id,
        "maxResults": 100,     # máximo permitido
        "textFormat": "plainText",
        "key": api_key,
        "order": "time",       # por fecha (puedes cambiar a "relevance")
    }

    next_page_token = None

    while True:
        if next_page_token:
            params["pageToken"] = next_page_token
        else:
            params.pop("pageToken", None)

        r = requests.get(base_url, params=params, timeout=30)
        data = r.json()

        # Errores típicos: comentarios deshabilitados, API key mala, etc.
        if "error" in data:
            raise RuntimeError(f"Error API: {data['error']}")

        items = data.get("items", [])
        for it in items:
            top = it["snippet"]["topLevelComment"]["snippet"]
            top_comment_id = it["snippet"]["topLevelComment"]["id"]

            all_rows.append({
                "type": "top_level",
                "comment_id": top_comment_id,
                "parent_id": "",
                "author": top.get("authorDisplayName", ""),
                "author_channel_url": top.get("authorChannelUrl", ""),
                "like_count": top.get("likeCount", 0),
                "published_at": top.get("publishedAt", ""),
                "updated_at": top.get("updatedAt", ""),
                "text": top.get("textDisplay", ""),
            })

            # Respuestas incluidas (puede que no estén todas si hay muchas)
            replies = it.get("replies", {}).get("comments", [])
            for rep in replies:
                rep_snip = rep["snippet"]
                all_rows.append({
                    "type": "reply",
                    "comment_id": rep.get("id", ""),
                    "parent_id": top_comment_id,
                    "author": rep_snip.get("authorDisplayName", ""),
                    "author_channel_url": rep_snip.get("authorChannelUrl", ""),
                    "like_count": rep_snip.get("likeCount", 0),
                    "published_at": rep_snip.get("publishedAt", ""),
                    "updated_at": rep_snip.get("updatedAt", ""),
                    "text": rep_snip.get("textDisplay", ""),
                })

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        # Pequeña pausa para ir suave con la API
        time.sleep(0.1)

    return all_rows

def main():
    video_id = extract_video_id(YOUTUBE_URL)

    rows = fetch_all_comments(API_KEY, video_id)
    if not rows:
        print("No se han encontrado comentarios (o están deshabilitados).")
        return

    df = pd.DataFrame(rows)

    # Asegura que existe la carpeta
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    df.to_excel(out_path, index=False)

    print(f"✅ Guardado: {out_path}")
    print(f"Total filas (comentarios+respuestas incluidas): {len(df)}")

if __name__ == "__main__":
    main()
