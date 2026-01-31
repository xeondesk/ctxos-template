#!/usr/bin/env python3
"""
Graph Engine Example - Demonstrates context graph operations and analysis.

This example shows how to:
1. Create and manage context graphs
2. Add entities and relationships
3. Query graph data
4. Perform graph analysis
5. Visualize graph structures
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import Entity, EntityType, EntitySeverity, Signal, SignalType, Context
from core.graph.graph_engine import demo_graph


class GraphNode:
    """Simple graph node representation."""
    
    def __init__(self, id: str, label: str, node_type: str, properties: Dict[str, Any] = None):
        self.id = id
        self.label = label
        self.type = node_type
        self.properties = properties or {}
        self.edges = []
    
    def add_edge(self, target_node: 'GraphNode', edge_type: str, properties: Dict[str, Any] = None):
        """Add an edge to another node."""
        edge = {
            'target': target_node,
            'type': edge_type,
            'properties': properties or {}
        }
        self.edges.append(edge)
    
    def __repr__(self):
        return f"GraphNode(id='{self.id}', label='{self.label}', type='{self.type}')"


class ContextGraph:
    """Simple context graph implementation."""
    
    def __init__(self, name: str):
        self.name = name
        self.nodes = {}
        self.edges = []
    
    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, properties: Dict[str, Any] = None):
        """Add an edge between nodes."""
        if source_id in self.nodes and target_id in self.nodes:
            self.nodes[source_id].add_edge(self.nodes[target_id], edge_type, properties)
            self.edges.append({
                'source': source_id,
                'target': target_id,
                'type': edge_type,
                'properties': properties or {}
            })
    
    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """Get all neighboring nodes."""
        if node_id not in self.nodes:
            return []
        
        neighbors = []
        for edge in self.nodes[node_id].edges:
            neighbors.append(edge['target'])
        
        return neighbors
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find a path between two nodes using BFS."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        visited = set()
        queue = [(source_id, [source_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == target_id:
                return path
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            for neighbor in self.get_neighbors(current_id):
                if neighbor.id not in visited:
                    queue.append((neighbor.id, path + [neighbor.id]))
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            'name': self.name,
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'node_types': {node_type: len([n for n in self.nodes.values() if n.type == node_type]) 
                          for node_type in set(n.type for n in self.nodes.values())},
            'edge_types': {edge_type: len([e for e in self.edges if e['type'] == edge_type]) 
                          for edge_type in set(e['type'] for e in self.edges)}
        }
    
    def visualize_ascii(self):
        """Create a simple ASCII visualization of the graph."""
        print(f"\n📊 Graph: {self.name}")
        print("=" * 50)
        
        for node_id, node in self.nodes.items():
            print(f"\n🔸 {node.label} ({node.type})")
            for edge in node.edges:
                print(f"   └─[{edge['type']}]→ {edge['target'].label} ({edge['target'].type})")


def example_1_basic_graph_creation():
    """Example 1: Create a basic context graph."""
    print("\n" + "="*60)
    print("Example 1: Basic Graph Creation")
    print("="*60)
    
    # Create a new graph
    graph = ContextGraph("Security Context")
    
    # Create nodes representing different entities
    domain_node = GraphNode("domain_1", "example.com", "domain", {
        "registrar": "NameCheap",
        "created_date": "2020-01-15",
        "status": "active"
    })
    
    ip_node = GraphNode("ip_1", "192.168.1.100", "ip", {
        "country": "US",
        "provider": "AWS",
        "is_public": True
    })
    
    subdomain_node = GraphNode("subdomain_1", "api.example.com", "subdomain", {
        "service": "API Gateway",
        "status": "active"
    })
    
    email_node = GraphNode("email_1", "admin@example.com", "email", {
        "domain": "example.com",
        "verified": True
    })
    
    # Add nodes to graph
    graph.add_node(domain_node)
    graph.add_node(ip_node)
    graph.add_node(subdomain_node)
    graph.add_node(email_node)
    
    # Create relationships
    graph.add_edge("domain_1", "ip_1", "resolves_to", {"record_type": "A"})
    graph.add_edge("subdomain_1", "domain_1", "subdomain_of", {})
    graph.add_edge("email_1", "domain_1", "belongs_to", {})
    graph.add_edge("subdomain_1", "ip_1", "resolves_to", {"record_type": "A"})
    
    # Display graph
    graph.visualize_ascii()
    
    # Show statistics
    stats = graph.get_statistics()
    print(f"\n📈 Graph Statistics:")
    print(f"  Total Nodes: {stats['nodes']}")
    print(f"  Total Edges: {stats['edges']}")
    print(f"  Node Types: {stats['node_types']}")
    print(f"  Edge Types: {stats['edge_types']}")
    
    return graph


def example_2_graph_queries():
    """Example 2: Query the graph for information."""
    print("\n" + "="*60)
    print("Example 2: Graph Queries")
    print("="*60)
    
    # Create a sample graph
    graph = example_1_basic_graph_creation()
    
    # Query 1: Find neighbors of a node
    print("\n🔍 Query 1: Neighbors of 'example.com'")
    domain_node = graph.get_node("domain_1")
    if domain_node:
        neighbors = graph.get_neighbors("domain_1")
        print(f"  Found {len(neighbors)} neighbors:")
        for neighbor in neighbors:
            print(f"    - {neighbor.label} ({neighbor.type})")
    
    # Query 2: Find paths between nodes
    print("\n🔍 Query 2: Path from 'admin@example.com' to '192.168.1.100'")
    path = graph.find_path("email_1", "ip_1")
    if path:
        print(f"  Path found: {' → '.join([graph.get_node(node_id).label for node_id in path])}")
    else:
        print("  No path found")
    
    # Query 3: Find all nodes of a specific type
    print("\n🔍 Query 3: All IP nodes")
    ip_nodes = [node for node in graph.nodes.values() if node.type == "ip"]
    print(f"  Found {len(ip_nodes)} IP nodes:")
    for node in ip_nodes:
        print(f"    - {node.label} (Country: {node.properties.get('country', 'Unknown')})")


def example_3_threat_modeling():
    """Example 3: Use graph for threat modeling."""
    print("\n" + "="*60)
    print("Example 3: Threat Modeling with Graph")
    print("="*60)
    
    # Create a threat scenario graph
    threat_graph = ContextGraph("Threat Scenario")
    
    # Create entities
    web_server = GraphNode("web_1", "web-server-01", "server", {
        "os": "Ubuntu 20.04",
        "services": ["nginx", "ssh"],
        "patch_level": "2023-12-01"
    })
    
    database = GraphNode("db_1", "postgres-primary", "database", {
        "type": "PostgreSQL",
        "version": "13.7",
        "encryption": False
    })
    
    vulnerability = GraphNode("vuln_1", "CVE-2023-1234", "vulnerability", {
        "severity": "HIGH",
        "cve": "CVE-2023-1234",
        "affected_service": "nginx"
    })
    
    attacker = GraphNode("attacker_1", "External Attacker", "attacker", {
        "location": "Internet",
        "motivation": "Data theft"
    })
    
    data_asset = GraphNode("data_1", "Customer PII", "data", {
        "type": "PII",
        "sensitivity": "HIGH",
        "records": 50000
    })
    
    # Add nodes to graph
    for node in [web_server, database, vulnerability, attacker, data_asset]:
        threat_graph.add_node(node)
    
    # Create relationships
    threat_graph.add_edge("web_1", "db_1", "connects_to", {"port": 5432})
    threat_graph.add_edge("vuln_1", "web_1", "affects", {})
    threat_graph.add_edge("attacker_1", "vuln_1", "exploits", {})
    threat_graph.add_edge("db_1", "data_1", "stores", {})
    
    # Visualize threat model
    threat_graph.visualize_ascii()
    
    # Analyze attack paths
    print("\n🎯 Attack Path Analysis:")
    attack_paths = [
        ("attacker_1", "data_1"),
        ("attacker_1", "db_1"),
        ("attacker_1", "web_1")
    ]
    
    for source, target in attack_paths:
        path = threat_graph.find_path(source, target)
        if path:
            path_labels = [threat_graph.get_node(node_id).label for node_id in path]
            print(f"  🚨 Path to {target}: {' → '.join(path_labels)}")
        else:
            print(f"  ✅ No path to {target}")
    
    # Calculate risk score (simplified)
    print("\n📊 Risk Assessment:")
    high_vulns = [n for n in threat_graph.nodes.values() 
                  if n.type == "vulnerability" and n.properties.get("severity") == "HIGH"]
    sensitive_data = [n for n in threat_graph.nodes.values() 
                      if n.type == "data" and n.properties.get("sensitivity") == "HIGH"]
    
    risk_score = len(high_vulns) * len(sensitive_data) * 10
    print(f"  High Vulnerabilities: {len(high_vulns)}")
    print(f"  Sensitive Data Assets: {len(sensitive_data)}")
    print(f"  Calculated Risk Score: {risk_score}")


def example_4_dynamic_graph_updates():
    """Example 4: Dynamic graph updates and real-time analysis."""
    print("\n" + "="*60)
    print("Example 4: Dynamic Graph Updates")
    print("="*60)
    
    # Create initial graph
    graph = ContextGraph("Dynamic Network")
    
    # Add initial nodes
    initial_nodes = [
        GraphNode("router_1", "core-router", "router", {"ip": "10.0.0.1"}),
        GraphNode("server_1", "web-server", "server", {"ip": "10.0.0.10"}),
        GraphNode("server_2", "db-server", "server", {"ip": "10.0.0.20"})
    ]
    
    for node in initial_nodes:
        graph.add_node(node)
    
    graph.add_edge("server_1", "router_1", "connected_to", {})
    graph.add_edge("server_2", "router_1", "connected_to", {})
    
    print("📊 Initial Network Topology:")
    graph.visualize_ascii()
    
    # Simulate network changes
    print("\n🔄 Simulating Network Changes...")
    
    # Add new server
    new_server = GraphNode("server_3", "app-server", "server", {"ip": "10.0.0.30"})
    graph.add_node(new_server)
    graph.add_edge("server_3", "router_1", "connected_to", {})
    print("  ✓ Added new app-server")
    
    # Add connection between servers
    graph.add_edge("server_1", "server_2", "communicates_with", {"protocol": "HTTP"})
    graph.add_edge("server_1", "server_3", "communicates_with", {"protocol": "API"})
    print("  ✓ Added inter-server communication")
    
    # Add security event
    security_event = GraphNode("event_1", "Suspicious Login", "security_event", {
        "timestamp": datetime.now().isoformat(),
        "severity": "MEDIUM",
        "source_ip": "192.168.1.100"
    })
    graph.add_node(security_event)
    graph.add_edge("event_1", "server_1", "targeted", {})
    print("  ✓ Added security event")
    
    # Show updated graph
    print("\n📊 Updated Network Topology:")
    graph.visualize_ascii()
    
    # Final statistics
    stats = graph.get_statistics()
    print(f"\n📈 Final Statistics:")
    print(f"  Total Nodes: {stats['nodes']}")
    print(f"  Total Edges: {stats['edges']}")
    print(f"  Node Types: {stats['node_types']}")


def main():
    """Run all graph examples."""
    print("CtxOS Graph Engine Examples")
    print("=" * 60)
    
    # Run built-in demo if available
    try:
        print("\n🔧 Running built-in graph engine demo...")
        demo_graph()
    except Exception as e:
        print(f"Built-in demo not available: {e}")
    
    # Run custom examples
    example_1_basic_graph_creation()
    example_2_graph_queries()
    example_3_threat_modeling()
    example_4_dynamic_graph_updates()
    
    print("\n" + "="*60)
    print("✅ All graph examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()