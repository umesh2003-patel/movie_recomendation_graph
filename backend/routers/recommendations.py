"""
Recommendations router — multi-hop graph traversal queries.
These are exactly the queries where a graph DB outshines relational schemas.
"""

from fastapi import APIRouter, HTTPException
from database import get_session
from neo4j.exceptions import ServiceUnavailable

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/movie/{title}")
def recommend_for_movie(title: str, limit: int = 6):
    """
    Recommend movies via 3-hop traversal:
    Movie <- Actor -> Movie (same actor), then rank by shared genre + rating.
    A pure SQL version would need 3+ self-joins on a bridge table.
    """
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec:Movie)
                WHERE rec.title <> $title
                WITH rec, count(a) AS shared_actors
                OPTIONAL MATCH (m:Movie {title: $title})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec)
                WITH rec, shared_actors, count(g) AS shared_genres
                RETURN rec.title AS title,
                       rec.year AS year,
                       rec.rating AS rating,
                       rec.poster_url AS poster_url,
                       shared_actors,
                       shared_genres,
                       (shared_actors * 2 + shared_genres * 3 + coalesce(rec.rating, 0)) AS score
                ORDER BY score DESC LIMIT $limit
                """,
                title=title,
                limit=limit,
            )
            return [dict(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/actor-network/{name}")
def actor_network(name: str, hops: int = 2):
    """
    Find all actors reachable within N hops from a given actor via shared movies.
    Classic graph traversal — impossible to do efficiently in SQL.
    """
    hops = min(hops, 3)  # cap to protect the free-tier DB
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH path = (a:Actor {name: $name})-[:ACTED_IN*1..4]->(m:Movie)<-[:ACTED_IN*1..4]-(other:Actor)
                WHERE other.name <> $name
                RETURN DISTINCT other.name AS actor, length(path) AS distance
                ORDER BY distance ASC LIMIT 20
                """,
                name=name,
            )
            return [dict(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/similar-genre/{genre}")
def movies_by_genre(genre: str, limit: int = 12):
    """Fetch movies for a specific genre, ordered by rating."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (m:Movie)-[:IN_GENRE]->(g:Genre {name: $genre})
                RETURN m.title AS title, m.year AS year,
                       m.rating AS rating, m.poster_url AS poster_url
                ORDER BY m.rating DESC LIMIT $limit
                """,
                genre=genre,
                limit=limit,
            )
            return [dict(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/genres")
def list_genres():
    """List all genres with movie counts."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (g:Genre)<-[:IN_GENRE]-(m:Movie)
                RETURN g.name AS genre, count(m) AS movie_count
                ORDER BY movie_count DESC
                """
            )
            return [dict(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")
