
def parseEdgeFile(fname):
    ''' Returns a list of (source, target, regulation) edges.
    File format must be:
    1) optional comment lines/column headers beginning with #
    2) data lines where the first column is an edge of the form TARGET_GENE = TYPE_REG(SOURCE_GENE)
    3) other columns in the line must be space, tab, or comma separated
    
    '''
    edgelist=[]
    with open(fname,'r') as f:
        for l in f.readlines():
            if l.strip():
                if l[0] == '#':
                    continue
                wordlist=l.replace(',',' ').replace('=',' ').split()
                target=wordlist[0]
                regsource=wordlist[1].replace('(',' ').replace(')',' ').split()
                if "a" in regsource[0] and "r" not in regsource[0]:
                    reg="a"
                elif "r" in regsource[0] and "a" not in regsource[0]:
                    reg = "r"
                else:
                    raise ValueError("Regulation type ill-specified in edge list.")
                source=regsource[1]
                edgelist.append((source,target,reg))
    return edgelist

def parseNodeFile(fname):
    ''' Returns a list of nodes from the file.
    File format must be: 
    1) optional comment lines/column headers beginning with # 
    2) data lines beginning with NODE_NAME
    3) other columns in the line must be space, tab, or comma separated
    
    '''
    nodelist = []
    with open(fname,'r') as f:
        for l in f.readlines():
            if l.strip():
                if l[0] == '#':
                    continue
                wordlist=l.replace(',',' ').split()
                nodelist.append(wordlist[0])
    return nodelist
