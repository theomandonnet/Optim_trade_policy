""" Optimize french trade policy
"""
#%%
from calendar import c
import numpy as np
from numpy.core.einsumfunc import _greedy_path
import matplotlib.pyplot as plt
import scipy.optimize as sco
from scipy.stats import norm
import json
import cvxpy as cp
import pandas as pd


data_countries=pd.read_excel("List_Countries.xlsx")
trois_blocs = ['Europe', 'Northern Am.', 'Asia']
liste_europe = np.array(data_countries.loc[:,'Europe'])
liste_am = np.array(data_countries.loc[:,'America'])
liste_asia = np.array(data_countries.loc[:,'Asia'])


create_little_json =False
if create_little_json:
    f = open('List_Emi.json')
    list_emi = json.load(f)
    f.close()

    f = open('List_ChinaEmi.json')
    list_chinaemi = json.load(f)
    f.close()

    f=open('GDP_data.json')
    GDP_data = json.load(f)
    f.close()


sources = ['CEPII','OECD','IIASA','PIK']
ssps = ['SSP1','SSP2','SSP3','SSP4','SSP5']
reg_list=[]
if create_little_json:
    for r in list(list_emi['CEPII']['SSP1'].keys()):
        if r in ['OtherAnnex1', 'OtherEmerging', 'OtherOil', 'RestOfWorld', 'LEA', 'LENA','Transport', 'WorldOther','Int. Aviation','Int. Shipping',]:
            continue
        list_gdp = [[GDP_data[source][s][r]["2030"] for source in sources] for s in ssps]
        if np.min(list_gdp)!=0.:
            reg_list.append(r)

def moy_gdp(ssp,country):
    res = []
    for source in sources:
        res.append(GDP_data[source][ssp][country]["2030"])
    return np.mean(res)

if create_little_json:
    dict_world_gdp_2030 = {}
    for ssp in ssps:
        ssp_parsource={}
        for source in sources:
            gdpworld=0
            for r in reg_list:
                gdpworld+= np.mean(GDP_data[source][ssp][r]["2030"])
            ssp_parsource[source]=gdpworld
        dict_world_gdp_2030[ssp]=ssp_parsource
    dict_world_gdp={'2015':75230,'2030':dict_world_gdp_2030}
    json1=json.dumps(dict_world_gdp)
    f = open("data_opti/GDP_World.json","w")
    f.write(json1)
    f.close()


if create_little_json:
    my_dict={}
    for s in range(len(ssps)):
        inner = {}
        for source in sources:
            inner[source] = GDP_data[source]["SSP{}".format(s+1)]["France"]["2030"]
        my_dict["SSP{}".format(s+1)] = inner
    json1 = json.dumps(my_dict)
    f = open("data_opti/GDP_France.json","w")
    f.write(json1)
    f.close()

    for r in reg_list:
        if r in list(GDP_data["CEPII"]["SSP1"].keys()):
            my_dict={}
            for s in range(len(ssps)):
                inner={}
                list_emi_pays = []
                for source in sources:
                    gdp = GDP_data[source]["SSP{}".format(s+1)][r]["2030"]
                    myints=list(np.array(list_emi[source]["SSP{}".format(s+1)][r]['GHGtot']["2030"])/gdp)
                    inner[source]=np.mean(myints)
                    list_emi_pays+=myints
                mu,sigma = norm.fit(list_emi_pays)
                inner["distrib norm"] = [mu, sigma]
                my_dict["SSP{}".format(s+1)] = inner                
            json1 = json.dumps(my_dict)
            f = open("data_opti/Emi_"+r+".json","w")
            f.write(json1)
            f.close()
            print(r)
