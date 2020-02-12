#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 08:53:30 2019

@author: rhou
"""

import warnings
warnings.filterwarnings("ignore")
import os, sys
import argparse
import matplotlib
matplotlib.use('agg')
import pandas as pd
import numpy as np
try:
    import seaborn as sns 
except ImportError:
    sys.exit('\n\nError: seaborn module is missing, please install it before proceeding.')
try:
    import igraph as ig
except ImportError:
    sys.exit('\n\nError: igraph module is missing, please install it before proceeding.')
try:
    import networkx as nx
except ImportError:
    sys.exit('\n\nError: NetworkX module is missing, please install it before proceeding.')
try:
    import pygraphviz as pgv
except ImportError:
    sys.exit('\n\nError: PyGraphviz module is missing, please install it before proceeding.')
    
#filter adjacency matrix
def ChooseTopEdges(adjM, keepTopEdge):
    if keepTopEdge == 0:
        return adjM
    edgeDict = {'s':[],'t':[],'v':[]}
    for idx in adjM.index:
        for col in adjM.columns:
            edgeDict['s'].append(idx)
            edgeDict['t'].append(col)
            if adjM.ix[idx,col] <=0:
                edgeDict['v'].append((-1.0) * adjM.ix[idx,col])
            else:
                edgeDict['v'].append(adjM.ix[idx,col])
                
    edgeD = pd.DataFrame(edgeDict).sort_values(by=['v'], ascending=False)
    edgeD = edgeD.head(keepTopEdge)
            
    nadjM = pd.DataFrame(0.0, index=adjM.index,columns=adjM.index)
    for idx in edgeD.index:
        nadjM.ix[edgeD.ix[idx,['s']],edgeD.ix[idx,['t']]] = adjM.ix[edgeD.ix[idx,['s']],edgeD.ix[idx,['t']]]
    return nadjM

# build delta adjacency matrix
def BuildDeltaAdjM(edgeDF, origlabels, labels, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge):
    edgeDF['Sending cluster'] = edgeDF['Sending cluster'].astype(str)
    edgeDF['Target cluster'] = edgeDF['Target cluster'].astype(str)
    adjM1 = pd.DataFrame(0.0, index=origlabels, columns=origlabels)
    adjSpecM1 = pd.DataFrame(0.0, index=origlabels, columns=origlabels)
    adjCountM1 = pd.DataFrame(0, index=origlabels, columns=origlabels)
    adjM2 = pd.DataFrame(0.0, index=origlabels, columns=origlabels)
    adjSpecM2 = pd.DataFrame(0.0, index=origlabels, columns=origlabels)
    adjCountM2 = pd.DataFrame(0, index=origlabels, columns=origlabels)
    for idx in edgeDF.index:
        if (edgeDF.ix[idx, 'Ligand detection rate in condition 1']>frequencyThreshold)&(edgeDF.ix[idx, 'Receptor detection rate in condition 1']>frequencyThreshold):
            adjM1.ix[str(edgeDF.ix[idx,'Sending cluster']), str(edgeDF.ix[idx,'Target cluster'])] += edgeDF.ix[idx,'Edge expression weight in condition 1']
            adjSpecM1.ix[str(edgeDF.ix[idx,'Sending cluster']), str(edgeDF.ix[idx,'Target cluster'])] += edgeDF.ix[idx,'Edge specificity weight in condition 1']
            adjCountM1.ix[str(edgeDF.ix[idx,'Sending cluster']), str(edgeDF.ix[idx,'Target cluster'])] += 1
        if (edgeDF.ix[idx, 'Ligand detection rate in condition 2']>frequencyThreshold)&(edgeDF.ix[idx, 'Receptor detection rate in condition 2']>frequencyThreshold):
            adjM2.ix[str(edgeDF.ix[idx,'Sending cluster']), str(edgeDF.ix[idx,'Target cluster'])] += edgeDF.ix[idx,'Edge expression weight in condition 2']
            adjSpecM2.ix[str(edgeDF.ix[idx,'Sending cluster']), str(edgeDF.ix[idx,'Target cluster'])] += edgeDF.ix[idx,'Edge specificity weight in condition 2']
            adjCountM2.ix[str(edgeDF.ix[idx,'Sending cluster']), str(edgeDF.ix[idx,'Target cluster'])] += 1

    # remove isolated nodes
    adjM1.index = labels
    adjM1.columns = labels
    adjSpecM1.index = labels
    adjSpecM1.columns = labels
    adjCountM1.index = labels
    adjCountM1.columns = labels
    ilist1 = adjM1.index[adjM1.max(axis=1)>0]
    clist1 = adjM1.columns[adjM1.max(axis=0)>0]
    nlist1 = sorted(list(set(ilist1).union(set(clist1))))
    
    adjM2.index = labels
    adjM2.columns = labels
    adjSpecM2.index = labels
    adjSpecM2.columns = labels
    adjCountM2.index = labels
    adjCountM2.columns = labels
    ilist2 = adjM2.index[adjM2.max(axis=1)>0]
    clist2 = adjM2.columns[adjM2.max(axis=0)>0]
    nlist2 = sorted(list(set(ilist2).union(set(clist2))))
    nlist = sorted(list(set(nlist1).union(set(nlist2))))
    
    adjM1 = adjM1.ix[nlist,nlist]
    adjSpecM1 = adjSpecM1.ix[nlist,nlist]
    adjCountM1 = adjCountM1.ix[nlist,nlist]
    adjM2 = adjM2.ix[nlist,nlist]
    adjSpecM2 = adjSpecM2.ix[nlist,nlist]
    adjCountM2 = adjCountM2.ix[nlist,nlist]
    #to average expression
    for idx in nlist:
        for col in nlist:
            if adjCountM1.ix[idx,col] != 0:
                adjM1.ix[idx,col] = adjM1.ix[idx,col]/adjCountM1.ix[idx,col]
            if adjCountM2.ix[idx,col] != 0:
                adjM2.ix[idx,col] = adjM2.ix[idx,col]/adjCountM2.ix[idx,col]
    
    adjMD = adjM1 - adjM2
    adjSpecMD = adjSpecM1 - adjSpecM2
    adjCountMD = adjCountM1 - adjCountM2
    
    adjM1 = ChooseTopEdges(adjM1, keepTopEdge)
    adjSpecM1 = ChooseTopEdges(adjSpecM1, keepTopEdge)
    adjCountM1 = ChooseTopEdges(adjCountM1, keepTopEdge)
    adjM2 = ChooseTopEdges(adjM2, keepTopEdge)
    adjSpecM2 = ChooseTopEdges(adjSpecM2, keepTopEdge)
    adjCountM2 = ChooseTopEdges(adjCountM2, keepTopEdge)
    adjMD = ChooseTopEdges(adjMD, keepTopEdge)
    adjSpecMD = ChooseTopEdges(adjSpecMD, keepTopEdge)
    adjCountMD = ChooseTopEdges(adjCountMD, keepTopEdge)
    
    ilist1 = adjM1.index[adjM1.max(axis=1)>0]
    clist1 = adjM1.columns[adjM1.max(axis=0)>0]
    nlist1 = sorted(list(set(ilist1).union(set(clist1))))
    ilist2 = adjM2.index[adjM2.max(axis=1)>0]
    clist2 = adjM2.columns[adjM2.max(axis=0)>0]
    nlist2 = sorted(list(set(ilist2).union(set(clist2))))
    ilist3 = adjMD.index[adjMD.max(axis=1)>0]
    clist3 = adjMD.columns[adjMD.max(axis=0)>0]
    nlist3 = sorted(list(set(ilist3).union(set(clist3))))
    nlist = sorted(list(set(nlist1).union(set(nlist2)).union(set(nlist3))))
    adjM1 = adjM1.ix[nlist,nlist]
    adjM2 = adjM2.ix[nlist,nlist]
    adjMD = adjMD.ix[nlist,nlist]
    
    ilist1 = adjSpecM1.index[adjSpecM1.max(axis=1)>0]
    clist1 = adjSpecM1.columns[adjSpecM1.max(axis=0)>0]
    nlist1 = sorted(list(set(ilist1).union(set(clist1))))
    ilist2 = adjSpecM2.index[adjSpecM2.max(axis=1)>0]
    clist2 = adjSpecM2.columns[adjSpecM2.max(axis=0)>0]
    nlist2 = sorted(list(set(ilist2).union(set(clist2))))
    ilist3 = adjSpecMD.index[adjSpecMD.max(axis=1)>0]
    clist3 = adjSpecMD.columns[adjSpecMD.max(axis=0)>0]
    nlist3 = sorted(list(set(ilist3).union(set(clist3))))
    nlist = sorted(list(set(nlist1).union(set(nlist2)).union(set(nlist3))))
    adjSpecM1 = adjSpecM1.ix[nlist,nlist]
    adjSpecM2 = adjSpecM2.ix[nlist,nlist]
    adjSpecMD = adjSpecMD.ix[nlist,nlist]
    
    ilist1 = adjCountM1.index[adjCountM1.max(axis=1)>0]
    clist1 = adjCountM1.columns[adjCountM1.max(axis=0)>0]
    nlist1 = sorted(list(set(ilist1).union(set(clist1))))
    ilist2 = adjCountM2.index[adjCountM2.max(axis=1)>0]
    clist2 = adjCountM2.columns[adjCountM2.max(axis=0)>0]
    nlist2 = sorted(list(set(ilist2).union(set(clist2))))
    ilist3 = adjCountMD.index[adjCountMD.max(axis=1)>0]
    clist3 = adjCountMD.columns[adjCountMD.max(axis=0)>0]
    nlist3 = sorted(list(set(ilist3).union(set(clist3))))
    nlist = sorted(list(set(nlist1).union(set(nlist2)).union(set(nlist3))))
    adjCountM1 = adjCountM1.ix[nlist,nlist]
    adjCountM2 = adjCountM2.ix[nlist,nlist]
    adjCountMD = adjCountMD.ix[nlist,nlist]
    
    nxgW1 = nx.MultiDiGraph(adjM1)
    nxgS1 = nx.MultiDiGraph(adjSpecM1)
    nxgC1 = nx.MultiDiGraph(adjCountM1)
    nxgW2 = nx.MultiDiGraph(adjM2)
    nxgS2 = nx.MultiDiGraph(adjSpecM2)
    nxgC2 = nx.MultiDiGraph(adjCountM2)
    nxgWD = nx.MultiDiGraph(adjMD)
    nxgSD = nx.MultiDiGraph(adjSpecMD)
    nxgCD = nx.MultiDiGraph(adjCountMD)
    return edgeDF, adjM1, adjSpecM1, adjCountM1, nxgW1, nxgS1, nxgC1, adjM2, adjSpecM2, adjCountM2, nxgW2, nxgS2, nxgC2, adjMD, adjSpecMD, adjCountMD, nxgWD, nxgSD, nxgCD

# build adjacency matrix
def BuildAdjM(edgeDF, origlabels, labels, specificityThreshold, weightThreshold, keepTopEdge):
    # only keep edges of interest
    if 'delta specificity' in edgeDF.columns:
        edgeDF = edgeDF.ix[(edgeDF['delta specificity']>specificityThreshold)&(edgeDF['delta weight']>weightThreshold),]
    else:
        edgeDF = edgeDF.ix[(edgeDF['product of specified']>specificityThreshold)&(edgeDF['original ligand']>weightThreshold)&(edgeDF['original receptor']>weightThreshold),]
    edgeDF['sending cluster name'] = edgeDF['sending cluster name'].astype(str)
    edgeDF['target cluster name'] = edgeDF['target cluster name'].astype(str)
            
    adjM = pd.DataFrame(0.0, index=origlabels, columns=origlabels)
    adjSpecM = pd.DataFrame(0.0, index=origlabels, columns=origlabels)
    adjCountM = pd.DataFrame(0, index=origlabels, columns=origlabels)
    for idx in edgeDF.index:
        if 'delta specificity' in edgeDF.columns:
            adjM.ix[str(edgeDF.ix[idx,'sending cluster name']), str(edgeDF.ix[idx,'target cluster name'])] += edgeDF.ix[idx,'delta weight']
            adjSpecM.ix[str(edgeDF.ix[idx,'sending cluster name']), str(edgeDF.ix[idx,'target cluster name'])] += edgeDF.ix[idx,'delta specificity']
        else:
            adjM.ix[str(edgeDF.ix[idx,'sending cluster name']), str(edgeDF.ix[idx,'target cluster name'])] += edgeDF.ix[idx,'product of original']
            adjSpecM.ix[str(edgeDF.ix[idx,'sending cluster name']), str(edgeDF.ix[idx,'target cluster name'])] += edgeDF.ix[idx,'product of specified']
        adjCountM.ix[str(edgeDF.ix[idx,'sending cluster name']), str(edgeDF.ix[idx,'target cluster name'])] += 1

    adjM.index = labels
    adjM.columns = labels
    adjSpecM.index = labels
    adjSpecM.columns = labels
    adjCountM.index = labels
    adjCountM.columns = labels
    ilist = adjM.index[adjM.max(axis=1)>0]
    clist = adjM.columns[adjM.max(axis=0)>0]
    nlist = sorted(list(set(ilist).union(set(clist))))
    adjM = adjM.ix[nlist,nlist]
    adjSpecM = adjSpecM.ix[nlist,nlist]
    adjCountM = adjCountM.ix[nlist,nlist]
    
    adjM = ChooseTopEdges(adjM, keepTopEdge)
    ilist = adjM.index[adjM.max(axis=1)>0]
    clist = adjM.columns[adjM.max(axis=0)>0]
    nlist = sorted(list(set(ilist).union(set(clist))))
    adjM = adjM.ix[nlist,nlist]
    adjSpecM = ChooseTopEdges(adjSpecM, keepTopEdge)
    ilist = adjSpecM.index[adjSpecM.max(axis=1)>0]
    clist = adjSpecM.columns[adjSpecM.max(axis=0)>0]
    nlist = sorted(list(set(ilist).union(set(clist))))
    adjSpecM = adjSpecM.ix[nlist,nlist]
    adjCountM = ChooseTopEdges(adjCountM, keepTopEdge)
    ilist = adjCountM.index[adjCountM.max(axis=1)>0]
    clist = adjCountM.columns[adjCountM.max(axis=0)>0]
    nlist = sorted(list(set(ilist).union(set(clist))))
    adjCountM = adjCountM.ix[nlist,nlist]
    
    nxgW = nx.MultiDiGraph(adjM)
    nxgS = nx.MultiDiGraph(adjSpecM)
    nxgC = nx.MultiDiGraph(adjCountM)
    return edgeDF, adjM, adjSpecM, adjCountM, nxgW, nxgS, nxgC

def IgraphFromAdjacency(adjM, layout, labels, cltSizes, clusterDistance):
    # insert nodes and edges into the graph object
    g = ig.Graph(directed=True)
    g.add_vertices(adjM.shape[0])
    g.vs["name"] = labels
    g.vs["weight"] = cltSizes
    
    edgeList = []
    edgeWeightList = []
    for s in range(len(adjM)):
        for t in range(len(adjM)):
            if adjM.iloc[s,t] > 0:
                edgeList.append((s,t))
                edgeWeightList.append(adjM.iloc[s,t])
    g.add_edges(edgeList)
    g.es['weight'] = edgeWeightList
    
    # set node positions based on the layout
    if layout == 'circle' or layout == 'sphere':
        pos_list = g.layout(layout).coords
    else:
        # set the seed to make the graph reproducable
        np.random.seed(0)
        init_coords = np.random.random((len(adjM), 2)).tolist()
        try:
            pos_list = g.layout(layout, seed=init_coords, weights='weight',).coords
        except Exception:  
            # hack for excepting attribute error for empty graphs...
            try:
                pos_list = g.layout(layout, seed=init_coords).coords
            except Exception:
                pos_list = g.layout(layout).coords

    posDict = {n: [p[0]*clusterDistance, -p[1]*clusterDistance] for n, p in enumerate(pos_list)}
    posAryList = []
    for i in sorted(posDict.keys()):
        posAryList.append(posDict[i])
    posArray = np.array(posAryList)
    return posArray, posDict

def DrawDeltaGraphvizPlot(readmeStr, typeStr, numStr, nxgS1, adjSpecM1, nxgS2, adjSpecM2, nxgSD, adjSpecMD, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold, weightThreshold, frequencyThreshold, signalType, weightType, layout, plotFormat):
    # draw networks of both datasets
    
    # convert to a graphviz graph
    nxgS1 = nx.nx_agraph.to_agraph(nxgS1)
    nxgS1.graph_attr.update(fontname = "Arial")
    nxgS1.graph_attr.update(fontsize = fontSize)
    nxgS1.graph_attr.update(margin = 0)
    nxgS1.graph_attr.update(ratio="compress")
    nxgS1.graph_attr.update(label='Network in condition 1\nEdge weight: ' + typeStr)
    nxgS1.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    # set edge properties
    maxVal = adjSpecM1.max().max()
    for ed in nxgS1.edges():
        sn = ed[0]
        tn = ed[1]
        ed.attr['color'] = '#FF0000'
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            if numStr == 'float':
                ed.attr['label'] = '%.3f' % (adjSpecM1.ix[sn, tn])
            elif numStr == 'int':
                ed.attr['label'] = '%d' % (adjSpecM1.ix[sn, tn])
        else:
            if adjSpecM1.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjSpecM1.ix[sn, tn]*edgeWidth/maxVal)
    
    # set node color
    nxgS1.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    maxCltSize = max(cltSizeDict.values())
    for lb in labels: 
        try:
            nd=nxgS1.get_node(lb)
        except:
            continue
            
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
    
    plotFileName = 'network_cond1_%s-based_layout_%s.%s' % (typeStr, layout, plotFormat)
    readmeStr += 'network_cond1_%s-based_layout_xx.%s: cluster-to-cluster communication network in condition 1, the edge weight is %s.\n' % (typeStr, plotFormat, typeStr)
    
    plotFileName = os.path.join(resultDir, plotFileName)
    warnings.simplefilter("error")
    while True:
        try:
            nxgS1.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgS1.draw(plotFileName,prog='neato') 
                break
            for nd in nxgS1.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    
    nxgS2 = nx.nx_agraph.to_agraph(nxgS2)
    nxgS2.graph_attr.update(fontname = "Arial")
    nxgS2.graph_attr.update(fontsize = fontSize)
    nxgS2.graph_attr.update(margin = 0)
    nxgS2.graph_attr.update(ratio="compress")
    nxgS2.graph_attr.update(label='Network in condition 2\nEdge weight: ' + typeStr)
    nxgS2.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    # set edge properties
    maxVal = adjSpecM2.max().max()
    for ed in nxgS2.edges():
        sn = ed[0]
        tn = ed[1]
        ed.attr['color'] = '#00FF00'
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            if numStr == 'float':
                ed.attr['label'] = '%.3f' % (adjSpecM2.ix[sn, tn])
            elif numStr == 'int':
                ed.attr['label'] = '%d' % (adjSpecM2.ix[sn, tn])
        else:
            if adjSpecM2.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjSpecM2.ix[sn, tn]*edgeWidth/maxVal)
    
    # set node color
    nxgS2.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    maxCltSize = max(cltSizeDict.values())
    for lb in labels: 
        try:
            nd=nxgS2.get_node(lb)
        except:
            continue
            
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
    
    plotFileName = 'network_cond2_%s-based_layout_%s.%s' % (typeStr, layout, plotFormat)
    readmeStr += 'network_cond2_%s-based_layout_xx.%s: cluster-to-cluster communication network in condition 2, the edge weight is %s.\n' % (typeStr, plotFormat, typeStr)
    
    plotFileName = os.path.join(resultDir, plotFileName)
    warnings.simplefilter("error")
    while True:
        try:
            nxgS2.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgS2.draw(plotFileName,prog='neato') 
                break
            for nd in nxgS2.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    
    # draw delta networks
                
    # convert to a graphviz graph
    nxgSD = nx.nx_agraph.to_agraph(nxgSD)
    nxgSD.graph_attr.update(fontname = "Arial")
    nxgSD.graph_attr.update(fontsize = fontSize)
    nxgSD.graph_attr.update(margin = 0)
    nxgSD.graph_attr.update(ratio="compress")
    nxgSD.graph_attr.update(label='Delta Network\nEdge weight: delta ' + typeStr)
    nxgSD.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    # set edge properties
    maxValP = adjSpecMD.max().max()
    maxValN = adjSpecMD.min().min()
    if maxValN >= 0:
        maxValN = maxValP
    for ed in nxgSD.edges():
        sn = ed[0]
        tn = ed[1]
        if adjSpecMD.ix[sn, tn] > 0 and adjSpecM2.ix[sn, tn] > 0 and float(adjSpecM1.ix[sn, tn])/adjSpecM2.ix[sn, tn] > 2:
            ed.attr['color'] = '#FF0000'
        elif adjSpecMD.ix[sn, tn] < 0 and adjSpecM1.ix[sn, tn] > 0 and float(adjSpecM2.ix[sn, tn])/adjSpecM1.ix[sn, tn] > 2:
            ed.attr['color'] = '#00FF00'
        else:
            ed.attr['color'] = '#FFFF00'
        if adjSpecMD.ix[sn, tn] > 0 and ed.attr['color'] != '#FFFF00':#to red
            sclc = float(adjSpecMD.ix[sn, tn])/maxValP*1.0
            ed.attr['color'] = matplotlib.colors.to_hex([1.0, 1.0-sclc, 0.0])
        elif adjSpecMD.ix[sn, tn] < 0 and ed.attr['color'] != '#FFFF00':
            sclc = float(adjSpecMD.ix[sn, tn])/maxValN*1.0
            ed.attr['color'] = matplotlib.colors.to_hex([1.0-sclc, 1.0, 0.0])
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            if numStr == 'float':
                ed.attr['label'] = '%.3f' % (adjSpecMD.ix[sn, tn])
            elif numStr == 'int':
                ed.attr['label'] = '%d' % (adjSpecMD.ix[sn, tn])
        else:
            if adjSpecMD.ix[sn, tn] > 0:
                if adjSpecMD.ix[sn, tn]*edgeWidth/maxValP < 1:
                    ed.attr['penwidth'] = 1
                else:
                    ed.attr['penwidth'] = int(float(adjSpecMD.ix[sn, tn])*edgeWidth/maxValP)
            else:
                if adjSpecMD.ix[sn, tn]*edgeWidth/maxValN < 1:
                    ed.attr['penwidth'] = 1
                else:
                    ed.attr['penwidth'] = int(float(adjSpecMD.ix[sn, tn])*edgeWidth/maxValN)
                
    
    # set node color
    nxgSD.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    maxCltSize = max(cltSizeDict.values())
    for lb in labels: 
        try:
            nd=nxgSD.get_node(lb)
        except:
            continue
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
    
    plotFileName = 'network_delta_diff_%s-based_layout_%s.%s' % (typeStr, layout, plotFormat)
    readmeStr += 'network_delta_diff_%s-based_layout_xx.%s: cluster-to-cluster communication network in which the edge weight is the difference of %s.\n' % (typeStr, plotFormat, typeStr)
    
    plotFileName = os.path.join(resultDir, plotFileName)
    warnings.simplefilter("error")
    while True:
        try:
            nxgSD.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgSD.draw(plotFileName,prog='neato') 
                break
            for nd in nxgSD.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    
    # draw fold change networks
    # calculate fold changes
    adjSpecM1 = adjSpecM1.astype(float)
    adjSpecM2 = adjSpecM2.astype(float)
    adjSpecMF = pd.DataFrame(0.0, index=adjSpecMD.index, columns=adjSpecMD.columns)
    for idx in adjSpecMD.index:
        for col in adjSpecMD.columns:
            if adjSpecMD.ix[idx, col] > 0:
                if adjSpecM2.ix[idx, col] > 0:
                    adjSpecMF.ix[idx, col] = adjSpecM1.ix[idx, col]/adjSpecM2.ix[idx, col]
            else:
                if adjSpecM1.ix[idx, col] > 0:
                    adjSpecMF.ix[idx, col] = adjSpecM2.ix[idx, col]/adjSpecM1.ix[idx, col]
    maxVal = adjSpecMF.max().max()
    #set inf as 2 x max fold change
    for idx in adjSpecMD.index:
        for col in adjSpecMD.columns:
            if adjSpecMD.ix[idx, col] > 0:
                if adjSpecM2.ix[idx, col] == 0:
                    adjSpecMF.ix[idx, col] = maxVal * 2
            else:
                if adjSpecM1.ix[idx, col] == 0:
                    adjSpecMF.ix[idx, col] = maxVal * 2
    maxVal = adjSpecMF.max().max()
    
    # convert to a graphviz graph
    nxgSF = nx.MultiDiGraph(adjSpecMF)
    nxgSF = nx.nx_agraph.to_agraph(nxgSF)
    nxgSF.graph_attr.update(fontname = "Arial")
    nxgSF.graph_attr.update(fontsize = fontSize)
    nxgSF.graph_attr.update(margin = 0)
    nxgSF.graph_attr.update(ratio="adjSpecMD")
    nxgSF.graph_attr.update(label='Delta Network\nEdge weight: fold change of ' + typeStr)
    nxgSF.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    # set edge properties
    for ed in nxgSF.edges():
        sn = ed[0]
        tn = ed[1]
        if adjSpecMD.ix[sn, tn] > 0 and adjSpecM2.ix[sn, tn] > 0 and adjSpecM1.ix[sn, tn]/adjSpecM2.ix[sn, tn] > 2:
            ed.attr['color'] = '#FF0000'
        elif adjSpecMD.ix[sn, tn] < 0 and adjSpecM1.ix[sn, tn] > 0 and adjSpecM2.ix[sn, tn]/adjSpecM1.ix[sn, tn] > 2:
            ed.attr['color'] = '#00FF00'
        else:
            ed.attr['color'] = '#FFFF00'
        sclc = float(adjSpecMF.ix[sn, tn])/maxVal*1.0
        if adjSpecMD.ix[sn, tn] > 0 and ed.attr['color'] != '#FFFF00':#to red
            ed.attr['color'] = matplotlib.colors.to_hex([1.0, 1.0-sclc, 0.0])
        elif adjSpecMD.ix[sn, tn] < 0 and ed.attr['color'] != '#FFFF00':
            ed.attr['color'] = matplotlib.colors.to_hex([1.0-sclc, 1.0, 0.0])
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            if adjSpecMD.ix[sn, tn] > 0:
                ed.attr['label'] = '%.2f' % (adjSpecMF.ix[sn, tn])
            else:
                ed.attr['label'] = '-%.2f' % (adjSpecMF.ix[sn, tn])
        else:
            if adjSpecMF.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjSpecMF.ix[sn, tn]*edgeWidth/maxVal)
            
    # set node color
    nxgSF.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    maxCltSize = max(cltSizeDict.values())
    for lb in labels: 
        try:
            nd=nxgSF.get_node(lb)
        except:
            continue
            
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
    
    plotFileName = 'network_fold_change_%s-based_layout_%s.%s' % (typeStr, layout, plotFormat)
    readmeStr += 'network_fold_change_%s-based_layout_xx.%s: cluster-to-cluster communication network in which the edge weight is the fold change of %s.\n' % (typeStr, plotFormat, typeStr)
    
    plotFileName = os.path.join(resultDir, plotFileName)
    warnings.simplefilter("error")
    while True:
        try:
            nxgSF.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgSF.draw(plotFileName,prog='neato') 
                break
            for nd in nxgSF.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    
    for idx in adjSpecMD.index:
        for col in adjSpecMD.columns:
            if adjSpecMD.ix[idx, col] > 0:
                if adjSpecM2.ix[idx, col] == 0:
                    adjSpecMF.ix[idx, col] = adjSpecM1.ix[idx, col] / adjSpecM2.ix[idx, col]
            else:
                if adjSpecM1.ix[idx, col] == 0:
                    adjSpecMF.ix[idx, col] = adjSpecM2.ix[idx, col] / adjSpecM1.ix[idx, col]
    return readmeStr, adjSpecMF

def DrawGraphvizPlot(readmeStr, typeStr, numStr, nxgS, adjSpecM, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold, weightThreshold, frequencyThreshold, signalType, weightType, layout, plotFormat):
    
    # convert to a graphviz graph
    nxgS = nx.nx_agraph.to_agraph(nxgS)
    
    # draw whole network
    nxgS.graph_attr.update(fontname = "Arial")
    nxgS.graph_attr.update(fontsize = fontSize)
    nxgS.graph_attr.update(margin = 0)
    nxgS.graph_attr.update(ratio="fill")
    nxgS.graph_attr.update(label='Edge weight: ' + typeStr)
    nxgS.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    
    # set edge properties
    maxVal = adjSpecM.max().max()
    for ed in nxgS.edges():
        sn = ed[0]
        tn = ed[1]
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[sn])]
        ed.attr['color'] = matplotlib.colors.to_hex(newcol)
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            if numStr == 'float':
                ed.attr['label'] = '%.3f' % (adjSpecM.ix[sn, tn])
            elif numStr == 'int':
                ed.attr['label'] = '%d' % (adjSpecM.ix[sn, tn])
        else:
            if adjSpecM.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjSpecM.ix[sn, tn]*edgeWidth/maxVal)
    
    # set node color
    nxgS.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    maxCltSize = max(cltSizeDict.values())
    for lb in labels: 
        try:
            nd=nxgS.get_node(lb)
        except:
            continue
            
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
    
    if dataType == '':
        plotFileName = 'network_%s-based_layout_%s.%s' % (typeStr, layout, plotFormat)
        readmeStr += 'network_%s-based_layout_xx.%s: the cluster-to-cluster communication network in which the edge weight is %s.\n' % (typeStr, plotFormat, typeStr)
    
    else:
        plotFileName = '%s_network_%s-based_layout_%s.%s' % (dataType, typeStr, layout, plotFormat)
        readmeStr += 'xxx_network_%s-based_layout_xx.%s: dynamic cluster-to-cluster communication network in which the edge weight is %s.\n' % (typeStr, plotFormat, typeStr)
    
    plotFileName = os.path.join(resultDir, plotFileName)
    warnings.simplefilter("error")
    while True:
        try:
            nxgS.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgS.draw(plotFileName,prog='neato') 
                break
            for nd in nxgS.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    return readmeStr
    
def BuildDeltaInterClusterNetwork(origlabels, labels, cltSizes, edgeDF, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, signalType, weightType, layout, plotFormat, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance, resultDir, dataType=''):
    readmeStr = '\n'
    
    # color scheme
    colors = sns.hls_palette(n_colors=len(labels)).as_hex()
    colorDict = {}
    cltSizeDict = {}
    for idx in range(len(colors)):
        colorDict[labels[idx]] = colors[idx]
        colorDict[origlabels[idx]] = colors[idx]
        cltSizeDict[labels[idx]] = cltSizes[idx]
        cltSizeDict[origlabels[idx]] = cltSizes[idx]
    
    # build adjacency matrix
    edgeDF, adjM1, adjSpecM1, adjCountM1, nxgW1, nxgS1, nxgC1, adjM2, adjSpecM2, adjCountM2, nxgW2, nxgS2, nxgC2, adjMD, adjSpecMD, adjCountMD, nxgWD, nxgSD, nxgCD = BuildDeltaAdjM(edgeDF, origlabels, labels, specificityThreshold, weightThreshold, frequencyThreshold,keepTopEdge)
    
    # get igraph layout from adjacency matrix
    wposArray, wposDict = IgraphFromAdjacency(adjMD, layout, labels, cltSizes, clusterDistance)
    
    ## draw use graphviz
    #============edge count
    readmeStr, adjCountMF = DrawDeltaGraphvizPlot(readmeStr, 'edge-count', 'int', nxgC1, adjCountM1, nxgC2, adjCountM2, nxgCD, adjCountMD, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold,weightThreshold,frequencyThreshold,signalType,weightType,layout,plotFormat)
    
    #============average weight
    readmeStr, adjMF = DrawDeltaGraphvizPlot(readmeStr, 'average-expression', 'float', nxgW1, adjM1, nxgW2, adjM2, nxgWD, adjMD, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold,weightThreshold,frequencyThreshold,signalType,weightType,layout,plotFormat)
    
    #============total specificity
    readmeStr, adjSpecMF = DrawDeltaGraphvizPlot(readmeStr, 'total-specificity', 'float', nxgS1, adjSpecM1, nxgS2, adjSpecM2, nxgSD, adjSpecMD, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold,weightThreshold,frequencyThreshold,signalType,weightType,layout,plotFormat)
    
    adjMFileName = os.path.join(resultDir, '%s_Mtx.xlsx' % dataType)
    readmeStr += 'xxx_Mtx.xlsx: all adjacency matrices of the dynamic networks.\n'
    
    writer = pd.ExcelWriter(adjMFileName, engine='xlsxwriter')
    readmeDict = {'colA':['README'],'colB':['']}
    readmeDict['colA'].append('Matrix 1')
    readmeDict['colB'].append('Edge-count-based adjacency matrix in condition 1')
    readmeDict['colA'].append('Matrix 2')
    readmeDict['colB'].append('Edge-count-based adjacency matrix in condition 2')
    readmeDict['colA'].append('Matrix 3')
    readmeDict['colB'].append('Adjacency matrix in which each element is the difference between Matrix 1 and Matrix 2')
    readmeDict['colA'].append('Matrix 4')
    readmeDict['colB'].append('Adjacency matrix in which each element is the fold change between Matrix 1 and Matrix 2')
    readmeDict['colA'].append('Matrix 5')
    readmeDict['colB'].append('Total-specificity-based adjacency matrix in condition 1')
    readmeDict['colA'].append('Matrix 6')
    readmeDict['colB'].append('Total-specificity-based adjacency matrix in condition 2')
    readmeDict['colA'].append('Matrix 7')
    readmeDict['colB'].append('Adjacency matrix in which each element is the difference between Matrix 5 and Matrix 6')
    readmeDict['colA'].append('Matrix 8')
    readmeDict['colB'].append('Adjacency matrix in which each element is the fold change between Matrix 5 and Matrix 6')
    readmeDict['colA'].append('Matrix 9')
    readmeDict['colB'].append('Average-expression-based adjacency matrix in condition 1')
    readmeDict['colA'].append('Matrix 10')
    readmeDict['colB'].append('Average-expression-based adjacency matrix in condition 2')
    readmeDict['colA'].append('Matrix 11')
    readmeDict['colB'].append('Adjacency matrix in which each element is the difference between Matrix 9 and Matrix 10')
    readmeDict['colA'].append('Matrix 12')
    readmeDict['colB'].append('Adjacency matrix in which each element is the fold change between Matrix 9 and Matrix 10')
    readmeDF = pd.DataFrame(readmeDict)
    readmeDF.to_excel(writer, sheet_name='README', index=False, header=False)
    adjCountM1.to_excel(writer, sheet_name='Matrix 1')
    adjCountM2.to_excel(writer, sheet_name='Matrix 2')
    adjCountMD.to_excel(writer, sheet_name='Matrix 3')
    adjCountMF.to_excel(writer, sheet_name='Matrix 4')
    adjSpecM1.to_excel(writer, sheet_name='Matrix 5')
    adjSpecM2.to_excel(writer, sheet_name='Matrix 6')
    adjSpecMD.to_excel(writer, sheet_name='Matrix 7')
    adjSpecMF.to_excel(writer, sheet_name='Matrix 8')
    adjM1.to_excel(writer, sheet_name='Matrix 9')
    adjM2.to_excel(writer, sheet_name='Matrix 10')
    adjMD.to_excel(writer, sheet_name='Matrix 11')
    adjMF.to_excel(writer, sheet_name='Matrix 12')
    writer.save()
    
    with open(os.path.join(resultDir,'README.txt'), 'w') as file_object:
        file_object.write('README\n')
        file_object.write('\n')
        file_object.write('The cell-to-cell signaling database: %s\n' % signalType)
        file_object.write('The weight type of cell-to-cell signaling: %s\n' % weightType)
        if keepTopEdge != 0:
            file_object.write('Top edges to draw: %s\n' % keepTopEdge)
        else:
            file_object.write('Top edges to draw: all\n')
        file_object.write('\n')
        file_object.write('Expression threshold: %s\n' % weightThreshold)
        file_object.write('Specificity threshold: %s\n' % specificityThreshold)
        file_object.write('Detection threshold: %s\n' % frequencyThreshold)
        file_object.write('\n')
        file_object.write(readmeStr)

def BuildInterClusterNetwork(origlabels, labels, cltSizes, edgeDF, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, signalType, weightType, layout, plotFormat, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance, resultDir, dataType=''):
    readmeStr = '\n'
    
    # color scheme
    colors = sns.hls_palette(n_colors=len(labels)).as_hex()
    colorDict = {}
    cltSizeDict = {}
    for idx in range(len(colors)):
        colorDict[labels[idx]] = colors[idx]
        colorDict[origlabels[idx]] = colors[idx]
        cltSizeDict[labels[idx]] = cltSizes[idx]
        cltSizeDict[origlabels[idx]] = cltSizes[idx]
    
    # build adjacency matrix
    edgeDF, adjM, adjSpecM, adjCountM, nxgW, nxgS, nxgC = BuildAdjM(edgeDF, origlabels, labels, specificityThreshold, weightThreshold, keepTopEdge)
    
    # get igraph layout from adjacency matrix
    wposArray, wposDict = IgraphFromAdjacency(adjM, layout, labels, cltSizes, clusterDistance)
    
    ## draw use graphviz
    #============edge count
    readmeStr = DrawGraphvizPlot(readmeStr, 'edge-count', 'int', nxgC, adjCountM, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold,weightThreshold,frequencyThreshold,signalType,weightType,layout,plotFormat)
    
    #============total weight
    readmeStr = DrawGraphvizPlot(readmeStr, 'total-expression', 'float', nxgW, adjM, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold,weightThreshold,frequencyThreshold,signalType,weightType,layout,plotFormat)
    
    #============total specificity
    readmeStr = DrawGraphvizPlot(readmeStr, 'total-specificity', 'float', nxgS, adjSpecM, dataType, resultDir, plotWidth, plotHeight, fontSize, edgeWidth, colorDict, cltSizeDict, maxClusterSize, wposDict, labels, specificityThreshold,weightThreshold,frequencyThreshold,signalType,weightType,layout,plotFormat)
    
    if dataType == '':
        edgeDFFileName = os.path.join(resultDir, 'Edges.csv')
        readmeStr += 'Edges.csv: all filtered edges.\n'
        adjMFileName = os.path.join(resultDir, 'Mtx.xlsx')
        readmeStr += 'Mtx.xlsx: three adjacency matrices of the networks.\n'
    else:
        edgeDFFileName = os.path.join(resultDir, '%s_Edges.csv' % dataType)
        readmeStr += 'xxx_edges.csv: all filtered dynamic edges.\n'
        adjMFileName = os.path.join(resultDir, '%s_Mtx.xlsx' % dataType)
        readmeStr += 'xxx_Mtx.xlsx: three adjacency matrices of the dynamic networks.\n'
    
    if weightType == 'mean':
        columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand average expression value', 
            'Ligand derived specificity of average expression value', 'Receptor detection rate', 'Receptor average expression value', 
            'Receptor derived specificity of average expression value', 'Edge average expression weight', 'Edge average expression derived specificity']
    else:
        columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand total expression value', 
            'Ligand derived specificity of total expression value', 'Receptor detection rate', 'Receptor total expression value', 
            'Receptor derived specificity of total expression value', 'Edge total expression weight', 'Edge total expression derived specificity']
    edgeDF.columns = columns
    edgeDF.to_csv(edgeDFFileName, columns=columns, index=False)
    
    writer = pd.ExcelWriter(adjMFileName, engine='xlsxwriter')
    readmeDict = {'colA':['README'],'colB':['']}
    readmeDict['colA'].append('Matrix 1')
    readmeDict['colB'].append('Edge-count-based adjacency matrix')
    readmeDict['colA'].append('Matrix 2')
    readmeDict['colB'].append('Total-specificity-based adjacency matrix')
    readmeDict['colA'].append('Matrix 3')
    readmeDict['colB'].append('Total-expression-based adjacency matrix')
    readmeDF = pd.DataFrame(readmeDict)
    readmeDF.to_excel(writer, sheet_name='README', index=False, header=False)
    adjCountM.to_excel(writer, sheet_name='Matrix 1')
    adjSpecM.to_excel(writer, sheet_name='Matrix 2')
    adjM.to_excel(writer, sheet_name='Matrix 3')
    writer.save()
    
    # save edge list
    if keepTopEdge == 0:
        edgeDict = {'sending cluster name':[], 'target cluster name':[], 'weight':[], 'count':[], 'specificity':[]}
        for send in adjM.index:
            for target in adjM.columns:
                if adjM.ix[send, target] > 0:
                    edgeDict['sending cluster name'].append(send.replace('\n',' '))
                    edgeDict['target cluster name'].append(target.replace('\n',' '))
                    edgeDict['weight'].append(adjM.ix[send, target])
                    edgeDict['count'].append(adjCountM.ix[send, target])
                    edgeDict['specificity'].append(adjSpecM.ix[send, target])
        if dataType == '':
            edgeFileName = os.path.join(resultDir, 'network_edges.csv')
            readmeStr += 'network_edges.csv: five weights of each cluster-to-cluster edge in the network.\n'
        else:
            edgeFileName = os.path.join(resultDir, '%s_network_edges.csv' % (dataType))
            readmeStr += '%s_network_edges.csv: five weights of each cluster-to-cluster edge in the %s network.\n' % (dataType,dataType)
    
        edgeDF = pd.DataFrame(edgeDict)
        edgeDF['weight per pair'] = edgeDF['weight']/edgeDF['count']
        edgeDF['specificity per pair'] = edgeDF['specificity']/edgeDF['count']
        edgeDF = edgeDF.ix[:,['sending cluster name', 'target cluster name', 'weight', 'specificity', 'count', 'weight per pair', 'specificity per pair']]
        newCol = ['Sending cluster name', 'Target cluster name', 'Total expression', 'Total specificity', 'Edge count', 'Average expression', 'Average specificity']
        edgeDF.columns = newCol
        edgeDF.sort_values(by="Total expression", ascending=False).to_csv(edgeFileName,columns=newCol,index=False)
    
    with open(os.path.join(resultDir,'README.txt'), 'w') as file_object:
        file_object.write('README\n')
        file_object.write('\n')
        file_object.write('The cell-to-cell signaling database: %s\n' % signalType)
        file_object.write('The weight type of cell-to-cell signaling: %s\n' % weightType)
        if keepTopEdge != 0:
            file_object.write('Top edges to draw: %s\n' % keepTopEdge)
        else:
            file_object.write('Top edges to draw: all\n')
        file_object.write('\n')
        file_object.write('Expression threshold: %s\n' % weightThreshold)
        file_object.write('Specificity threshold: %s\n' % specificityThreshold)
        file_object.write('Detection threshold: %s\n' % frequencyThreshold)
        file_object.write('\n')
        file_object.write(readmeStr)

def FilterDeltaEdges(sourceFolder, signalType, weightType, frequencyThreshold):
    olddapcols = ['sending cluster name', 'ligand', 'receptor', 'target cluster name', 'delta ligand frequency', 'delta ligand expression', 'delta ligand specificity', 'delta receptor frequency', 'delta receptor expression', 'delta receptor specificity', 'delta weight', 'delta specificity']
    refinedOldcols = ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Delta ligand detection rate', 'Delta ligand expression', 'Delta ligand specificity', 'Delta receptor detection rate', 'Delta receptor expression', 'Delta receptor specificity', 'Delta edge expression weight', 'Delta edge specificity weight']
    
    uredgeDF = pd.read_csv(os.path.join(sourceFolder, 'Delta_edges_'+signalType, 'UP-regulated_%s.csv' % (weightType)), index_col=None, header=0)
    realuredgeDF = uredgeDF.ix[(uredgeDF['Ligand detection rate in condition 1']>frequencyThreshold)&(uredgeDF['Receptor detection rate in condition 1']>frequencyThreshold)&(uredgeDF['Ligand detection rate in condition 2']>frequencyThreshold)&(uredgeDF['Receptor detection rate in condition 2']>frequencyThreshold),]
    realuredgeDF['Delta ligand detection rate'] = realuredgeDF['Ligand detection rate in condition 2'] - realuredgeDF['Ligand detection rate in condition 1']
    realuredgeDF['Delta receptor detection rate'] = realuredgeDF['Receptor detection rate in condition 2'] - realuredgeDF['Receptor detection rate in condition 1']
    realuredgeDF = realuredgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster',  'Delta ligand detection rate', 'Delta ligand expression', 'Delta ligand specificity', 'Delta receptor detection rate', 'Delta receptor expression', 'Delta receptor specificity', 'Delta edge expression weight', 'Delta edge specificity weight']]
    realuredgeDF.columns = olddapcols
    realuredgeDF = realuredgeDF.reset_index()
    realuredgeDF = realuredgeDF.ix[:,realuredgeDF.columns[1:]]
    urapedgeDF = uredgeDF.ix[((uredgeDF['Ligand detection rate in condition 1']<=frequencyThreshold)|(uredgeDF['Receptor detection rate in condition 1']<=frequencyThreshold))&(uredgeDF['Ligand detection rate in condition 2']>frequencyThreshold)&(uredgeDF['Receptor detection rate in condition 2']>frequencyThreshold),]
    urapedgeDF = urapedgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate in condition 2', 'Ligand expression in condition 2', 'Ligand specificity in condition 2', 'Receptor detection rate in condition 2', 'Receptor expression in condition 2', 'Receptor specificity in condition 2', 'Edge expression weight in condition 2', 'Edge specificity weight in condition 2']]
    urapedgeDF.columns = olddapcols
    urdpedgeDF = uredgeDF.ix[(uredgeDF['Ligand detection rate in condition 1']>frequencyThreshold)&(uredgeDF['Receptor detection rate in condition 1']>frequencyThreshold)&((uredgeDF['Ligand detection rate in condition 2']<=frequencyThreshold)|(uredgeDF['Receptor detection rate in condition 2']<=frequencyThreshold)),]
    urdpedgeDF = urdpedgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate in condition 1', 'Ligand expression in condition 1', 'Ligand specificity in condition 1', 'Receptor detection rate in condition 1', 'Receptor expression in condition 1', 'Receptor specificity in condition 1', 'Edge expression weight in condition 1', 'Edge specificity weight in condition 1']]
    urdpedgeDF.columns = olddapcols
    
    dredgeDF = pd.read_csv(os.path.join(sourceFolder, 'Delta_edges_'+signalType, 'DOWN-regulated_%s.csv' % (weightType)), index_col=None, header=0)
    realdredgeDF = dredgeDF.ix[(dredgeDF['Ligand detection rate in condition 1']>frequencyThreshold)&(dredgeDF['Receptor detection rate in condition 1']>frequencyThreshold)&(dredgeDF['Ligand detection rate in condition 2']>frequencyThreshold)&(dredgeDF['Receptor detection rate in condition 2']>frequencyThreshold),]
    realdredgeDF['Delta ligand detection rate'] = realdredgeDF['Ligand detection rate in condition 1'] - realdredgeDF['Ligand detection rate in condition 2']
    realdredgeDF['Delta receptor detection rate'] = realdredgeDF['Receptor detection rate in condition 1'] - realdredgeDF['Receptor detection rate in condition 2']
    realdredgeDF = realdredgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster',  'Delta ligand detection rate', 'Delta ligand expression', 'Delta ligand specificity', 'Delta receptor detection rate', 'Delta receptor expression', 'Delta receptor specificity', 'Delta edge expression weight', 'Delta edge specificity weight']]
    realdredgeDF.columns = olddapcols
    realdredgeDF = realdredgeDF.reset_index()
    realdredgeDF = realdredgeDF.ix[:,realdredgeDF.columns[1:]]
    drapedgeDF = dredgeDF.ix[((dredgeDF['Ligand detection rate in condition 1']<=frequencyThreshold)|(dredgeDF['Receptor detection rate in condition 1']<=frequencyThreshold))&(dredgeDF['Ligand detection rate in condition 2']>frequencyThreshold)&(dredgeDF['Receptor detection rate in condition 2']>frequencyThreshold),]
    drapedgeDF = drapedgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate in condition 2', 'Ligand expression in condition 2', 'Ligand specificity in condition 2', 'Receptor detection rate in condition 2', 'Receptor expression in condition 2', 'Receptor specificity in condition 2', 'Edge expression weight in condition 2', 'Edge specificity weight in condition 2']]
    drapedgeDF.columns = olddapcols
    drdpedgeDF = dredgeDF.ix[(dredgeDF['Ligand detection rate in condition 1']>frequencyThreshold)&(dredgeDF['Receptor detection rate in condition 1']>frequencyThreshold)&((dredgeDF['Ligand detection rate in condition 2']<=frequencyThreshold)|(dredgeDF['Receptor detection rate in condition 2']<=frequencyThreshold)),]
    drdpedgeDF = drdpedgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate in condition 1', 'Ligand expression in condition 1', 'Ligand specificity in condition 1', 'Receptor detection rate in condition 1', 'Receptor expression in condition 1', 'Receptor specificity in condition 1', 'Edge expression weight in condition 1', 'Edge specificity weight in condition 1']]
    drdpedgeDF.columns = olddapcols
    
    apedgeDF = pd.read_csv(os.path.join(sourceFolder, 'Delta_edges_'+signalType, 'Appeared_%s.csv' % (weightType)), index_col=None, header=0)
    realapedgeDF = apedgeDF.ix[(apedgeDF['Delta ligand detection rate']>frequencyThreshold)&(apedgeDF['Delta receptor detection rate']>frequencyThreshold),refinedOldcols]
    realapedgeDF.columns = olddapcols
    
    dpedgeDF = pd.read_csv(os.path.join(sourceFolder, 'Delta_edges_'+signalType, 'Disappeared_%s.csv' % (weightType)), index_col=None, header=0)
    realdpedgeDF = dpedgeDF.ix[(dpedgeDF['Delta ligand detection rate']>frequencyThreshold)&(dpedgeDF['Delta receptor detection rate']>frequencyThreshold),refinedOldcols]
    realdpedgeDF.columns = olddapcols
    
    stedgeDF = pd.read_csv(os.path.join(sourceFolder, 'Delta_edges_'+signalType, 'Stable_%s.csv' % (weightType)), index_col=None, header=0)
    stapedgeDF = stedgeDF.ix[((stedgeDF['Ligand detection rate in condition 1']<=frequencyThreshold)|(stedgeDF['Receptor detection rate in condition 1']<=frequencyThreshold))&(stedgeDF['Ligand detection rate in condition 2']>frequencyThreshold)&(stedgeDF['Receptor detection rate in condition 2']>frequencyThreshold),]
    stapedgeDF = stapedgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate in condition 2', 'Ligand expression in condition 2', 'Ligand specificity in condition 2', 'Receptor detection rate in condition 2', 'Receptor expression in condition 2', 'Receptor specificity in condition 2', 'Edge expression weight in condition 2', 'Edge specificity weight in condition 2']]
    stapedgeDF.columns = olddapcols
    stdpedgeDF = stedgeDF.ix[((stedgeDF['Ligand detection rate in condition 2']<=frequencyThreshold)|(stedgeDF['Receptor detection rate in condition 2']<=frequencyThreshold))&(stedgeDF['Ligand detection rate in condition 1']>frequencyThreshold)&(stedgeDF['Receptor detection rate in condition 1']>frequencyThreshold),]
    stdpedgeDF = stdpedgeDF.ix[:,['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate in condition 1', 'Ligand expression in condition 1', 'Ligand specificity in condition 1', 'Receptor detection rate in condition 1', 'Receptor expression in condition 1', 'Receptor specificity in condition 1', 'Edge expression weight in condition 1', 'Edge specificity weight in condition 1']]
    stdpedgeDF.columns = olddapcols
    
    realapedgeDF = pd.concat([realapedgeDF, urapedgeDF, drapedgeDF, stapedgeDF]).reset_index()
    realapedgeDF = realapedgeDF.ix[:,realapedgeDF.columns[1:]]
    realdpedgeDF = pd.concat([realdpedgeDF, urdpedgeDF, drdpedgeDF, stdpedgeDF]).reset_index()
    realdpedgeDF = realdpedgeDF.ix[:,realdpedgeDF.columns[1:]]
    
    alledgeDF = pd.read_csv(os.path.join(sourceFolder, 'Delta_edges_'+signalType, 'All_edges_%s.csv' % (weightType)), index_col=None, header=0)
    
    kindDict = {'all':alledgeDF,'appeared':realapedgeDF, 'disappeared':realdpedgeDF, 'up_regulated':realuredgeDF, 'down_regulated':realdredgeDF}
    return kindDict
    
def MainNetwork(sourceFolder, signalType, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, layout, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance):
    # load data
    clusterMapFilename = os.path.join(sourceFolder, 'ClusterMapping.csv')
    if os.path.exists(clusterMapFilename):
        # process node properties for single dataset
        clusterMapDF = pd.read_csv(clusterMapFilename, index_col=None, header=0)
        clusterSizeDF = clusterMapDF.groupby('cluster').count()
        origlabels = [str(i) for i in clusterSizeDF.index]
        labels = [str(i)+'\n(%s cells)' % clusterSizeDF.ix[i,'cell'] for i in clusterSizeDF.index]
        cltSizes = [float(clusterSizeDF.ix[i,'cell']) for i in clusterSizeDF.index]
        
        # load edge properties
        edgeDF = pd.read_csv(os.path.join(opt.sourceFolder,'Edges_%s.csv' % signalType), index_col=None, header=0)
        
        # only keep edges of interest
        if weightType == 'mean':
            selectCols= ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand average expression value', 
            'Ligand derived specificity of average expression value', 'Receptor detection rate', 'Receptor average expression value', 
            'Receptor derived specificity of average expression value', 'Edge average expression weight', 'Edge average expression derived specificity']
        else:
            selectCols= ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand total expression value', 
            'Ligand derived specificity of total expression value', 'Receptor detection rate', 'Receptor total expression value', 
            'Receptor derived specificity of total expression value', 'Edge total expression weight', 'Edge total expression derived specificity']
        edgeDF = edgeDF.ix[:,selectCols]
        edgeDF.columns = ["sending cluster name", "ligand", "receptor", "target cluster name", "frequency ligand", "original ligand", "specified ligand", "frequency receptor", "original receptor", "specified receptor", "product of original", "product of specified"]
        edgeDF = edgeDF.ix[(edgeDF['product of specified']>specificityThreshold)&(edgeDF['original ligand']>weightThreshold)&(edgeDF['original receptor']>weightThreshold)&(edgeDF['frequency ligand']>frequencyThreshold)&(edgeDF['frequency receptor']>frequencyThreshold),]
        print('#### %s edges are loaded' % len(edgeDF))
        if len(edgeDF) == 0:
            print('#### DONE')
            return
        
        #cluster to cluster weighted directed network
        print('#### plotting the weighted directed cell-to-cell communication network')
        resultDir = os.path.join(sourceFolder,'Network_exp_%s_spe_%s_det_%s_top_%s_signal_%s_weight_%s' % (weightThreshold,specificityThreshold,frequencyThreshold, keepTopEdge,signalType, weightType))
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        print('#### the folder "%s" has been created to save the analysis results' % os.path.abspath(resultDir))
        BuildInterClusterNetwork(origlabels, labels, cltSizes, edgeDF, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, signalType, weightType, layout, plotFormat, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance, resultDir)
    else:
        # process node properties for delta dataset
        sumClusterDF = pd.read_excel(os.path.join(sourceFolder, 'cluster_comparison.xlsx'), index_col=None, header=0)
        sumClusterDF['Cluster'] = sumClusterDF['Cluster'].astype(str)
        origlabels = sorted([str(i) for i in set(sumClusterDF['Cluster'])])
        labels = []
        cltSizes = []
        
        for clt in origlabels:
            cltDF = sumClusterDF.ix[sumClusterDF['Cluster'] == clt,].sort_values(by=['Population (cells)'])
            if len(cltDF) == 2:
                refSize = sumClusterDF.ix[(sumClusterDF['Cluster'] == clt)&(sumClusterDF['Source'] == 'reference dataset'),'Population (cells)']
                tgtSize = sumClusterDF.ix[(sumClusterDF['Cluster'] == clt)&(sumClusterDF['Source'] == 'target dataset'),'Population (cells)']
                deltaSize = int(tgtSize) - int(refSize)
            else:
                deltaSize = int(cltDF.iloc[0,1])
                if cltDF.iloc[0,2] == 'reference dataset':
                    deltaSize = -1 * deltaSize
            if deltaSize > 0:
                labels.append(clt+'\n(+%s cells)' % deltaSize)
                cltSizes.append(int(deltaSize))
            else:
                labels.append(clt+'\n(%s cells)' % deltaSize)
                cltSizes.append(int(-1*deltaSize))
        
        # load edge data and filter them based on the detection threshold
        dynamDict = FilterDeltaEdges(sourceFolder, signalType, weightType, frequencyThreshold)
        resultDir = os.path.join(sourceFolder,'Delta_Network_exp_%s_spe_%s_det_%s_top_%s_signal_%s_weight_%s' % (weightThreshold,specificityThreshold,frequencyThreshold,keepTopEdge,signalType, weightType))
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        print('#### the folder "%s" has been created to save the analysis results' % os.path.abspath(resultDir))
        for kind in dynamDict.keys():
            if kind != 'all':
                continue
            tempedgeDF = dynamDict[kind]
            #cluster to cluster weighted directed network
            print ('#### plotting the weighted directed cell-to-cell communication network for delta interactions')
            BuildDeltaInterClusterNetwork(origlabels, labels, cltSizes, tempedgeDF, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, signalType, weightType, layout, plotFormat, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance, resultDir, kind)
    
    print('#### DONE')
            
def BuildSingleLRInterClusterNetwork(origlabels, labels, cltSizes, edgeDF, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, ls, rs, signalType, weightType, layout, plotFormat, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance, resultDir, dataType = ''):
    readmeStr = '\n'
    
    # color scheme
    colors = sns.hls_palette(n_colors=len(labels)).as_hex()
    colorDict = {}
    cltSizeDict = {}
    for idx in range(len(colors)):
        colorDict[labels[idx]] = colors[idx]
        colorDict[origlabels[idx]] = colors[idx]
        cltSizeDict[labels[idx]] = cltSizes[idx]
        cltSizeDict[origlabels[idx]] = cltSizes[idx]
    labelDict = {}
    for idx in range(len(labels)):
        labelDict[origlabels[idx]] = labels[idx]
    
    # build adjacency matrix
    edgeDF, adjM, adjSpecM, adjCountM, nxgWOrig, nxgSOrig, nxgCOrig = BuildAdjM(edgeDF, origlabels, labels, specificityThreshold, weightThreshold, keepTopEdge)
    
    sendClts = list(set(edgeDF['sending cluster name']))
    targetClts = list(set(edgeDF['target cluster name']))
    sendDict = {}
    sendMaxWgt = 0
    sendMaxSpc = 0
    for sendClt in sendClts:
        sendDict[labelDict[sendClt]] = edgeDF.ix[edgeDF['sending cluster name']==sendClt, ['original ligand', 'specified ligand']].values[0]
        if sendMaxWgt < sendDict[labelDict[sendClt]][0]:
            sendMaxWgt = sendDict[labelDict[sendClt]][0]
        if sendMaxSpc < sendDict[labelDict[sendClt]][1]:
            sendMaxSpc = sendDict[labelDict[sendClt]][1]
    targetDict = {}
    targetMaxWgt = 0
    targetMaxSpc = 0
    for targetClt in targetClts:
        targetDict[labelDict[targetClt]] = edgeDF.ix[edgeDF['target cluster name']==targetClt,['original receptor', 'specified receptor']].values[0]
        if targetMaxWgt < targetDict[labelDict[targetClt]][0]:
            targetMaxWgt = targetDict[labelDict[targetClt]][0]
        if targetMaxSpc < targetDict[labelDict[targetClt]][1]:
            targetMaxSpc = targetDict[labelDict[targetClt]][1]
            
    # get igraph layout from adjacency matrix
    wposArray, wposDict = IgraphFromAdjacency(adjM, layout, labels, cltSizes, clusterDistance)
    
    ls=ls+'\nLigand'
    rs=rs+'\nReceptor'
    #============total weight simple graph
    # convert to a graphviz graph
    nxgW = nx.nx_agraph.to_agraph(nxgWOrig)
    nxgW.graph_attr.update(fontname = "Arial")
    nxgW.graph_attr.update(fontsize = fontSize)
    nxgW.graph_attr.update(margin = 0)
    nxgW.graph_attr.update(ratio="fill")
    nxgW.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    
    # set edge properties
    maxVal = adjM.max().max()
    for ed in nxgW.edges():
        sn = ed[0]
        tn = ed[1]
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[sn])]
        ed.attr['color'] = matplotlib.colors.to_hex(newcol)
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            ed.attr['label'] = '%.3f' % (adjM.ix[sn, tn])
        else:
            if adjM.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjM.ix[sn, tn]*edgeWidth/maxVal)
    
    # set node color
    nxgW.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    maxCltSize = max(cltSizeDict.values())
    for lb in labels: 
        try:
            nd=nxgW.get_node(lb)
        except:
            continue
            
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
        
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
        
    if dataType == '':
        plotFileName = 'network_%s-%s_layout_%s.%s' % (ls.split('\n')[0], rs.split('\n')[0], layout, plotFormat)
        readmeStr += 'network_%s-%s_layout_xx.%s: the cluster-to-cluster communication network of %s-%s.\n' % (ls.split('\n')[0], rs.split('\n')[0], plotFormat, ls.split('\n')[0], rs.split('\n')[0])
    else:
        plotFileName = '%s_network_%s-%s_layout_%s.%s' % (dataType, ls.split('\n')[0], rs.split('\n')[0], layout, plotFormat)
        readmeStr += '%s_network_%s-%s_layout_xx.%s: the %s cluster-to-cluster communication network of %s-%s.\n' % (dataType, ls.split('\n')[0], rs.split('\n')[0], plotFormat, dataType, ls.split('\n')[0], rs.split('\n')[0])
    plotFileName = os.path.join(resultDir, plotFileName)
    warnings.simplefilter("error")
    while True:
        try:
            nxgW.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgW.draw(plotFileName,prog='neato') 
                break
            for nd in nxgW.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    
    #============total weight hypergraph
    # convert to a graphviz graph
    nxgW = nx.nx_agraph.to_agraph(nxgWOrig)
    nxgW.graph_attr.update(fontname = "Arial")
    nxgW.graph_attr.update(fontsize = fontSize)
    nxgW.graph_attr.update(margin = 0)
    nxgW.graph_attr.update(overlap = 'voronoi')
    nxgW.graph_attr.update(ratio="fill")
    nxgW.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
        
    nxgW.node_attr['style']='filled,setlinewidth(0)'
    idx = 0 
    for lb in labels: 
        try:
            nd=nxgW.get_node(lb)
        except:
            continue
        nd.attr['shape'] = 'circle'
        if maxClusterSize != 0:
            radis = cltSizeDict[nd]*maxClusterSize/maxCltSize
            nd.attr['width'] = str(round(radis,2))
            nd.attr['height'] = str(round(radis,2))
            
        nd.attr['fixedsize'] = 'true'
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[nd])]
        nd.attr['fillcolor'] = matplotlib.colors.to_hex(newcol)
        nd.attr['pin'] = 'true'
        nd.attr['pos'] = '%s,%s' % (wposDict[idx][0]*plotWidth/2,wposDict[idx][1]*plotHeight/2)
        nd.attr['fontsize'] = fontSize
        nd.attr['fontname'] = "Arial"
        idx += 1
    # add ligand and receptor node
    nxgW.add_node(ls,label=ls,fillcolor='#66ff00',shape='box',fontsize=fontSize,fontname = "Arial")
    nxgW.add_node(rs,label=rs,fillcolor='#ff0000',shape='box',fontsize=fontSize,fontname = "Arial")
    
    #change direct comm to lr-via comm
    nedgeList = nxgW.edges()
    nxgW.remove_edges_from(nxgW.edges())
    if edgeWidth == 0:
        nxgW.add_edge(ls,rs,arrowhead='diamond')
    else:
        nxgW.add_edge(ls,rs,arrowhead='diamond',penwidth=int(edgeWidth))
    oldtns = []
    oldsns = []
    for ed in nedgeList:
        sn = ed[0]
        tn = ed[1]
        if tn not in oldtns:
            if edgeWidth == 0:
                nxgW.add_edge(rs,tn,color=matplotlib.colors.to_hex([i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[tn])]),fontsize=fontSize, fontname="Arial",label = '%.3f' % (adjM.ix[sn, tn]))
            else:
                if targetDict[tn][0]*edgeWidth/targetMaxWgt < 1:
                    nxgW.add_edge(rs,tn,color=matplotlib.colors.to_hex([i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[tn])]),penwidth=1)
                else:
                    nxgW.add_edge(rs,tn,color=matplotlib.colors.to_hex([i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[tn])]),penwidth=float(targetDict[tn][0]*edgeWidth/targetMaxWgt))
            oldtns.append(tn)
        if sn not in oldsns:
            if edgeWidth == 0:
                nxgW.add_edge(sn,ls,color=matplotlib.colors.to_hex([i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[sn])]),fontsize=fontSize, fontname="Arial",label = '%.3f' % (adjM.ix[sn, tn]))
            else:
                if sendDict[sn][0]*edgeWidth/sendMaxWgt < 1:
                    nxgW.add_edge(sn,ls,color=matplotlib.colors.to_hex([i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[sn])]),penwidth=1)
                else:
                    nxgW.add_edge(sn,ls,color=matplotlib.colors.to_hex([i+0.5*(1-i) for i in matplotlib.colors.to_rgb(colorDict[sn])]),penwidth=float(sendDict[sn][0]*edgeWidth/sendMaxWgt))
            oldsns.append(sn)
    
    if dataType == '':
        plotFileName = 'hypergraph_%s-%s_layout_%s.%s' % (ls.split('\n')[0], rs.split('\n')[0], layout, plotFormat)
        readmeStr += 'hypergraph_%s-%s_layout_xx.%s: the cluster-to-cluster communication network of %s-%s.\n' % (ls.split('\n')[0], rs.split('\n')[0], plotFormat, ls.split('\n')[0], rs.split('\n')[0])
    else:
        plotFileName = '%s_hypergraph_%s-%s_layout_%s.%s' % (dataType, ls.split('\n')[0], rs.split('\n')[0], layout, plotFormat)
        readmeStr += '%s_hypergraph_%s-%s_layout_xx.%s: the %s cluster-to-cluster communication network of %s-%s.\n' % (dataType, ls.split('\n')[0], rs.split('\n')[0], plotFormat, dataType, ls.split('\n')[0], rs.split('\n')[0])
    plotFileName = os.path.join(resultDir, plotFileName)
    
    warnings.simplefilter("error")
    while True:
        try:
            nxgW.draw(plotFileName,prog='fdp') 
            break
        except RuntimeWarning as rw:
            errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
            if len(errorNodeList)==0:
                errorNodeList = [m[m.find("'")+1:m.find("',")] for m in str(rw).split("Warning:") if 'too small' in m]
                nxgW.draw(plotFileName,prog='neato') 
                break
            for nd in nxgW.nodes():
                if str(nd) in errorNodeList:
                    nd.attr['xlabel'] = str(nd)
                    nd.attr['label'] = ''
            continue
    warnings.simplefilter("ignore")
    
    if dataType == '':
        edgeDFFileName = os.path.join(resultDir, 'Edges.csv')
        readmeStr += 'Edges.csv: all filtered edges via %s-%s.\n' % (ls.split('\n')[0], rs.split('\n')[0])
        adjMFileName = os.path.join(resultDir, 'Mtx.xlsx')
        readmeStr += 'Mtx.xlsx: two adjacency matrices of the networks of %s-%s.\n' % (ls.split('\n')[0], rs.split('\n')[0])
    else:
        edgeDFFileName = os.path.join(resultDir, '%s_Edges.csv' % dataType)
        readmeStr += '%s_edges.csv: all filtered %s edges via %s-%s.\n' % (dataType,dataType,ls.split('\n')[0], rs.split('\n')[0])
        adjMFileName = os.path.join(resultDir, '%s_Mtx.xlsx' % dataType)
        readmeStr += '%s_Mtx.xlsx: two adjacency matrices of the %s networks of %s-%s.\n' % (dataType,dataType,ls.split('\n')[0], rs.split('\n')[0])
    
    if weightType == 'mean':
        columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand average expression value', 
            'Ligand derived specificity of average expression value', 'Receptor detection rate', 'Receptor average expression value', 
            'Receptor derived specificity of average expression value', 'Edge average expression weight', 'Edge average expression derived specificity']
    else:
        columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand total expression value', 
            'Ligand derived specificity of total expression value', 'Receptor detection rate', 'Receptor total expression value', 
            'Receptor derived specificity of total expression value', 'Edge total expression weight', 'Edge total expression derived specificity']
    edgeDF.columns = columns
    edgeDF.sort_values(by=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster'], ascending=False).to_csv(edgeDFFileName, columns=columns, index=False)
    
    writer = pd.ExcelWriter(adjMFileName, engine='xlsxwriter')
    readmeDict = {'colA':['README'],'colB':['']}
    readmeDict['colA'].append('Matrix 1')
    readmeDict['colB'].append('Specificity-based adjacency matrix')
    readmeDict['colA'].append('Matrix 2')
    readmeDict['colB'].append('Expression-based adjacency matrix')
    readmeDF = pd.DataFrame(readmeDict)
    readmeDF.to_excel(writer, sheet_name='README', index=False, header=False)
    adjSpecM.to_excel(writer, sheet_name='Matrix 1')
    adjM.to_excel(writer, sheet_name='Matrix 2')
    writer.save()
    
    with open(os.path.join(resultDir,'README.txt'), 'w') as file_object:
        file_object.write('README\n')
        file_object.write('\n')
        file_object.write('The cell-to-cell signaling database: %s\n' % signalType)
        file_object.write('The weight type of cell-to-cell signaling: %s\n' % weightType)
        file_object.write('Top edges to draw: %s\n' % keepTopEdge)
        file_object.write('\n')
        file_object.write('Expression threshold: %s\n' % weightThreshold)
        file_object.write('Specificity threshold: %s\n' % specificityThreshold)
        file_object.write('Detection threshold: %s\n' % frequencyThreshold)
        file_object.write('\n')
        file_object.write(readmeStr)

def MainLRNetwork(sourceFolder, signalType, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, ls, rs, plotFormat, layout, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance):
    # check if it is delta network
    originalFileName = os.path.join(sourceFolder, 'Edges_%s.csv' % (signalType))
    if os.path.exists(originalFileName):
        # load edge info
        edgeDF = pd.read_csv(os.path.join(sourceFolder, 'Edges_%s.csv' % (signalType)), index_col=None, header=0)
        # only keep edges of interest
        if weightType == 'mean':
            selectCols= ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand average expression value', 
            'Ligand derived specificity of average expression value', 'Receptor detection rate', 'Receptor average expression value', 
            'Receptor derived specificity of average expression value', 'Edge average expression weight', 'Edge average expression derived specificity']
        else:
            selectCols= ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand total expression value', 
            'Ligand derived specificity of total expression value', 'Receptor detection rate', 'Receptor total expression value', 
            'Receptor derived specificity of total expression value', 'Edge total expression weight', 'Edge total expression derived specificity']
        edgeDF = edgeDF.ix[:,selectCols]
        edgeDF.columns = ["sending cluster name", "ligand", "receptor", "target cluster name", "frequency ligand", "original ligand", "specified ligand", "frequency receptor", "original receptor", "specified receptor", "product of original", "product of specified"]
        edgeDF = edgeDF.ix[(edgeDF['product of specified']>specificityThreshold)&(edgeDF['original ligand']>weightThreshold)&(edgeDF['original receptor']>weightThreshold)&(edgeDF['frequency ligand']>frequencyThreshold)&(edgeDF['frequency receptor']>frequencyThreshold),]
        edgeDF['ligand'] = edgeDF['ligand'].astype(str)
        edgeDF['receptor'] = edgeDF['receptor'].astype(str)
        edgeDF = edgeDF.ix[(edgeDF['ligand']==ls) & (edgeDF['receptor']==rs),]
        # process node properties for single dataset
        clusterMapFilename = os.path.join(sourceFolder, 'ClusterMapping.csv')
        clusterMapDF = pd.read_csv(clusterMapFilename, index_col=None, header=0)
        clusterSizeDF = clusterMapDF.groupby('cluster').count()
        origlabels = [str(i) for i in clusterSizeDF.index]
        labels = [str(i)+'\n(%s cells)' % clusterSizeDF.ix[i,'cell'] for i in clusterSizeDF.index]
        cltSizes = [float(clusterSizeDF.ix[i,'cell']) for i in clusterSizeDF.index]
        print('#### %s edges are loaded' % len(edgeDF))
        if len(edgeDF) == 0:
            print('#### DONE')
            return
        
        #single-LR-based cluster to cluster weighted directed network
        resultDir = os.path.join(sourceFolder,'LRNetwork_%s-%s_exp_%s_spe_%s_det_%s_top_%s_signal_%s_weight_%s' % (ls,rs,weightThreshold,specificityThreshold,frequencyThreshold, keepTopEdge,signalType, weightType))
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        print('#### the folder "%s" has been created to save the analysis results' % os.path.abspath(resultDir))
        BuildSingleLRInterClusterNetwork(origlabels, labels, cltSizes, edgeDF, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, ls, rs, signalType, weightType, layout, plotFormat, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance, resultDir)
    print('#### DONE')
          
def DrawBipartieGraph(flag, readmeStr, curDF, sendCltLabel, targetCltLabel, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance, resultDir, signalType, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, dataType):
    
    # prepare lr edges.
    curDF['ligand'] = curDF['ligand'].astype(str)
    curDF['receptor'] = curDF['receptor'].astype(str)
    curDF['cellligand'] = curDF['sending cluster name'] + curDF['target cluster name'] + "->" + curDF['ligand']
    curDF['cellreceptor'] = curDF['sending cluster name'] + curDF['target cluster name'] + "->" + curDF['receptor']
    curDF['cellpair'] = curDF['sending cluster name'] + curDF['target cluster name']
    
    # for expression
    if keepTopEdge > 0:
        if dataType == '':
            curDFE = curDF.sort_values(by=['product of original'], ascending=False).head(keepTopEdge)
        else:
            curDFE = curDF.sort_values(by=['delta weight'], ascending=False).head(keepTopEdge)
    else:
        curDFE = curDF
    ligandSetE = sorted(list(set(curDFE['cellligand'])))
    receptorSetE = sorted(list(set(curDFE['cellreceptor'])))
    cellpairSetE = sorted(list(set(curDFE['cellpair'])))
    # lr node position
    ligandSetE = ['send:'+i for i in ligandSetE]
    receptorSetE = ['target:'+i for i in receptorSetE]
    vlE = (ligandSetE+receptorSetE)
    vtlE = [False]*len(ligandSetE) + [True]*len(receptorSetE)
    elE = []
    for idx in curDFE.index:
        elE.append((vlE.index('send:'+curDFE.ix[idx, 'sending cluster name'] + curDFE.ix[idx, 'target cluster name'] + "->" + curDFE.ix[idx, 'ligand']),vlE.index('target:'+curDFE.ix[idx, 'sending cluster name'] + curDFE.ix[idx, 'target cluster name'] + "->" +curDFE.ix[idx, 'receptor'])))
    gE = ig.Graph.Bipartite(vtlE, elE, directed = True)
    gE.vs["name"] = vlE
    pos_listE = gE.layout('bipartite').coords
    posDictE = {}
    for vIdx in range(len(vlE)):
        posDictE[vlE[vIdx]] = [pos_listE[vIdx][1],pos_listE[vIdx][0]*clusterDistance/2]
    newLYS = posDictE[receptorSetE[0]][0]
    newRYS = posDictE[ligandSetE[0]][0]*2*clusterDistance
    for li in ligandSetE:
        posDictE[li][0] = newLYS
    for ri in receptorSetE:
        posDictE[ri][0] = newRYS
        
    # for specificity
    if keepTopEdge > 0:
        if dataType == '':
            curDFS = curDF.sort_values(by=['product of specified'], ascending=False).head(keepTopEdge)
        else:
            curDFS = curDF.sort_values(by=['delta specificity'], ascending=False).head(keepTopEdge)
    else:
        curDFS = curDF
    ligandSetS = sorted(list(set(curDFS['cellligand'])))
    receptorSetS = sorted(list(set(curDFS['cellreceptor'])))
    cellpairSetS = sorted(list(set(curDFS['cellpair'])))
    # lr node position
    ligandSetS = ['send:'+i for i in ligandSetS]
    receptorSetS = ['target:'+i for i in receptorSetS]
    vlS = (ligandSetS+receptorSetS)
    vtlS = [False]*len(ligandSetS) + [True]*len(receptorSetS)
    elS = []
    for idx in curDFS.index:
        elS.append((vlS.index('send:'+curDFS.ix[idx, 'sending cluster name'] + curDFS.ix[idx, 'target cluster name'] + "->" + curDFS.ix[idx, 'ligand']),vlS.index('target:'+curDFS.ix[idx, 'sending cluster name'] + curDFS.ix[idx, 'target cluster name'] + "->" +curDFS.ix[idx, 'receptor'])))
    gS = ig.Graph.Bipartite(vtlS, elS, directed = True)
    gS.vs["name"] = vlS
    pos_listS = gS.layout('bipartite').coords
    posDictS = {}
    for vIdx in range(len(vlS)):
        posDictS[vlS[vIdx]] = [pos_listS[vIdx][1],pos_listS[vIdx][0]*clusterDistance/2]
    newLYS = posDictS[receptorSetS[0]][0]
    newRYS = posDictS[ligandSetS[0]][0]*2*clusterDistance
    for li in ligandSetS:
        posDictS[li][0] = newLYS
    for ri in receptorSetS:
        posDictS[ri][0] = newRYS
    
    #adjacency matrix
    adjM = pd.DataFrame(0.0, index=ligandSetE+receptorSetE, columns=ligandSetE+receptorSetE)
    adjSpecM = pd.DataFrame(0.0, index=ligandSetS+receptorSetS, columns=ligandSetS+receptorSetS)
    if dataType == '':
        for idx in curDFE.index:
            adjM.ix['send:'+curDFE.ix[idx, 'cellligand'], 'target:'+curDFE.ix[idx, 'cellreceptor']] += curDFE.ix[idx, 'product of original']
        for idx in curDFS.index:
            adjSpecM.ix['send:'+curDFS.ix[idx, 'cellligand'], 'target:'+curDFS.ix[idx, 'cellreceptor']] += curDFS.ix[idx, 'product of specified']
    else:
        for idx in curDFE.index:
            adjM.ix['send:'+curDFE.ix[idx, 'cellligand'], 'target:'+curDFE.ix[idx, 'cellreceptor']] += curDFE.ix[idx, 'delta weight']
        for idx in curDFS.index:
            adjSpecM.ix['send:'+curDFS.ix[idx, 'cellligand'], 'target:'+curDFS.ix[idx, 'cellreceptor']] += curDFS.ix[idx, 'delta specificity']
    
    #to graphviz format
    nxgW = nx.MultiDiGraph(adjM)
    nxgS = nx.MultiDiGraph(adjSpecM)
    nxgW = nx.nx_agraph.to_agraph(nxgW)
    nxgS = nx.nx_agraph.to_agraph(nxgS)
    
    #edge color
    edgeCount = adjM.astype(bool).sum().sum()
    edgecolors = sns.hls_palette(n_colors=edgeCount).as_hex()
    import random
    random.seed(0)
    random.shuffle(edgecolors)
    
    #draw weight based bipartie graph
    # draw whole network
    nxgW.graph_attr.update(fontname = "Arial")
    nxgW.graph_attr.update(fontsize = fontSize)
    nxgW.graph_attr.update(rankdir = "LR")
    nxgW.graph_attr.update(margin = 0)
    nxgW.graph_attr.update(label='Edge weight: product of expression levels\n%s' % (flag))
    nxgW.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    
    #set nodes
    nxgW.node_attr['style']='rounded,filled,setlinewidth(0)'
    for nd in nxgW.nodes():
        nd.attr['fontname'] = "Arial"
        nd.attr['fontsize'] = fontSize
        nd.attr['width'] = 0.13*fontSize
        nd.attr['height'] = 0.03*fontSize
        nd.attr['pos'] = '%s,-%s!' % (posDictE[str(nd)][0],posDictE[str(nd)][1])
        nd.attr['pin'] = 'true'
        nd.attr['fixedsize'] = 'true'
        nd.attr['shape'] = 'box'
        if 'send:' in str(nd):
            nd.attr['fillcolor'] = '#66ff0080'
            nd.attr['label'] = str(nd).split("->")[1]
        else:
            nd.attr['fillcolor'] = '#ff000080'
            nd.attr['label'] = str(nd).split("->")[1]
    #set node cluster:
    for cps in sorted(cellpairSetE):
        tcDF = curDF.ix[curDF['cellpair']==cps]
        lligandSet = sorted(list(set(tcDF['cellligand'])))
        rreceptorSet = sorted(list(set(tcDF['cellreceptor'])))
    
        lligandSet = ['send:'+i for i in lligandSet]
        rreceptorSet = ['target:'+i for i in rreceptorSet]
        nxgW.add_subgraph(lligandSet, name='cluster_Sending Clusters:'+cps, margin=3)
        nxgW.add_subgraph(rreceptorSet, name='cluster_Target Clusters:'+cps, margin=3)
        
    #set edges
    maxVal = adjM.max().max()
    idx = 0 
    for ed in nxgW.edges():
        sn = ed[0]
        tn = ed[1]
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(edgecolors[idx])]
        ed.attr['color'] = matplotlib.colors.to_hex(newcol)
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            ed.attr['label'] = '%.3f' % (adjM.ix[sn, tn])
        else:
            if adjM.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjM.ix[sn, tn]*edgeWidth/maxVal)
        idx += 1
        
    if dataType == '':
        plotFileName = 'From_%s_to_%s_exp.%s' % (sendCltLabel[0:sendCltLabel.rfind(' (')].replace('|','_'), targetCltLabel[0:targetCltLabel.rfind(' (')].replace('|','_'), plotFormat)
        readmeStr += 'From_%s_to_%s.%s_exp: the ligand-receptor pairs from "%s" to "%s" whose edge weights are products of expression levels.\n' % (sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')], plotFormat, sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')])
    else:
        plotFileName = '%s_from_%s_to_%s_exp.%s' % (dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0], plotFormat)
        readmeStr += '%s_from_%s_to_%s_exp.%s: the %s ligand-receptor pairs from "%s" to "%s" whose edge weights are products of expression levels.\n' % (dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0], plotFormat, dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0])
    
    plotFileName = os.path.join(resultDir, plotFileName)
    nxgW.draw(plotFileName,prog='neato')
    
    #draw specificity based bipartie graph
    # draw whole network
    nxgS.graph_attr.update(fontname = "Arial")
    nxgS.graph_attr.update(fontsize = fontSize)
    nxgS.graph_attr.update(rankdir = "LR")
    nxgS.graph_attr.update(margin = 0)
    nxgS.graph_attr.update(label='Edge weight: product of specificities\n%s' % (flag))
    nxgS.graph_attr.update(size = "%s,%s" % (plotWidth, plotHeight))
    
    #set nodes
    nxgS.node_attr['style']='rounded,filled,setlinewidth(0)'
    for nd in nxgS.nodes():
        nd.attr['fontname'] = "Arial"
        nd.attr['fontsize'] = fontSize
        nd.attr['width'] = 0.13*fontSize
        nd.attr['height'] = 0.03*fontSize
        nd.attr['pos'] = '%s,-%s!' % (posDictS[str(nd)][0],posDictS[str(nd)][1])
        nd.attr['pin'] = 'true'
        nd.attr['fixedsize'] = 'true'
        nd.attr['shape'] = 'box'
        if 'send:' in str(nd):
            nd.attr['fillcolor'] = '#66ff0080'
            nd.attr['label'] = str(nd).split("->")[1]
        else:
            nd.attr['fillcolor'] = '#ff000080'
            nd.attr['label'] = str(nd).split("->")[1]
    #set node cluster:
    for cps in sorted(cellpairSetS):
        tcDF = curDF.ix[curDF['cellpair']==cps]
        lligandSet = sorted(list(set(tcDF['cellligand'])))
        rreceptorSet = sorted(list(set(tcDF['cellreceptor'])))
    
        lligandSet = ['send:'+i for i in lligandSet]
        rreceptorSet = ['target:'+i for i in rreceptorSet]
        nxgW.add_subgraph(lligandSet, name='cluster_Sending Clusters:'+cps, margin=3)
        nxgW.add_subgraph(rreceptorSet, name='cluster_Target Clusters:'+cps, margin=3)
        
    #set edges
    maxVal = adjSpecM.max().max()
    idx = 0 
    for ed in nxgS.edges():
        sn = ed[0]
        tn = ed[1]
        newcol = [i+0.5*(1-i) for i in matplotlib.colors.to_rgb(edgecolors[idx])]
        ed.attr['color'] = matplotlib.colors.to_hex(newcol)
        if edgeWidth == 0:
            ed.attr['fontsize'] = fontSize
            ed.attr['fontname'] = "Arial"
            ed.attr['label'] = '%.3f' % (adjSpecM.ix[sn, tn])
        else:
            if adjSpecM.ix[sn, tn]*edgeWidth/maxVal < 1:
                ed.attr['penwidth'] = 1
            else:
                ed.attr['penwidth'] = int(adjSpecM.ix[sn, tn]*edgeWidth/maxVal)
        idx += 1
        
    if dataType == '':
        plotFileName = 'From_%s_to_%s_spe.%s' % (sendCltLabel[0:sendCltLabel.rfind(' (')].replace('|','_'), targetCltLabel[0:targetCltLabel.rfind(' (')].replace('|','_'), plotFormat)
        readmeStr += 'From_%s_to_%s.%s_spe: the ligand-receptor pairs from "%s" to "%s" whose edge weights are products of specificities.\n' % (sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')], plotFormat, sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')])
    else:
        plotFileName = '%s_from_%s_to_%s_spe.%s' % (dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0], plotFormat)
        readmeStr += '%s_from_%s_to_%s_spe.%s: the %s ligand-receptor pairs from "%s" to "%s" whose edge weights are products of specificities.\n' % (dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0], plotFormat, dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0])
    plotFileName = os.path.join(resultDir, plotFileName)
    nxgS.draw(plotFileName,prog='neato')
    
    #save edges
    if dataType == '':
        curDF = curDF.sort_values(by=['product of specified'],ascending=[False])
        dataFileName = 'From_%s_to_%s_edges.csv' % (sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')])
        dataFileName = dataFileName.replace('|','_')
        readmeStr += 'From_%s_to_%s_edges.csv: all filtered edges from "%s" to "%s".\n' % (sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')], sendCltLabel[0:sendCltLabel.rfind(' (')], targetCltLabel[0:targetCltLabel.rfind(' (')])
        if weightType == 'mean':
            columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand average expression value', 
                'Ligand derived specificity of average expression value', 'Receptor detection rate', 'Receptor average expression value', 
                'Receptor derived specificity of average expression value', 'Edge average expression weight', 'Edge average expression derived specificity']
        else:
            columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand total expression value', 
                'Ligand derived specificity of total expression value', 'Receptor detection rate', 'Receptor total expression value', 
                'Receptor derived specificity of total expression value', 'Edge total expression weight', 'Edge total expression derived specificity']
        oldcols = ["sending cluster name", "ligand", "receptor", "target cluster name", "frequency ligand", "original ligand", "specified ligand",
                   "frequency receptor", "original receptor", "specified receptor", "product of original", "product of specified"]
    else:
        curDF = curDF.sort_values(by=['delta specificity'],ascending=[False])
        dataFileName = '%s_from_%s_to_%s_edges.csv' % (dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0])
        readmeStr += '%s_from_%s_to_%s_edges.csv: all filtered %s edges from "%s" to "%s".\n' % (dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0], dataType, sendCltLabel.split('\n')[0], targetCltLabel.split('\n')[0])
        if weightType == 'mean':
            columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Delta ligand detection rate', 'Delta ligand average expression value', 
                'Delta ligand derived specificity of average expression value', 'Delta receptor detection rate', 'Delta receptor average expression value', 
                'Delta receptor derived specificity of average expression value', 'Edge delta average expression weight', 'Edge delta average expression derived specificity']
        else:
            columns=['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Delta ligand detection rate', 'Delta ligand total expression value', 
                'Delta ligand derived specificity of total expression value', 'Delta receptor detection rate', 'Delta receptor total expression value', 
                'Delta receptor derived specificity of total expression value', 'Edge delta total expression weight', 'Edge delta total expression derived specificity']
        oldcols = ['sending cluster name', 'ligand', 'receptor', 'target cluster name', 'delta ligand frequency', 'delta ligand expression', 'delta ligand specificity', 
                   'delta receptor frequency', 'delta receptor expression', 'delta receptor specificity', 'delta weight', 'delta specificity']
    dataFileName = os.path.join(resultDir, dataFileName)
    curDF = curDF.ix[:,oldcols]
    curDF.columns = columns
    curDF.to_csv(dataFileName, index=False, header=True, columns= columns)
    
    return readmeStr
    
def BuildInterClusterPlot(origlabels, labelDict, edgeDF, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance, resultDir, signalType, dataType = ''):
    readmeStr = '\n'
    
    for sendClt in origlabels:
        for targetClt in origlabels:
            flag = '%s -> %s' % (sendClt, targetClt)
            curDF = edgeDF.ix[(edgeDF['sending cluster name']==sendClt)&(edgeDF['target cluster name']==targetClt),]
            if dataType == '':
                curDF = curDF.sort_values(by=['product of specified'], ascending=False)
            else:
                curDF = curDF.sort_values(by=['delta specificity'], ascending=False)
            if len(curDF) > 0:
                print('#### plotting ligand-receptor pairs from "%s" to "%s"' % (sendClt, targetClt))
                readmeStr = DrawBipartieGraph(flag, readmeStr, curDF, labelDict[sendClt], labelDict[targetClt], plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance, resultDir, signalType, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, dataType)
            
    with open(os.path.join(resultDir,'README.txt'), 'w') as file_object:
        file_object.write('README\n')
        file_object.write('\n')
        file_object.write('The cell-to-cell signaling database: %s\n' % signalType)
        file_object.write('The weight type of cell-to-cell signaling: %s\n' % weightType)
        if keepTopEdge != 0:
            file_object.write('Top edges to draw: %s\n' % keepTopEdge)
        else:
            file_object.write('Top edges to draw: all\n')
        file_object.write('\n')
        file_object.write('Expression threshold: %s\n' % weightThreshold)
        file_object.write('Specificity threshold: %s\n' % specificityThreshold)
        file_object.write('Detection threshold: %s\n' % frequencyThreshold)
        file_object.write('\n')
        file_object.write(readmeStr)
    
def MainCltPair(sourceFolder, signalType, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance):
    # check if it is delta network
    originalFileName = os.path.join(sourceFolder, 'Edges_%s.csv' % (signalType))
    if os.path.exists(originalFileName):
        # load edge info
        edgeDF = pd.read_csv(os.path.join(sourceFolder, 'Edges_%s.csv' % (signalType)), index_col=None, header=0)
        # process node properties for single dataset
        clusterMapDF = pd.read_csv(os.path.join(sourceFolder, 'ClusterMapping.csv'), index_col=None, header=0)
        clusterSizeDF = clusterMapDF.groupby('cluster').count()
        origlabels = [str(i) for i in clusterSizeDF.index]
        labelDict = {}
        for i in clusterSizeDF.index:
            labelDict[str(i)] = str(i)+' (%s cells)' % clusterSizeDF.ix[i,'cell']
    
        # only keep edges of interest
        if weightType == 'mean':
            selectCols= ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand average expression value', 
            'Ligand derived specificity of average expression value', 'Receptor detection rate', 'Receptor average expression value', 
            'Receptor derived specificity of average expression value', 'Edge average expression weight', 'Edge average expression derived specificity']
        else:
            selectCols= ['Sending cluster', 'Ligand symbol', 'Receptor symbol', 'Target cluster', 'Ligand detection rate', 'Ligand total expression value', 
            'Ligand derived specificity of total expression value', 'Receptor detection rate', 'Receptor total expression value', 
            'Receptor derived specificity of total expression value', 'Edge total expression weight', 'Edge total expression derived specificity']
        edgeDF = edgeDF.ix[:,selectCols]
        edgeDF.columns = ["sending cluster name", "ligand", "receptor", "target cluster name", "frequency ligand", "original ligand", "specified ligand", "frequency receptor", "original receptor", "specified receptor", "product of original", "product of specified"]
        edgeDF = edgeDF.ix[(edgeDF['product of specified']>specificityThreshold)&(edgeDF['original ligand']>weightThreshold)&(edgeDF['original receptor']>weightThreshold)&(edgeDF['frequency ligand']>frequencyThreshold)&(edgeDF['frequency receptor']>frequencyThreshold),]
        print('#### %s edges are loaded' % len(edgeDF))
        if len(edgeDF) == 0:
            print('#### DONE')
            return
        
        #cluster to cluster edges
        resultDir = os.path.join(sourceFolder,'CltPair_exp_%s_spe_%s_det_%s_top_%s_signal_%s_weight_%s' % (weightThreshold,specificityThreshold,frequencyThreshold, keepTopEdge,signalType, weightType))
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        print('#### the folder "%s" has been created to save the analysis results' % os.path.abspath(resultDir))
        BuildInterClusterPlot(origlabels, labelDict, edgeDF, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance, resultDir, signalType)
        
    else:
        # process node properties for delta dataset
        sumClusterDF = pd.read_excel(os.path.join(sourceFolder, 'cluster_comparison.xlsx'), index_col=None, header=0)
        sumClusterDF['Cluster'] = sumClusterDF['Cluster'].astype(str)
        origlabels = sorted([str(i) for i in set(sumClusterDF['Cluster'])])
        labelDict = {}
        for clt in origlabels:
            cltDF = sumClusterDF.ix[sumClusterDF['Cluster'] == clt,].sort_values(by=['Population (cells)'])
            if len(cltDF) == 2:
                deltaSize = int(cltDF.iloc[1,1]) - int(cltDF.iloc[0,1])
            else:
                deltaSize = int(cltDF.iloc[0,1])
            labelDict[clt] = clt+' (%s cells)' % deltaSize
        
            if len(cltDF) == 2:
                refSize = sumClusterDF.ix[(sumClusterDF['Cluster'] == clt)&(sumClusterDF['Source'] == 'reference dataset'),'Population (cells)']
                tgtSize = sumClusterDF.ix[(sumClusterDF['Cluster'] == clt)&(sumClusterDF['Source'] == 'target dataset'),'Population (cells)']
                deltaSize = int(tgtSize) - int(refSize)
            else:
                deltaSize = int(cltDF.iloc[0,1])
                if cltDF.iloc[0,2] == 'reference dataset':
                    deltaSize = -1 * deltaSize
            if deltaSize > 0:
                labelDict[clt] = clt+'\n(+%s cells)' % deltaSize
            else:
                labelDict[clt] = clt+'\n(%s cells)' % deltaSize
        
        # load edge data and filter them based on the detection threshold
        dynamDict = FilterDeltaEdges(sourceFolder, signalType, weightType, frequencyThreshold)
        resultDir = os.path.join(sourceFolder,'Delta_CltPair_exp_%s_spe_%s_det_%s_top_%s_signal_%s_weight_%s' % (weightThreshold,specificityThreshold,frequencyThreshold,keepTopEdge,signalType, weightType))
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        print('#### the folder "%s" has been created to save the analysis results' % os.path.abspath(resultDir))
        for kind in dynamDict.keys():
            if kind == 'all':
                continue
            tempedgeDF = dynamDict[kind]
            #cluster to cluster edges
            print('#### plotting %s cluster-to-cluster interactions' % kind)
            BuildInterClusterPlot(origlabels, labelDict, tempedgeDF, weightType, specificityThreshold, weightThreshold, frequencyThreshold, keepTopEdge, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance, resultDir, signalType, kind)
    
    print('#### DONE')
        
        
#===================================================================#
#-------------------------------START-------------------------------#
#===================================================================#

if __name__ == '__main__':
    #process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--sourceFolder', required=True, help="the path to the folder of extracted edges from ExtractEdges.py or DiffEdges.py")
    parser.add_argument('--signalType', default='lrc2p', help='lrc2p (default) | lrc2as | the name of the ligand-receptor interaction database file without extension')
    parser.add_argument('--weightType', default='mean', help="mean (default) | sum, method to calculate the expression level of a ligand/receptor in a cell type")
    parser.add_argument('--specificityThreshold', type=float, default=0, help='do not draw the edges whose specificities are not greater than the threshold (default 0).')
    parser.add_argument('--expressionThreshold', type=float, default=0, help='do not draw the edges in which expression levels of the ligand and the receptor are not greater than the threshold (default 0).')
    parser.add_argument('--detectionThreshold', type=float, default=0.2, help='do not draw the interactions in which detection rates of the ligand and the receptor are lower than the threshold (default 0.2).')
    parser.add_argument('--keepTopEdge', type=int, default=0, help='only draw top n interactions that passed the thresholds (default 0 means all interactions that passed the thresholds will be drawn).')
    
    parser.add_argument('--plotWidth', type=int, default=12, help="resulting plot's width (default 12).")
    parser.add_argument('--plotHeight', type=int, default=10, help="resulting plot's height (default 10).")
    parser.add_argument('--plotFormat', default='pdf', help="pdf (default) | png | svg, format of the resulting plot(s)")
    parser.add_argument('--edgeWidth', type=float, default=0, help='maximum thickness of edges in the plot (default 0: edge weight is shown as a label around the edge).')
    parser.add_argument('--clusterDistance', type=float, default=1, help='relative distance between clusters (default value is 1; if clusterDistance >1, the distance will be increased, if clusterDistance >0 and clusterDistance <1, the distance will be decreased).')
    
    parser.add_argument('--drawClusterPair', default='n', help='n(o) (default) | y(es)')
    
    parser.add_argument('--layout', default='kk', help="kk (default) | circle | random | sphere; 'kk' stands for Kamada-Kawai force-directed algorithm")
    parser.add_argument('--fontSize', type=int, default=8, help='font size for node labels (default 8).')
    parser.add_argument('--maxClusterSize', type=int, default=0, help='maximum radius of the clusters (default 0: all clusters have identical radius).')
    
    parser.add_argument('--drawNetwork', default='y', help='y(es) (default) | n(o)')
    parser.add_argument('--drawLRNetwork', nargs='*', help="ligand and receptor's symbols")
    
    
    opt = parser.parse_args()
    
    #check sourceFolder
    if not os.path.exists(opt.sourceFolder):
        sys.exit("The source dataset's folder does not exist.")
        
    #check signalType
    signalType = os.path.basename(opt.signalType)
    if os.path.exists(os.path.join(opt.sourceFolder,'ClusterMapping.csv')):
        if not os.path.exists(os.path.join(opt.sourceFolder,'Edges_%s.csv' % opt.signalType)):
            sys.exit("Cannot find 'Edges_%s.csv' file in the speicified folder." % opt.signalType)
    elif not os.path.exists(os.path.join(opt.sourceFolder,'Delta_edges_%s' % opt.signalType)):
        sys.exit("Cannot find 'Delta_edges_%s' folder in the speicified folder." % opt.signalType)
        
    #check weightType
    avaWeightTypeList = ['mean', 'sum']
    if opt.weightType.lower() not in avaWeightTypeList:
        sys.exit("The weightType can only be 'mean' or 'sum'.")
    else:
        weightType = opt.weightType.lower()
        
    #check specificityThreshold
    if opt.specificityThreshold > 1.0 or opt.specificityThreshold < 0.0:
        specificityThreshold = 0.01
    else:
        specificityThreshold = opt.specificityThreshold
        
    #check expressionThreshold
    if opt.expressionThreshold < 0.0:
        weightThreshold = 0
    else:
        weightThreshold = opt.expressionThreshold
        
    #check detectionThreshold
    if opt.detectionThreshold < 0.0:
        detectionThreshold = 0
    else:
        detectionThreshold = opt.detectionThreshold
    
    #check keepTopEdge
    if opt.keepTopEdge < 0:
        keepTopEdge = 0
    else:
        keepTopEdge = opt.keepTopEdge
        
    #check plotformat
    avaFormatList = ["pdf", "png", "svg"]
    if opt.plotFormat.lower() not in avaFormatList:
        sys.exit("The given plot format is not permitted.")
    else:
        plotFormat = opt.plotFormat.lower()
    
    #check if draw network plot
    drawClusterPairStr = opt.drawClusterPair.lower()
    if drawClusterPairStr[0] == 'y':
        drawClusterPair = True
    elif drawClusterPairStr[0] == 'n':
        drawClusterPair = False
        
    drawNetworkPlotStr = opt.drawNetwork.lower()
    if drawNetworkPlotStr[0] == 'y':
        drawNetworkPlot = True
    elif drawNetworkPlotStr[0] == 'n':
        drawNetworkPlot = False
    else:
        sys.exit("drawNetwork parameter can only be 'y' or 'n'.")
        
    #check plot size
    if opt.plotWidth < 0:
        opt.plotWidth = 1
    else:
        plotWidth = opt.plotWidth
    if opt.plotHeight < 0:
        opt.plotHeight = 1
    else:
        plotHeight = opt.plotHeight
        
    #check edgeWidth
    if opt.edgeWidth < 0:
        edgeWidth = 0
    else:
        edgeWidth = opt.edgeWidth
        
    #check clusterDistance
    if opt.clusterDistance < 0:
        clusterDistance = -opt.clusterDistance
    else:
        clusterDistance = opt.clusterDistance
        
    #check fontSize
    if opt.fontSize < 0:
        fontSize = 1
    else:
        fontSize = opt.fontSize
        
    if drawClusterPair:
        #pass argument check, show input data
        print('===================================================')
        print('Input data:')
        print('The source dataset folder: %s' % opt.sourceFolder)
        print('The ligand-receptor interaction database: %s' % signalType)
        print('The weight type of cell-to-cell signaling: %s' % weightType)
        print('The detection threshold for interactions to draw is: %s' % detectionThreshold)
        print('The specicificity threshold for interactions to draw is: %s' % specificityThreshold)
        print('The expression threshold for interactions to draw is: %s' % weightThreshold)
        if keepTopEdge > 0:
            print('Top ligand-receptor pairs to draw is: %s' % keepTopEdge)
        print('The font size for cluster labels: %s' % fontSize)
        print('The edge width: %s' % edgeWidth)
        print('The relative distance between clusters: %s' % clusterDistance)
        print('The plot width: %s' % plotWidth)
        print('The plot height: %s' % plotHeight)
        print('The plot format: %s' % plotFormat)
        print('===================================================')
        print('#### start to construct ligand-receptor pairs between clusters')
        
        #start to construct ligand-receptor pairs between clusters
        MainCltPair(opt.sourceFolder, signalType, weightType, specificityThreshold, weightThreshold, detectionThreshold, keepTopEdge, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, clusterDistance)
    else:
            
        #check layout
        avaLayoutList = ['fr', 'drl', 'kk', 'lgl', 'random', 'rt', 'sphere', 'circle']
        if opt.layout.lower() not in avaLayoutList:
            sys.exit("The given layout is not permitted.")
        else:
            layout = opt.layout.lower()
        
        #check maxClusterSize
        if opt.maxClusterSize < 0:
            maxClusterSize = 0
        else:
            maxClusterSize = opt.maxClusterSize
            
        #check if draw single-LR network
        if opt.drawLRNetwork is not None:
            if len(opt.drawLRNetwork) != 2:
                sys.exit("drawLRNetwork can only accept one ligand-receptor pair.")
                
            #check if symbols are legal
            if os.path.exists(os.path.join(opt.sourceFolder, 'Edges_%s.csv' % (signalType))):
                edgeDF = pd.read_csv(os.path.join(opt.sourceFolder, 'Edges_%s.csv' % (signalType)), index_col=None, header=0)
                edgeDF['Ligand symbol'] = edgeDF['Ligand symbol'].astype(str)
                edgeDF['Receptor symbol'] = edgeDF['Receptor symbol'].astype(str)
                if len(edgeDF.ix[(edgeDF['Ligand symbol'] == opt.drawLRNetwork[0])&(edgeDF['Receptor symbol'] == opt.drawLRNetwork[1]),])>0:
                    ls = opt.drawLRNetwork[0]
                    rs = opt.drawLRNetwork[1]
                elif len(edgeDF.ix[(edgeDF['Ligand symbol'] == opt.drawLRNetwork[1])&(edgeDF['Receptor symbol'] == opt.drawLRNetwork[0]),])>0:
                    ls = opt.drawLRNetwork[1]
                    rs = opt.drawLRNetwork[0]
                else:
                    sys.exit("Cannot find %s-%s pair or %s-%s pair in the dataset." % (opt.drawLRNetwork[0], opt.drawLRNetwork[1], opt.drawLRNetwork[1], opt.drawLRNetwork[0]))
            
            #pass argument check, show input data
            print('===================================================')
            print('Input data:')
            print('Ligand: %s' % ls)
            print('Receptor: %s' % rs)
            print('The source dataset folder: %s' % opt.sourceFolder)
            print('The ligand-receptor interaction database: %s' % signalType)
            print('The weight type of cell-to-cell signaling: %s' % weightType)
            print('The detection threshold for interactions to draw is: %s' % detectionThreshold)
            print('The specicificity threshold for interactions to draw is: %s' % specificityThreshold)
            print('The expression threshold for interactions to draw is: %s' % weightThreshold)
            if keepTopEdge > 0:
                print('Top cluster-to-cluster edges to draw is: %s' % keepTopEdge)
            print('The network layout: %s' % layout)
            print('The font size for cluster labels: %s' % fontSize)
            print('The edge width: %s' % edgeWidth)
            print('The maximum radius of the clusters: %s' % maxClusterSize)
            print('The relative distance between clusters: %s' % clusterDistance)
            print('The plot width: %s' % plotWidth)
            print('The plot height: %s' % plotHeight)
            print('The plot format: %s' % plotFormat)
            print('===================================================')
            print('#### start to construct the %s-%s-mediated cell-to-cell communication network' % (ls,rs))
        
            #start to draw single-LR network
            MainLRNetwork(opt.sourceFolder, signalType, weightType, specificityThreshold, weightThreshold, detectionThreshold, keepTopEdge, ls, rs, plotFormat, layout, plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance)
            
        elif drawNetworkPlot:
            #pass argument check, show input data
            print('===================================================')
            print('Input data:')
            print('The source dataset folder: %s' % opt.sourceFolder)
            print('The ligand-receptor interaction database: %s' % signalType)
            print('The weight type of cell-to-cell signaling: %s' % weightType)
            print('The detection threshold for interactions to draw is: %s' % detectionThreshold)
            print('The specicificity threshold for interactions to draw is: %s' % specificityThreshold)
            print('The expression threshold for interactions to draw is: %s' % weightThreshold)
            if keepTopEdge > 0:
                print('Top cluster-to-cluster edges to draw is: %s' % keepTopEdge)
            print('The network layout: %s' % layout)
            print('The font size for cluster labels: %s' % fontSize)
            print('The edge width: %s' % edgeWidth)
            print('The maximum radius of the clusters: %s' % maxClusterSize)
            print('The relative distance between clusters: %s' % clusterDistance)
            print('The plot width: %s' % plotWidth)
            print('The plot height: %s' % plotHeight)
            print('The plot format: %s' % plotFormat)
            print('===================================================')
            print('#### start to construct the cell-to-cell communication network')
            
            #start to construct the cell-to-cell communication network
            MainNetwork(opt.sourceFolder, signalType, weightType, specificityThreshold, weightThreshold, detectionThreshold, keepTopEdge, layout, plotFormat,plotWidth, plotHeight, fontSize, edgeWidth, maxClusterSize, clusterDistance)
        else:
            sys.exit('Please check your equation parameters.')
            