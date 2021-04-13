import random, time, itertools, sys
import DSGRN
import dsgrn_utilities.graphtranslation as graphtranslation
from functools import partial
from inspect import getmembers, isfunction
import dsgrn_net_gen.filters as filters
from copy import deepcopy

#####################################################################################################################
# Function for perturbing networks.
#####################################################################################################################

def perturbNetwork(params_init, network_spec):
    '''
    Get a list of essential DSGRN network specifications perturbed around an essential seed network given parameters
    in params (see below). Duplicate networks are possible because there is no graph isomorphism checking. Empirical
    usage suggests that the number of duplicates is too small to warrant the computational cost of checking.

    :param params_init: params is a dictionary with the following key,value pairs.
        Required:
        "numneighbors" : integer > 0, how many networks to construct
        "probabilities" : dictionary with node and edge operations keying the probability that the operation will occur
                          template: {"addNode" : p1, "removeNode" : p2, "addEdge" : p3, "removeEdge" : p4}
                          with p1-p4 between 0 and 1, and p1+p2+p3+p4 = 1. If the summation condition does not hold,
                          the probabilities will be rescaled to sum to 1. Setting any probability to zero will ensure
                          that the operation does not occur.
        "range_operations" : [int,int] min to max # of node/edge changes allowed per graph, endpoint inclusive
        "maxparams" : the maximum number of DSGRN parameters allowed per network. Choosing this value too small will
                        eliminate many networks. Picking the value is tricky, as it depends where in network space the
                        search is occurring. In general, 10,000 is small, 500,000 is moderate, and 1,000,000,000 is on
                        the very edge of computability.
        Optional:
        "nodelist" : a list of node labels (strings) acceptable to add to the network,
                    default = [], unconstrained addition of nodes with dummy names
        "edgelist" : a list of ("source","target","regulation") tuples to add as edges to the network
                    default = [], unconstrained addition of edges to existing nodes
                   NOTE: negative self-loops are removed before perturbation, as these are not currently implemented in DSGRN
        "time_to_wait" : integer number of seconds to wait before halting perturbation procedure (avoid infinite while loop)
                        default = 30
        "filters" : dictionary of filter function name strings from filters.py keying input dictionaries
                    with the needed keyword arguments for each function
                    format: {"function_name1" : kwargs_dict_1, "function_name2" : kwargs_dict_2, ... }
                    See filters.py for the implemented filter functions and their arguments.
                    default = {"is_connected" : {}}, only weakly connected networks are accepted
        "compressed_output" : True or False (true or false in .json format), default = True, prints count of warnings
                            instead of printing every network spec that fails filtering. This substantially reduces
                            printing to terminal and should only be set to False for troubleshooting, since printing
                            is a bottleneck.
        "DSGRN_optimized" : True or False (true or false in .json format), default = True, prioritizes adding new edges
                            to nodes missing in- or out-edges, which can decrease computation time.
                            Set to False to remove this bias.
                            NOTE: Can still get nodes without in- or out-edges if probabilities["removeEdge"] is nonzero
        "random_seed" : random seed (set to time.time() for stochastic results in make_jobs.py)
    :param network_spec: DSGRN network specification string
    :return: list of essential DSGRN network specification strings

    '''


    # Initialize
    params = deepcopy(params_init) # required for makejobs.run() to work
    networks = set([])
    params, starting_graph = setup(params,network_spec)
    sanity_check_edges(network_spec,starting_graph)
    starting_netspec = graphtranslation.createEssentialNetworkSpecFromGraph(starting_graph)
    if enforce_filters(starting_graph,starting_netspec,params):
        # add the starting network if it meets the filtering criteria
        networks.add(starting_netspec)
    start_time = time.time()
    count = 0

    # Perturb
    while (len(networks) < params['numneighbors']) and (time.time()-start_time < params['time_to_wait']):
        count += 1
        # add nodes and edges based on params and get the network spec for the new graph
        graph = perform_operations(starting_graph.clone(),params)
        if graph:
            netspec = graphtranslation.createEssentialNetworkSpecFromGraph(graph)
            # check that the network spec is DSGRN computable with few enough parameters and satisfies user-supplied filters
            if enforce_filters(graph,netspec,params):
                networks.add(netspec)
        else:
            params["msg_dict"]["Aborted"] += 1
        if not count%1000 and params["compressed_output"]:
            update_line(params["msg_dict"],len(networks))

    # last update of warnings
    if params["compressed_output"]:
        update_line(params["msg_dict"],len(networks))

    # inform user of the number of networks produced and return however many networks were made
    if time.time()-start_time >= params['time_to_wait']:
        print("\nProcess timed out.")
    print("\nSaving {} networks.".format(len(networks)))
    return list(networks)


