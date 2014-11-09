'''
Created on Apr 18, 2014

@author: jeromethai
'''

from cvxopt import matrix
import numpy as np

class Graph:
    """A graph containing nodes and links"""
    def __init__(self, description=None, nodes={}, links={}, ODs={}, paths={}, 
                 numnodes=0, numlinks=0, numODs=0, numpaths=0, nodes_position={}, indlinks={}, indods={}, indpaths={}):
        self.description = description
        self.nodes = nodes
        self.links = links
        self.ODs = ODs
        self.paths = paths
        self.numnodes = numnodes
        self.numlinks = numlinks
        self.numODs = numODs
        self.numpaths = numpaths
        self.nodes_position = nodes_position
        self.indlinks = indlinks # indexation for matrix generations
        self.indods = indods # indexation for matrix generations
        self.indpaths = indpaths # indexation for matrix generations
        
    
    def add_node(self, position=None):
        """Add a node with coordinates as a tuple"""
        self.numnodes += 1
        self.nodes_position[self.numnodes] = position
        self.nodes[self.numnodes] = Node(position, inlinks={}, outlinks={}, startODs={}, endODs={})
        
        
    def add_nodes_from_list(self, list):
        """Add nodes from list of positions"""
        for position in list: self.add_node(position)
        
          
    def add_link(self, startnode, endnode, route=1, flow=0.0, delay=0.0, ffdelay=0.0, delayfunc=None):
        """Add a link"""
        formatStr = 'ERROR: node {} doesn\'t exist, graph countains {} nodes.'
        startnode, endnode, route = int(startnode), int(endnode), int(route)
        if startnode == endnode: print 'ERROR: self-loop not allowed.'; return
        if startnode < 1 or startnode > self.numnodes: print formatStr.format(startnode, self.numnodes); return
        if endnode < 1 or endnode > self.numnodes: print formatStr.format(endnode, self.numnodes); return
        
        if (startnode, endnode, route) in self.links:
            print 'ERROR: link ({},{},{}) already exists.'.format(startnode, endnode, route); return
        else:
            link = Link(startnode, endnode, route, float(flow), float(delay), float(ffdelay), delayfunc, {})
            self.indlinks[(startnode, endnode, route)] = self.numlinks
            self.numlinks += 1
            self.links[(startnode, endnode, route)] = link
            self.nodes[startnode].outlinks[(startnode, endnode, route)] = link
            self.nodes[endnode].inlinks[(startnode, endnode, route)] = link
            if delayfunc is not None:
                link.ffdelay = delayfunc.ffdelay
                link.delay = delayfunc.compute_delay(link.flow)
                    
   
    def add_links_from_list(self, list, delaytype):
        """Add links from list
        the list is must contain starnode, endnode, ffdelay, and parameters of delay functions
        """
        for startnode, endnode, route, ffdelay, parameters in list:
            self.add_link(startnode, endnode, route, 0.0, ffdelay, ffdelay, delayfunc=create_delayfunc(delaytype, parameters))
   
   
    def add_od(self, origin, destination, flow=0.0):
        """Add an OD pair"""
        formatStr = 'ERROR: node {} doesn\'t exist, graph countains {} nodes.'
        origin, destination = int(origin), int(destination)
        if origin == destination: print 'ERROR: self-loop not allowed.'; return
        if origin < 1 or origin > self.numnodes: print formatStr.format(origin, self.numnodes); return
        if destination < 1 or destination > self.numnodes: print formatStr.format(destination, self.numnodes); return
        
        if (origin, destination) in self.ODs:
            print 'ERROR: OD ({},{}) already exists'.format(origin, destination); return
        else:
            self.indods[(origin, destination)] = self.numODs
            self.numODs += 1
            od = OD(origin, destination, float(flow), {})
            self.ODs[(origin, destination)] = od
            self.nodes[origin].startODs[(origin, destination)] = od
            self.nodes[destination].endODs[(origin, destination)] = od
   
   
    def add_ods_from_list(self, list):
        """Add OD's from list
        the list is must contain origin, destimation, ffdelay, flow
        """
        for origin, destination, flow in list: self.add_od(origin, destination, flow)
   
   
    def add_path(self, link_ids):
        """Add a path"""
        origin = link_ids[0][0]
        destination = link_ids[len(link_ids)-1][1]
        if not (origin, destination) in self.ODs: print 'ERROR: OD ({},{}) doesn\'t exist.'.format(origin, destination); return
        
        for i in range(len(link_ids)-1):
            if link_ids[i][1] != link_ids[i+1][0]: print 'ERROR: path not valid.'; return
        
        for path in self.ODs[(origin, destination)].paths.values():
            if [(link.startnode,link.endnode,link.route) for link in path.links] == link_ids: print 'ERROR: path already exists.'; return
        
        links = []; delay = 0.0; ffdelay = 0.0
        for id in link_ids:
            link = self.links[(id[0], id[1], id[2])]; links.append(link); delay += link.delay; ffdelay += link.ffdelay
            
        self.ODs[(origin, destination)].numpaths += 1
        route = self.ODs[(origin, destination)].numpaths
        path = Path(origin, destination, route, links, 0.0, delay, ffdelay)
        self.indpaths[(origin, destination, route)] = self.numpaths
        self.numpaths += 1
        self.paths[(origin, destination, route)] = path
        self.ODs[(origin, destination)].paths[(origin, destination, route)] = path
        for link in links:
            self.links[(link.startnode, link.endnode, link.route)].numpaths += 1
            self.links[(link.startnode, link.endnode, link.route)].paths[(origin, destination, route)] = path   
        
        
    def visualize(self, general=False, nodes=False, links=False, ODs=False, paths=False, only_pos_flows=False, tol=1e-3):
        """Visualize graph"""
        if general:
            print 'Description: ', self.description
            print 'Nodes: ', self.nodes
            print 'Number of nodes: ', self.numnodes
            print 'Links: ', self.links
            print 'Number of links: ', self.numlinks
            print 'OD pairs: ', self.ODs
            print 'Number of OD pairs: ', self.numODs
            print 'Paths: ', self.paths
            print 'Number of paths: ', self.numpaths
            print 'Nodes\' position: ', self.nodes_position
            print 'Link indexation', self.indlinks
            print 'OD indexation', self.indods
            print 'Path indexation', self.indpaths
            print
  
        if nodes:
            for id, node in self.nodes.items():
                print 'Node id: ', id
                print 'Position', node.position
                print 'In-links: ', node.inlinks
                print 'Out-links: ', node.outlinks
                print 'Start ODs: ', node.startODs
                print 'End ODs: ', node.endODs
                print
     
        if links:    
            for id, link in self.links.items():
                if link.flow > tol or not only_pos_flows:
                    print 'Link id: ', id
                    print 'Flow: ', link.flow
                    print 'Number of paths: ', link.numpaths
                    print 'Paths: ', link.paths
                    print 'Delay: ', link.delay
                    print 'Free flow delay: ', link.ffdelay
                    if link.delayfunc is not None: print 'Type of delay function: ', link.delayfunc.type
                    print
        
        if ODs:
            for id, od in self.ODs.items():
                print 'OD pair id: ', id
                print 'Flow: ', od.flow
                print 'Number of paths: ', od.numpaths
                print 'Paths: ', od.paths
                print
     
        if paths:   
            for id, path in self.paths.items():
                print 'Path id: ', id
                print 'Links: ', [(link.startnode, link.endnode, link.route) for link in path.links]
                print 'Flow: ', path.flow
                print 'Delay: ', path.delay
                print 'Free flow delay: ', path.ffdelay
                print 
        
        
    def get_linkflows(self):
        """Get link flows in a column cvxopt matrix"""
        linkflows = matrix(0.0, (self.numlinks, 1))
        for id,link in self.links.items(): linkflows[self.indlinks[id]] = link.flow
        return linkflows
    
    
    def get_ffdelays(self):
        """Get ffdelays in a column cvxopt matrix"""
        ffdelays = matrix(0.0, (self.numlinks, 1))
        for id,link in self.links.items(): ffdelays[self.indlinks[id]] = link.delayfunc.ffdelay
        return ffdelays
    
    
    def get_slopes(self):
        """Get slopes in a column cvxopt matrix"""
        slopes = matrix(0.0, (self.numlinks, 1))
        for id,link in self.links.items(): slopes[self.indlinks[id]] = link.delayfunc.slope
        return slopes
    
    
    def get_coefs(self):
        """Get coefficients of the polynomial delay functions in cvx"""
        type = self.links.values()[0].delayfunc.type
        if type != 'Polynomial': print 'Delay functions must be polynomial'; return
        n, degree = self.numlinks, self.links.values()[0].delayfunc.degree
        coefs = matrix(0.0, (n, degree))
        for id,link in self.links.items():
            i = self.indlinks[id]
            for j in range(degree): coefs[i,j] = link.delayfunc.coef[j]
        return coefs
    
    
    def update_linkflows_linkdelays(self, linkflows):
        """Update link flows and link delays in Graph object"""
        for id,link in self.links.items(): flow = linkflows[self.indlinks[id]]; link.flow, link.delay = flow, link.delayfunc.compute_delay(flow)
        
        
    def update_pathdelays(self):
        """Update path delays in Graph object"""
        for path in self.paths.values():
            delay = 0.0
            for link in path.links: delay += link.delay
            path.delay = delay
        
        
    def update_pathflows(self, pathflows):
        """Update path flows in Graph object"""
        for id,path in self.paths.items(): path.flow = pathflows[self.indpaths[id]]
        
    
