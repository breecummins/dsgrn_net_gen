import networkx as nx

def constrained_inedges(graph,kwargs={}):
    '''
    Sets min and/or max number of inedges.
    :param graph: A dsgrn_net_gen.graphtranslation object
    :param kwargs: A dictionary with the keys "min_inedges" and/or "max_inedges"
    :return: (True, "") or (False, error message), True if no node has a number of inedges that fall outside the bounds (endpoint inclusive)
    '''
    for u in graph.vertices():
        N = len([v for v in graph.vertices() if u in graph.adjacencies(v)])
        if ("min_inedges" in kwargs and N < kwargs["min_inedges"]) or ("max_inedges" in kwargs and N > kwargs["max_inedges"]):
            return False, "Number of in-edges not in range"
    return True, ""


def constrained_outedges(graph,kwargs={}):
    '''
    Sets min and/or max number of outedges.
    :param graph: A dsgrn_net_gen.graphtranslation object
    :param kwargs: A dictionary with the keys "min_outedges" and/or "max_outedges"
    :return: (True, "") or (False, error message), True if no node has a number of inedges that fall outside the bounds (endpoint inclusive)
    '''
    for u in graph.vertices():
        N = len(graph.adjacencies(u))
        if ("min_outedges" in kwargs and N < kwargs["min_outedges"]) or ("max_outedges" in kwargs and N > kwargs["max_outedges"]):
            return False, "Number of out-edges not in range"
    return True, ""


def is_feed_forward(graph,kwargs={}):
    '''
    Checks if a network has no loops between two or more nodes. Self-edges allowed.
    :param graph: A dsgrn_net_gen.graphtranslation object
    :param kwargs: empty dictionary, here for API compliance
    :return: (True, "") or (False, error message), True if satisfied
    '''
    G = nx.DiGraph()
    G.add_edges_from(graph.edges())
    G.add_nodes_from(graph.vertices())
    scc = nx.strongly_connected_components(G)
    # throw out graphs with non-trivial cycles
    if any(len(s) > 1 for s in scc):
        return False, "Not feed-forward"
    return True, ""


def is_strongly_connected(graph,kwargs={}):
    '''
    Checks if a network has a directed path from each node to every other node.
    :param graph: A dsgrn_net_gen.graphtranslation object
    :param kwargs: empty dictionary, here for API compliance
    :return: (True, "") or (False, error message), True if satisfied
    '''
    G = nx.DiGraph()
    G.add_edges_from(graph.edges())
    G.add_nodes_from(graph.vertices())
    if G and nx.is_strongly_connected(G):
        return True, ""
    else:
        return False, "Not strongly connected"


def is_connected(graph,kwargs={}):
    '''
    Checks if a network has a sequence of edges from each node to every other node regardless of edge direction.
    This is weak connectivity in a directed graph.
    :param graph: A dsgrn_net_gen.graphtranslation object
    :param kwargs: empty dictionary, here for API compliance
    :return: (True, "") or (False, error message), True if satisfied
    '''
    G = nx.DiGraph()
    G.add_edges_from(graph.edges())
    G.add_nodes_from(graph.vertices())
    if G and nx.is_weakly_connected(G):
        return True, ""
    else:
        return False, "Not connected"
