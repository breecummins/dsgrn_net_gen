# Getting started

This module accepts DSGRN network specifications and generates a collection of DSGRN-computable networks in the neighborhood of the input network(s), subject to constraints in a parameter file in .json format.

__Dependencies:__ Python 3.6/3.7, networkx, DSGRN (https://github.com/shaunharker/DSGRN or https://github.com/marciogameiro/DSGRN) and its dependencies.

__DSGRN References:__ http://epubs.siam.org/doi/abs/10.1137/15M1052743, https://link.springer.com/chapter/10.1007/978-3-319-67471-1_19, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5975363/, https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006121

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

Alternatively, in a script or ipython or jupyter notebook, do
```python
from dsgrn_net_gen.makejobs import Job

job = Job("params.json")
job.run()
```

The keywords in the .json parameter dictionary are given as follows. See the `tests` folder for example parameter .json files.

# Parameters 
__Required:__

  `networkfile`         =   Path to a text file containing either a single network specification
                            or a list of them (comma-separated and surrounded by square
                            brackets, saved as plain text) to act as a seed network for generating neighboring networks. Use a file containing the empty list (square brackets []) to generate networks without a starting seed.

   `numneighbors`    =   Maximum number of neighboring networks to find (integer);
                            process may time out before this number is reached. 
                            
   `probabilities`      =   dictionary with operations for adding and removing nodes and edges keying 
                               the probability that the operation will occur
                               template = 
                               {"addNode" : p1, "removeNode" : p2, "addEdge" : p3, "removeEdge" : p4}, where the "p" variables are floats between 0 and 1.
                               The entries should sum to 1. If this is not true, all entries will be rescaled
                               so that the sum is 1.
                             
                                                   
   `range_operations`   =   [int,int] min to max # of node/edge changes allowed per graph, 
                               endpoint inclusive. When set equal to `[n,n]`, then exactly `n` operations will be performed according to the probability distribution `probabilities`.
                               
    
   `maxparams`         =   Accept networks with this number of DSGRN parameters or fewer
                               
                              



__Optional__: 

  `resultsdir`     =   path to location where results directory is to be stored, 
                            default is current directory

`time_to_wait`        =   Maximum time in seconds (integer) allowed to calculate perturbed networks;
                            intended as a fail-safe when there are not enough computable networks 
                            in the neighborhood,
                            default = 30

`nodefile`            =   path to a text file containing the names of nodes to add, one line per name, default = no file

 `edgefile`            =   path to text file containing named edges to add, one per line,
                            in the form TARGET_NODE = TYPE_REG(SOURCE_NODE),
                            where TYPE_REG  is "a" (activation) or "r" (repression), default = no file

   `filters`             =   dictionary of function names keying dictionaries with keyword arguments
                            format: 
                            {"function_name1" : kwargs_dict_1, "function_name2" : kwargs_dict_2, ... }
                            See filters.py for the implemented filter functions and their arguments. 
                            The default is to seek only connected networks:
                            default = {"is_connected" : {}}
                        
  `compressed_output`   =   (true or false) default = true, prints count of warnings instead of printing every network 
                            specification that fails filtering. This should only be set to false for troubleshooting.
                            
   `DSGRN_optimized`     =   (true or false) default = true, prioritizes adding new edges to nodes missing in- or out-edges.
                            This should only be set to false if nodes without in- or out-edges are desired.
                            The case of no out-edges is currently under development.
                            
   `random_seed`         =   (integer) random seed for pseudo-random number generator, default = system time (for stochastic results) 

__NOTES:__

* Currently, all DSGRN networks generated by this algorithm are analyzed in essential mode (see https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006121 for a brief mention). Briefly, essential means that every edge in the network has a nontrivial role in the network dynamics. Calculations in essential mode occur even if the input network is written in inessential mode, which includes edges that may not be effectively functioning. Calculating in essential mode usually results in a much smaller parameter graph, which means much faster computation. 

* Currently, DSGRN does not support self-repressing edges or zero out-edges except in `develop` branches that are pre-alpha. However, nodes with no in-edges are supported. 

* Currently, DSGRN supports most node topologies with up to 4 in-edges, but has spotty coverage for the number of associated out-edges. These values can be calculated using https://github.com/marciogameiro/DSGRN, but the code maintainer will have to be contacted. For this reason, `constrained_inedges` should probably have a max value no greater than 4. Currently, `constrained_outedges` has a heuristic upper bound of 5 outedges. But again, contact the maintainer to have more topologies implemented.

* Using the `constrained_inedges` and `constrained_outedges` filters may substantially reduce computation time when the upper bound of `range_operations` is high and adding an edge has high probability.

* Network searches will always assume that activating edges are summed together. Activating edges that are multiplied will be recast into addition, potentially enlarging the size of the parameter graph for 3 or more in-edges. (See references for more detail.)

* New filters can be implemented in `dsgrn_net_gen.filters` to provide more complex constraints on the neighborhood search. The API is 
    
        new_function(graph,kwargs={})
    where `graph` is a graph object from `dsgrn_net_gen.graphtranslation`. Output is `True, ""` or `False, "warning message"`.

# Output

The list of DSGRN network specifications from the search process is saved to a file 
```
resultsdir/dsgrn_net_gen<datetime>/networks<datetime>/networks.txt
``` 
To make into a Python list, open ipython and do
```python
import ast
networks = ast.literal_eval(open("networks.txt").read())
```
The folder
```
resultsdir/dsgrn_net_gen<datetime>/inputfiles<datetime>
``` 
contains copies of the network file and parameters file used as inputs for the search process.

# Understanding parameter interactions


The number of resulting networks from the search process can be unexpected due to dependence between the input files and between the parameters themselves. In particular, parameters cannot be chosen independently, because they work together to reduce the search space of networks. 

The parameter `probabilities` biases the search space toward operations of specific types. For example, if only `addNodes` and `addEdges` are nonzero, and the removals have zero probability, then nodes and/or edges will only be added to the seed network. This means that the seed network will always be a subgraph of any network generated by the search process. This leads to further interactions. Suppose the number of DSGRN parameters associated to the seed network is `N`. Then the user must set `maxparams = M > N`, otherwise no networks will be accepted during the search process. 

Likewise, if only `removeNodes` and `removeEdges` are nonzero, then every perturbed network is a subgraph of the seed network. If the seed network is small, then only a few perturbed networks can be produced. 
Finding a balance between removals and additions given the form of the seed network can be a delicate task, and likely will take some experimentation.

Other interactions can occur with the parameter `range_operations`. This parameter controls how many additions and removals are allowed to occur during the generation of a single perturbed network. Suppose the user sets `range_operations = [8,10]`, so that the minimum number of additions and removals is 8, and the maximum is 10. This is a large number of operations for moderately sized networks, and therefore `maxparams` will have to be set high in order for any networks to be accepted during the search process when the probability of adding nodes and/or edges is high. Also, there need to be enough nodes and edges in the `nodefile` and `edgefile` paths to support the requested number of operations, if these files are specified. 

The functions in `filters` also bias which networks are accepted during the search process. If a user requests only strongly connected networks, for example, then many networks will be rejected because they do not meet this criterion. In this case, the parameter `time_to_wait` will have to be large enough to ensure a reasonable sample size, provided it exists in the neighborhood. 

# Troubleshooting

During the search process, there are running summary statements printed to standard output showing the current state of the search. The output `Accepted: # networks` tells the user how many networks have been accepted so far. The other messages can help a user figure out what is happening if not enough networks are being produced. The warnings include

```
    Aborted: # networks
    Too many params: # networks
    Not computable: # networks   
```

`Aborted` networks are those networks for which there are not enough nodes and/or edges left to satisfy the number of requested operations. In particular, `nodefile` or `edgefile` may have too few entries, the empty graph may have been produced and further removals are requested, or the complete graph may have been produced and further additions are requested. `Too many params` means the networks were rejected because the number of DSGRN parameters exceeded `maxparams` as specified in the parameter .json file. `Not computable` means that the network cannot be computed by DSGRN. This means that there are too many in-edges at some node, too many out-edges at some node, or (as of this writing) 0 out-edges at some node. DSGRN is limited to a certain number of in- and out-edges. At the time of this writing, 5 in-edges or 5 out-edges is likely too many (although not always).

In addition, there are specific warnings for each filter in `filters`, and these are self-explanatory if a user understands the `filters` they specify. At the time of this writing, the filter messages include
 ```
 Not connected: # networks
 Not strongly connected: # networks
 Not feed-forward: # networks
 Out-edges not in range: # networks
 In-edges not in range: # networks
 ```
 

## Common problems with network searches

1. There are no networks produced. 
    * The seed network has a node that has too many in-edges or too many out-edges, and the `probabilities` parameter has non-zero probabilities only for adding nodes and edges. In this case, no DSGRN computable networks can be constructed, because there will always be a non-computable subnetwork. At the time of this writing, 5 in-edges or 5 out-edges at a single node is likely too many (although not always). You must either (a) reduce the number of edges in your seed network, or (b) change your `probabilities` parameter so that removing nodes and/or edges is permitted.
      
     * The `maxparams` parameter may be too small. For example, if the seed network has 5000 parameters, but `maxparams` is 1000, and the `probabilities` parameter has non-zero probabilities only for adding nodes and edges, then no networks will be accepted. Thus there is always a subgraph with 5000 parameters. Since every produced network has at most 1000 parameters, all networks will be rejected. To check the number of parameters for a (DSGRN computable) seed network, open `ipython` or a Jupyter notebook and execute the following:
        ```
        import DSGRN
        network = DSGRN.Network("networkfile.txt")
        pg = DSGRN.ParameterGraph(network) 
        pg.size()
        ```
       where `"networkfile.txt"` is a single DSGRN network specification (i.e., is not a list of specifications). You can also initialize a `DSGRN.Network` object with a network specification as a string rather than in a file. So you can copy a specific network out of a file or off the commandline. If the seed network is not DSGRN computable, you can add edges until it is strongly connected and check the number of parameters. If any node has too many in- or out-edges, then the network will also not be DSGRN computable.
     * The `nodefile` path is specified, but points to a file with no new nodes to add, and the only non-zero `probabilities` parameter is `addNode`. 
    
     * The `edgefile` path is specified, but points to a file with no new edges to add, and the only non-zero `probabilities` parameter is `addEdge`. 

     * The `edgefile` has only non-allowable edges, such as negative self-loops (which are never added to the network); or edges that can only result in a non-computable network and the `probabilities` for removing nodes and edges are zero.
         
     * The `edgefile` has only edges that connect nodes that are not in `node_file` or in the seed network.

2. There are many fewer networks produced than requested.
    * The `time_to_wait` parameter may be too small.
    * The specified `filters` may be too restrictive.
    * `range_operations` can be either too permissive, leading to a huge network space that is hard to search, or too restrictive, limiting the search to a very small neighborhood. Hopefully there is a clue in the process summary described in the Troubleshooting section. 
    * Constraints in the `nodefile` and `edgefile` lists of nodes and edges can limit the number of networks that is possible to construct. Be aware that files with few nodes and/or edges can reduce the number of permissible networks.
    * The `probabilities` parameter may emphasizing the wrong kind of operations. For example, if `addNode = 0.1` and `addEdge = 0.9`, but you only have 2 nodes to begin with, then there could be very few networks that meet all specified criteria, and it could take a very long sampling time to find any networks with substantially more nodes. Note that there's an interplay with `range_operations` here. If `range_operations = [1,10]`, then you're likely to get at least a few networks with more nodes, but if `range_operations = [1,3]`, then it will be hard to find networks with more nodes.
    
3. Unexpected nodes and edges are added. 
    * `nodefile` is not specified and so nodes with automatically generated names are added. This is also true of `edgefile`.
            
## Generating a neighboring network

It may be useful to understand how a neighboring network is generated in order to solve a problem. The algorithm first chooses a random number in the interval `range_operations`, say `n`. Then `n` random variables are independently drawn from the discrete probability distribution given by the (possibly rescaled) parameter `probabilities`. The discrete distribution is over the four operations `removeNode`, `removeEdge`, `addNode`, and `addEdge`. The operations to the seed network are performed in the order listed. That is, if there are three `removeNode` operations chosen from the random sampling process, then three randomly chosen nodes and their connecting edges are removed before anything else happens. Second, randomly chosen edges are removed, provided that there remain more edges to remove than have already been deleted. For example, if 5 edges have chosen to be removed, and there are four connecting edges removed during node removal, then one more edge will be removed in the second step. Third, randomly chosen nodes are added (from `nodefile` if provided), and fourth, randomly chosen edges are added  (from `edgefile` if provided). 

The parameter `DSGRN_optimized = true` prioritizes adding edges to nodes that are missing in- or out-edges. This biases network search space toward DSGRN computable networks. It is recommended to leave this parameter set to the default `true` unless the user specifically wants nodes with no in-edges or no out-edges. Recall that nodes with no out-edges are currently not DSGRN computable in the released versions of DSGRN.

Notice that when `removeNode` and `removeEdge` have `probabilities` entries of 0, then the seed network will always be a subgraph of all neighboring networks. Likewise, when `addNode` and `addEdge` are 0, then all neighboring networks are subgraphs of the seed network. 

