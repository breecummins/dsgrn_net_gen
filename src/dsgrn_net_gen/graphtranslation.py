import copy

########################
# Directed Graph Class #
########################


class Graph:

    def __init__(self):
        """ Initialize an empty graph object """
        self.vertices_ = set()
        self.adjacency_lists_ = {}
        self.vertex_labels_ = {}
        self.edge_labels_ = {}

    def add_vertex(self, v, label=''):
        """ Add the vertex v to the graph and associate a label if one is given """
        if v in self.vertices_: return
        self.vertices_.add(v)
        self.adjacency_lists_[v] = set()
        self.vertex_labels_[v] = label
        self.edge_labels_[v] = {}

    def add_edge(self, u, v, label=''):
        """ Add the edge u -> v to the graph and associate a label if one is given """
        self.add_vertex(u)
        self.add_vertex(v)
        self.adjacency_lists_[u].add(v)
        self.edge_labels_[u][v] = label

    def remove_edge(self, u, v):
        """ Remove the edge u -> v from the graph """
        self.adjacency_lists_[u].discard(v)
        self.edge_labels_[u].pop(v, None)

    def remove_vertex(self, u):
        """ Remove the node u and all edges from the graph """
        self.vertices_.discard(u)
        self.adjacency_lists_.pop(u, None)
        self.vertex_labels_.pop(u, None)
        self.edge_labels_.pop(u, None)
        for v in self.vertices():
            self.adjacency_lists_[v].discard(u)

    def vertex_label(self, v):
        """ Return the label on the vertex v """
        return self.vertex_labels_[v]

    def get_vertex_from_label(self, label):
        """ Return the vertex v with label 'label'. Error if non-unique. """
        vertices = [v for v in self.vertices_ if self.vertex_label(v) == label]
        N = len(vertices)
        if N == 1:
            return vertices[0]
        elif N == 0:
            return None
        elif N > 1:
            raise ValueError("Non-unique vertex labels.")

    def edge_label(self, u, v):
        """ Return the label on the edge u -> v """
        return self.edge_labels_[u][v]

    def vertices(self):
        """ Return the set of vertices in the graph """
        return self.vertices_

    def size(self):
        """ Return the number of vertices in the graph """
        return len(self.vertices_)

    def edges(self):
        """ Return a complete list of directed edges (u,v) in the graph """
        return [(u, v) for u in self.vertices() for v in self.adjacencies(u)]

    def adjacencies(self, v):
        """ Return the set of adjacencies (outedges) of v, i.e. { u : v -> u } """
        return self.adjacency_lists_[v]

    def inedges(self,v):
        """ Return the inedges of v, i.e. { u : u -> v } """
        return [u for u in self.vertices_ if v in self.adjacency_lists_[u]]

    def clone(self):
        """ Return a copy of this graph """
        return copy.deepcopy(self)

    def graphviz(self):
        """ Return a graphviz string describing the graph and its labels """
        gv = 'digraph {\n'
        indices = {v: str(k) for k, v in enumerate(self.vertices())}
        for v in self.vertices():
            gv += indices[v] + '[label="' + self.vertex_label(v) + '"];\n'
        for (u, v) in self.edges():
            gv += indices[u] + ' -> ' + indices[v] + ' [label="' + self.edge_label(u,v) + '"];\n'
        return gv + '}\n'

    def transpose(self):
        """ Return a new graph with edge direction reversed. """
        G = Graph()
        for v in self.vertices(): G.add_vertex(v, self.vertex_label(v))
        for (u, v) in self.edges(): G.add_edge(v, u, self.edge_label(u, v))
        return G


##################################################
# Translation to and from network specifications
##################################################



def createEssentialNetworkSpecFromGraph(graph):
    # take a graph and return a DSGRN network spec file

    # get nodes in order
    vs = { v : graph.vertex_label(v) for v in sorted(list(graph.vertices())) }

    # get inedges
    graph_edges = { name : [(a, graph.edge_label(a, v)) for a in graph.inedges(v)] for v,name in vs.items() }

    # generate network spec lines
    network_spec_lines = []
    for node,inedges in  graph_edges.items():
        act = " + ".join([vs[i] for (i, r) in inedges if r == 'a'])
        if act: act = "(" + act + ")"
        rep = "".join(["(~" + vs[i] + ")" for (i, r) in inedges if r == 'r'])
        network_spec_lines.append(node + " : " + act + rep + " : E\n")

    # alphabetize lines
    network_spec = "".join(sorted(network_spec_lines))
    return network_spec


def getGraphFromNetworkSpec(network_spec):
    # take a DSGRN network spec and return an graphtranslation.Graph
    if not network_spec:
        return Graph()
    eqns = filter(bool, network_spec.split("\n"))
    nodelist = []
    innodes = []
    for l in eqns:
        words = l.replace('(', ' ').replace(')', ' ').replace('+', ' ').replace('*', ' ').split()
        if words[-2:] == [':', 'E']:
            words = words[:-2]
        nodelist.append(words[0])
        innodes.append(words[2:])  # get rid of ':' at index 1
    graph = Graph()
    for k, node in enumerate(nodelist):  # need the index as node name to preserve original network order in perturbed networks
        graph.add_vertex(k, label=node)
    for outnode, ies in enumerate(innodes):
        for ie in ies:
            if ie[0] == '~':
                ie = ie[1:]
                reg = 'r'
            else:
                reg = 'a'
            innode = nodelist.index(ie)
            graph.add_edge(innode, outnode, label=reg)
    return graph
