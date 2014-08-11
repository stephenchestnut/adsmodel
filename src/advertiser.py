# Copyright 2013, all rights reserved.
# Stephen Chestnut and Rico Zenklusen
# Johns Hopkins University


# List of classes
#
# Advertiser - describe a single advertiser
#  
# Publisher - describe a single publisher, derived from Advertiser
#
# AdExchange - creation and management of Advertiser and Publisher instances

import networkx
import csv
import gurobipy
import copy

class Advertiser:
    # An instance defines a single advertiser
    
    advertiser_id = -1        
    name = 'name'
    #type of business
    business_type = 'Z'     
    #number of ads credits
    _ads_per_day = 0        
    _ad_balance = 0
    #list of prefered publishers
    _prefered_pub_ids = []
    #geographic market
    location = 'location'

    def __init__(self, advertiser_id, name, business_type, ads_per_day, loc, prefered_pub_ids):
        self.advertiser_id = advertiser_id
        self.name = name
        self.business_type = business_type
        self._ads_per_day = ads_per_day
        self._ad_balance = 0
        self.location = loc
        self._prefered_pub_ids = prefered_pub_ids

    def __repr__(self):
        return self.name

    def __str__(self):
        dlm = ', '
        ret = str(self.advertiser_id) + dlm
        ret += self.name + dlm
        ret += self.business_type + dlm
        ret += self.location + dlm
        ret += str(self._ad_balance) + ' ads' + dlm
        ret += str(self._ads_per_day) + ' ads/day' + dlm
        ret += 'prefers publishers ' + str(self._prefered_pub_ids)
        return ret

    def allows(self, ad):
        #advertisers do no publish - always return False
        return False

    def prefers(self, pub):
        #T/F this Advertiser prefers the Publisher pub
        return (pub.advertiser_id in self._prefered_pub_ids)

    def max_ads(self):
        #maximum number of ads to publish from this advertiser
        return self._ads_per_day + self._ad_balance

    def max_pubs(self):
        #advertisers do no publish
        return 0

    def update_balance_advertiser(self, number_ads):
        self._ad_balance += self._ads_per_day - number_ads

    def update_balance_publisher(self, number_pubs):
        pass

class Publisher(Advertiser):
    # An instance defines a single publisher

    #maximum number of ads to publish
    _pubs=0
    #list of excluded advertisers
    _excluded_ad_ids = []

    def __init__(self, advertiser_id, name, business_type, ads_per_day, pubs, loc, prefered_pub_ids, excl_ad_ids):
        Advertiser.__init__(self,advertiser_id,name,business_type,ads_per_day,loc,prefered_pub_ids)
        self._pubs = pubs
        self._excluded_ads = excl_ad_ids

    def __str__(self):
        dlm = ', '
        ret = Advertiser.__str__(self) + dlm
        ret += str(self._pubs) + ' receipts/day' + dlm
        ret += 'excludes advertisers '+ str(self._excluded_ads)
        return ret    

    def allows(self, ad):
        #T/F this Publisher allows ads from Advertiser ad
        return (ad.advertiser_id not in self._excluded_ad_ids) and (ad.business_type != self.business_type)

    def max_ads(self):
        return Advertiser.max_ads(self) + self._pubs/2
    
    def max_pubs(self):
        return self._pubs

    def update_balance_publisher(self, number_pubs):
        self._ad_balance += (number_pubs+1)/2 #round up

class AdHistory:
    # A class to store and access historical data from an AdExchange instance
    _history = []  #list of historical AdExchange.  The solutions are unreliable since I can't store them 

    def __init__(self):
        pass

    def __len__(self):
        return len(self._history)

    def save(self, adex):

        self._history += [adex.copy()]

    def report_total_ads(self):
        #return a history of all ads published, split according t
        hist = []
        for adex in self._history:
            hist += [adex.report_total_ads()]

        return hist
        
    def report_detailed_ads(self):
        #return a list containing prefered ad history, and number of ads split 
        # according to distance
        hist =[ [] ]
        for adex in self._history:
            day_data = adex.report_detailed_ads()
            if len(day_data) > len(hist):
                hist += [ [0] * len(hist[0]) ]
            for ii,x in enumerate(day_data):
                hist[ii] += [x]
        return hist

    def report_prefered_ad_distribution(self):
        #return a 6 element list for each advertiser giving (elements 0-4) how many ads
        # went to each of its prefered publishers and (element 5) the number of 
        # non-prefered ads
        pass
        
    