##########################################################################################
# Initialization functions
##########################################################################################

def setup(params,network_spec):
    # make starting graph, make sure network_spec is essential, and add network_spec to list of networks
    starting_graph = graphtranslation.getGraphFromNetworkSpec(network_spec)
    # set defaults
    params = set_defaults(params,starting_graph)
    # remove negative self-regulation from edgelist
    if params["edgelist"]:
        params["edgelist"] = filter_edgelist(params["edgelist"])
    # make sure probabilities are normalized and take the cumsum
    params["probabilities"] = make_probability_vector(params["probabilities"])
    # make range_operations end-point inclusive
    params["range_operations"] = [params["range_operations"][0],params["range_operations"][1]+1]
    random.seed(params["random_seed"])
    return params, starting_graph


def set_defaults(params,starting_graph):
    if "nodelist" not in params or not params["nodelist"]:
        params["nodelist"] = []
    else:
        nodeset = set(params["nodelist"])
        for v in starting_graph.vertices():
            nodeset.add(starting_graph.vertex_label(v))
        params["nodelist"] = list(nodeset)
    if "edgelist" not in params or not params["edgelist"]:
        params["edgelist"] = []
    else:
        edgeset = set(params["edgelist"])
        for (u,v) in starting_graph.edges():
            edgeset.add((starting_graph.vertex_label(u),starting_graph.vertex_label(v),starting_graph.edge_label(u,v)))
        params["edgelist"] = list(edgeset)
    if "time_to_wait" not in params:
        params["time_to_wait"] = 30
    if "filters" not in params:
        params["filters"] = [partial(filters.is_connected,kwargs={})]
    else:
        names = list(params["filters"].keys())
        funcs = [o for o in getmembers(filters) if isfunction(o[1]) and o[0] in names]
        not_implemented = set(names).difference([o[0] for o in funcs])
        if not_implemented:
            raise ValueError("\nFilter(s) {} not implemented in filters.py. Please correct the name or add a function.\n".format(not_implemented))
        params["filters"] = [partial(o[1],kwargs=params["filters"][o[0]]) for o in funcs]
    if "compressed_output" not in params:
        params["compressed_output"] = True
    params["msg_dict"] = {"Accepted" : 0, "Aborted" : 0}
    if "DSGRN_optimized" not in params:
        params["DSGRN_optimized"] = True
    return params


def filter_edgelist(edgelist):
    # filter edgelist to remove negative self-loops
    el = edgelist[:]
    for e in edgelist:
        if e[0] == e[1] and e[2] == "r":
            el.remove(e)
    return el


def make_probability_vector(probabilities):
    probs = [probabilities[k] for k in ["addNode","addEdge","removeEdge","removeNode"]]
    cs =  list(itertools.accumulate(probs))
    return [c/cs[-1] for c in cs]


def sanity_check_edges(network_spec,starting_graph):
    try:
        DSGRN.Network(network_spec)
    except RuntimeError as r:
        if str(r) == "Problem parsing network specification file: Repeated inputs in logic":
            raise ValueError("Seed network has a multiedge. Not currently supported by DSGRN.")
    for (u,w) in starting_graph.edges():
        if u == w and starting_graph.edge_label(u,w) == "r":
            raise ValueError("Seed network has a self-repressing edge. Not currently supported by DSGRN.")


##########################################################################################
# Filtering and warning functions
##########################################################################################

def enforce_filters(graph,netspec,params):
    if check_computability(params, netspec):
        if not params["filters"] or user_filtering(graph, params, netspec):
            return True
    return False


def check_computability(params,network_spec):
    if not network_spec:
        msg = "Not computable"
        add_warning(msg, network_spec, params["compressed_output"], params["msg_dict"])
        return False
    network = DSGRN.Network(network_spec)
    try:
        paramgraph=DSGRN.ParameterGraph(network)
        smallenough = paramgraph.size() <= params['maxparams']
        if not smallenough:
            msg = "Too many params"
            add_warning(msg,network_spec, params["compressed_output"], params["msg_dict"])
        return smallenough
    except (AttributeError, RuntimeError):
        msg = "Not computable"
        add_warning(msg, network_spec, params["compressed_output"], params["msg_dict"])
        return False


