# Copyright 2014 the National Renewable Energy Laboratory

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
This class contains a structure to store hydrodynamic data from WAMTI,
AQWA, Nemoh, or another code that calculates hydrodynamic coefficients
and excitation forces

Author: Michael Lawson, Yi-Hsiang Yu, Carlos Michelen
'''

import numpy as np

import os

import matplotlib.pyplot as plt

from scipy import interpolate

from scipy.linalg import hankel, expm

from progressbar import ProgressBar, Bar, Percentage

class Raw(object):
    '''
    Empty class to store raw data
    '''
    def __init__(self):
        pass


class HydrodynamicCoefficients(object):
    '''Hydrodynamic coefficients
    '''
    def __init__(self):
        self.irf             = ImpulseResponseFunction()
        self.ss              = StateSpaceRealization()

class ImpulseResponseFunction(object):
    '''Impulse response function data
    '''
    def __init__(self):
        pass

class StateSpaceRealization(object):
    '''State space realization data
    '''
    def __init__(self):
        pass

class HydrodynamicData(object):
    '''Hydrodynamic data from BEM simulations
    '''

    def __init__(self):
        # Default values
        self.rho            = 1000.
        self.g              = 9.81
        self.wave_dir       = 0.
        self.num_bodies     = 0     
                     
        # np.array([])     
        self.cg             = 'not_defined'                          
        self.cb             = 'not_defined'                           
        self.k              = 'not_defined'                           
        self.T              = 'not_defined'                                                       
        self.w              = 'not_defined'                     
        
        # np.floats()
        self.wp_area        = 'not_defined'                             
        self.buoy_force     = 'not_defined'     
        self.disp_vol       = 'not_defined'                         
        self.water_depth    = 'not_defined'                           
        self.body_num       = 'not_defined'                    
        
        # strings
        self.name            = 'not_defined'
        self.bem_code        = 'not_defined'
        self.bem_raw_data    = 'not_defined'

        # objects
        self.am              = HydrodynamicCoefficients()    
        self.rd              = HydrodynamicCoefficients()  
        self.ex              = HydrodynamicCoefficients()  
        self.rao             = HydrodynamicCoefficients()
        self.ssy             = HydrodynamicCoefficients()
        
        
    def __repr__(self):
        '''Custom output
        '''
        out_string = 'Body name: ' + str(self.name) + \
            '\n    Body number: ' + str(self.body_num) +\
            '\n    Total number of bodies: ' + str(self.num_bodies) + \
            '\n    Displaced volume (m^3): ' + str(self.disp_vol) + \
            '\n    Center of gravity (m): ' + str(self.cg) + \
            '\n    Center of buoyancy (m): ' + str(self.cb)
        return out_string


    def calc_irf_excitation(self, t_length=100.0, n_t = 1001, n_w=1001):
        '''Function to calculate the excitation impulse response function
        '''
        self.ex.irf.t = np.linspace(-t_length,t_length,n_t)
        self.ex.irf.w = np.linspace(np.min(self.w),np.max(self.w),n_w)

        self.ex.irf.f = np.zeros([self.ex.mag.shape[0], self.ex.mag.shape[1], self.ex.irf.t.size])

        ex_re_interp = np.zeros([self.ex.mag.shape[0], self.ex.mag.shape[1], self.ex.irf.w.size ])
        ex_im_interp = np.zeros([self.ex.mag.shape[0], self.ex.mag.shape[1], self.ex.irf.w.size ])

        # Interpolate the radiation damping matrix for the IRF calculation
        flip = False

        if self.w[0] > self.w[1]:

            w_tmp = np.flipud(self.w)
            flip = True

        else:

            w_tmp = self.w

        for i in xrange(self.ex.mag.shape[0]):

            for j in xrange(self.ex.mag.shape[1]):

                if flip is True:

                    ex_tmp_re = np.flipud(self.ex.re[i, j, :])
                    ex_tmp_im = np.flipud(self.rd.im[i, j, :])

                else:

                    ex_tmp_re = self.ex.re[i,j,:]
                    ex_tmp_im = self.ex.im[i,j,:]


                f_re = interpolate.interp1d(x=w_tmp, y=ex_tmp_re)
                f_im = interpolate.interp1d(x=w_tmp, y=ex_tmp_im)
                ex_re_interp[i,j,:] = f_re(self.ex.irf.w)
                ex_im_interp[i,j,:] = f_im(self.ex.irf.w)

        pbar_maxval = self.ex.irf.t.size*self.ex.mag.shape[0]*self.ex.mag.shape[1]
        pbar = ProgressBar(widgets=['Calculating the excitation force impulse response function for ' + self.name + ':',Percentage(), Bar()], maxval=pbar_maxval).start()
        count = 1
        for t_ind, t in enumerate(self.ex.irf.t):

            for i in xrange(self.ex.mag.shape[0]):

                for j in xrange(self.ex.mag.shape[1]):
                    tmp = ex_re_interp[i,j,:]*np.cos(self.ex.irf.w*t) - ex_im_interp[i,j,:]*np.sin(self.ex.irf.w*t)
                    tmp *= 1.0/np.pi
                    self.ex.irf.f[i,j,t_ind] = np.trapz(y=tmp,x=self.ex.irf.w)
                    pbar.update(count)
                    count += 1

        pbar.finish()

    def calc_ss_excitation(self, t_end=100, n_t = 1001, n_w=1001):
        raise Exception('The calc_ss_excitation function is not yet implemented')

    def calc_irf_radiation(self, t_end=100, n_t = 1001, n_w=1001):
        '''Function to calculate the wave radiation impulse response function
        '''

        self.rd.irf.t = np.linspace(0,t_end,n_t)
        self.rd.irf.w = np.linspace(np.min(self.w),np.max(self.w),n_w)

        self.rd.irf.L = np.zeros( [ self.am.inf.shape[0],self.am.inf.shape[1],self.rd.irf.t.size ] )
        self.rd.irf.K = np.zeros( [ self.am.inf.shape[0],self.am.inf.shape[1],self.rd.irf.t.size ] )

        rd_interp = np.zeros( [ self.rd.all.shape[0], self.rd.all.shape[1], self.rd.irf.w.size ])

        # Interpolate the radiation damping matrix for the IRF calculation
        flip = False

        if self.w[0] > self.w[1]:

            w_tmp = np.flipud(self.w)
            flip = True

        else:

            w_tmp = self.w

        for i in xrange(self.rd.all.shape[0]):

            for j in xrange(self.rd.all.shape[1]):

                if flip is True:

                    rdTmp = np.flipud(self.rd.all[i,j,:])

                else:
                    rdTmp = self.rd.all[i,j,:]

                f = interpolate.interp1d(x=w_tmp, y=rdTmp)
                rd_interp[i,j,:] = f(self.rd.irf.w) 

        # Calculate the IRF
        pbar = ProgressBar(widgets=['Calculating the radiation damping impulse response function for ' + self.name + ':',Percentage(), Bar()], maxval=np.size(self.rd.irf.t)*self.rd.all.shape[0]*self.rd.all.shape[1]).start()
        count = 1
        for t_ind, t in enumerate(self.rd.irf.t):

            for i in xrange(self.rd.all.shape[0]):

                for j in xrange(self.rd.all.shape[1]):
                    # Radiation damping calculation method
                    tmpL = 2./np.pi*rd_interp[i,j,:]*np.sin(self.rd.irf.w*t)
                    tmpK = 2./np.pi*rd_interp[i,j,:]*np.cos(self.rd.irf.w*t)
                    self.rd.irf.K[i,j,t_ind] = np.trapz(y=tmpK,x=self.rd.irf.w)
                    self.rd.irf.L[i,j,t_ind] = np.trapz(y=tmpL,x=self.rd.irf.w)
                    pbar.update(count)
                    count += 1

        pbar.finish()

    def calc_ss_radiation(self, max_order=10, r2_thresh=0.95 ):
        '''Function to calculate state space realization
        
        Inputs:
        Kr       - impulse response function
        ss_max    - maximum order of the state space realization
        R2Thresh - R2 threshold that must be met either by the R2 value for K_{r}
        dt       - time step used for the sampling frequency of the impulse response function

        Outputs:
        Ass - time-invariant state matrix
        Bss - time-invariant input matrix
        Css - time-invariant output matrix
        Dss - time-invariant feedthrough matrix
        k_ss_est - Impusle response function as cacluated from state space approximation
        status - status of the realization, 0 - zero hydrodynamic coefficients
        1 - state space realization meets R2 threshold
        2 - state space realization does not
        meet R2 threshold and at ss_max limit
               
        [Ass,Bss,Css,Dss,Krest,status]       
        SS_TD(bodyTemp.hydroForce.irkb(:,ii,jj),simu.ss_max,simu.R2Thresh,simu.dt)
        '''
        dt                  = self.rd.irf.t[2]-self.rd.irf.t[1]
        numFreq             = np.size(self.rd.irf.t) 
        r2bt                = np.zeros( [ self.am.inf.shape[0],self.am.inf.shape[0],numFreq] )
        k_ss_est            = np.zeros( numFreq )
        self.rd.ss.irk_bss     = np.zeros( [ self.am.inf.shape[0],self.am.inf.shape[0],numFreq] )
        self.rd.ss.A           = np.zeros([6,self.am.inf.shape[1],max_order,max_order])
        self.rd.ss.B           = np.zeros([6,self.am.inf.shape[1],max_order,1])
        self.rd.ss.C           = np.zeros([6,self.am.inf.shape[1],1,max_order])
        self.rd.ss.D           = np.zeros([6,self.am.inf.shape[1],1])
        self.rd.ss.irk_bss     = np.zeros([6,self.am.inf.shape[1],numFreq])
        self.rd.ss.rad_conv    = np.zeros([6,self.am.inf.shape[1]])
        self.rd.ss.it          = np.zeros([6,self.am.inf.shape[1]])
        self.rd.ss.r2t         = np.zeros([6,self.am.inf.shape[1]])
        
        pbar = ProgressBar(widgets=['Calculating radiation damping state space coefficients for ' + self.name + ':',Percentage(), Bar()], maxval=self.am.inf.shape[0]*self.am.inf.shape[1]).start()
        count = 0
        for i in xrange(self.am.inf.shape[0]):

            for j in xrange(self.am.inf.shape[1]):

                r2bt = np.linalg.norm(self.rd.irf.K[i,j,:]-self.rd.irf.K.mean(axis=2)[i,j])
                
                ss = 2 #Initial state space order

                if r2bt != 0.0:
                    while True:
                        
                        #Perform Hankel Singular Value Decomposition
                        y=dt*self.rd.irf.K[i,j,:]                    
                        h=hankel(y[1::])
                        u,svh,v=np.linalg.svd(h)
                        
                        u1 = u[0:numFreq-2,0:ss]
                        v1 = v.T[0:numFreq-2,0:ss]
                        u2 = u[1:numFreq-1,0:ss]
                        sqs = np.sqrt(svh[0:ss].reshape(ss,1))
                        invss = 1/sqs
                        ubar = np.dot(u1.T,u2)

                        a = ubar*np.dot(invss,sqs.T)
                        b = v1[0,:].reshape(ss,1)*sqs
                        c = u1[0,:].reshape(1,ss)*sqs.T
                        d = y[0]        

                        CoeA = dt/2
                        CoeB = 1
                        CoeC = -CoeA
                        CoeD = 1

                        iidd = np.linalg.inv(CoeA*np.eye(ss)-CoeC*a)               #(T/2*I + T/2*A)^{-1}         = 2/T(I + A)^{-1}
                        
                        ac = np.dot(CoeB*a-CoeD*np.eye(ss),iidd)                   #(A-I)2/T(I + A)^{-1}         = 2/T(A-I)(I + A)^{-1}
                        bc = (CoeA*CoeB-CoeC*CoeD)*np.dot(iidd,b)                  #(T/2+T/2)*2/T(I + A)^{-1}B   = 2(I + A)^{-1}B
                        cc = np.dot(c,iidd)                                        #C * 2/T(I + A)^{-1}          = 2/T(I + A)^{-1}
                        dc = d + CoeC*np.dot(np.dot(c,iidd),b)                     #D - T/2C (2/T(I + A)^{-1})B  = D - C(I + A)^{-1})B

                        for jj in xrange(numFreq):

                            k_ss_est[jj] = np.dot(np.dot(cc,expm(ac*dt*jj)),bc)    #Calculate impulse response function from state space approximation
      
                        R2TT = np.linalg.norm(self.rd.irf.K[i,j,:]-k_ss_est)          #Calculate 2 norm of the difference between know and estimated values impulse response function
                        R2T = 1 - np.square(R2TT/r2bt)                             #Calculate the R2 value for impulse response function

                        if R2T >= r2_thresh:                                       #Check to see if threshold for the impulse response is meet
                        
                            status = 1                                             #%Set status
                            break
                        
                        if ss == max_order:                                        #Check to see if limit on the state space order has been reached
                        
                            status = 2                                             #%Set status
                            break
                        
                        ss=ss+1                                                    #Increase state space order
                                            
                    self.rd.ss.A[i,j,0:ac.shape[0],0:ac.shape[0]]  = ac
                    self.rd.ss.B[i,j,0:bc.shape[0],0                ]  = bc[:,0]
                    self.rd.ss.C[i,j,0                ,0:cc.shape[1]]  = cc[0,:]
                    self.rd.ss.D[i,j]                                      = dc
                    self.rd.ss.irk_bss[i,j,:]  = k_ss_est
                    self.rd.ss.rad_conv[i,j] = status
                    self.rd.ss.r2t[i,j] = R2T
                    self.rd.ss.it[i,j] = ss

                count += 1
                pbar.update(count)

        pbar.finish()
        
    def plot_irf_rdiation(self,components):
        '''
        Function to plot the IRF

        Inputs:
        components -- A list of components to plot. E.g [[0,0],[1,1],[2,2]]
        
        Outputs:
        None -- A plot is displayed. The plt.show() command may need to be used
        depending on your python env settings
        '''  
        
        f, ax = plt.subplots(components.shape[0], sharex=True, figsize=(8,10))
                
        # Plot added mass and damping
        for i,comp in enumerate(components):
            
            x = comp[0]
            y = comp[1]
            t = self.rd.irf.t
            L = self.rd.irf.L[x,y,:]
            K = self.rd.irf.K[x,y,:]

            ax[i].set_ylabel('comp ' + str(x) + ',' + str(y))

            ax[i].plot(t,L,label='L')
            ax[i].plot(t,K,label='K ddt(L)')
                  
        ax[0].set_title('IRF for ' + str(self.name))
        ax[0].legend()
        ax[i].set_xlabel('Time (s)')
        

    def plot_am_rd(self,components):
        '''
        Function to plot the added mass and radiation damping coefficients

        Inputs:
        components -- A list of components to plot. E.g [[0,0],[1,1],[2,2]]
        
        Outputs:
        None -- A plot is displayed. The plt.show() command may need to be used
        depending on your python env settings
        '''                        
        
        f, ax = plt.subplots(2, sharex=True, figsize=(8,10))
        
        # Frame 0 - added mass
        ax[0].plot()
        ax[0].set_title('Hydrodynamic coefficients for ' + str(self.name))    
        ax[0].set_ylabel('Added mass')
        
        # Frame 1 - radiation damping
        ax[1].plot()
        ax[1].set_xlabel('Wave frequency (rad/s)')
        ax[1].set_ylabel('Radiation damping')
        
        # Plot added mass and damping
        for i,comp in enumerate(components):
            
            x = comp[0]
            y = comp[1]
            w = self.w
            rd = self.rd.all[x,y,:]
            am = self.am.all[x,y,:]

            ax[0].plot(w,am,'x-',label='Component (' + str(x) + ', ' + str(y) + ')')
            ax[1].plot(w,rd,'x-',label='Component (' + str(x) + ', ' + str(y) + ')')
            
        # Show legend on frame 0
        ax[0].legend(loc=0)

    def plot_excitation(self,components):
        '''
        Function to plot wave excitation coefficients
        
        Inputs:
        components -- A list of components to plot. E.g [0,1,2,5]
        
        Outputs:
        None -- A plot is displayed. The plt.show() command may need to be used
        depending on your python env settings
        '''
        
        f, ax = plt.subplots(4, sharex=True,figsize=(8,10))

        # Frame 0 - magnitude
        ax[0].plot()
        ax[0].set_ylabel('Ex force - mag')
        ax[0].set_title('Excitation force for ' + str(self.name))    

        # Frame 1 - phase
        ax[1].plot()        
        ax[1].set_xlabel('Wave frequency (rad/s)')        
        ax[1].set_ylabel('Ex force - phase')

        # Frame 2 - real
        ax[2].plot()
        ax[2].set_ylabel('Ex force - real')
        
        # Frame 3 - imaginary
        ax[3].plot()
        ax[3].set_ylabel('Ex force - imaginary')
        
        for i,comp in enumerate(components):
            
            m = comp
            w = self.w
            re = self.ex.re[:,m]
            im = self.ex.im[:,m]
            mag = self.ex.mag[:,m]
            phase = self.ex.phase[:,m]

            ax[0].plot(w,mag,'x-',label='Component (' + str(m+1) + ')')
            ax[1].plot(w,phase,'x-',label='Component (' + str(m+1) + ')')
            ax[2].plot(w,re,'x-',label='Component (' + str(m+1) + ')')
            ax[3].plot(w,im,'x-',label='Component (' + str(m+1) + ')')

            ax[0].legend(loc=0)

def generate_file_names(out_file):
    '''
    Function to generate filenames needed by hydroData module

    Inputs:
    outFile -- Name of hydrodynamic data file

    Outputs:
    files -- a dictionary of file generate_file_names
    '''
    out_file = os.path.abspath(out_file)
    (path,file) = os.path.split(out_file)
 
    files = {}
    files['out'] = os.path.join(path,file)
    files['hdf5'] = os.path.join(path,file[0:-4] + '.h5')
    files['pickle'] = os.path.join(path,file[0:-4] + '.p')

    return files
