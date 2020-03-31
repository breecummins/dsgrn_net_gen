# Getting started

This module accepts DSGRN network specifications and generates a collection of DSGRN-computable networks in the neighborhood of the input network(s), subject to constraints in a parameter file in json format.

__Dependencies:__ Python 3.6/3.7, networkx, DSGRN (https://github.com/shaunharker/DSGRN or https://github.com/marciogameiro/DSGRN) and its dependencies.

To install, do
```bash    
    cd dsgrn_net_gen
    . install.sh
```

To run tests to confirm the code is working as expected, do

```bash    
    cd tests
    pytest
```

Calling script is `dsgrn_net_gen/call_job.py`:
```bash    
    python call_job.py <params.json>
```    

Alternatively, in a script, or ipython, or jupyter notebook, do
```python
from dsgrn_net_gen.makejobs import Job

job = Job("params.json")
job.run()
```

See the `examples` folder for examples of the json parameter file. The keywords in the json parameter dictionary are given as follows.

# Parameters 
__Required:__

    networkfile         =   path to a text file containing either a single network specification
                            or a list of them (comma-separated and surrounded by square
                            brackets, saved as plain text)

    numneighbors    =   Maximum number of neighboring networks to find (integer);
                            process may time out before this number is reached. 
                            
                                
A date and time stamped results folder will be produced. By default, it's stored in the current directory, but the user may optionally specify a different location.

    computationsdir     =   path to location where results directory is to be stored 
                            default is current directory


The following are optional parameters that control the behavior of the neighborhood search.

    probabilities      =   dictionary with operations for adding and removing nodes and edges keying 
                           the probability that the operation will occur
                           default = 
                           {"addNode" : 0.50, "removeNode" : 0.0, "addEdge" : 0.50, "removeEdge" : 0.0}
                           The entries sum to 1. If this is not true, all entries will be normalized 
                           so that the sum is 1.
                         
                                               
    range_operations   =   [int,int] min to max # of node/edge changes allowed per graph, 
                           endpoint inclusive
                           default = [1,5]

    maxparams           =   Accept networks with this number of DSGRN parameters or fewer
                            default = 20000

    time_to_wait        =   Maximum time in seconds (integer) allowed to calculate perturbed networks;
                            intended as a fail-safe when there are not enough computable networks 
                            in the neighborhood
                            default = 30

    nodefile            =   path to a text file containing the names of nodes to add, one line per name
                            default = no file

    edgefile            =   path to text file containing named edges to add, one per line,
                            in the form TARGET_NODE = TYPE_REG(SOURCE_NODE),
                            where TYPE_REG  is "a" (activation) or "r" (repression)
                            default = no file

    filters             =   dictionary of function names keying dictionaries with keyword arguments
                            format: 
                            {"function_name1" : kwargs_dict_1, "function_name2" : kwargs_dict_2, ... }
                            See filters.py for the implemented filter functions and their arguments. 
                            The default is to seek only connected networks:
                            default = {"is_connected" : {}}
                        
    compressed_output   =   (true or false) prints count of warnings instead of printing every network 
                            specification that fails filtering. 
                            This should only be set to false for trouble-shooting.
                            default = true
                            
    DSGRN_optimized     =   (true or false) prioritizes adding new edges to nodes missing in- or out-edges.
                            This should only be set to false if nodes without in- or out-edges are desired.
                            default = true
                            
    random_seed         =   (integer) random seed for pseudo-random number generator
                            default = system time (for stochastic results) 

__NOTES:__

* Network perturbations will always assume that activating edges are summed together. Activating edges that are multiplied will be recast into addition, potentially changing the size of the parameter graph.

* All networks are analyzed in essential mode, even if they are written in non-essential mode.

    
* New filters can be implemented in `dsgrn_net_gen.filters`. 

* Using the `constrained_inedges` and `constrained_outedges` filters may substantially reduce computation time in some cases.

# Output

## Neighboring networks

The list of DSGRN network specifications from the search process is saved to a file 
```
computationsdir/networks<datetime>/networks.txt
``` 
To make into a Python list, open ipython and do
```python
import ast
networks = ast.literal_eval(open("networks.txt").read())
```

# Troubleshooting


The number of resulting perturbations from the search process can be unexpected due to dependence between the input files and between the parameters themselves. In particular, parameters cannot be chosen independently, because they work together to reduce the search space of networks. 

The parameter `probabilities` biases the search space toward operations of specific types. For example, if only `addNodes` and `addEdges` are nonzero, and the removals have zero probability, then nodes and/or edges will only be added to the seed network. This means that the seed network will always be a subgraph of any network generated by the perturbation process. This leads to further interactions. Suppose the number of DSGRN parameters associated to the seed network is `N`. Then the user must set `maxparams = M > N`, otherwise no networks will be accepted during the search process. 

Likewise, if only `removeNodes` and `removeEdges` are nonzero, then every perturbed network is a subgraph of the seed network. If the seed network is small, then only a few perturbed networks can be produced. 
Finding a balance between removals and additions given the form of the seed network can be a delicate task, and likely will take some experimentation.

Other interactions can occur with the parameter `range_operations`. This parameter controls how many additions and removals are allowed to occur during the generation of a single perturbed network. Suppose the user sets `range_operations = [8,10]`, so that the minimum number of additions and removals is 8, and the maximum is 10. This is a large number of operations, and therefore `maxparams` will have to be set high in order for any networks to be accepted during the search process. Also, there need to be enough nodes and edges in the `nodefile` and `edgefile` paths to support the requested number of operations, if these parameters are specified.

The functions in `filters` also bias which networks are accepted during the search process. If a user requests only strongly connected networks, for example, then many networks will be rejected because they do not meet this criterion. In this case, the parameter `time_to_wait` will have to be large enough to ensure a reasonable sample size. 

During the search process, there are running summary statements printed to standard output showing the current state of the search. The output `Accepted networks : # networks` tells the user how many networks have been accepted into the perturbations list so far. The other messages can help a user figure out what is happening if not enough networks are being produced. The warnings include

```
    Aborted networks : # networks
    Too many parameters : # networks
    Network spec not computable : # networks   
```

`Aborted networks` are those networks for which there are not enough nodes and/or edges left to satisfy the number of requested operations. In particular, `nodefile` or `edgefile` may have too few entries, the empty graph may have been produced and further removals are requested, or the complete graph may have been produced and further additions are requested. `Too many parameters` means the networks were rejected because the number of DSGRN parameters exceeded `maxparams`. `Network spec not computable` means that the network cannot be computed by DSGRN. This means that there are too many in-edges at some node, too many out-edges at some node, or (as of this writing) 0 out-edges at some node. DSGRN is limited to a certain number of in- and out-edges. At the time of this writing, 5 in-edges or 5 out-edges is likely too many (although not always).

In addition, there are specific warnings for each filter in `filters`, and these are self-explanatory if a user understands the `filters` they specify. At the time of this writing, the filter messages include
 ```
 Not strongly connected : # networks
 Not feed-forward : # networks
 Number of out-edges not in range : # networks
 Number of in-edges not in range : # networks
 ```
 

## Common problems with network searches

1. There are no networks produced. 
    * The seed network has a node that has too many in-edges or too many out-edges, and the `probabilities` parameter has non-zero probabilities only for adding nodes and edges. In this case, no DSGRN computable networks can be constructed, because there will always be a non-computable subnetwork. At the time of this writing, 5 in-edges or 5 out-edges at a single node is likely too many (although not always). You must either (a) reduce the number of edges in your seed network, or (b) change your `probabilities` parameter so that removing nodes and/or edges is permitted.
      
     * The `maxparams` parameter may be too small. For example, if the seed network has 5000 parameters, but `maxparams` is 1000, and the `probabilities` parameter has non-zero probabilities only for adding nodes and edges, then no networks will be accepted. Thus there is always a subgraph with 5000 parameters. Since every produced network has more than a 1000 parameters, all networks will be rejected. To check the number of parameters for a seed network, repeat the previous steps and do
        ```
        import DSGRN
        network = DSGRN.Network("networkfile.txt")
        pg = DSGRN.ParameterGraph(network) 
        pg.size()
        ```
       where `"networkfile.txt"` is a single DSGRN network specification (i.e., is not a list of specifications).
     * The `node_file` path is specified, but points to an empty file, and the only non-zero `probabilities` parameter is `addNode`. 
    
     * The `edge_file` path is specified, but points to an empty file, and the only non-zero `probabilities` parameter is `addEdge`. 

     * The `edge_file` has only non-allowable edges, such as negative self-loops (which are never added to the network); or edges that can only result in a non-computable network and the `probabilities` for removing nodes and edges are zero.
         
     * The `edge_file` has only edges that connect nodes that are not in `node_file` or in the seed network.

2. There are many fewer networks produced than requested.
    * The `time_to_wait` parameter may be too small.
    * The specified `filters` may be too restrictive.
    * Network space may be too large. Restricting `range_operations` to a narrower interval may help.
    * Constraints in the `node_file` and `edge_file` lists of nodes and edges can limit the number of networks that is possible to construct. Be aware that files with few nodes and/or edges can reduce the number of permissible networks.
    * The `probabilities` parameter may emphasizing the wrong kind of operations. For example, if `addNode = 0.1` and `addEdge = 0.9`, but you only have 3 nodes, then there are very few networks that are likely to be created, and it will take a very long sampling time to find any networks with substantially more nodes. Note that there's an interplay with `range_operations` here. If `range_operations = [1,10]`, then you're likely to get at least a few networks with more nodes, but if `range_operations = [1,3]`, then it will be hard to find networks with more nodes.
            
### Generating a neighboring network

It may be useful to understand how a neighboring network is generated in order to solve a problem. The first step is to choose a random number in the interval `range_operations`, say `n`. Then `n` random variables are independently drawn from the discrete probability distribution given by the (possibly normalized) parameter `probabilities`. The discrete distribution is over the four operations `addNode`, `addEdge`, `removeEdge`, and `removeNode`. The operations to the seed network are performed in the order listed. That is, if there are three `addNode` operations chosen from the random sampling process, then three randomly chosen nodes are added (from `nodefile` if provided) before anything else happens. Second, randomly chosen edges are added (from `edgefile` if provided), third, randomly chosen edges are removed, and fourth, randomly chosen nodes and their connecting edges are removed.

The parameter `DSGRN_optimized = true` prioritizes adding edges to nodes that are missing in- or out-edges. This biases network search space toward DSGRN computable networks. It is recommended to leave this parameter set to the default `true` unless the user specifically wants nodes with no in-edges or no out-edges. There is no optimization for removing edges to produce DSGRN computable networks, so be prepared to have more non-computable networks when the removal probabilities are nonzero.

