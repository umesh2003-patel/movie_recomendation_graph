"""
Actors router — actor detail, filmography, co-actor network.
"""

from fastapi import APIRouter, HTTPException
from database import get_session
from neo4j.exceptions import ServiceUnavailable

router = APIRouter(prefix="/actors", tags=["Actors"])


@router.get("/")
def list_actors(limit: int = 30):
    """List actors ordered by number of movies."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)
                RETURN a.name AS name, a.born AS born, count(m) AS movie_count
                ORDER BY movie_count DESC LIMIT $limit
                """,
                limit=limit,
            )
            return [dict(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/{name}")
def get_actor(name: str):
    """Get actor detail with full filmography."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (a:Actor {name: $name})-[r:ACTED_IN]->(m:Movie)
                RETURN a,
                       collect({title: m.title, year: m.year, role: r.role, rating: m.rating}) AS movies
                """,
                name=name,
            )
            row = result.single()
            if not row:
                raise HTTPException(404, f"Actor '{name}' not found.")
            a = row["a"]
            return {
                "name": a.get("name"),
                "born": a.get("born"),
                "movies": sorted(row["movies"], key=lambda x: x["year"] or 0, reverse=True),
            }
    except HTTPException:
        raise
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/{name}/co-actors")
def co_actors(name: str, limit: int = 10):
    """
    Find actors who most frequently co-starred with the given actor.
    This is a 2-hop traversal: Actor -> Movie <- Actor.
    """
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (a:Actor {name: $name})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(co:Actor)
                WHERE co.name <> $name
                RETURN co.name AS co_actor, count(m) AS shared_movies,
                       collect(m.title) AS movies_together
                ORDER BY shared_movies DESC LIMIT $limit
                """,
                name=name,
                limit=limit,
            )
            return [dict(r) for r in result]
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")
