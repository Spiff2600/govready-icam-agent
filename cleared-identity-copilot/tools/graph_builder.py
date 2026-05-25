"""
graph_builder.py
Builds a NetworkX graph of identity relationships.
Nodes: users, roles, systems, clouds.
Edges: has_role, accesses, delegates_to.
"""
from __future__ import annotations

from typing import Any

import networkx as nx

from tools.risk_scoring import score_user

RISK_COLORS = {
    "CRITICAL": "#c0392b",
    "HIGH": "#e67e22",
    "MED": "#f1c40f",
    "LOW": "#27ae60",
}


def build_identity_graph(users: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_node("Azure Gov", node_type="cloud", label="Azure Gov", risk_level="LOW")
    graph.add_node("AWS GovCloud", node_type="cloud", label="AWS GovCloud", risk_level="LOW")

    for user in users:
        scored = score_user(user)
        graph.add_node(
            user["user_id"],
            node_type="user",
            label=user.get("name", user["user_id"]),
            risk_level=scored["risk_level"],
            risk_score=scored["composite_score"],
            title=user.get("title", ""),
            account_type=user.get("account_type", "human"),
        )
        if user.get("azure_roles"):
            graph.add_edge(user["user_id"], "Azure Gov", relation="accesses")
        if user.get("aws_permission_sets"):
            graph.add_edge(user["user_id"], "AWS GovCloud", relation="accesses")
        for role in user.get("azure_roles", []):
            role_node = f"AZ::{role['role_name']}"
            graph.add_node(role_node, node_type="role", label=role["role_name"], risk_level=scored["risk_level"])
            graph.add_edge(user["user_id"], role_node, relation="has_role")
            graph.add_edge(role_node, "Azure Gov", relation=role.get("assignment_type", "assigned"))
        for permission in user.get("aws_permission_sets", []):
            role_node = f"AWS::{permission['permission_set']}"
            graph.add_node(role_node, node_type="role", label=permission["permission_set"], risk_level=scored["risk_level"])
            graph.add_edge(user["user_id"], role_node, relation="has_role")
            graph.add_edge(role_node, "AWS GovCloud", relation=permission.get("assignment_type", "assigned"))
        if "credential_sharing_confirmed" in user.get("risk_indicators", []):
            graph.add_edge(user["user_id"], "SVC001", relation="delegates_to")
    return graph


def get_graph_data_for_plotly(graph: nx.DiGraph) -> dict[str, list[dict[str, Any]]]:
    positions = nx.spring_layout(graph, seed=42, k=0.9)
    nodes: list[dict[str, Any]] = []
    for node_id, attrs in graph.nodes(data=True):
        x, y = positions[node_id]
        nodes.append(
            {
                "id": node_id,
                "x": float(x),
                "y": float(y),
                "label": attrs.get("label", node_id),
                "node_type": attrs.get("node_type", "unknown"),
                "risk_level": attrs.get("risk_level", "LOW"),
                "risk_score": attrs.get("risk_score", 10),
                "color": RISK_COLORS.get(attrs.get("risk_level", "LOW"), "#7f8c8d"),
                "title": attrs.get("title", ""),
                "account_type": attrs.get("account_type", ""),
            }
        )
    edges: list[dict[str, Any]] = []
    for source, target, attrs in graph.edges(data=True):
        edges.append(
            {
                "source": source,
                "target": target,
                "relation": attrs.get("relation", "relates_to"),
                "source_x": float(positions[source][0]),
                "source_y": float(positions[source][1]),
                "target_x": float(positions[target][0]),
                "target_y": float(positions[target][1]),
            }
        )
    return {"nodes": nodes, "edges": edges}


def find_privilege_escalation_paths(graph: nx.DiGraph) -> list[list[Any]]:
    paths: list[list[Any]] = []
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("node_type") != "user":
            continue
        risk_level = attrs.get("risk_level")
        if risk_level not in {"CRITICAL", "HIGH"}:
            continue
        try:
            if nx.has_path(graph, node_id, "Azure Gov") and nx.has_path(graph, node_id, "AWS GovCloud"):
                paths.append([node_id, "Azure Gov", "AWS GovCloud"])
        except nx.NetworkXError:
            continue
    return paths


def get_blast_radius(graph: nx.DiGraph, user_id: str) -> dict[str, Any]:
    if user_id not in graph:
        return {"user_id": user_id, "reachable_nodes": [], "reachable_count": 0, "role_count": 0, "clouds": []}
    reachable = sorted(nx.descendants(graph, user_id))
    role_count = sum(1 for node in reachable if graph.nodes[node].get("node_type") == "role")
    clouds = [node for node in reachable if graph.nodes[node].get("node_type") == "cloud"]
    return {
        "user_id": user_id,
        "reachable_nodes": reachable,
        "reachable_count": len(reachable),
        "role_count": role_count,
        "clouds": clouds,
    }
