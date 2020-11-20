
from gurobipy import *
import numpy as np
import pandas as pd


model = Model('COCOmbustion')




eff = 0.38             # [kWhelec / kWh thermique] efficacité énergétique
P = 150                #MWé
T = 7500               #h/an

prod = P*T/eff      # [MWh thermique/an] énergie à produire par la centrale 
ratiocmin = 0.1        # ratio carbone dans le LFC
durée = 20             # [ans]  durée d'exploitation
pcibr = (18-21*0.05)*1000/3.6     # [MWh/kt]  
pcibf = (18-21*0.2)*1000/3.6      # [MWh/kt]
pcibt = 18*1000/3.6               # [MWh/kt]    
pcirv = (18-21*0.4)*1000/3.6      # [MWh/kt]   
pcic= 25*1000/3.6                 # [MWh/kt]   
spci=(18-21*0.05)*1000/3.6        # [MWh/kt]   PCI de la masse de biomasse séchée
consobt = 0.025*1000        # [MWh/kt] Valeur de l'autoconso nécessaire au broyage du boisfrais
consobb = 0.08*1000         # [MWh/kt] Valeur de l'autoconso nécessaire au broyage du boisfrais

#CAPEX
CF = 10050000          #cout fixe en euros O&M liés à la capacité de la centrale
invest = 500000        # [e] prix du dédoublement de la capacité de stockage bois
sech50 = 300000       # [e] prix séchage de 50kt
sech150 = 600000      # [e] prix séchage de 150kt
cout_tremie = 1.2*1000     # e/(kt/an) en fonction des tonnes de biomasse non torréfiée
cout_co2 = 5
#Couts Variables 
CV = 67*1000 *P      #e/MWé
couts_bio_50 = 430*277 # e/MWH (430e/TJ = 430*277 e/TJ)
couts_bio = 215*277    # e/MWh


#                      [Mwh/kt], [%], [e/kt],[e/MWh],    [kt/an]     k[t/an]       [tco2/kt]    [km]
combustible,               pci, eau, achat, vente,     cf,   dispo1,          dispo2,       ges, route, mer= multidict({
'charbon'         : [pcic,    1,    75*1000,  43.2,     0, GRB.INFINITY,GRB.INFINITY,   3000,      0,    0],

'Caroline-du-Sud' : [pcibt,   1,   190*1000,   115,100000,      700,               0,        1.7,   250, 7000],
'Brésil'          : [pcibt,   1,   170*1000,   115,120000,      600,               0,        1.7,  1000, 8500],
 'Québec'         : [pcibt,   1,   180*1000,   115,110000,      450,               0,        1.7,   500, 5000],
'Canada Pacifique': [pcibt,   1,   250*1000,   115,100000,     1000,               0,        1.7,   800,16500],
'Portugal'        : [pcibt,   1,   240*1000,   115,  5000,      350,               0,        1.7,  1700,    0],
'Russie'          : [pcibt,   1,   300*1000,   115,  6000,      600,               0,        1.7,  3000,    0],

'MA'              : [pcibf, 1.2,   128*1000,   115,     0,       18,              21,           1.3,   250,    0],
'Cévennes30'      : [pcibf, 1.2,   120*1000,   115,     0,       21,              43,           1.3,   210,    0],
'Cévennes48'      : [pcibf ,1.2,   128*1000,   115,     0,       12,              75,           1.3,   230,    0],
'Cévennes07'      : [pcibf, 1.2,   116*1000,   115,     0,       47,              56,           1.3,   200,    0],
'Bouche du Rhone' : [pcibf, 1.2,    44*1000,   115,     0,       47,              51,           1.3,    20,    0],
'Vaucluse'        : [pcibf, 1.2,    76*1000,   115,     0,       24,              28,           1.3,   100,    0],
'Var'             : [pcibf, 1.2,    60*1000,   115,     0,       27,              27,           1.3,    60,    0],
'Hautes Alpes'    : [pcibf, 1.2,   100*1000,   115,     0,       15,              21,           1.3,   160,    0],
'Alpes Hte Provence':[pcibf,1.2,    88*1000,   115,     0,       26,              37,           1.3,   130,    0],
'Autres1'         : [pcibf, 1.2,   116*1000,   115,     0,       27,              27,           1.3,   200,    0],
'Autres2'         : [pcibf, 1.2,   156*1000,   115,     0,       56,              56,           1.3,   300,    0],
'Autres3'         : [pcibf, 1.2,   196*1000,   115,     0,       93,              93,           1.3,   400,    0],

'rv1'             : [pcirv, 1.4,         0,     115,    0,      313,             313,          0.1,  0,  0],

'br'              : [pcibr,   1,    12*1000,   115,     0,       85,             240,           10,     0,    0]
})

