"""
CognoDB / Neo4j driver singleton.
Reads connection details from environment variables — never hard-coded.
"""

import os
from contextlib import contextmanager
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("CONGODB_CONNECTION_URL", "")
USERNAME = os.getenv("CONGODB_USERNAME", "cognodb")
PASSWORD = os.getenv("CONGODB_PASSWORD", "")

_driver = None


def get_driver():
    """Return the singleton Neo4j driver, creating it if needed."""
    global _driver
    if _driver is None:
        if not URI or not PASSWORD:
            raise RuntimeError(
                "CognoDB connection details missing. "
                "Set CONGODB_CONNECTION_URL and CONGODB_PASSWORD."
            )
        _driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    return _driver


def verify_connectivity():
    """Verify the database is reachable. Returns (ok: bool, message: str)."""
    try:
        get_driver().verify_connectivity()
        return True, "Connected to CognoDB"
    except ServiceUnavailable as e:
        return False, f"Database unreachable: {e}"
    except AuthError as e:
        return False, f"Authentication failed: {e}"
    except Exception as e:
        return False, f"Connection error: {e}"


@contextmanager
def get_session():
    """Context manager that yields a Neo4j session."""
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def close_driver():
    """Close the driver (called on app shutdown)."""
    global _driver
    if _driver:
        _driver.close()
        _driver = None
