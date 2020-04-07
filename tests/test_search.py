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


def check_size(networks):
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
    return conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params


def test1():
    networks = run("params_X1X2X3_A.json")
    # for n in networks:
    #     print(n)
    #     print("\n")
    assert(len(networks)==10)
    conn, sconn, ff, numnodes, numedges, mininedges, maxinedges, minoutedges, maxoutedges,params = check_size(networks)
    assert(all(conn))
    assert(numedges.count(5) == 1)
    assert(all([e >= 5 for e in numedges]))
    assert(all([n >= 3 for n in numnodes]))
    assert(all([p < 1000 for p in params]))
