from dsgrn_net_gen.makejobs import Job
import subprocess, os, ast


def run(paramfile):
    job = Job(paramfile)
    job.run()
    ndir = subprocess.getoutput("ls -td ./computations*/networks*/ | head -1")
    resultsfile = os.path.join(ndir, "networks.txt")
    networks = ast.literal_eval(open(resultsfile).read())
    subprocess.call("rm -r " + ndir, shell=True)
    subprocess.call("rm -r " + subprocess.getoutput("ls -td ./computations*/ | head -1"), shell=True)
    return networks


def test1():
    networks = run("params_X1X2X3_A.json")
    assert(len(networks)==10)

