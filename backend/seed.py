"""
seed.py — Load realistic movie data into CognoDB.
Run once: python seed.py

Uses parameterised Cypher with MERGE to be idempotent (safe to re-run).
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

URI = os.getenv("CONGODB_CONNECTION_URL")
USERNAME = os.getenv("CONGODB_USERNAME", "cognodb")
PASSWORD = os.getenv("CONGODB_PASSWORD")

# ── Seed data ────────────────────────────────────────────────────────────────

MOVIES = [
    {"title": "The Matrix", "year": 1999, "rating": 8.7, "tagline": "Welcome to the real world.", "poster_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg"},
    {"title": "The Matrix Reloaded", "year": 2003, "rating": 7.2, "tagline": "Free your mind.", "poster_url": "https://image.tmdb.org/t/p/w500/9TBE7O2tHo3KFZBqcFyRvQZJQRJ.jpg"},
    {"title": "The Matrix Revolutions", "year": 2003, "rating": 6.7, "tagline": "Everything that has a beginning has an end.", "poster_url": "https://image.tmdb.org/t/p/w500/lh4aGpd3U9rm9B8Oqr6CUgQLtZL.jpg"},
    {"title": "John Wick", "year": 2014, "rating": 7.4, "tagline": "Don't set him off.", "poster_url": "https://image.tmdb.org/t/p/w500/fZPSd91yGE9fCcCe6OoQr6E3Bev.jpg"},
    {"title": "Speed", "year": 1994, "rating": 7.3, "tagline": "Get ready for rush hour.", "poster_url": "https://image.tmdb.org/t/p/w500/kVB9hNMiTNGYsVvFi8qCNDf0Pvh.jpg"},
    {"title": "Point Break", "year": 1991, "rating": 7.2, "tagline": "100% pure adrenaline.", "poster_url": "https://image.tmdb.org/t/p/w500/rCdOiPnHHMC5fdTLtxLCBQaKOXk.jpg"},
    {"title": "Much Ado About Nothing", "year": 1993, "rating": 7.3, "tagline": "A romantic comedy.", "poster_url": "https://image.tmdb.org/t/p/w500/2N5GmDCn5lWM8VHt9rKFzrqrGMy.jpg"},
    {"title": "Inception", "year": 2010, "rating": 8.8, "tagline": "Your mind is the scene of the crime.", "poster_url": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg"},
    {"title": "Interstellar", "year": 2014, "rating": 8.6, "tagline": "Mankind was born on Earth. It was never meant to die here.", "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"},
    {"title": "The Dark Knight", "year": 2008, "rating": 9.0, "tagline": "Why so serious?", "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"},
    {"title": "Memento", "year": 2000, "rating": 8.4, "tagline": "Some memories are best forgotten.", "poster_url": "https://image.tmdb.org/t/p/w500/yuNs09hvpHVU1cBTCAk9zxsL2oW.jpg"},
    {"title": "Pulp Fiction", "year": 1994, "rating": 8.9, "tagline": "Just because you are a character doesn't mean you have character.", "poster_url": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg"},
    {"title": "Kill Bill: Vol. 1", "year": 2003, "rating": 8.1, "tagline": "Here comes the bride.", "poster_url": "https://image.tmdb.org/t/p/w500/v7TaX8kXMXs5yFFGR41guUDNcnB.jpg"},
    {"title": "Goodfellas", "year": 1990, "rating": 8.7, "tagline": "Three decades of life in the mafia.", "poster_url": "https://image.tmdb.org/t/p/w500/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg"},
    {"title": "The Departed", "year": 2006, "rating": 8.5, "tagline": "Lies. Betrayal. Sacrifice. How far will you take it?", "poster_url": "https://image.tmdb.org/t/p/w500/nT97ifVT2J1yMQmeq20Qblg61T.jpg"},
    {"title": "Avengers: Endgame", "year": 2019, "rating": 8.4, "tagline": "Whatever it takes.", "poster_url": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg"},
    {"title": "Iron Man", "year": 2008, "rating": 7.9, "tagline": "Heroes aren't born. They're built.", "poster_url": "https://image.tmdb.org/t/p/w500/78lPtwv72eTNqFW9COBF8ldiE5x.jpg"},
    {"title": "Captain America: Civil War", "year": 2016, "rating": 7.8, "tagline": "Divided We Fall", "poster_url": "https://image.tmdb.org/t/p/w500/rAGiXaUfPzY7CDd3MykBGPKAbGR.jpg"},
    {"title": "Guardians of the Galaxy", "year": 2014, "rating": 8.0, "tagline": "You're welcome.", "poster_url": "https://image.tmdb.org/t/p/w500/r7vmZjiyZw9rpJMQJdXpjgiCOk9.jpg"},
    {"title": "Forrest Gump", "year": 1994, "rating": 8.8, "tagline": "The world will never be the same once you've seen it through the eyes of Forrest Gump.", "poster_url": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg"},
]

ACTORS = [
    {"name": "Keanu Reeves", "born": 1964},
    {"name": "Laurence Fishburne", "born": 1961},
    {"name": "Carrie-Anne Moss", "born": 1967},
    {"name": "Hugo Weaving", "born": 1960},
    {"name": "Leonardo DiCaprio", "born": 1974},
    {"name": "Joseph Gordon-Levitt", "born": 1981},
    {"name": "Elliot Page", "born": 1987},
    {"name": "Tom Hardy", "born": 1977},
    {"name": "Christian Bale", "born": 1974},
    {"name": "Heath Ledger", "born": 1979},
    {"name": "Guy Pearce", "born": 1967},
    {"name": "John Travolta", "born": 1954},
    {"name": "Samuel L. Jackson", "born": 1948},
    {"name": "Uma Thurman", "born": 1970},
    {"name": "Ray Liotta", "born": 1954},
    {"name": "Robert De Niro", "born": 1943},
    {"name": "Matt Damon", "born": 1970},
    {"name": "Jack Nicholson", "born": 1937},
    {"name": "Robert Downey Jr.", "born": 1965},
    {"name": "Chris Evans", "born": 1981},
    {"name": "Scarlett Johansson", "born": 1984},
    {"name": "Tom Hanks", "born": 1956},
    {"name": "Chadwick Boseman", "born": 1976},
    {"name": "Mark Ruffalo", "born": 1967},
    {"name": "Chris Pratt", "born": 1979},
    {"name": "Matthew McConaughey", "born": 1969},
    {"name": "Anne Hathaway", "born": 1982},
    {"name": "Wentworth Miller", "born": 1972},
]

DIRECTORS = [
    {"name": "Lana Wachowski", "born": 1965},
    {"name": "Lilly Wachowski", "born": 1967},
    {"name": "Christopher Nolan", "born": 1970},
    {"name": "Quentin Tarantino", "born": 1963},
    {"name": "Martin Scorsese", "born": 1942},
    {"name": "Anthony Russo", "born": 1970},
    {"name": "James Gunn", "born": 1970},
    {"name": "Robert Zemeckis", "born": 1952},
    {"name": "Jon Favreau", "born": 1966},
    {"name": "Jan de Bont", "born": 1943},
    {"name": "Kathryn Bigelow", "born": 1951},
]

GENRES = ["Action", "Sci-Fi", "Thriller", "Drama", "Crime", "Comedy", "Romance", "Adventure", "Fantasy"]

ACTED_IN = [
    # The Matrix trilogy
    ("Keanu Reeves", "The Matrix", "Neo"),
    ("Keanu Reeves", "The Matrix Reloaded", "Neo"),
    ("Keanu Reeves", "The Matrix Revolutions", "Neo"),
    ("Laurence Fishburne", "The Matrix", "Morpheus"),
    ("Laurence Fishburne", "The Matrix Reloaded", "Morpheus"),
    ("Laurence Fishburne", "The Matrix Revolutions", "Morpheus"),
    ("Carrie-Anne Moss", "The Matrix", "Trinity"),
    ("Carrie-Anne Moss", "The Matrix Reloaded", "Trinity"),
    ("Hugo Weaving", "The Matrix", "Agent Smith"),
    # John Wick / Speed / Point Break (Keanu cross-overs)
    ("Keanu Reeves", "John Wick", "John Wick"),
    ("Keanu Reeves", "Speed", "Jack Traven"),
    ("Keanu Reeves", "Point Break", "Johnny Utah"),
    # Much Ado
    ("Keanu Reeves", "Much Ado About Nothing", "Don John"),
    # Inception
    ("Leonardo DiCaprio", "Inception", "Dom Cobb"),
    ("Joseph Gordon-Levitt", "Inception", "Arthur"),
    ("Elliot Page", "Inception", "Ariadne"),
    ("Tom Hardy", "Inception", "Eames"),
    # Interstellar
    ("Matthew McConaughey", "Interstellar", "Cooper"),
    ("Anne Hathaway", "Interstellar", "Brand"),
    ("Matt Damon", "Interstellar", "Mann"),
    # Dark Knight
    ("Christian Bale", "The Dark Knight", "Bruce Wayne"),
    ("Heath Ledger", "The Dark Knight", "Joker"),
    ("Tom Hardy", "The Dark Knight", "Bane"),
    # Memento
    ("Guy Pearce", "Memento", "Leonard"),
    # Pulp Fiction
    ("John Travolta", "Pulp Fiction", "Vincent Vega"),
    ("Samuel L. Jackson", "Pulp Fiction", "Jules Winnfield"),
    ("Uma Thurman", "Pulp Fiction", "Mia Wallace"),
    # Kill Bill
    ("Uma Thurman", "Kill Bill: Vol. 1", "The Bride"),
    # Goodfellas
    ("Ray Liotta", "Goodfellas", "Henry Hill"),
    ("Robert De Niro", "Goodfellas", "Jimmy Conway"),
    # The Departed
    ("Leonardo DiCaprio", "The Departed", "Billy Costigan"),
    ("Matt Damon", "The Departed", "Colin Sullivan"),
    ("Jack Nicholson", "The Departed", "Frank Costello"),
    ("Mark Ruffalo", "The Departed", "Dignam"),
    # MCU
    ("Robert Downey Jr.", "Iron Man", "Tony Stark"),
    ("Robert Downey Jr.", "Avengers: Endgame", "Tony Stark"),
    ("Chris Evans", "Captain America: Civil War", "Steve Rogers"),
    ("Chris Evans", "Avengers: Endgame", "Steve Rogers"),
    ("Scarlett Johansson", "Captain America: Civil War", "Natasha Romanoff"),
    ("Scarlett Johansson", "Avengers: Endgame", "Natasha Romanoff"),
    ("Samuel L. Jackson", "Iron Man", "Nick Fury"),
    ("Chadwick Boseman", "Captain America: Civil War", "T'Challa"),
    ("Chadwick Boseman", "Avengers: Endgame", "T'Challa"),
    ("Mark Ruffalo", "Avengers: Endgame", "Bruce Banner"),
    ("Chris Pratt", "Guardians of the Galaxy", "Peter Quill"),
    # Forrest Gump
    ("Tom Hanks", "Forrest Gump", "Forrest Gump"),
]

DIRECTED = [
    ("Lana Wachowski", "The Matrix"),
    ("Lilly Wachowski", "The Matrix"),
    ("Lana Wachowski", "The Matrix Reloaded"),
    ("Lilly Wachowski", "The Matrix Reloaded"),
    ("Lana Wachowski", "The Matrix Revolutions"),
    ("Lilly Wachowski", "The Matrix Revolutions"),
    ("Christopher Nolan", "Inception"),
    ("Christopher Nolan", "Interstellar"),
    ("Christopher Nolan", "The Dark Knight"),
    ("Christopher Nolan", "Memento"),
    ("Quentin Tarantino", "Pulp Fiction"),
    ("Quentin Tarantino", "Kill Bill: Vol. 1"),
    ("Martin Scorsese", "Goodfellas"),
    ("Martin Scorsese", "The Departed"),
    ("Anthony Russo", "Avengers: Endgame"),
    ("Anthony Russo", "Captain America: Civil War"),
    ("Jon Favreau", "Iron Man"),
    ("James Gunn", "Guardians of the Galaxy"),
    ("Robert Zemeckis", "Forrest Gump"),
    ("Jan de Bont", "Speed"),
    ("Kathryn Bigelow", "Point Break"),
]

MOVIE_GENRES = {
    "The Matrix": ["Action", "Sci-Fi"],
    "The Matrix Reloaded": ["Action", "Sci-Fi"],
    "The Matrix Revolutions": ["Action", "Sci-Fi"],
    "John Wick": ["Action", "Thriller"],
    "Speed": ["Action", "Thriller"],
    "Point Break": ["Action", "Thriller"],
    "Much Ado About Nothing": ["Comedy", "Romance"],
    "Inception": ["Action", "Sci-Fi", "Thriller"],
    "Interstellar": ["Sci-Fi", "Drama", "Adventure"],
    "The Dark Knight": ["Action", "Crime", "Thriller"],
    "Memento": ["Thriller", "Drama"],
    "Pulp Fiction": ["Crime", "Drama"],
    "Kill Bill: Vol. 1": ["Action", "Crime"],
    "Goodfellas": ["Crime", "Drama"],
    "The Departed": ["Crime", "Drama", "Thriller"],
    "Avengers: Endgame": ["Action", "Sci-Fi", "Adventure"],
    "Iron Man": ["Action", "Sci-Fi", "Adventure"],
    "Captain America: Civil War": ["Action", "Sci-Fi"],
    "Guardians of the Galaxy": ["Action", "Sci-Fi", "Comedy"],
    "Forrest Gump": ["Drama", "Comedy", "Romance"],
}


def seed(driver):
    with driver.session() as session:
        print("[...] Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("[...] Creating Genre nodes...")
        for genre in GENRES:
            session.run("MERGE (:Genre {name: $name})", name=genre)

        print("[...] Creating Movie nodes...")
        for m in MOVIES:
            session.run(
                """
                MERGE (m:Movie {title: $title})
                SET m.year = $year, m.rating = $rating,
                    m.tagline = $tagline, m.poster_url = $poster_url
                """,
                **m,
            )

        print("[...] Creating Actor nodes...")
        for a in ACTORS:
            session.run("MERGE (a:Actor {name: $name}) SET a.born = $born", **a)

        print("[...] Creating Director nodes...")
        for d in DIRECTORS:
            session.run("MERGE (d:Director {name: $name}) SET d.born = $born", **d)

        print("[...] Creating ACTED_IN relationships...")
        for actor, movie, role in ACTED_IN:
            session.run(
                """
                MATCH (a:Actor {name: $actor}), (m:Movie {title: $movie})
                MERGE (a)-[:ACTED_IN {role: $role}]->(m)
                """,
                actor=actor, movie=movie, role=role,
            )

        print("[...] Creating DIRECTED relationships...")
        for director, movie in DIRECTED:
            session.run(
                """
                MATCH (d:Director {name: $director}), (m:Movie {title: $movie})
                MERGE (d)-[:DIRECTED]->(m)
                """,
                director=director, movie=movie,
            )

        print("[...] Creating IN_GENRE relationships...")
        for movie, genres in MOVIE_GENRES.items():
            for genre in genres:
                session.run(
                    """
                    MATCH (m:Movie {title: $movie}), (g:Genre {name: $genre})
                    MERGE (m)-[:IN_GENRE]->(g)
                    """,
                    movie=movie, genre=genre,
                )

        # Count summary
        counts = session.run("""
            MATCH (m:Movie) WITH count(m) AS movies
            MATCH (a:Actor) WITH movies, count(a) AS actors
            MATCH (d:Director) WITH movies, actors, count(d) AS directors
            MATCH (g:Genre) RETURN movies, actors, directors, count(g) AS genres
        """).single()
        print(f"\n[OK] Seed complete!")
        print(f"   Movies: {counts['movies']}, Actors: {counts['actors']}, "
              f"Directors: {counts['directors']}, Genres: {counts['genres']}")


if __name__ == "__main__":
    if not URI or not PASSWORD:
        print("[ERROR] Missing CONGODB_CONNECTION_URL or CONGODB_PASSWORD in .env")
        exit(1)
    print(f"[...] Connecting to {URI} ...")
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    try:
        driver.verify_connectivity()
        print("[OK] Connected!")
        seed(driver)
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
    finally:
        driver.close()
