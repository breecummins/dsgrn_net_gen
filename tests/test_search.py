from dsgrn_net_gen.makejobs import Job
import subprocess, os, ast
import dsgrn_net_gen.graphtranslation as gt
from dsgrn_net_gen.filters import *
import DSGRN


def run(paramfile):
    job = Job(paramfile)
    job.run()
    ndir = subprocess.getoutput("ls -td ./dsgrn_net_gen_results*/networks*/ | head -1")
    resultsfile = os.path.join(ndir, "networks.txt")
    networks = ast.literal_eval(open(resultsfile).read())
    subprocess.call("rm -r " + ndir, shell=True)
    subprocess.call("rm -r " + subprocess.getoutput("ls -td ./dsgrn_net_gen_results*/ | head -1"), shell=True)
    return networks


def check_size(networks,original_graph):
    sconn = []
    conn = []
    ff = []
    numedges = []
    numnodes = []
    maxinedges = 0
    mininedges = 10
    maxoutedges = 0
    minoutedges = 10
    params = []
    for netspec in networks:
        graph = gt.getGraphFromNetworkSpec(netspec)
        issubgraph = is_subgraph(graph,original_graph)
        conn.append(is_connected(graph))
        sconn.append(is_strongly_connected(graph))
        ff.append(is_feed_forward(graph))
        numedges.append(len(graph.edges()))
        numnodes.append(len(graph.vertices()))
        maxinedges = max([max([len(graph.inedges(v)) for v in graph.vertices()]), maxinedges])
        mininedges = min([min([len(graph.inedges(v)) for v in graph.vertices()]), mininedges])
        maxoutedges = max([max([len(graph.adjacencies(v)) for v in graph.vertices()]),maxoutedges])
        minoutedges = min([min([len(graph.adjacencies(v)) for v in graph.vertices()]), minoutedges])
        params.append(DSGRN.ParameterGraph(DSGRN.Network(netspec)).size())
    return conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params,issubgraph


def is_subgraph(graph,subgraph):
    for v in subgraph.vertices():
        if v not in graph.vertices() or graph.vertex_label(v) != subgraph.vertex_label(v):
            return False
    for e in subgraph.edges():
        if e not in graph.edges() or graph.edge_label(e[0],e[1]) != subgraph.edge_label(e[0],e[1]):
            return False
    else:
        return True


def test1():
    original = open("networkspec_X1X2X3.txt").read()
    subgraph = gt.getGraphFromNetworkSpec(original)
    networks = run("params_X1X2X3_A.json")
    # for n in networks:
    #     print(n)
    #     print("\n")
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params,issubgraph = check_size(networks,subgraph)
    assert(all(conn))
    assert(numedges.count(5) == 1)
    assert(issubgraph)
    assert(all([e >= 5 for e in numedges]))
    assert(all([n >= 3 for n in numnodes]))
    assert(all([p <= 100000 for p in params]))


def test2():
    original = open("networkspec_X1X2X3.txt").read()
    subgraph = gt.getGraphFromNetworkSpec(original)
    networks = run("params_X1X2X3_B.json")
    # for n in networks:
    #     print(n)
    #     print("\n")
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params,issubgraph = check_size(networks,subgraph)
    assert(all(sconn))
    assert(not any([f[0] for f in ff]))
    assert(numedges.count(5) == 0)
    assert(issubgraph)
    assert(all([e >= 8 for e in numedges]))
    assert(all([n >= 3 for n in numnodes]))
    assert(all([p <= 10000000 for p in params]))
    assert(maxinedges <= 3)
    assert(mininedges >= 2)
    assert(minoutedges > 0)


if __name__ == "__main__":
    test2()