#!/usr/bin/env python3

"""A collection of helper functions for neo4j operations.

"""

from neo4j import GraphDatabase


def test_neo4j_connectivity(uri: str = "bolt://0.0.0.0:7687",
                            user: str = "neo4j",
                            password: str = "neo4j") -> bool:
    """
    Test connectivity to a Neo4j database.

    Parameters
    ----------
    uri : str, optional
        The URI of the Neo4j database, by default "bolt://0.0.0.0:7687".
    user : str, optional
        The username for the database, by default "neo4j".
    password : str, optional
        The password for the user, by default "neo4j".

    Returns
    -------
    bool
        True if connected successfully, False otherwise.
    """
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # Test a simple query
            session.run("MATCH (n) RETURN n LIMIT 1")
        return True
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        return False
    finally:
        if driver:
            driver.close()