boisfrais =   ['MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']
boisrecycle = ['br']
charbon =     ['charbon']
boistorrefie =['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =  ['rv1']
sechage =     boisfrais+residuvert
biomasse =    boisfrais+boisrecycle+boistorrefie+residuvert
bois_brute =  boisfrais+boisrecycle+residuvert
#Création liste des valeurs de quota (dépassement ou pas) calculés
Quota=[]

#Listes des points e l'approximation linéaires des prix RV
cout_vert=20*[0]
dispo_rv=np.array([0,1,7,22,29,52,57,143,210,313])                         #kt/an
prix_rv=np.array([0,4000,7000,10000,16000,25000,31000,46000,61000,76000])  #e/kt
ges_route_total_rv=20*[0]
route_rv=np.array([0,10,20,30,50,80,100,150,200,250])
ges_rv=0.16*route_rv*dispo_rv                                               #0.16 tCO2/km/kt


#------VARIABLES DECISIONNELLES RELLES-----
C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS,name='masse')
#variable de masse séchée,S, (après le séchage) et non séchée, NS, pour chaque année pour chaque combustible 
S=model.addVars (sechage, 20, lb =0, vtype= GRB.CONTINUOUS,name='masseSeche')
NS=model.addVars (sechage, 20, lb =0, vtype= GRB.CONTINUOUS,name='masseNS')

#Variable permettant de calculer les couts selon taux d'incorporation de la biomasse
X = model.addVars (20,lb=0,vtype=GRB.BINARY,name='incorpbinaire')
incorp = model.addVars (20,lb=0,vtype=GRB.CONTINUOUS,name='incorp')

#-------VARIABLES DECISIONNELLES BINAIRES -----
#variables binaires d'achat de capacité de stockage modéré s50 ou grand s150
s50 = model.addVars (20,lb = 0, vtype = GRB.INTEGER)
s150 = model.addVars (20,lb = 0, vtype = GRB.INTEGER)
#variable binaire de la capacité de stockage doublée ou non. Vaut 1 si le stockage double est rentable
stock = model.addVar (lb = 0, vtype = GRB.BINARY) 
#variables binaires pour ajouter le cf lorsqu'on achète du bois torréfié
cf_bt = model.addVars (boistorrefie, lb = 0, vtype = GRB.BINARY)

#------FONCTION DE PROFIT-----

def profit(c):
    return pci[c]*eff*vente[c] - achat[c]
#profit après séchage de la biomasse avec un pci de 5% humidité (spci)
def sprofit(c):
    return spci*eff*vente[c] - eau[c]*achat[c]


#----------------VARIABLES APPROXIMATION LINEAIRE-----

lambda_rv=model.addVars(10,20,vtype=GRB.CONTINUOUS,ub=1)
for i in range(20):
    model.addSOS(GRB.SOS_TYPE2,[lambda_rv[j,i] for j in range(10)])
    
lambda_route_rv=model.addVars(10,20,vtype=GRB.CONTINUOUS,ub=1)
for i in range(20):
    model.addSOS(GRB.SOS_TYPE2,[lambda_route_rv[j,i] for j in range(10)])
prix_total_rv=dispo_rv*prix_rv



#-----------------CONTRAINTES------

for i in range(durée):
    model.addConstr(sum(C[c,i] for c in biomasse) <= 0.5*sum(C[c,i] for c in charbon+boistorrefie+boisrecycle+residuvert+boisfrais)*(1+X[i]))
    incorp[i] = ((couts_bio_50) *(X[i]) + (couts_bio)*(1-X[i]))
    
#-----séchage
for i in range(durée):
    #il faut que la somme de la masse mise dans les séchoirs (avant séchage) à l'année i soit inférieur à la capcité de stockage mis en place les années précédentes
    model.addConstr(sum(eau[c]*S[c,i] for c in sechage) <= sum(s50[j]*50+s150[j]*150 for j in range(durée)))
    for c in sechage:
    #masse séchée avant séchage + masse non séchée = masse achetée
        model.addConstr(eau[c]*S[c,i] + NS[c,i]  == C[c,i] )
        
#Pas plus de 5 séchoirs, de quelconque capacité
model.addConstr(sum(s50[i]+s150[i] for i in range(durée)) <= 5)

for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(sum(pci[c]*C[c,i]  for c in combustible)+sum((NS[c,i]-C[c,i])*pci[c] for c in sechage)+sum(spci*S[c,i] for c in sechage) == prod)
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-(ratiocmin*(sum(C[c,i] for c in boisfrais+boisrecycle+boistorrefie+residuvert))) >= 0)
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in bois_brute))<= 1.5*365*(1+stock))


