import numpy
import matplotlib.pyplot as plt
import itertools
import os
import copy
from scipy.interpolate import interp1d

class margDistSCPP(object):
    """
    Wrapper for marinal distribution self confirming price predictions.
    
     There should be one tuple per good, that is
        len(self.data) == self.m
        NOTE:
            If bins are [1,2,3,4] then the first bin
            contains all values within the range [1,2)
            (including 1 excluding 2), [2,3) and 
            [3,4] notice the last bin edge is inclusive
    
    savePickle and loadPickle are inherited from the pointSCPP class
    
    Formats of txt files:
        for probability distributions;
            rows alternate probability distribution - bins
            e.g. row 1 is probability distribution for good 1
                 row 2 is bins for prob. in row 1
                 row 3 is probability distribution for good 2
                 row 4 is bins for prob. in row 2
                 
                 
        for histograms, it is the same pattern only replacing probabilities with integer counts.
    """
#    def __init__(self, margDistData = None):
    def __init__(self, *args, **kwargs):
        """
        marginalDistributionPrediction should be a list of size m of tuples
        each tuple specifies a normalized histogram count and bin edges
        """          
        # initialize as empty
        margDist = kwargs.get('margDist')
        m = kwargs.get('m')
        
        if margDist:
            if isinstance(margDist,numpy.ndarray):
                if self.validateData(margDistData=margDist):
                    self.data = margDist
                    if isinstance(margDist,list):
                        self.m = len(margDist)
                    else:
                        self.m = 1
            elif isinstance(margDist, str):
                filename, fileExt = os.path.splitext(margDist)
                if fileExt == '.pkl':
                    self.loadPickle(margDist)
                else:
                    raise ValueError('Unknown file type: {0}'.format(fileExt))
            elif isinstance(margDist, margDistSCPP):
                #will default to a deepcopy copy constructor...
                self.data = copy.deepcopy(margDist.data)
                self.m    = copy.deepcopy(margDist.m)
            else:
                raise ValueError('Uknown parameter type.')

        elif args:
            
            if isinstance(args[0],str):
                filename, fileExt = os.path.splitext(args[0])
                if fileExt == '.pkl':
                    self.loadPickle(args[0])
                else:
                    raise ValueError('Unknown file type: {0}'.format(fileExt))
                
            elif isinstance(args[0],margDistSCPP):
                self.data = copy.deepcopy(args[0].data)
                self.m    = copy.deepcopy(args[0].m)
                
            elif isinstance(args[0],list):
                self.validateData(args[0])
                self.data = args[0]
                self.m = len(args[0])
                
            elif isinstance(args[0],tuple):
                self.validateData(args[0])
                self.data = args[0]
                self.m = 1
