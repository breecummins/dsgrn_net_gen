from dsgrn_net_gen.makejobs import Job
import subprocess, os, ast, sys, shutil, json
import dsgrn_net_gen.graphtranslation as gt
import dsgrn_net_gen.networksearch as ns
from dsgrn_net_gen.filters import *
import DSGRN
from pathlib import Path
from dsgrn_net_gen.fileparsers import parseEdgeFile, parseNodeFile

shutil.rmtree('temp_results', ignore_errors=True)
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
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params,issubgraph = check_size(networks,subgraph)
    assert(all([s[0] for s in conn]))
    assert(numedges.count(5) == 1)
    assert(issubgraph)
    assert(all([e >= 5 for e in numedges]))
    assert(all([n >= 3 for n in numnodes]))
    assert(all([p <= 100000 for p in params]))


def test2():
    networks = run("params_X1X2X3_B.json")
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
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params = check_size(networks)
    assert(numedges.count(5) == 1)
    assert(all([e <= 5 for e in numedges]))
    assert(all([n <= 3 for n in numnodes]))
    assert(all([p <= 10000 for p in params]))
    for netspec in networks:
        graph = gt.getGraphFromNetworkSpec(netspec)
        assert(is_subgraph(original_graph,graph))


def test4():
    # check that original edges are added to edgelist
    params = json.load(open("params_X1X2X3_A.json"))
    network_spec = open(params["networkfile"]).read()
    edgelist = parseEdgeFile(params["edgefile"])
    nodelist = parseNodeFile(params["nodefile"])
    params["edgelist"] = edgelist
    params["nodelist"] = nodelist
    params, starting_graph = ns.setup(params,network_spec)
    assert(len(params["edgelist"]) == len(edgelist)+5)
    assert(("X1","X1","a") in params["edgelist"] and ("X3","X1","r") in params["edgelist"] and ("X1","X2","a") in params["edgelist"] and ("X1","X3","a") in params["edgelist"] and ("X2","X3","a") in params["edgelist"])
    assert(set(params["nodelist"]) == set(["X1","X2","X3","X4","X5"]))


def test5():
    # check that original edges are not added to empty edgelist
    params = json.load(open("params_X1X2X3_C.json"))
    network_spec = open(params["networkfile"]).read()
    if "edgefile" in params and params["edgefile"].strip():
        edgelist = parseEdgeFile(params["edgefile"])
    else:
        edgelist = None
    if "nodefile" in params and params["nodefile"].strip():
        nodelist = parseNodeFile(params["nodefile"])
    else:
        nodelist = None
    params["edgelist"] = edgelist
    params["nodelist"] = nodelist
    params, starting_graph = ns.setup(params,network_spec)
    assert(params["edgelist"] == [])
    assert(("X1","X1","a") not in params["edgelist"] and ("X3","X1","r") not in params["edgelist"] and ("X1","X2","a") not in params["edgelist"] and ("X1","X3","a") not in params["edgelist"] and ("X2","X3","a") not in params["edgelist"])
    assert(params["nodelist"] == [])


def test6():
    # sanity check edges of starting network
    network_spec = open("networkspec_with_selfrep.txt").read()
    starting_graph = gt.getGraphFromNetworkSpec(network_spec)
    try:
        ns.sanity_check_edges(network_spec,starting_graph)
        raise RuntimeError("Shouldn't pass this test.")
    except ValueError as v:
        assert(str(v)=="Seed network has a self-repressing edge. Not currently supported by DSGRN.")

    network_spec = open("networkspec_with_multiedges.txt").read()
    starting_graph = gt.getGraphFromNetworkSpec(network_spec)
    try:
        ns.sanity_check_edges(network_spec,starting_graph)
        raise RuntimeError("Shouldn't pass this test.")
    except ValueError as v:
        assert(str(v)=="Seed network has a multiedge. Not currently supported by DSGRN.")

    network_spec = open("networkspec_with_multiedges2.txt").read()
    starting_graph = gt.getGraphFromNetworkSpec(network_spec)
    try:
        ns.sanity_check_edges(network_spec,starting_graph)
        raise RuntimeError("Shouldn't pass this test.")
    except ValueError as v:
        assert(str(v)=="Seed network has a multiedge. Not currently supported by DSGRN.")


def test7():
    # check node removal
    original = open("networkspec_X1X2X3.txt").read()
    original_graph = gt.getGraphFromNetworkSpec(original)
    networks = run("params_X1X2X3_E.json")
    # Note: 'X2 : \nX3 : (X2)\n' will not be produced using Shaun's repository (0 out-edges not allowed)
    assert(set(networks).issubset(set(['X1 : (X1)(~X3) : E\nX2 : (X1) : E\nX3 : (X1 + X2) : E\n', 'X1 : (X1)(~X3) : E\nX3 : (X1) : E\n', 'X1 : (X1) : E\nX2 : (X1) : E\n','X2 :  : E\nX3 : (X2) : E\n'])))
    for _ in range(10):
        graph,numedges = ns.removeNodes(original_graph.clone(),1)
        spec = gt.createEssentialNetworkSpecFromGraph(graph)
        if spec == 'X1 : (X1)(~X3) : E\nX3 : (X1) : E\n':
            assert(numedges == 2)
        elif spec == 'X1 : (X1) : E\nX2 : (X1) : E\n':
            assert(numedges == 3)
        elif 'X2 :  : E\nX3 : (X2) : E\n':
            assert(numedges == 4)


def test8():
    # make sure regulation can swap
    networks = run("params_short.json")
    assert('X1 : (X1)(~X3) : E\nX2 : (~X1) : E\nX3 : (X1 + X2) : E\n' in networks)


if __name__ == "__main__":
    test8()