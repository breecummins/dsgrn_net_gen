import dsgrn_net_gen.networksearch as networksearch
import dsgrn_net_gen.fileparsers as fileparsers
import subprocess, os, json, shutil, ast, sys


class Job():

    def __init__(self,paramfile):
        self.paramfile = paramfile
        self.params = json.load(open(paramfile))
        # use datetime as unique identifier to avoid overwriting
        if "datetime" not in self.params:
            datetime = subprocess.check_output(['date +%Y_%m_%d_%H_%M_%S'],shell=True).decode(sys.stdout.encoding).strip()
        else:
            datetime = self.params["datetime"]
        resultsdir = "" if "resultsdir" not in self.params else self.params["resultsdir"]
        resultsdir =os.path.join(os.path.expanduser(resultsdir), "dsgrn_net_gen_results"+datetime)
        self.perturbationsdir = os.path.join(resultsdir,"networks"+datetime)
        os.makedirs(self.perturbationsdir)
        self.inputfilesdir = os.path.join(resultsdir,"inputs"+datetime)
        os.makedirs(self.inputfilesdir)
        # save parameter file to computations folder
        shutil.copy(self.paramfile,self.inputfilesdir)
        shutil.copy(self.params["networkfile"], self.inputfilesdir)
        #TODO: Record versions/git number of DSGRN and dsgrn_net_gen

    def _parsefile(self,eorn,parsefunc):
        f = eorn+"file"
        l = eorn+"list"
        if f in self.params and self.params[f].strip():
            try:
                self.params[l] = parsefunc(self.params[f])
                shutil.copy(self.params[f], self.inputfilesdir)
            except:
                raise ValueError("Invalid " + eorn + " file.")
        else:
            self.params[l] = None

    def run(self):
        # read network file
        networks = open(self.params["networkfile"]).read()
        if networks[0] == "[":
            networks = ast.literal_eval(networks)
        else:
            while networks[-1] == '\n':
                networks = networks[:-1]
            networks = [networks]
        sys.stdout.flush()
        self._parsefile('edge',fileparsers.parseEdgeFile)
        self._parsefile('node',fileparsers.parseNodeFile)
        print("\nNetwork search beginning.\n")
        perturbed_networks = []
        for network_spec in networks:
            perturbed_networks.extend(networksearch.perturbNetwork(self.params,network_spec))
        networks=list(set(perturbed_networks))
        with open(os.path.join(self.perturbationsdir,"networks.txt"),"w") as f:
            f.write(str(networks))
        print("\nNetwork search complete.\n")
        sys.stdout.flush()