#            elif isinstance(args[0],numpy.ndarray) or isinstance(args[0],list):
#                self.data = numpy.array(args[0])
#                self.m    = self.data.shape[0]
            else:
                raise ValueError('Unknown Value Type.')
        else:
            self.data = None
            self.m    = None
                
                
    @staticmethod
    def type():
        return "marginalDistributionSCPP"
    
    
    def expectedPrices(self,**kwargs):
        """
        Calculate the marginal expected price vector.
        
        By default will calculate the expected value as a sum of probabilities time
        bin centers
        
        iTsample will use the inverse transform sampling method to sample from the 
        distribution then the expected value will be computed as an average of these
        points
        
        Optional Inputs:
            kwargs['method'] = average or iTsample
            
            if kwargs['method'] == iTsample 
                the default number of samples is 8
            
            kwargs['nSamples'] the number of samples to use
                if kwargs['method'] == iTsample
        """
        
        method = kwargs.get('method','average')
                        
        if method == 'centerBinAverage':
            e = []
            for hist, binEdges in self.data:
                e.append(self.centerBinAvg(hist     = hist,
                                           binEdges = binEdges))
                
            return numpy.atleast_1d(e)
        
        if method == 'average':
            e = []
            for hist, binEdges in self.data:
                e.append(self.histAvg(hist     = hist,
                                      binEdges = binEdges))
                
            return numpy.atleast_1d(e)
        
        elif method == 'iTsample':
            
            nSamples = kwargs.get('nSamples',8)
                            
            samples = self.iTsample(nSamples=nSamples)
                
            #return the mean over marginal samples
            return numpy.mean(samples,0)
            
        else:
            print('margDistSCPP.expectedPrices()')
            print('Unknown method')
            raise AssertionError
    
    @staticmethod
    def histAvg(**kwargs):
        """
        Compute expected value of a histogram with out centering bins
        """
        hist     = kwargs.get('hist')
        if hist == None:
            raise KeyError("margDist.histAvg(...) - must provide histogram")
        
        binEdges = kwargs.get('binEdges')
        if binEdges == None:
            raise KeyError("margDist.binEdges(...) - must provide bin edges")
        
        p = hist / numpy.sum(hist*numpy.diff(binEdges),dtype=numpy.float)
        
        return numpy.dot(p,binEdges[:len(p)])
        
    @staticmethod
    def centerBinAvg(**kwargs):
        """
        A helper function for computing averages with a histogram
        take the value of a histogram bin to be equal to its center than 
        calculate the average as avg = \sum_i^n binCenter*prob(binCenter)
        
        Note:
            The histograms must be properly normalized.
        """
        hist     = kwargs['hist']
        binEdges = kwargs['binEdges']
        
        assert isinstance(hist,numpy.ndarray) or isinstance(binEdges,numpy.ndarray),\
            "hist and binEdges must be of type numpy.ndarray"
            
        numpy.testing.assert_almost_equal( numpy.sum(hist*numpy.diff(binEdges),dtype=numpy.float), 
                                           numpy.float(1.0) )
        
        numpy.testing.assert_equal( binEdges.shape[0], (hist.shape[0]+1) )
    
        return numpy.dot(hist, .5*(binEdges[:-1]+binEdges[1:]))
        
    def setPricePrediction(self, margDistData):
        if self.validateData(margDistData):
            self.data = margDistData
            
            if isinstance(margDistData,list):
                self.m = len(margDistData)
            else:
                self.m = 1
                
    @staticmethod
    def validateData(margDistData = None):
        assert isinstance(margDistData, list) or\
                isinstance(margDistData, tuple),\
                "{1} is not a list or tuple".format(margDistData)
        
        if isinstance(margDistData,list):
                      
            for hist,binEdges in margDistData:
                assert isinstance(hist,numpy.ndarray) and\
                        isinstance(binEdges,numpy.ndarray),\
                            "hist and binEdges must be numpy arrays."               
            
                numpy.testing.assert_almost_equal( 
                    numpy.sum(hist*numpy.diff(binEdges),dtype=numpy.float), 
                    numpy.float(1.0),
                    err_msg = "Marginal Distribution Data must be a valid PDF." )
                
        elif isinstance(margDistData,tuple):
            numpy.testing.assert_almost_equal(
                    numpy.sum( margDistData[0]*numpy.diff(margDistData[1]),dtype=numpy.float),
                    numpy.float(1.0),
                    err_msg = "Marginal Distribution Data must be a valid PDF." ) 
                                               
        # if you made it here you are good to go
        return True
    
    def margUps(self,**kwargs):
        """
        Will be in units of prices
        """
        expectedPrices = kwargs.get('expectedPrices',self.expectedPrices())
        
        return numpy.sqrt(self.margUpv(expectedPrices = expectedPrices))
    
    def margUpv(self,**kwargs):
        """
        Given a vector of marginal expected prices, computed either by sampling or
        arithmetically, calculate the upper partial 
        variance associated with each marginal distribution.
        
        will be in units of price**2
        """
        expectedPrices = kwargs.get('expectedPrices',self.expectedPrices())
        
        numpy.testing.assert_(expectedPrices.shape[0] == len(self.data), 
                              msg = "expectedPrice.shape[0] = {0} != len(self.data) = {1}".\
                              format(expectedPrices.shape[0],len(self.data)))
        
        upv = []
        for idx in range(expectedPrices.shape[0]):
            #get the prices
            binEdges = numpy.atleast_1d(self.data[idx][1])
            
            #get all bin indicies with prices greated than marginal expected value
            upperPriceIndicies = numpy.nonzero(binEdges>expectedPrices[idx])[0]
            
            #convert from indicies to prices
            upperPrices = numpy.atleast_1d(binEdges[upperPriceIndicies[:-1]])
            
            #the probability associated with each upper price
            upperPriceProb = numpy.atleast_1d(self.data[idx][0][upperPriceIndicies[:-1]])
            
            upv.append( numpy.sum( ((upperPrices-expectedPrices[idx])**2)*upperPriceProb ) )
            
        return numpy.array(upv)
    
    def bidPdf(self, *args, **kwargs):
        """
        Return the probability of winning each good given a bid vector
        
        Parameters
        ----------
        bids: numpy.ndarray
            The array of bids on each good
            
        interp: string [optional]
            A string indicating what type of interpolation to use.
        <kind> ::= 'linear' | 'nearest' | 'zero' | 'slinear' | 'quadratic' | 'cubic'
            
        Returns
        -------
        probBid: numpy.ndarray
            An array in which each element contains the probability that
            the bid is equal to the closing price Pr[closing price = bid]
            
        Note, the bid vector must be the same length as the number of
        marginal distributions (bids.shape[0] = self.m)
        """
        bids = None
        kind = kwargs.get('kind','linear')
        
        if not args:
            bids = numpy.atleast_1d(kwargs.get('bids'))
            if bids.shape[0] == 0:
                raise AssertionError('Must specify bid vector.')
        else:
            bids = args[0]
            
        numpy.testing.assert_(isinstance(bids,numpy.ndarray) or
                              isinstance(bids,list),
                              msg="bids must be a list or numpy.ndarray")
        
        if isinstance(bids,numpy.ndarray):
            numpy.testing.assert_equal(bids.shape[0],self.m)
        else:
            numpy.testing.assert_equal(len(bids),self.m)
        
        probBid = numpy.zeros(self.m)
        for i, margData in enumerate(self.data):
            hist, binEdges = margData 
            # assume that the histogram probabilities represent the center of the bins
            # and interpolate between them
            binCenters = .5*(binEdges[:-1]+binEdges[1:])
            interpObj = interp1d(binCenters, hist, kind)
            try:
                probBid[i] = interpObj(bids[i])
            #extend the bounds of the histogram
            except ValueError:
                if bids[i] > binCenters[-2]:
                    probBid[i]= hist[-1]
                elif bids[i] < binCenters[0]:
                    probBid[i] = hist[0]
                else:
                    raise ValueError('Unknown Boundary Condition Reached.')
            
        return probBid
    
    def bidCdf(self, *args, **kwargs):
        """
        Return the marginal cdf values for each given bid. that is
        Pr[closing price[i] <= bid[i]]
        
        Parameters
        ----------
        bids: numpy.ndarray
            The array of bids on each good
            
        interp: string [optional]
            A string indicating what type of interpolation to use.
            Default = 'linear'
            cubic may yeild negative values (bad for probabilities)
            lienar is the safest
        <interp> ::= 'linear' | 'nearest' | 'zero' | 'slinear' | 'quadratic' | 'cubic'
            
        Returns
        -------
        cdfBid: numpy.ndarray
            An array in which each element contains the probability that
            the bid is equal to the closing price Pr[closing price = bid]
            
        Note, the bid vector must be the same length as the number of
        marginal distributions (bids.shape[0] = self.m)
        """
        bids = None
        kind = kwargs.get('kind','linear')
    
        if not args:
            bids = kwargs.get(bids)
            if not bids:
                raise AssertionError('Must specify bid vector.')
        else:
            bids = args[0]
            
        numpy.testing.assert_(isinstance(bids,numpy.ndarray) or
                              isinstance(bids,list),
                              msg="bids must be a list or numpy.ndarray")
        if isinstance(bids,numpy.ndarray):
            numpy.testing.assert_equal(bids.shape[0],self.m)
        else:
            numpy.testing.assert_equal(len(bids),self.m)
        
        cdfBid = numpy.zeros(self.m)
        for i, margData in enumerate(self.data):
            
            hist, binEdges = margData
            if bids[i] > binEdges[-1]:
                cdfBid[i] = 1.0
            elif bids[i] < binEdges[0]:
                cdfBid[i] = 0.0
            else:
                cdf = numpy.cumsum( hist*numpy.diff(binEdges),
                                    dtype=numpy.float )
                
                f = interp1d(binEdges, numpy.hstack((0,cdf)), kind)
                cdfBid[i] = f(bids[i])
            
        return cdfBid
    
    def margCdf(self, x, good, kind = 'linear'):
        
        cdf = None
        
        if isinstance(good,int):
            
            hist,binEdges = self.data[good]
                        
            p = hist / numpy.float(numpy.dot(hist, numpy.diff(binEdges)))
            
            c = numpy.cumsum(p*numpy.diff(binEdges), dtype=numpy.float)
            
            f = interp1d(binEdges, numpy.hstack((0,c)), kind)
            
            cdf = f(x)
            
            if cdf > 1.0:
                raise ValueError("margDistScpp.margCdf\n" +\
                                 "cdf = {0} > 1.0".format(cdf))
            elif cdf < 0.0:
                raise ValueError("margDistScpp.margCdf\n" +\
                                 "cdf = {0} < 0.0".format(cdf))
                
        elif isinstance(good,list):
            cdf = numpy.zeros(len(good))
            
            for i, g in enumerate(good):
                
                hist, binEdges = self.data[g]
                
                p = hist / numpy.float(numpy.dot(hist, numpy.diff(binEdges)))
            
                cdf[i] = numpy.cumsum(p*numpy.diff(binEdges), dtype=numpy.float)
                
                if cdf[i] > 1.0:
                    raise ValueError("margDistScpp.margCdf\n" +\
                                     "cdf = {0} > 1.0".format(cdf[i]))
                elif cdf[i] < 0.0:
                    raise ValueError("margDistScpp.margCdf\n" +\
                                     "cdf = {0} < 0.0".format(cdf[i]))
                    
        return cdf
    
    def pWin(self, bundle, bids):
        p = 1.0
        for goodIdx, good in enumerate(bundle):
            if good == True:
                p*=self.margCdf(bids[goodIdx], goodIdx)
            else:
                p*=(1-self.margCdf(bids[goodIdx], goodIdx))
        return p
                
    def eval(self, q, goodIdx, kind = 'linear'):
        hist, binEdges = self.data[goodIdx]
        
        p = hist/numpy.float(numpy.dot(hist,numpy.diff(binEdges)))
        binCenters = .5*(binEdges[:-1]+binEdges[1:])
        
        
        if q < binCenters[0]:
            return p[0]
            
        elif q > binCenters[-1]:
            return p[-1]
        else:
            pmf = interp1d(binCenters,p,kind)
            return pmf(q)
        
    def iTsample(self, **kwargs):
        """
        Kept for backwards-combatibility of function call.
        """
        return self.sample(n_samples = kwargs.get('nSamples',8))
    
    def sample(self,n_samples = 8):
