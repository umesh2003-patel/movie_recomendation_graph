"""
Movies router — search, list, detail, create.
All Cypher queries are parameterised (no string concatenation).
"""

from fastapi import APIRouter, HTTPException, Query
from database import get_session
from neo4j.exceptions import ServiceUnavailable

router = APIRouter(prefix="/movies", tags=["Movies"])


def _movie_record(record) -> dict:
    m = record["m"]
    return {
        "id": m.element_id,
        "title": m.get("title"),
        "year": m.get("year"),
        "rating": m.get("rating"),
        "poster_url": m.get("poster_url"),
        "tagline": m.get("tagline"),
    }


@router.get("/")
def list_movies(skip: int = 0, limit: int = 20):
    """List movies with pagination."""
    try:
        with get_session() as session:
            result = session.run(
                "MATCH (m:Movie) RETURN m ORDER BY m.rating DESC SKIP $skip LIMIT $limit",
                skip=skip,
                limit=limit,
            )
            return [_movie_record(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable. Please try again later.")


@router.get("/search")
def search_movies(q: str = Query(..., min_length=1)):
    """Full-text search on movie titles."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (m:Movie)
                WHERE toLower(m.title) CONTAINS toLower($q)
                RETURN m ORDER BY m.rating DESC LIMIT 20
                """,
                q=q,
            )
            return [_movie_record(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/top")
def top_rated(limit: int = 10):
    """Return top-rated movies."""
    try:
        with get_session() as session:
            result = session.run(
                "MATCH (m:Movie) RETURN m ORDER BY m.rating DESC LIMIT $limit",
                limit=limit,
            )
            return [_movie_record(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/{title}")
def get_movie(title: str):
    """Get a single movie with its cast, director, and genres."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (m:Movie {title: $title})
                OPTIONAL MATCH (a:Actor)-[r:ACTED_IN]->(m)
                OPTIONAL MATCH (d:Director)-[:DIRECTED]->(m)
                OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
                RETURN m,
                       collect(DISTINCT {name: a.name, role: r.role, born: a.born}) AS cast,
                       collect(DISTINCT d.name) AS directors,
                       collect(DISTINCT g.name) AS genres
                """,
                title=title,
            )
            row = result.single()
            if not row:
                raise HTTPException(404, f"Movie '{title}' not found.")
            m = row["m"]
            return {
                "id": m.element_id,
                "title": m.get("title"),
                "year": m.get("year"),
                "rating": m.get("rating"),
                "poster_url": m.get("poster_url"),
                "tagline": m.get("tagline"),
                "cast": [c for c in row["cast"] if c["name"]],
                "directors": row["directors"],
                "genres": row["genres"],
            }
    except HTTPException:
        raise
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")
