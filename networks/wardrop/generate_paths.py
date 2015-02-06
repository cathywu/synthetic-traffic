'''
Created on Jul 23, 2014

@author: jeromethai
'''

import numpy as np
import networks.wardrop.ue_solver as ue
import networks.wardrop.path_solver as path
from cvxopt import matrix
from networks.wardrop.generate_graph import los_angeles
import networks.wardrop.shortest_paths as sh


theta = matrix([0.0, 0.0, 0.0, 0.15])


def test_helper(demand, paths):
    g = los_angeles(theta, 'Polynomial')[demand]
    for p in paths: g.add_path_from_nodes(p)
    P = path.linkpath_incidence(g)
    g.visualize(general=True)
    l1 = ue.solver(g, update=True)
    d1 = sum([link.delay*link.flow for link in g.links.values()])
    l2 = P*path.solver(g, update=True)
    d2 = sum([p.delay*p.flow for p in g.paths.values()])
    l3 = ue.solver(g, update=True, SO=True)
    d3 = sum([link.delay*link.flow for link in g.links.values()])
    l4 = P*path.solver(g, update=True, SO=True)
    d4 = sum([p.delay*p.flow for p in g.paths.values()])
    return l1,l2,l3,l4,d1,d2,d3,d4
    
    
def get_shortest_paths(g, K):
    """Get the K-shortest paths for all the OD pairs in the graph with current delay
    """
    paths = []
    for sink in [5,20,22]:
        sources = [od[0] for od in g.ODs.keys() if od[1]==sink]
        As = sh.mainKSP(g, sources, sink, K)
        for s in sources:
            for p in As[s]: paths.append(p)
    return paths
    

def get_paths(SO, K, demand, return_paths=True, ffdelays=False, path=None):
    """This experiment does the following tests:
    1. compute the UE/SO link flows using node-link formulation 
    2. get the link delays for the UE/SO link flow
    3. find the K-shortest paths for these delays/marginal delays (used ones under UE/SO)
    4. add these paths to the network
    5. compute the UE/SO path flows using link-path formulation
    6. check if we get the same UE/SO link flow
    
    Parameters:
    -----------
    SO: if False, compute the UE, if True, compute the SO
    K: number of shortest paths
    demand: choice of OD demand
    return_paths: if True, return paths
    ffdelays: if True the k-shortest paths are obtained from ff delays
    
    Return value:
    ------------
    """
    g = los_angeles(theta, 'Polynomial', path=path)[demand]
    if ffdelays: paths = get_shortest_paths(g, K)
    l1 = ue.solver(g, update=True, SO=SO)
    d1 = sum([link.delay*link.flow for link in g.links.values()])
    if SO:
        for link in g.links.values():
            link.delay = link.ffdelay*(1+0.75*(link.flow*link.delayfunc.slope)**4)
    if not ffdelays: paths = get_shortest_paths(g, K)
    if return_paths: return paths
    for p in paths: g.add_path_from_nodes(p)
    g.visualize(general=True)
    P = path.linkpath_incidence(g)
    l2 = P*path.solver(g, update=True, SO=SO)
    d2 = sum([p.delay*p.flow for p in g.paths.values()])
    print d1,d2
    return d1,d2,paths


def find_optimum_K(tol=1.0):
    """Find the minimum of k-shortest paths to get the same UE/SO
    for both node-link and link-path formulations
    
    Results:     tol    0.1       1.0       10.0
    -------
    SO=False: best = [2,3,3,4] [2,3,3,3] [2,2,2,3]
    SO=True: best = [2,4,7,9] [2,3,7,9] [2,2,4,7]
    """
    result = []
    for SO in [False, True]:
        best_k = []
        for i in range(4):
            for j in range(2,10):
                d1,d2,paths = get_paths(SO, j, i, False)
                if abs(d1-d2) < tol: best_k.append(j); break
        result.append(best_k)
        print result


def find_UESOpaths(SO, return_paths=True, random=False, path=None):
    """
    1. take the union for all optimum shortest paths for UE/SO
    2. compute UE/SO using node-link and link-path formulation for all demands
    3. compare results
    
    Parameters:
    -----------
    SO: if False, compute the UE, if True, compute the SO
    return_paths: if True, do only step 1 and return paths, if False, do steps 2 and 3
    """
    paths, ls, ds, ps = [], [], [], []
    K = [2,3,3,4] #[2, 2, 2, 3] [5,5,5,5]
    if SO: K = [2, 2, 4, 7] #[2,4,7,9]
    for i in range(4):
        tmp = get_paths(SO, K[i], i, path=path)
        for p in tmp:
            if p not in paths: paths.append(p)
    if return_paths: return paths
    for i in range(4):
        g = los_angeles(theta, 'Polynomial')[i]
        for p in paths: g.add_path_from_nodes(p)
        P = path.linkpath_incidence(g)
        g.visualize(general=True)
        l1 = ue.solver(g, update=True, SO=SO)
        d1 = sum([link.delay*link.flow for link in g.links.values()])
        p_flows = path.solver(g, update=True, SO=SO, random=random)
        l2 = P*p_flows
        d2 = sum([p.delay*p.flow for p in g.paths.values()])
        ls.append([l1,l2])
        ds.append([d1,d2])
        ps.append(p_flows)
    for i in range(4):
        print np.linalg.norm(ls[i][0] - ls[i][1])
        print ds[i][0], ds[i][1]
    print len(paths)


def test_feasible_pathflows(SO, demand, random=False):
    """Test function feasible_pathflows"""
    paths = find_UESOpaths(SO)
    g = los_angeles(theta, 'Polynomial')[demand]
    l1 = ue.solver(g, update=True, SO=SO)
    d1 = sum([link.delay*link.flow for link in g.links.values()])
    for p in paths: g.add_path_from_nodes(p)
    g.visualize(general=True)
    P = path.linkpath_incidence(g)
    l2 = P*path.solver(g, update=True, SO=SO, random=random)
    d2 = sum([p.delay*p.flow for p in g.paths.values()])
    ind_obs, ls, ds = {}, [], []
    ind_obs[0] = g.indlinks.keys()
    ind_obs[1] = [(36,37,1), (13,14,1), (17,8,1), (24,17,1), (28,22,1), (14,13,1), (17,24,1), (24,40,1), (14,21,1), (16,23,1)]
    ind_obs[2] = [(17,24,1), (24,40,1), (14,21,1), (16,23,1)]
    for i in range(len(ind_obs)):
        obs = [g.indlinks[id] for id in ind_obs[i]]
        obs = [int(i) for i in list(np.sort(obs))]
        ls.append(P*path.feasible_pathflows(g, l1[obs], obs, True))
        ds.append(sum([p.delay*p.flow for p in g.paths.values()]))
    print d1,d2,ds
    print np.linalg.norm(l1-l2), [np.linalg.norm(l1-ls[i]) for i in range(len(ind_obs))]


def main():  
    # d1,d2,paths = get_paths(False, 11, 2, False)
    #find_optimum_K()
    find_UESOpaths(False, False, True)
    #test_feasible_pathflows(False, 3, False)


if __name__ == '__main__':
    main()
