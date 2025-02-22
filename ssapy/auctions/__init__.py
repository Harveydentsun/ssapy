__all__ = ["auctionBase", "simultaneousAuction"]

from ssapy.agents.agentFactory import agentFactory

import multiprocessing
import numpy

def collectBids(agentList):
    
    bids = [agent.bid() for agent in agentList]
    return numpy.atleast_2d(bids)

def simAuctionHelper(**kwargs):
    agentType = kwargs.get('agentType')
        
    if isinstance(agentType,list):
        nAgents = len(agentType)
        
    elif isinstance(agentType,str):
        nAgents   = kwargs.get('nAgents',8)
        agentType = [agentType]*nAgents
    
    nGames          = kwargs.get('nGames')
        
    pricePrediction = kwargs.get('pricePrediction')
        
    m            = kwargs.get('m',5)
    minValuation = kwargs.get('minValuation',0)
    maxValuation = kwargs.get('maxValuation',50)
    
    verbose      = kwargs.get('verbose', False)

    retType      = kwargs.get('retType','bids')
    
    l            = kwargs.get('l')
    
    if retType == 'hob':
        selfIdx  = kwargs.get('selfIdx')
        if selfIdx == None:
            raise ValueError("ERROR - simulateAuction(...):\n" + \
                             "\t Must specify selfIdx when retType == 'hob'")
            
    if verbose:
        print('In simulateAuction(...)')
        print('agentType    = {0}'.format(agentType))
        print('nGames       = {0}'.format(nGames))
        print('m            = {0}'.format(m))
        print('minValuation = {0}'.format(minValuation))
        print('maxValuation = {0}'.format(maxValuation))
        print('retType      = {0}'.format(retType))

    if retType == 'bids':
        ret = numpy.zeros((nGames,nAgents,m))
    elif retType == 'firstPrice' or retType == 'hob':
        ret = numpy.zeros((nGames,m))
    else:
        raise ValueError("simulateAuction - Unknown return type")
    
    agents = [agentFactory(agentType = atype, m = m, vmin = minValuation, vmax = maxValuation) for atype in agentType]
    
    for itr in range(nGames):
        if verbose:
            print('running serial game {0}'.format(itr))

        if retType == 'firstPrice' or retType == 'secondPrice' or retType == 'hob':
            gameBids = numpy.zeros((nAgents,m))   
        
        if isinstance(pricePrediction,list):  
             
            for agentIdx, agent, pp in zip(numpy.arange(nAgents),agents,pricePrediction):
                
                agent.randomValuation(l = l)     
                    
                if retType == 'bids':
                    ret[itr, agentIdx, :] = agent.bid(pricePrediction = pp)
                            
                elif retType == 'firstPrice' or retType == 'secondPrice' or retType == 'hob':
                    gameBids[agentIdx,:] = agent.bid(pricePrediction = pp)
                    
        else:
            for agentIdx, agent in enumerate(agents):
                
                agent.randomValuation(l=l)
                
                if retType == 'bids':
                    ret[itr, agentIdx, :] = agent.bid(pricePrediction = pricePrediction)
                    
                elif retType == 'firstPrice' or retType == 'secondPrice' or retType == 'hob':
                        gameBids[agentIdx,:] = agent.bid(pricePrediction = pricePrediction)
            
        if retType == 'firstPrice':
            ret[itr,:] = numpy.max(gameBids,0)
            
        elif retType == 'hob':
            
            ret[itr,:] = numpy.max( numpy.delete(gameBids,selfIdx,0), 0 )
            
        elif retType == 'secondPrice':
            for goodIdx in range(gameBids.shape[1]):
                goodBids = gameBids[:,m]
                goodArgMax = numpy.argmax(goodBids)
                ret[itr,goodIdx] = numpy.max(numpy.delete(goodBids,goodArgMax))
            
    return ret
        
        