#        n_samples = kwargs.get('n_samples')
        
        samples = numpy.zeros((n_samples,len(self.data)))
        
        for goodIdx in range(len(self.data)):
            hist,binEdges = self.data[goodIdx]
            
            p = hist / numpy.float( numpy.dot(hist, numpy.diff(binEdges)) )
            
            for sampIdx in range(n_samples):
                samples[sampIdx,goodIdx] = binEdges[numpy.random.multinomial(1,p).argmax()]
                
        return samples
    
    def graphPdf(self,**kwargs):
        """
        Function to plot the data using matplot lib
        """
        if 'colorStyles' in kwargs:
            numpy.testing.assert_(len(kwargs['colorStyles']), len(self.data))
            colorStyles = kwargs['colorStyles']
        else:
            #pick some random styles
            colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
            lineStyles = ['-', '--', '-.', ':']
            markerStyles = ['o', 'v', '^', '<', '>', 's', 'p', '*', 'h', 'H', 'x', '+', 'D']
            
            colorStyles = [j[0] + j[1] for j in itertools.product(markerStyles,[i[0] + i[1] for i in itertools.product(colors,lineStyles)])]
            numpy.random.shuffle(colorStyles)
            colorStyles = colorStyles[:len(self.data)]
            
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        for i in range(len(self.data)):
            ax.plot(.5*(self.data[i][1][:-1]+self.data[i][1][1:]),self.data[i][0],colorStyles[i],label='Slot {0}'.format(i))
            
        if 'xlabel' in kwargs:
            plt.xlabel(kwargs['xlabel'])
        else:
            plt.xlabel('Prices')
            
        if 'ylabel' in kwargs:
            plt.ylabel(kwargs['ylabel'])
        else:
            plt.ylabel('Probability')
        
        if 'title' in kwargs:
            plt.title(kwargs['title'])
        else:
            plt.title('Price Distribution')
            
        plt.legend()
        if 'filename' in kwargs:
            plt.savefig(kwargs['filename'])
        else:
            plt.show()
        
    def graphCdf(self,**kwargs):
        if 'colorStyles' in kwargs:
            numpy.testing.assert_(len(kwargs['colorStyles']), len(self.data))
            colorStyles = kwargs['colorStyles']
        else:
            #pick some random styles
            colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
            lineStyles = ['-', '--', '-.', ':']
            markerStyles = ['o', 'v', '^', '<', '>', 's', 'p', '*', 'h', 'H', 'x', '+', 'D']
            colorStyles = [j[0] + j[1] for j in itertools.product(markerStyles,[i[0] + i[1] for i in itertools.product(colors,lineStyles)])]
            numpy.random.shuffle(colorStyles)
            colorStyles = colorStyles[:len(self.data)]
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        for i in range(len(self.data)):
            ax.plot(.5*(self.data[i][1][:-1]+self.data[i][1][1:]),numpy.cumsum(self.data[i][0]),colorStyles[i],label='Slot {0}'.format(i))
            
        if 'xlabel' in kwargs:
            plt.xlabel(kwargs['xlabel'])
        else:
            plt.xlabel('Prices')
            
        if 'ylabel' in kwargs:
            plt.ylabel(kwargs['ylabel'])
        else:
            plt.ylabel('Probability')
                   
        plt.legend()
        
        plt.show()
                 
    def graphPdfToFile(self,**kwargs):
        filename = kwargs.get('fname')
        if 'colorStyles' in kwargs:
            numpy.testing.assert_(len(kwargs['colorStyles']), len(self.data))
            colorStyles = kwargs['colorStyles']
        else:
            #pick some random colors
            cmap = plt.cm.get_cmap('hsv')
            colorStyles = [cmap(i) for i in numpy.linspace(0,0.9,len(self.data))]
            
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        for i in range(len(self.data)):
            ax.plot(.5*(self.data[i][1][:-1]+self.data[i][1][1:]),self.data[i][0],c=colorStyles[i],label='Good {0}'.format(i))
            
        if 'xlabel' in kwargs:
            plt.xlabel(kwargs['xlabel'])
        else:
            plt.xlabel('Prices')
            
        if 'ylabel' in kwargs:
            plt.ylabel(kwargs['ylabel'])
        else:
            plt.ylabel('Probability')
        
        if 'title' in kwargs:
            plt.title(kwargs['title'])
        else:
            plt.title('Price Distribution')
            
        leg = ax.legend(loc='best',fancybox=True)
        leg.get_frame().set_alpha(0.5)
        
        if filename is None:
            plt.show()
        else:
            plt.savefig(filename)
            
        plt.close()
        
    def savetxt(self,filename):
        with open(filename,'w') as f:
            for d in self.data:
                numpy.savetxt(f,d[0],newline=" ")
                f.write("\n")
                numpy.savetxt(f,d[1],newline=" ")
                f.write("\n")
                
    def loadWellmanCsv(self,filename):
        filename = os.path.realpath(filename)
        allCounts = numpy.loadtxt(filename,delimiter=",",dtype=numpy.float)
        self.m = allCounts.shape[0]
        maxPrice = allCounts.shape[1]
        self.data = []
        for margCounts in allCounts:
            self.data.append( (margCounts / numpy.sum(margCounts,dtype=numpy.float), 
                               numpy.arange(0,maxPrice+1)) )
            
            
        
            
        