def user_filtering(graph,params,netspec):
     for fil in params["filters"]:
        isgood, message = fil(graph)
        if not isgood:
            add_warning(message, netspec, params["compressed_output"], params["msg_dict"])
            return False
     return True


def add_warning(msg,network_spec,compressed_output,msg_dict):
    if compressed_output:
        if msg not in msg_dict:
            msg_dict[msg] = 1
        else:
            msg_dict[msg] += 1
    else:
        print("\n{}. Not using network spec: \n{}\n".format(msg, network_spec))
    return None


def update_line(msg_dict,N):
    msg_dict["Accepted"] = N
    mstr = "; ".join([msg + ": {}".format(count) for msg,count in msg_dict.items()])
    sys.stdout.write("\b" * len(mstr))
    sys.stdout.write(" " * len(mstr))
    sys.stdout.write("\b" * len(mstr))
    sys.stdout.write(mstr)
    sys.stdout.flush()


##############################################################################
# Stochastic numbers of additional edges and/or nodes to perturb the network.
##############################################################################

def perform_operations(graph,params):
    # choose the number of each type of operation
    numops = choose_operations(params)
    # apply operations in the proper order
    if graph:
        graph,num_edges = removeNodes(graph,numops[3])
    else:
        num_edges = 0
    if graph:
        ne = numops[2] - num_edges
        if ne > 0:
            graph = removeEdges(graph,ne)
    if numops[0] and graph is None:
        graph = graphtranslation.Graph()
    graph = addNodes(graph, params["nodelist"],numops[0])
    if graph and params["DSGRN_optimized"]:
        graph = addEdges_DSGRN_optimized(graph,params["edgelist"],numops[1])
    elif graph:
        graph = addEdges(graph, params["edgelist"], numops[1])
    return graph


def choose_operations(params):
    # choose a random number of graph additions or swaps
    numadds = random.randrange(*params["range_operations"])
    # generate operations with probabilities as given in params
    probs = sorted([random.uniform(0.0, 1.0) for _ in range(numadds)])
    numops=[0,0,0,0]
    for j in range(4):
        p = params["probabilities"][j]
        while probs and probs[0] <= p:
            numops[j]+=1
            probs.pop(0)
    return numops


################################################################################################
# Basic add and remove methods of the network perturbation.
################################################################################################

def removeEdges(graph,numedges):
    if len(graph.edges()) <= numedges:
        return None
    for _ in range(numedges):
        graph.remove_edge(*random.choice(graph.edges()))
    return graph


def removeNodes(graph,numnodes):
    if len(graph.vertices()) <= numnodes:
        return None, None
    numedges = 0
    for _ in range(numnodes):
        node = random.choice(list(graph.vertices()))
        numedges += sum([1 for e in graph.edges() if node in e])
        graph.remove_vertex(node)
    return graph,numedges


def addNodes(graph,nodelist,numnodes):
    # if nodelist, choose numnodes random nodes from nodelist
    # if no nodelist, make up names for new nodes
    for _ in range(numnodes):
        networknodenames = getNetworkLabels(graph)
        N = len(networknodenames)

        if not nodelist:
            # make unique node name
            newnodelabel = 'x'+str(N+1)
            c=1
            while newnodelabel in networknodenames:
                newnodelabel = 'x'+str(N+1+c)
                c+=1
        else:
            # filter nodelist to get only new nodes
            nl = [ n for n in nodelist if n not in networknodenames ]
            newnodelabel = getRandomListElement(nl)

        # add to graph
        if newnodelabel:
            graph.add_vertex(N,label=newnodelabel)
    return graph


