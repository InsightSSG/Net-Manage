#!/usr/bin/env python3

"""A collection of helper functions for neo4j operations.

"""

from neo4j import GraphDatabase
import networkx as nx


def get_num_nodes_edges(uri: str = "bolt://0.0.0.0:7687",
                        user: str = "neo4j",
                        password: str = "neo4j") -> tuple:
    """
    Get the total number of nodes and edges in a Neo4j database.

    Parameters
    ----------
    uri : str, optional
        The URI of the Neo4j database, by default "bolt://0.0.0.0:7687"
    user : str, optional
        The username for the Neo4j database, by default "neo4j"
    password : str, optional
        The password for the Neo4j database, by default "neo4j"

    Returns
    -------
    tuple
        A tuple containing the total number of nodes and edges.
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))

    total_nodes = 0
    total_edges = 0

    with driver.session() as session:
        # Get total nodes
        result = session.run("MATCH (n) RETURN COUNT(n)")
        total_nodes = result.single()[0]

        # Get total edges
        result = session.run("MATCH ()-[r]->() RETURN COUNT(r)")
        total_edges = result.single()[0]

    return total_nodes, total_edges


def networkx_to_neo4j(G: nx.Graph, uri: str = "bolt://0.0.0.0:7687",
                      user: str = "neo4j", password: str = "neo4j",
                      clear_db: bool = False):
    """
    Transfer a NetworkX graph to a Neo4j database.
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        # Optionally clear the existing data in the database
        if clear_db:
            session.run("MATCH (n) DETACH DELETE n")

        # Add or update nodes with properties
        for node, data in G.nodes(data=True):
            props = {k: v for k, v in data.items()}
            session.run("""
            MERGE (n:Node {id: $node})
            SET n += {props}
            """, node=node, props=props)

        # Add or update edges with properties
        for u, v, data in G.edges(data=True):
            props = {k: v for k, v in data.items()}
            session.run("""
            MATCH (a:Node {id: $u}), (b:Node {id: $v})
            MERGE (a)-[r:CONNECTED]->(b)
            SET r += {props}
            """, u=u, v=v, props=props)


def test_connectivity(uri: str = "bolt://0.0.0.0:7687",
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