class AdExchange:
    # A class for the entire exchange
    _graph = []
    _map = []
    _model = []

    def __init__(self, name='AdExchange',quiet=False):
        #default constructor
        self._graph = networkx.DiGraph()
        self._map = networkx.DiGraph()
        self._model = gurobipy.Model(name)
        self._model.ModelSense = gurobipy.GRB.MAXIMIZE
        if quiet:
            self._model.setParam('OutputFlag',0)
        
        self._build_map()

    def copy(self):
        # create a copy, gurobipy.LinExpr() attributes on each edge are not copied
        #  If self has been optimized the copy may have a different optimal solution (of same obj value)
        cpy = AdExchange()
        cpy._model = self._model.copy()
        cpy._model.optimize()
        cpy._map = copy.copy(self._map)
        cpy._graph = networkx.DiGraph()

        copymorphism = {} #A map from vertices of self._graph to vertices of cpy._graph
        for v in self._graph.nodes():
            cpy_v = copy.copy(v)
            copymorphism[v] = cpy_v
            cpy._graph.add_node(cpy_v, lin_constr=[gurobipy.LinExpr(), gurobipy.LinExpr()])
                                
        for e in self._graph.edges():
            cpy_u = copymorphism[e[0]]
            cpy_v = copymorphism[e[1]]
            cpy._graph.add_edge( cpy_u, cpy_v, var=cpy._model.getVarByName( e[0].name + str(e[0].advertiser_id) + '->' + e[1].name + str(e[1].advertiser_id)))

            #if self._model.getAttr('Status') == 2: #if the self model has been optimized
            #cpy._model.optimize()

        return cpy

    @classmethod
    def from_sample_data(cls, quiet=False):
        #constructor from sample data
        inst = cls('Sample',quiet)
        inst._load_sample_data()
        inst._build_graph_model()
        inst.update()
        return inst

    #@classmethod
    #def simple_

    def _build_map(self):
        #define the geographical relationships of the businesses
        self._map.add_nodes_from(['Canton','Fells Point','Harbor East','Fed Hill','Dundalk','N/A'])
        self._map.add_edge('Dundalk','Canton',distance=1)
        self._map.add_edge('Fells Point','Canton',distance=1)
        self._map.add_edge('Fells Point','Harbor East',distance=1)
        self._map.add_edge('Fed Hill','Harbor East',distance=1)
        self._map.add_edge('Canton','Dundalk',distance=1)
        self._map.add_edge('Canton','Fells Point',distance=1)
        self._map.add_edge('Harbor East','Fells Point',distance=1)
        self._map.add_edge('Harbor East','Fed Hill',distance=1)        
        
        for v in ['Canton','Fells Point','Harbor East','Fed Hill','Dundalk']:
            self._map.add_edge('N/A',v,distance=0)    

    def _load_sample_data(self):
        #open the csv file
        with open('../dat/AdData.csv') as f:
            r = csv.reader(f)
            pref_pubs=[] #contains 1 list/advertiser of preferred publishers
            excl_ads=[] #a tuple giving the excluded advertisers for each publisher
            for row in r:
                a_id = int(row[0])
                a_name = row[1]
                a_type = row[2]
                pref_pubs = map( int , row[7].split(',') )
                a_loc=row[8]
                if not self._map.has_node(a_loc):
                    raise ValueError('Location ' + a_loc + ' is unknown')

                a_ads = 0 
                if row[5].isdigit(): 
                    a_ads += int(row[5])    #Ads purchased from the bank

                if row[3].isdigit():        #If this row describes a publisher
                    a_pubs = int(row[3])*2  #Ads published in 1 day

                    excl_ads = []
                    if row[9]!='':
                        excl_ads = map( int , row[9].split(',') )

                    self._graph.add_node(Publisher(a_id, a_name, a_type, a_ads, a_pubs, a_loc, pref_pubs, excl_ads),lin_constr=[gurobipy.LinExpr(), gurobipy.LinExpr()])
                else:
                    self._graph.add_node(Advertiser(a_id, a_name, a_type, a_ads, a_loc, pref_pubs),lin_constr=[gurobipy.LinExpr(), gurobipy.LinExpr()])
        # End file read
        
    def _build_graph_model(self):
        #finish the networkx.Graph describing the instance, set-up the gurobi model
        self._create_edges()
        self._create_constraint_matrix()
       
    def update(self):
        #solve the optimization problem for one day and update advertiser balances
        self._set_constraints()
        self._model.optimize()

        for v in self._graph.nodes():
            ads_placed = 0;
            ads_published = 0;
            
            for e in self._graph.out_edges(v,data=True):
                ads_placed += int(e[2]['var'].getAttr('X')) #will round down
            for e in self._graph.in_edges(v,data=True):
                ads_published += int(e[2]['var'].getAttr('X'))
                
            v.update_balance_advertiser(ads_placed)
            v.update_balance_publisher(ads_published)
        
    def _create_edges(self):
        #create edges in the advertising network, add a variable for each edge to the model,
        # and setup the objective function
        #to hold the objective function
        obj = gurobipy.LinExpr()
        
        #create the edges in the advertising graph and a model variable for each edge
        for ad in self._graph.nodes():
            for pub in self._graph.nodes():
                if pub.allows(ad):
                    if ad.prefers(pub):
                        c = 2.0
                    else:
                        dist = networkx.shortest_path_length(self._map, ad.location, pub.location, 'distance')
                        c = 1.0/(1+dist)
                    e_var = self._model.addVar(lb=0,ub=(pub.max_pubs()/2),obj=c,name=(ad.name + str(ad.advertiser_id) + '->' + pub.name + str(pub.advertiser_id)))
                    obj += c*e_var
                    self._graph.add_edge( ad, pub, var=e_var)
        #tell the model to incorporate the edges
        self._model.update()

    def _create_constraint_matrix(self):
        #lhs of the inequalities

        #clear old matrix
        for v in self._graph.nodes():
            self._graph.node[v]['lin_constr'][0].clear()
            self._graph.node[v]['lin_constr'][1].clear()

        #build new constraint matrix
        for e in self._graph.edges(data=True):
            self._graph.node[e[0]]['lin_constr'][0] += e[2]['var'] #advertiser constraint
            self._graph.node[e[1]]['lin_constr'][1] += e[2]['var'] #publisher constraint
            
    def _set_constraints(self):

        #set up the linear expressions for the constraint matrix
        self._create_constraint_matrix()
        
        #remove any old constraints
        for constr in self._model.getConstrs():
            self._model.remove( constr )
        self._model.update()

        #add advertising and publishing constraints as appropriate
        for v in self._graph.nodes():
            self._model.addConstr(self._graph.node[v]['lin_constr'][0],gurobipy.GRB.LESS_EQUAL,v.max_ads(), v.name + '-' + str(v.advertiser_id) + ' ads') #advertising constraint
            if self._graph.node[v]['lin_constr'][1].size() > 0: #don't bother to add empty constraints
                self._model.addConstr(self._graph.node[v]['lin_constr'][1],gurobipy.GRB.LESS_EQUAL,v.max_pubs(), v.name + '-' + str(v.advertiser_id) + ' pubs') #publishing constraint
        self._model.update()

    def model_description(self):
        # return a string that describes the constraints
        return 'Prefered edges are given weight 2, other edges are weighted by the inverse of the distance between '\
                +'the advertiser and publisher.  Each advertiser may run a negative balance no larger than the maximum '\
                +'of advertisements it will earn by publishing on that day.  Each publisher will accept no more than '\
                +'half of its total ads from any one advertiser.'

    def report_solution_table(self):
        # return a table with the current solution
        ret = []        
        nodes = self._graph.nodes()
        
        # column headers
        row = [' ']
        for v in nodes:
            row += [v.name]
        row += ['ads placed', 'constraint']
        ret += [row]

        # advertiser on row, publisher no column
        # number of ads placed at each publisher, total number placed, constraint
        colsum = [0]*len(nodes)
        row_constr_sum = 0
        for u in nodes:
            row = [u.name]
            rowsum = 0
            for ii,v in enumerate(nodes):
                if self._graph.has_edge(u,v):
                    row += [int( self._graph[u][v]['var'].getAttr('X') )]
                    rowsum += row[-1]
                    colsum[ii] += row[-1]
                else:
                    row += [' - ']
            constr = self._model.getConstrByName(u.name + '-' + str(u.advertiser_id) + ' ads')
            row += [rowsum, int( constr.getAttr('RHS') )]
            row_constr_sum += row[-1]
            ret += [row]

        # total number of ads published by each publisher, total ads published, sum of row constraints
        row = ['ads published']
        for ii,v in enumerate(nodes):
            row += [colsum[ii]]
        row += [sum(colsum), row_constr_sum]
        ret += [row]

        # constraints on publishers, sum of column constraints
        row = ['constraint']
        col_constr_sum = 0
        for v in nodes:
            constr = self._model.getConstrByName(v.name + '-' + str(v.advertiser_id) + ' pubs')
            if constr is None:
                row += [ 0 ]
            else:
                row += [ int( constr.getAttr('RHS') ) ]
                col_constr_sum += row[-1]
        row += [col_constr_sum, ' ']
        ret += [row]
                
        return ret
                
    def report_ad_balances(self):
        # return a list of current ad balances
        pass

    def report_total_ads(self):
        # return the total number of ads
        ret = 0
        for e in self._graph.edges(data=True):
            ret += int(e[2]['var'].getAttr('X'))
        return ret

    def report_detailed_ads(self):
        # report a list with 0th element as number of prefered adds, each index i>0
        # gives the number of ads at distance i-1.  The max distance having a positive
        # number of ads is the last reported (and determines the length of the output)
        max_dist = self._map.number_of_nodes()
        ret = [0]
        for e in self._graph.edges(data=True):
            e_ads = int(e[2]['var'].getAttr('X'))
            if e_ads>0:
                if e[0].prefers(e[1]):
                    ret[0] += e_ads
                else:
                    k = int(networkx.shortest_path_length(self._map, e[0].location, e[1].location, 'distance'))
                    if (len(ret)-1) <= k:  #extend the length of the returned vector
                        ret += [0]*(k + 2 - len(ret))
                    ret[k+1] = e_ads
        return ret

    def report_prefered_ad_details(self):
        #break prefered ads down according to publisher
        #return a dictionary where keys are advertisers and
        #values are number of prefered ads

        ret = {}
        for ad in self._graph.nodes():
            vec = [0]*len(ad._prefered_pub_ids)
            for pub in self._graph.nodes():
                if ad.prefers(pub):
                    vec[ ad._prefered_pub_ids.index(pub.advertiser_id) ] = int(self._graph[ad][pub]['var'].getAttr('X'))
            ret[ad] = vec

        return ret
                    
        