def addEdges(graph,edgelist,numedges):
    # if no edgelist, then a random edge is added to the network
    # if edgelist is specified, a random choice is made from the filtered edgelist
    # (repressing self-loops removed)
    # numedges = number of edges to add

    # get info from graph
    networknodenames = getNetworkLabels(graph)
    N = len(networknodenames)
    edges = set([(v, a, graph.edge_label(v, a)) for (v, a) in graph.edges()])

    # get allowable edges for this graph
    if edgelist:
        el = list(set([tuple(getVertexFromLabel(graph, e[:2]) + [e[2]]) for e in edgelist if set(e[:2]).issubset(
            networknodenames)]).difference(edges))

    # add edges
    for _ in range(numedges):
        # choose an edge from the list
        if edgelist:
            while el:
                newedge = getRandomListElement(el)
                if newedge:
                    el.remove(newedge)
                    if newedge[:2] not in graph.edges():
                        graph.add_edge(*newedge)
                        break
                else:
                    # punt if can't add an edge
                    return None
        # otherwise produce random edge that is not a negative self-loop
        else:
            if len(graph.edges()) == len(graph.vertices())**2:
                # stop if graph is complete
                return None
            newedge = getRandomEdge(N)
            while newedge[:2] in graph.edges() or (newedge[0]==newedge[1] and newedge[2]=='r'):
                newedge = getRandomEdge(N)
            # since graph is not complete, an edge can always be added
            edges.add(newedge)
            graph.add_edge(*newedge)
    return graph


def addConnectingEdges(graph, nodes, edgelist):
    # add connecting edges for nodes in list

    # get info from graph
    networknodenames = getNetworkLabels(graph)
    N = len(networknodenames)

    # add edges for prioritized nodes, punt if edges cannot be constructed
    need = getMissingEdges(graph,nodes)
    while need:
        nv, edge_type = getRandomListElement(need)
        n = graph.vertex_label(nv)
        if edgelist:
            if edge_type == "in":
                el_in = [tuple(getVertexFromLabel(graph, e[:2]) + [e[2]]) for e in edgelist if n == e[1] and e[0] in networknodenames]
                newedge = getRandomListElement(el_in)
            else:
                el_out = [tuple(getVertexFromLabel(graph, e[:2]) + [e[2]]) for e in edgelist if n == e[0] and e[1] in networknodenames]
                newedge = getRandomListElement(el_out)
            if not newedge:
                return None
        else:
            newv, newr = getHalfEdge(nv,N)
            if edge_type == "in":
                newedge = (newv, nv, newr)
            else:
                newedge = (nv, newv, newr)
        graph.add_edge(*newedge)
        need = getMissingEdges(graph,nodes)
    return graph


def addEdges_DSGRN_optimized(graph,edgelist,numedges):
    # prioritize nodes with missing in- and out-edges, and return None if there aren't enough edge perturbations
    # to correct them all
    # if no edgelist, then a random edge is added to the network
    # if edgelist is specified, a random choice is made from the filtered edgelist
    # (repressing self-loops removed)

    # record original number of edges
    M0 = len(graph.edges())
    # add prioritized edges
    graph = addConnectingEdges(graph, graph.vertices(), edgelist)
    if not graph:
        return None
    # adjust number of perturbations
    M1 = len(graph.edges())
    numedges -= (M1-M0)

    if numedges < 0:
        # punt if exceeded perturbations
        return None
    elif numedges == 0:
        # stop if achieved perturbations
        return graph
    else:
        # add remaining perturbations
        return addEdges(graph, edgelist, numedges)



#################################################################################################
# Helper functions to access graph labels and produce random choices.
##################################################################################################

def getNetworkLabels(graph):
    # need node names to choose new nodes/edges
    if graph is None:
        return []
    return [ graph.vertex_label(v) for v in graph.vertices() ]

def getVertexFromLabel(graph,nodelabels):
    return [ graph.get_vertex_from_label(n) for n in nodelabels ]

def getRandomNode(n):
    # pick node
    return random.randrange(n)

def getRandomEdge(n):
    # pick random edge
    return getRandomNode(n), getRandomNode(n), getRandomReg()

def getRandomReg():
    # pick regulation
    regbool = random.randrange(2)
    return 'a'*regbool + 'r'*(not regbool)

def getRandomListElement(masterlist):
    # pick randomly from list
    if not masterlist: return None
    else: return random.choice(sorted(masterlist))

def getHalfEdge(n,N):
    newv, newr = getRandomNode(N), getRandomReg()
    while newv == n and newr == "r":
        newv, newr = getRandomNode(N), getRandomReg()
    return newv,newr

def getMissingEdges(graph,vertices):
    need = []
    for v in vertices:
        if not graph.adjacencies(v):
            need.append((v,"out"))
        if not graph.inedges(v):
            need.append((v, "in"))
    return need




