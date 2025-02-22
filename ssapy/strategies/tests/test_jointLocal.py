import unittest
import numpy

from ssapy.strategies.jointLocal import jointLocalUpdate , jointLocal
from ssapy import listBundles, msListRevenue

class test_jointLocalBid(unittest.TestCase):
    def setUp(self):
        self.samples2d = numpy.atleast_2d([[1,1],   [20,3], [10,7], [15,5],
                                           [10,30], [15,26],[17,33], [2,40],
                                           [30,30], [27,42],[30,38], [29,40],
                                           [42,20], [38,7], [40,15], [33,10]])
        
        self.bundles2d = listBundles(2)
        self.l2d = 1
        self.v2d = [20,10] 
        self.revenue2d = msListRevenue(self.bundles2d, self.v2d, self.l2d)
        
    def test_jointLocalUpdate(self):
        ibids = [25.,25.]
        print(ibids)
        targetBid = 0
        ibids[targetBid] = \
            jointLocalUpdate(self.bundles2d, self.revenue2d, 
                             ibids,targetBid, 
                             self.samples2d, True)

        print(ibids)

    def test_jointLocal1(self):
        """
        Updates computed by hand given:
        v = [45,20], l = 1
        p(q_1 = 20) = 0.5 
        p(q_1 = 30) = 0.5
        p(q_2 = 15) = 0.2
        p(q_2 = 20) =  0.8
        
        Under independent prices p(q_1,q_2) = p(q_1)p(q_2)
        Hence:
        p(q_1 = 20, q_2 = 15) = 0.1
        p(q_1 = 20, q_2 = 20) = 0.4
        p(q_1 = 30, q_2 = 15) = 0.1
        p(q_1 = 30, q_2 = 20) = 0.4
        
        The joint pdf is represented with 1000 samples. 
        100 samples of [20,15]
        400 samples of [20,20]
        100 samples of [30,15]
        400 samples of [30,20]
        
        Ground Truth Anwers:
        Starting at [25,25]
        1.1) b1 <- 25
        1.2) b2 <- 10
        2.1) b1 <- 45
        2.2) b2 <- 0
        3.1) b1 <- 25
        3.2) b2 <- 0
        
        Therefore, starting at [25,25] converges to [45,0] after 3 iterations
        """
        samples = numpy.zeros((1000,2))
        samples[:100,:] = numpy.asarray([20,15])
        samples[100:500,:] = numpy.asarray([20,20])
        samples[500:600,:] = numpy.asarray([30,15])
        samples[600:,:] = numpy.asarray([30,20])
        
        m=2
        l = 1
        v = [45,20]
        bundles = listBundles(m)
        revenue = msListRevenue(bundles, v, l)
        bids = numpy.asarray([25.,25.])

        bids[0] = jointLocalUpdate(bundles,revenue,bids,0,samples,True)
        numpy.testing.assert_equal(bids[0], 25, "Update 1.1 Failed", True)
                
        bids[1] = jointLocalUpdate(bundles,revenue,bids,1,samples,True)
        numpy.testing.assert_equal(bids[1], 10, "Update 1.2 Failed", True )
                
        bids[0] = jointLocalUpdate(bundles,revenue,bids,0,samples,True)
        numpy.testing.assert_equal(bids[0], 45, "Update 2.1 Failed", True)
                
        bids[1] = jointLocalUpdate(bundles,revenue,bids,1,samples,True)
        numpy.testing.assert_equal(bids[1], 0, "Update 2.2 Failed", True)
                
        bids[0] = jointLocalUpdate(bundles,revenue,bids,0,samples,True)
        numpy.testing.assert_equal(bids[0], 45, "Update 3.1 Failed", True)
                
        bids[1] = jointLocalUpdate(bundles,revenue,bids,1,samples,True)
        numpy.testing.assert_equal(bids[1], 0, "Update 3.2 Failed", True)
        
        #should converge after 3 iterations
        bids = numpy.asarray([25.,25.])
        
        bids, converged, itr, tol = jointLocal(bundles, revenue, bids, samples, ret = 'all')
        
        numpy.testing.assert_array_equal(bids, numpy.asarray([45,0]), "margLocal bids test failed", True)
        
        numpy.testing.assert_equal(converged, True, "margLocal converged failed", True)
        
        numpy.testing.assert_equal(itr,3,"margLocal number of iterations failed.", True)
        
        numpy.testing.assert_almost_equal(tol, 0., 8, "margLocal tol failed", True)
        

if __name__ == "__main__":
    unittest.main()