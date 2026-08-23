"""
live_seed.py — Fetch real-time data from TMDB and load it into CognoDB.
Run: python live_seed.py

Requires TMDB_API_KEY in the .env file.
"""

import os
import httpx
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
URI = os.getenv("CONGODB_CONNECTION_URL")
USERNAME = os.getenv("CONGODB_USERNAME", "cognodb")
PASSWORD = os.getenv("CONGODB_PASSWORD")

# We will fetch 2 pages of popular movies (approx 40 movies)
PAGES_TO_FETCH = 2 

def get_tmdb_data(endpoint, params=None):
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    url = f"https://api.themoviedb.org/3/{endpoint}"
    
    response = httpx.get(url, params=params)
    response.raise_for_status()
    return response.json()

def load_live_data(driver):
    print("[...] Fetching real-time genre list from TMDB...")
    genres_data = get_tmdb_data("genre/movie/list")
    genre_mapping = {g['id']: g['name'] for g in genres_data['genres']}
    
    movies = []
    actors = {}      # dict to deduplicate actors
    directors = {}   # dict to deduplicate directors
    acted_in = []
    directed = []
    movie_genres = {}

    for page in range(1, PAGES_TO_FETCH + 1):
        print(f"[...] Fetching popular movies (Page {page})...")
        popular = get_tmdb_data("movie/popular", {"page": page})
        
        for m in popular["results"]:
            movie_title = m["title"]
            
            movies.append({
                "title": movie_title,
                "year": int(m["release_date"].split("-")[0]) if m.get("release_date") else None,
                "rating": m.get("vote_average", 0.0),
                "tagline": m.get("overview", "")[:100] + "...", # truncate overview for UI
                "poster_url": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get('poster_path') else None
            })
            
            # Map genres
            m_genres = [genre_mapping[gid] for gid in m.get("genre_ids", []) if gid in genre_mapping]
            if m_genres:
                movie_genres[movie_title] = m_genres
            
            # Fetch Cast & Crew for this movie
            print(f"   -> Fetching cast & crew for: {movie_title}")
            credits = get_tmdb_data(f"movie/{m['id']}/credits")
            
            # Top 6 actors per movie
            for cast in credits.get("cast", [])[:6]:
                actor_name = cast["name"]
                actors[actor_name] = {"name": actor_name, "born": None} # TMDB requires separate API call for birth year, keeping it simple
                acted_in.append((actor_name, movie_title, cast.get("character", "Unknown")))
                
            # Directors
            for crew in credits.get("crew", []):
                if crew["job"] == "Director":
                    dir_name = crew["name"]
                    directors[dir_name] = {"name": dir_name, "born": None}
                    directed.append((dir_name, movie_title))

            # Small delay to respect API rate limits
            time.sleep(0.1)

    print("\n---------------------------------------------------")
    print(f"[INFO] Fetched {len(movies)} movies, {len(actors)} actors, {len(directors)} directors.")
    print("[...] Pushing to CognoDB Graph Database...")
    
    with driver.session() as session:
        print("[...] Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("[...] Creating Genre nodes...")
        for genre_name in genre_mapping.values():
            session.run("MERGE (:Genre {name: $name})", name=genre_name)

        print("[...] Creating Movie nodes...")
        for m in movies:
            session.run(
                """
                MERGE (m:Movie {title: $title})
                SET m.year = $year, m.rating = $rating,
                    m.tagline = $tagline, m.poster_url = $poster_url
                """,
                **m,
            )

        print("[...] Creating Actor nodes...")
        for a in actors.values():
            session.run("MERGE (a:Actor {name: $name}) SET a.born = $born", **a)

        print("[...] Creating Director nodes...")
        for d in directors.values():
            session.run("MERGE (d:Director {name: $name}) SET d.born = $born", **d)

        print("[...] Creating ACTED_IN relationships...")
        for actor, movie, role in acted_in:
            session.run(
                """
                MATCH (a:Actor {name: $actor}), (m:Movie {title: $movie})
                MERGE (a)-[:ACTED_IN {role: $role}]->(m)
                """,
                actor=actor, movie=movie, role=role,
            )

        print("[...] Creating DIRECTED relationships...")
        for director, movie in directed:
            session.run(
                """
                MATCH (d:Director {name: $director}), (m:Movie {title: $movie})
                MERGE (d)-[:DIRECTED]->(m)
                """,
                director=director, movie=movie,
            )

        print("[...] Creating IN_GENRE relationships...")
        for movie, genres in movie_genres.items():
            for genre in genres:
                session.run(
                    """
                    MATCH (m:Movie {title: $movie}), (g:Genre {name: $genre})
                    MERGE (m)-[:IN_GENRE]->(g)
                    """,
                    movie=movie, genre=genre,
                )

        counts = session.run("""
            MATCH (m:Movie) WITH count(m) AS movies
            MATCH (a:Actor) WITH movies, count(a) AS actors
            MATCH (d:Director) WITH movies, actors, count(d) AS directors
            MATCH (g:Genre) RETURN movies, actors, directors, count(g) AS genres
        """).single()
        print(f"\n[OK] Live Seed complete!")
        print(f"   Movies: {counts['movies']}, Actors: {counts['actors']}, "
              f"Directors: {counts['directors']}, Genres: {counts['genres']}")


if __name__ == "__main__":
    if not TMDB_API_KEY:
        print("[ERROR] Missing TMDB_API_KEY in .env file.")
        exit(1)
    if not URI or not PASSWORD:
        print("[ERROR] Missing CONGODB_CONNECTION_URL or CONGODB_PASSWORD in .env")
        exit(1)
        
    print(f"[...] Connecting to {URI} ...")
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    try:
        driver.verify_connectivity()
        print("[OK] Connected to Database!")
        load_live_data(driver)
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
    finally:
        driver.close()