#---disponibilité des combustibles
    for c in combustible :
        if i < 10: #du coup on se retrouve < 2026
            model.addConstr(C[c,i] <= dispo1[c])
        elif i >= 10:
            model.addConstr(C[c,i] <= dispo2[c])

#---GES
    if i <5:
        Quota.append(80000-ges_route_total_rv[i]-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.16*C[c,i] for c in boisfrais)-quicksum(route[c]*0.09*C[c,i] for c in boistorrefie)-quicksum(mer[c]*0.015*C[c,i] for c in boistorrefie))
    elif i >=5 and i <10:
        Quota.append(60000-ges_route_total_rv[i]-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.16*C[c,i] for c in boisfrais)-quicksum(route[c]*0.09*C[c,i] for c in boistorrefie)-quicksum(mer[c]*0.015*C[c,i] for c in boistorrefie))
    elif i >=10 and i <15:
        Quota.append(40000-ges_route_total_rv[i]-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.16*C[c,i] for c in boisfrais)-quicksum(route[c]*0.09*C[c,i] for c in boistorrefie)-quicksum(mer[c]*0.015*C[c,i] for c in boistorrefie))                                                             
    elif i >=15 :
        Quota.append(20000-ges_route_total_rv[i]-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.16*C[c,i] for c in boisfrais)-quicksum(route[c]*0.09*C[c,i] for c in boistorrefie)-quicksum(mer[c]*0.015*C[c,i] for c in boistorrefie))
        

#---Modélisation de la fonction linéaire par morceaux du prix des résidus verts
    model.addConstr(quicksum(lambda_rv[j,i] for j in range(10))==1)
    model.addConstr(C['rv1',i]==quicksum(dispo_rv[j]*lambda_rv[j,i] for j in range(10)))
    cout_vert[i]=quicksum(prix_total_rv[j]*lambda_rv[j,i] for j in range(10))  

#---Modélisation de la fonction linéaire par morceaux du prix des résidus verts
    model.addConstr(quicksum(lambda_route_rv[j,i] for j in range(10))==1)
    model.addConstr(C['rv1',i]==quicksum(dispo_rv[j]*lambda_route_rv[j,i] for j in range(10)))
    ges_route_total_rv[i]=quicksum(ges_rv[j]*lambda_route_rv[j,i] for j in range(10))
    
#---Couts Fixes du bois torréfiés. Sion achète une provenance, cf_bt =1
    for c in boistorrefie:
        model.addConstr(sum(C[c,i] for i in range(durée)) == sum(C[c,i]*(cf_bt[c]) for i in range(durée)))
    
"""
#pas prise en compte puisque de toute façon pas assez de bt
    #Avant 10 ans on peut jusqu'a 60% de region, et apres 100% région
    if i < 10:
            #je veux 60% de R sur l'ensemble de la biomasse soit R/C = 0,6 donc R - 0,6C = 0
            model.addConstr((sum(C[c,i] for c in region))  >= 0.6*(sum(C[c,i] for c in biomasse)))
    if i >= 10:
           model.addConstr((sum(C[c,i] for c in region))  >= (sum(C[c,i] for c in biomasse)))
    model.addConstr((sum(C[c,i] for c in region))+(sum(C[c,i] for c in nonregion))==(sum(C[c,i] for c in region+nonregion)))
"""

#FONCTION OBJECTIF ------------------------------------

model.setObjective(sum(profit(c)*C[c,i]  for c in combustible for i in range(durée))
                   
                   +(sum(profit(c)*(NS[c,i]-C[c,i])+S[c,i]*sprofit(c) for c in sechage for i in range(durée)))
                   
                   -(sum(s50[i]*sech50 + s150[i]*sech150 for i in range(20)))
                   
                   +sum(cout_co2*Quota[i] for i in range(durée))
                   
                   #Calcul les pertes liées à l'autoconsommation électrique pour le broyage
                   - sum(consobt*C[c,i]*vente[c] for c in boistorrefie for i in range(durée)) 
                   - sum(consobb*C[c,i]*vente[c] for c in bois_brute for i in range(durée)) 

                   - sum(cout_vert[i] for i in range(durée))
                      
                   - CV 
                   
                   - sum(incorp[i] for i in range(durée))
                   
                   - sum(cf[c]*(cf_bt[c]) for c in boistorrefie)
                   
                   - sum(cout_tremie*C[c,i] for c in bois_brute for i in range (durée))
                   
                   - CF - stock*invest,GRB.MAXIMIZE)

model.write("final.lp")
model.optimize()

print('------OPTI ECONOMIQUE ---------')
print()
Obj=model.getObjective()
Opti=Obj.getValue()
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")