class Link:
    """A link in the graph"""
    def __init__(self, startnode, endnode, route, flow=0.0, delay=0.0, ffdelay=0.0, delayfunc=None, paths={}, numpaths=0):
        self.startnode = startnode
        self.endnode = endnode
        self.route = route  #if multiple edges
        self.flow = flow  #flow on the link
        self.delay = delay  #delay on the link
        self.ffdelay = ffdelay #free flow delay
        self.delayfunc = delayfunc
        self.paths = paths  #set of paths passing through
        self.numpaths = numpaths
        

class Node:
    """A node in the graph"""
    def __init__(self, position, inlinks, outlinks, startODs, endODs):
        self.position = position
        self.inlinks = inlinks
        self.outlinks = outlinks
        self.startODs = startODs   #set of OD pairs with origin at node
        self.endODs = endODs   #set of OD pairs with destination at node 
        
        
class Path:
    """A path in the graph"""
    def __init__(self, origin, destination, route, links, flow=0.0, delay=0.0, ffdelay=0.0):
        self.o = origin #origin node
        self.d = destination #destination node
        self.route = route #index of path associated to this od pair
        self.links = links #set of all links on the path
        self.flow = flow
        self.delay = delay
        self.ffdelay = ffdelay
        
class OD:
    """OD pairs"""
    def __init__(self, origin, destination, flow=0.0, paths={}, numpaths=0):
        self.o = origin
        self.d = destination
        self.flow = flow
        self.paths = paths # set of all paths for the OD pair
        self.numpaths = numpaths
       
       
class PolyDelay:
    """Polynomial Delay function
    delay(x) = ffdelay + sum_k coef[k]*(slope*x)^k"""
    def __init__(self, ffdelay, slope, coef):
        self.ffdelay = ffdelay
        self.slope = slope # this can be seen as inverse capacities
        self.coef = coef
        self.degree = len(coef)
        self.type = 'Polynomial'
        
    def compute_delay(self, flow):
        """Compute delay"""
        return self.ffdelay + np.dot(self.coef, np.power(flow, range(1,self.degree+1)))
        

def create_delayfunc(type, parameters=None):
    """Create a Delay function of a specific type"""
    if type == 'None': return None
    if type == 'Polynomial': return PolyDelay(parameters[0], parameters[1], parameters[2])
    if type == 'Other': return Other(parameters[0], parameters[1], parameters[2])


def create_graph_from_list(list_nodes, list_links, delaytype, list_ods=None, description=None):
    """Create a graph from a list of of nodes and links
    """
    graph = Graph(description, {},{},{},{},0,0,0,0,{},{},{},{})
    graph.add_nodes_from_list(list_nodes)
    graph.add_links_from_list(list_links, delaytype)
    if list_ods is not None: graph.add_ods_from_list(list_ods)
    return graph