if create_little_json:
    gdpUE=0
    emiUE=0
    gdpAm=0
    emiAm=0
    gdpAs=0
    emiAs=0
    dictUE={}
    dictAm={}
    dictAs={}
    for s in range(5):
        innerUE={}
        innerAm={}
        innerAs={}
        gdp_UE={}
        gdp_Am={}
        gdp_As={}
        for source in sources:
            for r in reg_list:
                if r in list(GDP_data["CEPII"]["SSP1"].keys()):
                    intensr = np.array(list_emi[source]["SSP{}".format(s+1)][r]['GHGtot']["2030"])
                    gdpr =  GDP_data[source]["SSP{}".format(s+1)][r]["2030"]
                    
                    if r in liste_europe:
                        gdpUE+= gdpr
                        emiUE+= np.mean(intensr)
                    if r in liste_am:
                        gdpAm+=  gdpr
                        emiAm+= np.mean(intensr)
                    if r in liste_asia:
                        gdpAs+=  gdpr
                        emiAs+= np.mean(intensr)
            gdp_UE[source]=gdpUE
            gdp_Am[source]=gdpAm
            gdp_As[source]=gdpAs
            innerUE[source]=emiUE/gdpUE
            innerAm[source]=emiAm/gdpAm
            innerAs[source]=emiAs/gdpAs
        dictUE["SSP{}".format(s+1)] = innerUE
        dictAm["SSP{}".format(s+1)] = innerAm
        dictAs["SSP{}".format(s+1)] = innerAs
    distribemissionsUE = np.zeros((5,4*len(intensr)))
    distribemissionsAm = np.zeros((5,4*len(intensr)))
    distribemissionsAs = np.zeros((5,4*len(intensr)))
    for r in reg_list:
        if r in list(GDP_data["CEPII"]["SSP1"].keys()):
            for s in range(5):
                emiralssources=[]
                for source in sources:
                    emir = np.array(list_emi[source]["SSP{}".format(s+1)][r]['GHGtot']["2030"])
                    emiralssources+=list(emir)
                if r in liste_europe:
                    distribemissionsUE[s,:]+=np.array(emiralssources)/np.mean([gdp_UE[source] for source in sources])
                if r in liste_am:
                    distribemissionsAm[s,:]+=np.array(emiralssources)/np.mean([gdp_Am[source] for source in sources])
                if r in liste_asia:
                    distribemissionsAs[s,:]+=np.array(emiralssources)/np.mean([gdp_As[source] for source in sources])
    for s in range(5):
        mu,sigma = norm.fit(distribemissionsUE[s])
        dictUE["SSP{}".format(s+1)]["distrib norm"] = [mu, sigma]
        mu,sigma = norm.fit(distribemissionsAm[s])
        dictAm["SSP{}".format(s+1)]["distrib norm"] = [mu, sigma]
        mu,sigma = norm.fit(distribemissionsAs[s])
        dictAs["SSP{}".format(s+1)]["distrib norm"] = [mu, sigma]

    json1 = json.dumps(dictUE)
    f = open("data_opti/Emi_UE.json","w")
    f.write(json1)
    f.close()
    json1 = json.dumps(dictAm)
    f = open("data_opti/Emi_America.json","w")
    f.write(json1)
    f.close()
    json1 = json.dumps(dictAs)
    f = open("data_opti/Emi_Asia.json","w")
    f.write(json1)
    f.close()


#######################################################################################################
# PARAMETRES
#######################################################################################################
#%%


reg_list = np.array(data_countries.loc[:,'Countries'])
nbreg = len(reg_list)

cible_EC = 249000 ## A modifier

f = open('data_opti/GDP_France.json')
gdp_france = json.load(f)
f.close()

f=open('data_opti/GDP_World.json')
dict_worldgdp = json.load(f)
f.close()


gdpFR = [[gdp_france["SSP{}".format(s+1)][source] for source in sources] for s in range(len(ssps))]
moy_intens = np.zeros((len(ssps),len(sources),nbreg))
distrib_intes = np.zeros((nbreg,len(ssps),2))

for s in range(len(ssps)):
    for r in range(nbreg):
        for source in range(len(sources)):
            f = open('data_opti/Emi_'+reg_list[r]+'.json')
            inte = json.load(f)[ssps[s]][sources[source]]
            moy_intens[s,source,r] = inte
            f.close()
        
        f = open('data_opti/Emi_'+reg_list[r]+'.json')
        dis = json.load(f)[ssps[s]]["distrib norm"]
        distrib_intes[r,s,:] = dis
        f.close()

