from dsgrn_net_gen.makejobs import Job
import subprocess, os, ast, sys
import dsgrn_net_gen.graphtranslation as gt
from dsgrn_net_gen.filters import *
import DSGRN
from pathlib import Path

Path("temp_results").mkdir(exist_ok=True)


def run(paramfile):
    job = Job(paramfile)
    job.run()
    ndir = subprocess.getoutput("ls -td temp_results/dsgrn_net_gen_results*/networks*/ | head -1")
    resultsfile = os.path.join(ndir, "networks.txt")
    networks = ast.literal_eval(open(resultsfile).read())
    subprocess.call("rm -r " + ndir, shell=True)
    subprocess.call("rm -r " + subprocess.getoutput("ls -td temp_results/dsgrn_net_gen_results*/ | head -1"), shell=True)
    return networks


def check_size(networks,original_graph=None):
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
    if original_graph:
        return conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params,is_subgraph(graph, original_graph)
    else:
        return conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params


def is_subgraph(graph,subgraph):
    for v in subgraph.vertices():
        #assume unique labels
        if subgraph.vertex_label(v) not in [graph.vertex_label(u) for u in graph.vertices()]:
            return False
    for e in subgraph.edges():
        nt = (subgraph.vertex_label(e[0]), subgraph.vertex_label(e[1]))
        node_translations = [(graph.vertex_label(E[0]), graph.vertex_label(E[1])) for E in graph.edges()]
        try:
            ind = node_translations.index(nt)
        except ValueError:
            return False
        E = graph.edges()[ind]
        if subgraph.edge_label(e[0],e[1]) != graph.edge_label(E[0],E[1]):
            return False
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
    assert(all([s[0] for s in conn]))
    assert(numedges.count(5) == 1)
    assert(issubgraph)
    assert(all([e >= 5 for e in numedges]))
    assert(all([n >= 3 for n in numnodes]))
    assert(all([p <= 100000 for p in params]))


def test2():
    original = open("networkspec_X1X2X3.txt").read()
    original_graph = gt.getGraphFromNetworkSpec(original)
    networks = run("params_X1X2X3_B.json")
    # for n in networks:
    #     print(n)
    #     print("\n")
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params = check_size(networks)
    assert(all([s[0] for s in sconn]))
    assert(not any([f[0] for f in ff]))
    assert(numedges.count(5) == 0)
    assert(is_subgraph)
    assert(all([e >= 8 for e in numedges]))
    assert(all([n >= 3 for n in numnodes]))
    assert(all([p <= 10000000 for p in params]))
    assert(mininedges >= 2)
    assert(minoutedges > 0)


def test3():
    original = open("networkspec_X1X2X3.txt").read()
    original_graph = gt.getGraphFromNetworkSpec(original)
    networks = run("params_X1X2X3_C.json")
    # for n in networks:
    #     print(n)
    #     print("\n")
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params = check_size(networks)
    assert(numedges.count(5) == 1)
    assert(all([e <= 5 for e in numedges]))
    assert(all([n <= 3 for n in numnodes]))
    assert(all([p <= 10000 for p in params]))
    for netspec in networks:
        graph = gt.getGraphFromNetworkSpec(netspec)
        if not is_subgraph(original_graph,graph):
            print(graph)
        assert(is_subgraph(original_graph,graph))


def test4():
    # test random seed
    networks = run("params_X1X2X3_D.json")
    if sys.version_info[1] == 7:
        assert(set(networks)==set(['X1 : (X1)(~X3) : E\nX2 : (X1) : E\nX3 : (X1 + X2) : E\n', 'X1 : (X1) : E\nX2 : (X1) : E\nX3 : (X2) : E\n', 'X1 : (X1)(~X3) : E\nX3 : (X1) : E\n']))
    elif sys.version_info[1] == 6:
        assert(set(networks)==set(['X1 : (X1)(~X3) : E\nX3 : (X1) : E\n', 'X1 : (~X3) : E\nX2 : (X1) : E\nX3 : (X2) : E\n', 'X1 : (X1)(~X3) : E\nX2 : (X1) : E\nX3 : (X1 + X2) : E\n']))
    else:
        raise ValueError("No test written for Python version {}.{}".format(sys.version_info[0],sys.version_info[1]))
    subprocess.call(["rm","-r", "temp_results/"])


if __name__ == "__main__":
    test4()