def simulateAuction(**kwargs):
    """
    Function to run an auction with specified participants, randomizing over valuation.
    
    Parameters
    ----------
    
    agentType: string or list of strings, required
        A string or list of strings specifying participating strategies.
        
    nAgents: int, optional
        If agentType is a string then this specifies the number of replicant
        agents that will participate. Each will draw their own valuation instance.
    
    m: int, optional - default = 5
        Number of goods up for auction.
        
    minValuation: float, optional - default = 0
        Minimum allowable valuation for the scheduling game
        
    maxValuation: float, optional - default = 50
        Maximum allowable valuation for the scheduling game       
        
    nGames: int, required
        The number of auctions to run
        
    parallel: bool, optional - default = True
        To run auction simulations in parallel or not.
        
    nProc: int, optional - default = multiprocessing.cpu_count()
        Number of cores to use if parallel flag is set to true.
        
    pricePrediction: (point, margDist, jointGmm) or list thereof, required
        Price prediction or list of price predictions 
        ( 1 for each agent ) used in the simulation
        
    verbose: bool, optional - default = False
        Flag to output debug information to std out.
        
        
    retType: string, optional - default = 'bids'
        A string specifying output of simulation.
        
        'bids' -> output all bids from all agents for all games
            return ndarray.shape (nGames,nAgents,m)
        'firstPrice' -> output highest bids for each good for each game
            return ndarray.shape = (nGames,m)
        'secondPrice' -> output second highest bids for each good in each game
            return ndarray.shape = (nGames,m)
            
        'hob' -> output highest other agent bid in each game.
            This option requires the specification of selfIdx
            return ndarray.shape = (nGames,m)
            
    selfIdx: int, required if retType == 'hob'
        Index of agent considered to be self. Excluded from max bid calculation.
    """

    agentType = kwargs.get('agentType')
        
    if isinstance(agentType,list):
        nAgents = len(agentType)
        
    elif isinstance(agentType,str):
        nAgents   = kwargs.get('nAgents',8)
        agentType = [agentType]*nAgents
    
    nGames          = kwargs.get('nGames')
    parallel        = kwargs.get('parallel',True)
    if parallel:
        nProc       = kwargs.get('nProc', multiprocessing.cpu_count())
        
    pricePrediction = kwargs.get('pricePrediction')
        
    m            = kwargs.get('m',5)
    minValuation = kwargs.get('minValuation',0)
    maxValuation = kwargs.get('maxValuation',50)
    
    verbose      = kwargs.get('verbose', False)

    retType      = kwargs.get('retType','bids')
    
    #can specify lambad (1 = perfect substitutes, 5 = perfect complements)
    l            = kwargs.get('l') 
    
    if retType == 'hob':
        selfIdx  = kwargs.get('selfIdx')
        if selfIdx == None:
            raise ValueError("ERROR - simulateAuction(...):\n" + \
                             "\t Must specify selfIdx when retType == 'hob'")
    
    if verbose:
        print('In simulateAuction(...)')
        print('agentType    = {0}'.format(agentType))
        print('nGames       = {0}'.format(nGames))
        print('parallel     = {0}'.format(parallel))
        if parallel:
            print('nProc    = {0}'.format(nProc))
        print('m            = {0}'.format(m))
        print('minValuation = {0}'.format(minValuation))
        print('maxValuation = {0}'.format(maxValuation))
        print('retType      = {0}'.format(retType))
        print('l            = {0}'.format(l))

    ret = []
    if parallel:
        pool = multiprocessing.Pool(nProc)
        
        nGameList = [nGames//nProc]*nProc
        nGameList[-1] += (nGames % nProc)
        
        if verbose:
            print('Running parallel simulation.')
            print('Number of cores = {0}'.format(nProc))
            print('Number of simulations per core = {0}'.format(nGameList))
            print('Total Number of simulations = {0}'.format((sum(nGameList))))

        results = []
        
        for p in range(nProc):
            subArgs = {}
            subArgs.update(kwargs)
            subArgs['parallel'] = False
            subArgs['nGames'] = nGameList[p]
            subArgs['verbose'] = False
                 
            results.append(pool.apply_async(simAuctionHelper, kwds = subArgs))

        pool.close()
        pool.join()
            

        for idx, r in enumerate(results):
            if idx == 0:
                ret = r.get()
            else:                
                ret = numpy.concatenate((ret,r.get()))
            r._value = []
            

            
    else:
        ret = simAuctionHelper(**kwargs)
        
    return ret               