moy_intens_blocs = np.zeros((len(ssps),len(sources),3))
distrib_intes_blocs = np.zeros((3,len(ssps),2))

blocs=['UE','America','Asia']
for bloc in range(3):
    f=open('data_opti/Emi_'+blocs[bloc]+'.json')
    my_dict=json.load(f)
    f.close()
    for s in range(len(ssps)):
        distrib_intes_blocs[bloc,s,:] = my_dict[ssps[s]]["distrib norm"]
        for source in range(len(sources)):
            moy_intens_blocs[s,source,bloc] = my_dict[ssps[s]][sources[source]]


# Pour la contrainte de capcacite d exportation
qactuel = np.array(data_countries.loc[:,'Share']/100)


qactuel_blocs = np.zeros(3)
for r in range(nbreg):
    if reg_list[r] in liste_europe:
        qactuel_blocs[0] += qactuel[r]
    if reg_list[r] in liste_am:
        qactuel_blocs[1] += qactuel[r]
    if reg_list[r] in liste_asia:
        qactuel_blocs[2] += qactuel[r]
    
print(qactuel_blocs)
pct_exportmax = 0.6
qmax = (1+ pct_exportmax)*np.array(qactuel)
qmax_blocs = (1+ pct_exportmax)*np.array(qactuel_blocs)


###################################################################################################
# Méthode 2 : Par scenarios et avec formulation initiale
###################################################################################################
#%% CVXPY 2nd formulation
#construct the problem with the secon formulation :
def opti_scenar(num_reg,moyennes_intens):
    q = cp.Variable(num_reg,nonneg=True)
    constr = []
    pis = cp.Parameter()
    pis.value = 1/(len(ssps)*len(sources))
    crit = 0
    for s in range(len(ssps)):
        for source in range(len(sources)):
            croiss=(dict_worldgdp['2030']['SSP%s'%(s+1)][sources[source]]-dict_worldgdp['2015'])/dict_worldgdp['2015']
            prix_quot=(1+(croiss)) * 54
            prix_quot=250
            crit += pis.value*prix_quot*cp.pos(0.3*gdpFR[s][source]*moyennes_intens[s,source]@q-cible_EC)
    if num_reg==3:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= 0.7*qmax_blocs]
    else:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax]
    objective = cp.Minimize(crit)
    prob = cp.Problem(objective,constr)
    result = prob.solve(max_iters=1000)
    print("Solution CVXPY - Scénarios")
    print(q.value)
    print("Respect contrainte somme : %s"%(np.isclose(np.sum(q.value),1., rtol=1e-5, atol=1e-5)))
    print("Respect positivité : %s"%(q.value>=0.).all())
    print("Valeur objectif : %s"%objective.value)
    return q.value
q_opti_scenar = opti_scenar(3,moy_intens_blocs)
#q_opti_scenar = opti_scenar(nbreg,moy_intens)

###################################################################################################
# Méthode 3 : SSP pour GDP et distrib normale pour emi associée au SSP tiré
###################################################################################################
#%% Autre implementation de l'alea -> on a une distribution par SSP et le tirage d'un SSP 
# pour avoir un effet de tendance mondiale
# Avec une distribution normale des intensites pour chaque region
def opti_gauss(num_reg,distrib):
    q = cp.Variable(num_reg,nonneg=True)
    constr = []
    M = 100
    crit = 0
    for i in range(M):
        s= np.random.randint(0,len(ssps))
        source_gdp = np.random.randint(0,len(sources))
        intens = np.array([np.random.normal(distrib[r,s,0],distrib[r,s,1]) for r in range(num_reg)])
        gdp_FR = gdpFR[s][source_gdp]/M
        croiss=(dict_worldgdp['2030']['SSP%s'%(s+1)][sources[source]]-dict_worldgdp['2015'])/dict_worldgdp['2015']
        prix_quot=(1+(croiss)) * 54
        prix_quot=250
         
        crit += cp.pos(0.3*gdp_FR*intens@q-cible_EC/M) * prix_quot
    if num_reg==3:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax_blocs]
    else:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax]
    objective = cp.Minimize(crit)
    prob = cp.Problem(objective,constr)
    result = prob.solve(max_iters=1000)
    print("Solution CVXPY - Gaussiennes")
    print(q.value)
    print("Respect contrainte somme : %s"%(np.isclose(np.sum(q.value),1., rtol=1e-5, atol=1e-5)))
    print("Respect positivité : %s"%(q.value>=0.).all())
    print("Valeur objectif : %s"%objective.value)
    return q.value
