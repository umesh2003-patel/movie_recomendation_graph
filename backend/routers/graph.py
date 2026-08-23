"""
Graph router — returns node/edge data for the interactive graph visualiser.
"""

from fastapi import APIRouter, HTTPException, Query
from database import get_session
from neo4j.exceptions import ServiceUnavailable

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/movie/{title}")
def movie_graph(title: str):
    """
    Return graph data (nodes + edges) centred on a movie:
    Movie <-> Actors, Director, Genres.
    Used by the react-force-graph visualiser on the frontend.
    """
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (m:Movie {title: $title})
                OPTIONAL MATCH (a:Actor)-[r1:ACTED_IN]->(m)
                OPTIONAL MATCH (d:Director)-[r2:DIRECTED]->(m)
                OPTIONAL MATCH (m)-[r3:IN_GENRE]->(g:Genre)
                WITH m, a, r1, d, r2, g, r3
                RETURN
                  collect(DISTINCT {id: elementId(m), label: m.title, type: 'Movie', rating: m.rating}) AS movies,
                  collect(DISTINCT {id: elementId(a), label: a.name, type: 'Actor'}) AS actors,
                  collect(DISTINCT {id: elementId(d), label: d.name, type: 'Director'}) AS directors,
                  collect(DISTINCT {id: elementId(g), label: g.name, type: 'Genre'}) AS genres,
                  collect(DISTINCT {source: elementId(a), target: elementId(m), label: 'ACTED_IN'}) AS acted_in,
                  collect(DISTINCT {source: elementId(d), target: elementId(m), label: 'DIRECTED'}) AS directed,
                  collect(DISTINCT {source: elementId(m), target: elementId(g), label: 'IN_GENRE'}) AS in_genre
                """,
                title=title,
            )
            row = result.single()
            if not row:
                raise HTTPException(404, f"Movie '{title}' not found.")

            nodes = (
                [n for n in row["movies"] if n["id"]]
                + [n for n in row["actors"] if n["id"]]
                + [n for n in row["directors"] if n["id"]]
                + [n for n in row["genres"] if n["id"]]
            )
            links = (
                [e for e in row["acted_in"] if e["source"] and e["target"]]
                + [e for e in row["directed"] if e["source"] and e["target"]]
                + [e for e in row["in_genre"] if e["source"] and e["target"]]
            )
            # Deduplicate nodes by id
            seen = set()
            unique_nodes = []
            for n in nodes:
                if n["id"] not in seen:
                    seen.add(n["id"])
                    unique_nodes.append(n)

            return {"nodes": unique_nodes, "links": links}
    except HTTPException:
        raise
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")


@router.get("/overview")
def graph_overview(limit: int = Query(default=30, le=80)):
    """
    Return a bird's-eye graph: top movies + their genres + top actors.
    Used for the Explore page.
    """
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (m:Movie)
                WITH m ORDER BY m.rating DESC LIMIT $limit
                OPTIONAL MATCH (a:Actor)-[:ACTED_IN]->(m)
                WITH m, a LIMIT 200
                OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
                RETURN
                  collect(DISTINCT {id: elementId(m), label: m.title, type: 'Movie', rating: m.rating}) AS movies,
                  collect(DISTINCT {id: elementId(a), label: a.name, type: 'Actor'}) AS actors,
                  collect(DISTINCT {id: elementId(g), label: g.name, type: 'Genre'}) AS genres,
                  collect(DISTINCT {source: elementId(a), target: elementId(m), label: 'ACTED_IN'}) AS acted_in,
                  collect(DISTINCT {source: elementId(m), target: elementId(g), label: 'IN_GENRE'}) AS in_genre
                """,
                limit=limit,
            )
            row = result.single()
            if not row:
                return {"nodes": [], "links": []}

            nodes = (
                [n for n in row["movies"] if n.get("id")]
                + [n for n in row["actors"] if n.get("id")]
                + [n for n in row["genres"] if n.get("id")]
            )
            links = (
                [e for e in row["acted_in"] if e.get("source") and e.get("target")]
                + [e for e in row["in_genre"] if e.get("source") and e.get("target")]
            )
            seen = set()
            unique_nodes = []
            for n in nodes:
                if n["id"] not in seen:
                    seen.add(n["id"])
                    unique_nodes.append(n)

            return {"nodes": unique_nodes, "links": links}
    except ServiceUnavailable:
        raise HTTPException(503, "Database is currently unreachable.")