charbonn = np.ones(shape=(20,1))
bt = np.ones(shape=(20,1))
br = np.ones(shape=(20,1))
bs = np.ones(shape=(20,1))
rv = np.ones(shape=(20,1))
ss = np.ones(shape=(20,1))
bf = np.ones(shape=(20,1))
bbb = np.ones(shape=(20,1))
rvs = np.ones(shape=(20,1))
bfs = np.ones(shape=(20,1))
for i in range(durée):
    charbonn[i,0]=int(sum(C[c,i].x for c in charbon))
    bt[i,0]=int(sum(C[c,i].x for c in boistorrefie))
    br[i,0]=int(sum(C[c,i].x for c in boisrecycle))
    rv[i,0]=int(sum(C[c,i].x for c in residuvert))-int(sum(eau[c]*S[c,i].x for c in residuvert))
    ss[i,0]=int(sum(eau[c]*S[c,i].x for c in sechage))
    bf[i,0]=int(sum(C[c,i].x for c in boisfrais))-int(sum(eau[c]*S[c,i].x for c in boisfrais))
    bbb[i,0]=int(sum(C[c,i].x for c in biomasse))
    rvs[i,0]=int(sum(eau[c]*S[c,i].x for c in residuvert))
    bfs[i,0]=int(sum(eau[c]*S[c,i].x for c in boisfrais))

data = np.concatenate((charbonn,bt),axis=1)
data = np.concatenate((data,br),axis=1)
data = np.concatenate((data,rv),axis=1)
data = np.concatenate((data,rvs),axis=1)
data = np.concatenate((data,bf),axis=1)
data = np.concatenate((data,bfs),axis=1)
comb = ['   Charbon','   BT','   BR','   RV','   RVS','   BF','   BFS']
duree = []
for i in range(durée):
    duree.append(i+1)
df = df = pd.DataFrame(data=data,index=duree,columns=comb)
print(df)
"""
#-------AFFICHE LES MASSES DE COMBUSTIBLES ACHETEES ----
for c in combustible:
    print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")
"""
#------ TEST CALCUL DU QUOTA -----

s=0
for i in Quota:
    s=s+i
print('Quota Carbone estimé à : ', int(LinExpr.getValue(s)),'euros')
#print('quot : variable de prise en compte quota carbone', quot.x)
"""
#-----TEST AFFICHAGE DES MASSES SECHEES OU NON / COMBUSTIBLES -----
for i in range(durée):
    print('masse achetée',c, int((sum(C[c,i].x for c in sechage))/1000),"Kt")
    print('masse séchée',c, int((sum(eau[c]*S[c,i].x for c in sechage))/1000),"Kt")
    print('masse NON séchée',c, int((sum(NS[c,i].x for c in sechage))/1000),"Kt")
"""    
"""  print()
#-----TEST AFFICHAGE DES MASSES SECHEES OU NON / TOTAL -----
print('-----recap')
print('masse  achetée', int((sum(C[c,i].x for i in range(20) for c in sechage))/1000),"Kt")    
print('masse  séchée', int((sum(eau[c]*S[c,i].x for i in range(20) for c in sechage)/1000)))
print('masse NON séchée', int((sum(NS[c,i].x for i in range(20) for c in sechage))/1000),"Kt")
"""
"""
#----TEST APPROVISIONNEMENT REGIONNAL-----
print('biomasse achetée',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in boisfrais+boisrecycle+residuvert+charbon))/1000))
print('biomasse R',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in region))/1000))
print('biomasse NR',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in nonregion))/1000))
"""
"""
for c in biomasse :
    print(c,nr[c].x)
for i in range(durée):
    print()
    print(i,'ans')
    if sum(C[c,i].x for c in biomasse) != 0:
        print(sum(C[c,i].x for c in region)/sum(C[c,i].x for c in biomasse)*100,'%')
"""
#------TEST AFFICHAGE DES CAPACITES DE SECHAGE------
#for i in range(durée):
#    print(s50[i])
#    print(s150[i])
#capacité totale de sechage sur les 20ans
print('Capacité de séchage : ',(LinExpr.getValue(sum(s50[i]*50+s150[i]*150 for i in range(20)))),':: Nb sécheurs ', LinExpr.getValue(sum(s50[i] + s150[i] for i in range(20))))
#-----AFFICHAGE CAPACITE DE STOCKAGE------
if stock.x>=1:
    print('Investissement dans le stockage de bois : Oui')
else:
    print('Pas d investissement dans les capacité de stockage journalières')
"""
# TEST AFFICHAGE LAMBDA
for i in range(20):
    print('lambda',i,sum(lambda_rv[j,i].x for j in range(10)))
"""
"""
for i in range(20):
    print(LinExpr.getValue(ges_route_total_rv[i]))
"""
"""
print(sum(C[c,i].x/1000 for c in boistorrefie+bois_brute for i in range(1)))
"""