#q_opti = opti_gauss(nbreg,distrib_intes)
q_opti = opti_gauss(3,distrib_intes_blocs)
###################################################################################################
# Optimisation dans le cas d'un futur connu - SSP connu et intensite = moyenne de la distrib gaussienne
###################################################################################################
def solution_pb_deterministe(num_reg,moyennes,s=0,source_gdp=2,verbose=False):
    q = cp.Variable(num_reg,nonneg=True)
    constr = []
    intens = moyennes[s,source_gdp] #emissions connues
    gdp_FR = gdpFR[s][source_gdp] #pib connu
    croiss=(dict_worldgdp['2030']['SSP%s'%(s+1)][sources[source]]-dict_worldgdp['2015'])/dict_worldgdp['2015']
    prix_quot=(1+(croiss)) * 54
    prix_quot=250
    crit = prix_quot*cp.pos(0.3*gdp_FR*intens@q-cible_EC)
    if num_reg==3:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax_blocs]
    else:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax]
    objective = cp.Minimize(crit)
    prob = cp.Problem(objective,constr)
    result = prob.solve(max_iters=1000)
    if verbose:
        print("Solution CVXPY - Cas déterministe - SSP %s - %s"%(ssps[s],sources[source_gdp]))
        print(q.value)
        print("Respect contrainte somme : %s"%(np.isclose(np.sum(q.value),1., rtol=1e-5, atol=1e-5)))
        print("Respect positivité : %s"%(q.value>=0.).all())
        print("Valeur objectif : %s"%objective.value)
    return q.value
q_deterministe = solution_pb_deterministe(3,moy_intens_blocs)
#q_deterministe = solution_pb_deterministe(nbreg,moy_intens)

################ 3D plots #####################################################################
#%%
parbloc=True
if parbloc:
    toutes_sol_determ = np.zeros((5,4,3))
    for s in range(len(ssps)):
        for source in range(len(sources)):
            toutes_sol_determ[s,source,:] = solution_pb_deterministe(3,moy_intens_blocs,s,source)

    xs = []
    ys = []
    zs = []
    for s in range(len(ssps)):
        for source in range(len(sources)):
            xs.append(toutes_sol_determ[s,source,0])
            ys.append(toutes_sol_determ[s,source,1])
            zs.append(toutes_sol_determ[s,source,2])
    fig = plt.figure(figsize=(12,12))
    ax = fig.add_subplot(projection='3d')
    ax.scatter(xs, ys, zs, marker='o',color='black',label='det. opt.',alpha=1, depthshade=False,s=70)
    ax.scatter([q_opti_scenar[0]],[q_opti_scenar[1]],[q_opti_scenar[2]],marker='x',color='green',label='stoch. opt.',alpha=1, depthshade=False,s=70)
    ax.scatter([qactuel_blocs[0]],[qactuel_blocs[1]],[qactuel_blocs[2]],marker='o',color='blue',label='current',alpha=1, depthshade=False,s=70)
    ax.set_xlabel('European share',size=19)
    ax.set_ylabel('American share',size=19)
    ax.set_zlabel('Asian share',size=19)
    ax.legend(prop={'size': 17})

    def make_dashedLines(x,y,z,ax):
        for i in range(0, len(x)):
            x_val, y_val, z_val = x[i],y[i],z[i]
            #ax.plot([0,x_val],[y_val,y_val],zs=[0,0], linestyle="dashed",color="black")
            #ax.plot([x_val,x_val],[0,y_val],zs=[0,0], linestyle="dashed",color="black")
            ax.plot([x_val,x_val],[y_val,y_val],zs=[0,z_val], linestyle="dashed",color="black")

    make_dashedLines(xs,ys,zs,ax)
    make_dashedLines([q_opti_scenar[0]],[q_opti_scenar[1]],[q_opti_scenar[2]],ax)
    make_dashedLines([qactuel_blocs[0]],[qactuel_blocs[1]],[qactuel_blocs[2]],ax)


    ax.view_init(25, 60)
    plt.tight_layout()
    plt.savefig("3dscatterplot.png")
    plt.show()

