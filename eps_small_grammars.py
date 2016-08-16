# -*- coding: utf-8 -*-
"""
Created on Thu May 12 18:05:13 2016

@author: arlittr
"""

'''
This file is a testbed for validating grammars

'''

import sys
sys.path.append('ibfm_utility')

import ibfm
import ibfm_utility
import os

def test_rule(rulename,rulepath,g):
    ibfm_utility.plotPgvGraph(g,'plots/beforeRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')
    r = ibfm_utility.grammars.Rule(rulename,os.path.join(rulepath,'lhs.csv'),os.path.join(rulepath,'rhs.csv'))
    r.recognize(g)
    g = r.apply(g)
#    g = r.apply(g,1)
    print(r.recognize_mappings)
    ibfm_utility.plotPgvGraph(g,filename='plots/afterRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')


if __name__ == '__main__':
    #get seed functional model
    filename = 'FunctionalModels/eps.csv'
    g = ibfm_utility.ImportFunctionalModel(filename,type='dsm')
    
    #test given rule (debug only)
#    rulename = 'AddSeriesAnyElectricalEnergy'
#    rulepath = 'ibfm_utility/rules/testRules/AddSeriesAnyElectricalEnergy/'
#    test_rule(rulename,rulepath,g)
    
    #create population from ruleset
    ruleset_path = 'ibfm_utility/rules/ruleset/'        
    rs = ibfm_utility.grammars.Ruleset(ruleset_path)
    breadth = 3
    depth = 3
    popu = rs.build_population_random_stack(g,breadth,depth) 
  
    #graph each member of population
    path = 'plots/graph_population/'
    extension = '.svg'
    for f in os.listdir(path): 
        if f.endswith(extension):
            os.remove(os.path.join(path,f)) 
    for label,rulename,location,graph in rs.get_population(popu):
        print(label,rulename,location,graph)
        path = 'plots/graph_population/'
        extension = '.svg'
        filename = '-'.join([str(label),rulename,str(location)])
        ibfm_utility.plotPgvGraph(graph,filename=os.path.join(path,filename)+extension,
                            promoteNodeLabels='function',
                            printRelationships='flowType')
    
    for label,rulename,location,graph in rs.get_population(popu): 
        if ibfm_utility.grammars.check_model(graph) == True:
            popu[label]['isSimulatable'] = True
        else:
            popu[label]['isSimulatable'] = False
    
    #Run every valid model in the population
    results = {}
    max_simultaneous_faults = 2
    for label,rulename,location,graph in rs.get_population(popu): 
        print(label,rulename)
        if popu[label]['isSimulatable'] == True:
            eps = ibfm.Experiment(graph)
            scenarios = []
            results = []
            for numfaults in range(1,max_simultaneous_faults+1):
                eps.run(numfaults)
                scenarios.extend(eps.getScenarios())
                results.extend(eps.getResults())
            
            #Calculate failure likelihoods
            #initialize new count of flow failures for this topology
            flowFailureCounts = {k:0 for k in [edge[2]['flowType'] for edge in graph.edges(data=True)]}
            #for each result, tally (and aggregate) the number of failures for each type of flow            
            for r in results:
                failedFlows = {k:v for k,v in r.items() if len(v)==2 and any(w is not 'Nominal' for w in v)}
#                failedFunctions = {k:v for k,v in r.items() if len(v)==3 and v[0]!='1'}
                #pull flow types back out from result data
                nodes = [k.split('_') for k in failedFlows.keys()]
                nodes = [('_'.join(n[:3]),'_'.join(n[3:])) for n in nodes]
                for n in nodes:
                    flowFailureCounts[graph.get_edge_data(n[0],n[1])[0]['flowType']] += 1
            
            #Get total incidence of each flow type
            flowTotalCounts = {k:0 for k in [edge[2]['flowType'] for edge in graph.edges(data=True)]}
            for edge in graph.edges(data=True):
                flowTotalCounts[edge[2]['flowType']] += 1
            for k in flowTotalCounts:
                flowTotalCounts[k] = flowTotalCounts[k] * (len(results)+1)
            
            flowFailureRatios = {k:flowFailureCounts[k]/float(flowTotalCounts[k]) for k in flowTotalCounts.keys()}
            centerOfLikelihood = sum([v for v in flowFailureCounts.values()])/float(sum([v for v in flowTotalCounts.values()]))
            flowFailureData = {'flowTotalCounts':flowTotalCounts,
                               'flowFailureCounts':flowFailureCounts,
                               'flowFailureRatios':flowFailureRatios,    
                               'centerOfLikelihood':centerOfLikelihood}
            popu[label]['flowFailureData'] = flowFailureData
            #For every scenario
                #aggregate all failure states (results)
                #calculate failure rate per function
                #create new dictionary of all flows
                #find all in/out flows for each function
                #calculate summative score for each flow (normalize?)
                #calculate center of likelihood
#            print('Scenarios')
#            print(scenarios[-1])
#
#            print('Results')
#            print(results[-1])
            
            print(label,centerOfLikelihood)

            