###################################################################################################
# Histogramme des réponses
###################################################################################################
#%% Histogrammes de reponse

# Test de la politique optimale
def criteremoy(ssp,source,my_q):
    curr_gdpFR = gdp_france["SSP{}".format(ssp+1)][sources[source]]
    return max(curr_gdpFR*(np.dot(moy_intens[ssp,source],my_q))-cible_EC,0)

def criteremoy_allsources(ssp,my_q):
    curr_gdpFR = 0
    moy_intens_moy = moy_intens.mean(axis=1)
    for source in range(4):
        curr_gdpFR += gdp_france["SSP{}".format(ssp+1)][sources[source]]

    curr_gdpFR = curr_gdpFR/4
    return max(curr_gdpFR*(np.dot(moy_intens_moy[ssp],my_q))-cible_EC,0)

def criteredis(my_q,intens,curr_gdpFR,curr_gdpW):
    #croiss=(curr_gdpW-dict_worldgdp['2015'])/dict_worldgdp['2015']
    #prix_quot=(1+(croiss)) * 54
    prix_quot=250   
    return prix_quot*max(curr_gdpFR*(np.dot(intens,my_q))-cible_EC,0)


Nbiter = 100000
val_opti = np.zeros(Nbiter)
val_opti_scenar = np.zeros(Nbiter)
val_opti_deterministe = np.zeros(Nbiter)
val_stratmoy = np.zeros(Nbiter)
#val_deuxpays = np.zeros(Nbiter)
val_actuelle = np.zeros(Nbiter)
# q2p = np.zeros(nbreg)
# q2p[3]=0.7
# if qmax[4]>= 0.5:
#     q2p[4]=0.5
# else:
#     q2p[4]=qmax[4]
# if qmax[-1]>= 0.5:
#     q2p[-1]=0.5
# else:
#     q2p[-1]=qmax[-1]
# remaining = 0.3 - np.sum([qactuel[i]*(reg_list[i]!='France')*(reg_list[i]!='Germany')*(reg_list[i]!='United States') for i in range(nbreg)])
# for i in range(nbreg):
#     if reg_list[i]!='France' and reg_list[i]!='Germany' and reg_list[i]!='United States':
#         q2p[i] = remaining/15
num_reg=nbreg
qmoy = 1/(num_reg-1)*np.ones(num_reg)
if num_reg==3:
    qactuel=qactuel_blocs


moyennes=True
for i in range(Nbiter):
    if moyennes:    
        s = np.random.randint(0,len(ssps))
        source = np.random.randint(0,len(sources))
        val_opti[i]=criteremoy(s,source,q_opti)
        val_opti_scenar[i]=criteremoy(s,source,q_opti_scenar)
        val_stratmoy[i]=criteremoy(s,source,qmoy)
        #val_deuxpays[i]=criteremoy(s,source,q2p)
        val_actuelle[i]=criteremoy(s,source,qactuel)
        val_opti_deterministe[i]=criteremoy(s,source,q_deterministe)
    else:
        s = np.random.randint(0,len(ssps))
        source_gdp = np.random.randint(0,len(sources))
        gdp_FRcurr = gdp_france[ssps[s]][sources[source_gdp]]
        curr_dgp_world = dict_worldgdp['2030']["SSP%s"%(s+1)][sources[source_gdp]]
        intens = np.array([np.random.normal(distrib_intes[r,s,0],distrib_intes[r,s,1]) for r in range(nbreg)])
        if num_reg==3:
            intens = np.array([np.random.normal(distrib_intes_blocs[r,s,0],distrib_intes_blocs[r,s,1]) for r in range(num_reg)])
        val_opti[i]=criteredis(q_opti,intens,gdp_FRcurr,curr_dgp_world)
        val_opti_scenar[i]=criteredis(q_opti_scenar,intens,gdp_FRcurr,curr_dgp_world)
        val_stratmoy[i]=criteredis(qmoy,intens,gdp_FRcurr,curr_dgp_world)
        #val_deuxpays[i]=criteredis(q2p,intens,gdp_FRcurr,curr_dgp_world)
        val_actuelle[i]=criteredis(qactuel,intens,gdp_FRcurr,curr_dgp_world)
        val_opti_deterministe[i]=criteredis(q_deterministe,intens,gdp_FRcurr,curr_dgp_world)

def freq0(x):
    res=0
    for i in range(len(x)):
        if x[i]==0.:
            res+=1
    return res/len(x)
freqs=[]
for s in range(5):
    for source in range(len(sources)):
        sol = solution_pb_deterministe(nbreg,moy_intens,s,source)
        gdp_FRcurr = gdp_france[ssps[s]][sources[source_gdp]]
        curr_dgp_world = dict_worldgdp['2030']["SSP%s"%(s+1)][sources[source_gdp]]
        vals = np.zeros(10000)
        for i in range(10000):
            intens = np.array([np.random.normal(distrib_intes[r,s,0],distrib_intes[r,s,1]) for r in range(nbreg)])
            vals[i] = criteredis(sol,intens,gdp_FRcurr,curr_dgp_world)
        freq=freq0(vals)
        freqs.append(freq)
        print("SSP {} - ".format(s+1) + sources[source]+ " :    %s pct"%(100*freq))


print("Frequences obtention de 0 : ")
print("Opti gaussien : %s"%(freq0(val_opti)))
print("Opti discret : %s"%(freq0(val_opti_scenar)))
print("Strat moy : %s"%(freq0(val_stratmoy)))
print("actuelle : %s"%(freq0(val_actuelle)))
print("deterministe : %s"%(freq0(val_opti_deterministe)))
rgb_cols = np.array([[0,0,0,1],[0,1,0,0.75],[1,1,0,0.5],[1,0,0,0.45]])
plt.figure()
plt.bar(np.arange(1,8,2),height=[freq0(val_opti_scenar),freq0(val_stratmoy),freq0(val_actuelle),np.mean(freqs)],color=rgb_cols)
plt.ylabel("Frequencies of the event 'No quota bought'")
plt.xticks(np.arange(1,8,2), 
['stoch. optimum', 'mean strategy', 'current', 'deter. optimum'],
rotation=45)
plt.tight_layout()
plt.show()

#exit()
def trans(x):
    #return x
    res=[]
    for i in range(len(x)):
        if x[i]!=0.:
            res.append(np.log(x[i]))
    return res
    
def histos():
    fig,ax = plt.subplots()
    ax.hist(trans(val_stratmoy),bins=300,color="green",alpha=0.75,label="mean strategy" )
    #ax.hist(trans(val_deuxpays),bins=300,color="blue",alpha=0.25,label="Germany-USA only")
    ax.hist(trans(val_actuelle),bins=300,color="orange",alpha=0.5,label="Current situation" )
    ax.hist(trans(val_opti),bins=300,color="black",label="stoch. optimum (gaussian)" )
    #plt.yscale('log')
    plt.xlabel("Log of Volume of quota bought (€2018)",size=15)
    plt.ylabel("Frequency",size=15)
    plt.legend(prop={'size': 15})
    plt.grid()
    
    fig,ax = plt.subplots()
    ax.hist(trans(val_stratmoy),bins=300,color="green",alpha=0.75,label="mean strategy")
    #ax.hist(trans(val_deuxpays),bins=300,color="blue",alpha=0.25,label="Germany-USA only")
    ax.hist(trans(val_actuelle),bins=300,color="orange",alpha=0.5,label="Current situation")
    ax.hist(trans(val_opti_scenar),bins=300,color="black",label="stoch. optimum")
    #plt.yscale('log')
    plt.xlabel("Log of Volume of quota bought (€2018)",size=15)
    plt.ylabel("Frequency",size=15)
    plt.legend(prop={'size': 15})
    plt.grid()
    

    fig,ax = plt.subplots()
    ax.hist(trans(val_opti_deterministe),bins=300,color="red",alpha=0.45,label="deterministic optimum")
    ax.hist(trans(val_opti_scenar),bins=300,color="green",alpha=0.45,label="stoch. optimum")
    #plt.yscale('log')
    plt.xlabel("Log of Volume of quota bought (€2018)",size=15)
    plt.ylabel("Frequency",size=15)
    plt.legend(prop={'size': 15})
    plt.grid()

    fig,ax = plt.subplots()
    ax.hist(trans(val_opti_deterministe),bins=300,color="red",alpha=0.45,label="deterministic optimum")
    ax.hist(trans(val_opti),bins=300,color="blue",alpha=0.45,label="stoch. optimum (gaussian)")
    #plt.yscale('log')
    plt.xlabel("Log of Volume of quota bought (€2018)",size=15)
    plt.ylabel("Frequency",size=15)
    plt.legend(prop={'size': 15})
    plt.grid()
    plt.show()

histos()


########################################################################################################
# Diagrammes circulaires
########################################################################################################
#%%
import matplotlib as mpl
mpl.rcParams['font.size'] = 18.0

val_opti_deterministe_ssp1 = np.zeros(Nbiter)
val_opti_deterministe_ssp2 = np.zeros(Nbiter)
val_opti_deterministe_ssp3 = np.zeros(Nbiter)
val_opti_deterministe_ssp4 = np.zeros(Nbiter)
val_opti_deterministe_ssp5 = np.zeros(Nbiter)

def solution_pb_deterministe_all_sources(num_reg,moyennes,s=0,verbose=False):
    q = cp.Variable(num_reg,nonneg=True)
    constr = []
    intens = moyennes[:,1:,:].mean(axis=1)[s] #emissions connues
    gdpFR_noCEPII=np.array(gdpFR)[:,1:]
    gdp_FR = np.mean(gdpFR_noCEPII,axis=1)[s] #pib connu
    #croiss=(dict_worldgdp['2030']['SSP%s'%(s+1)][sources[source]]-dict_worldgdp['2015'])/dict_worldgdp['2015']
    #prix_quot=(1+(croiss)) * 54
    prix_quot=250
    crit = prix_quot*cp.pos(0.3*gdp_FR*intens@q-cible_EC)
    if num_reg==3:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax_blocs]
    else:
        constr+=[ q <= 1, cp.sum(q) == 1,q <= qmax]
    objective = cp.Minimize(crit)
    prob = cp.Problem(objective,constr)
    prob.solve(max_iters=10000)
    if verbose:
        print("Solution CVXPY - Cas déterministe - SSP %s - Moyenne sur les sources"%(ssps[s]))
        print(q.value)
        print("Respect contrainte somme : %s"%(np.isclose(np.sum(q.value),1., rtol=1e-5, atol=1e-5)))
        print("Respect positivité : %s"%(q.value>=0.).all())
        print("Valeur objectif : %s"%objective.value)
    return q.value
#q_deterministe = solution_pb_deterministe(3,moy_intens_blocs)
q_deterministe_ssp1 = solution_pb_deterministe_all_sources(nbreg,moy_intens,s=0)
q_deterministe_ssp2 = solution_pb_deterministe_all_sources(nbreg,moy_intens,s=1)
q_deterministe_ssp3 = solution_pb_deterministe_all_sources(nbreg,moy_intens,s=2)
q_deterministe_ssp4 = solution_pb_deterministe_all_sources(nbreg,moy_intens,s=3)
q_deterministe_ssp5 = solution_pb_deterministe_all_sources(nbreg,moy_intens,s=4)

for i in range(Nbiter):
    val_opti_deterministe_ssp1[i]=criteremoy_allsources(0,q_deterministe_ssp1)
    val_opti_deterministe_ssp2[i]=criteremoy_allsources(1,q_deterministe_ssp2)
    val_opti_deterministe_ssp3[i]=criteremoy_allsources(2,q_deterministe_ssp3)
    val_opti_deterministe_ssp4[i]=criteremoy_allsources(3,q_deterministe_ssp4)  
    val_opti_deterministe_ssp5[i]=criteremoy_allsources(4,q_deterministe_ssp5)


#%%
def autopct_more_than_1(pct) :
    return ('%1.1f%%' % pct) if pct >= 1.45 else ''

dict_fignames={'qactuel' : 'current_policy', 'q_opti' : "optimal", 
    'q_opti_scenar' : "optimal_scenarios", 'q_deterministe_ssp1' : "deterministic_ssp1",
    'q_deterministe_ssp2' : "deterministic_ssp2",'q_deterministe_ssp3' : "deterministic_ssp3",
    'q_deterministe_ssp4' : "deterministic_ssp4",'q_deterministe_ssp5' : "deterministic_ssp5"}

qdictionary = {'qactuel':qactuel, 'q_opti':q_opti, 'q_deterministe_ssp1':q_deterministe_ssp1,
    'q_deterministe_ssp2':q_deterministe_ssp2, 'q_deterministe_ssp3':q_deterministe_ssp3,
    'q_deterministe_ssp4':q_deterministe_ssp4, 'q_deterministe_ssp5':q_deterministe_ssp5,
    'q_opti_scenar':q_opti_scenar}

for my_q in ['qactuel', 'q_opti', 'q_opti_scenar','q_deterministe_ssp1','q_deterministe_ssp2'
,'q_deterministe_ssp3','q_deterministe_ssp4','q_deterministe_ssp5'] :
    print(my_q)
    q = qdictionary[my_q]
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    sizes = pd.DataFrame(100*q,index=reg_list)
    explode = np.zeros_like(q)  # only "explode" the 2nd slice (i.e. 'Hogs')

    fig1, ax1 = plt.subplots(facecolor='white',figsize=(12,12))
    p,t,a = ax1.pie(np.reshape(sizes.values,(-1,)), explode=explode, labels=sizes.index, autopct=autopct_more_than_1,
            shadow=False, startangle=90,rotatelabels=180,labeldistance=None, pctdistance=0.8)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # create handles and labels for legend, take only those where value is > 1
    h,l = zip(*[(h,lab) for h,lab,i in zip(p,sizes.index.values,sizes.values) if i >= 1])

    ax1.legend(h, l,loc="best", bbox_to_anchor=(1,1))


    plt.tight_layout()
    plt.savefig("piechart_"+dict_fignames[my_q]+".png")
    plt.show()
    #plt.close()

    fig2, ax2 = plt.subplots(facecolor='white',figsize=(12,12))  
    x_pos = np.arange(45)/2
    bars = np.reshape(sizes.index.values,(-1,))
    height = np.reshape(sizes.values,(-1,))
    # Make the plot
    ax2.barh(x_pos, height, height=0.5)

    # Create names on the x-axis
    plt.yticks(x_pos, bars)
    plt.tight_layout()
    plt.savefig("barh_"+dict_fignames[my_q]+".png")
    
    # Show graphic
    plt.show()



#%%
########################################################################################################
# Calcul de distances de Kullback-Leiber
########################################################################################################

def kull(val1,val2):
    nb_bins = 300
    hist1=np.histogram(val1,bins=nb_bins)[0]
    hist2=np.histogram(val2,bins=nb_bins)[0]
    res=0
    for i in range(nb_bins):
        if hist1[i]!=0 and hist2[i] !=0:
            res+= hist1[i] * np.log(hist1[i] / hist2[i])
    return res

print("Divergence de K-L")
print("Opti vs Deterministe : %s"%kull(val_opti,val_opti_deterministe))
print("Opti vs Scenar : %s"%kull(val_opti,val_opti_scenar))
# %%
