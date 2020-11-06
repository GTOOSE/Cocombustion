from gurobipy import *
import numpy as np
import pandas as pd


model = Model('COCOmbustion')

CF = 10050000          #cout fixe en euros O&M liés à la capacité de la centrale
invest = 500000        # [e] prix du dédoublement de la capacité de stockage bois

eff = 0.38             # [kWhelec / kWh thermique] efficacité énergétique
prod = 990000/eff      # [kWh thermique/an] énergie à produire par la centrale 
ratiocmin = 0.1        # ratio carbone dans le LFC
durée = 20             # [ans]  durée d'exploitation
pcibr = 18-21*0.05     # [GJ/t]  
pcibf = 18-21*0.4      # [GJ/t]  
pcibt = 18             # [GJ/t]  
pcirv = 18-21*0.2     # [GJ/t]  
pcic= 25               # [GJ/t]  
spci=18-21*0.05       # [Mwh/t] PCI de la masse de biomasse séchée
consobt = 0.025        # [kWh/t] Valeur de l'autoconso nécessaire au broyage du boisfrais
consobb = 0.08         # [kWh/t] Valeur de l'autoconso nécessaire au broyage du boisfrais
#prix des dispositifs de séchage
sech50 = 300000       # [e] prix séchage de 50kt
sech150 = 600000      # [e] prix séchage de 150kt


#                      [Mwh/t], [%],    [e/Mwh]               [t/an]       [kco2/t]    [km]
combustible,               pci, eau, achat, vente,      dispo1,       dispo2,   ges, route, mer= multidict({
'charbon'         : [pcic/3.6,    1,    75,  43.2,GRB.INFINITY,GRB.INFINITY,      3,      0,    0],

'Caroline-du-Sud' : [pcibt/3.6,   1,   190,   115,      700000,           0, 0.0017,   250, 7000],
'Brésil'          : [pcibt/3.6,   1,   170,   115,      600000,           0, 0.0017,  1000, 8500],
 'Québec'         : [pcibt/3.6,   1,   180,   115,      450000,           0, 0.0017,   500, 5000],
'Canada Pacifique': [pcibt/3.6,   1,   250,   115,     1000000,           0, 0.0017,   800,16500],
'Portugal'        : [pcibt/3.6,   1,   240,   115,      350000,           0, 0.0017,  1700,    0],
'Russie'          : [pcibt/3.6,   1,   300,   115,      600000,           0, 0.0017,  3000,    0],

'MA'              : [pcibf/3.6, 1.2,   128,   115,       18000,       21000, 0.0013,   250,    0],
'Cévennes30'      : [pcibf/3.6, 1.2,   120,   115,       21000,       43000, 0.0013,   210,    0],
'Cévennes48'      : [pcibf/3.6 ,1.2,   128,   115,       12000,       75000, 0.0013,   230,    0],
'Cévennes07'      : [pcibf/3.6, 1.2,   116,   115,       47000,       56000, 0.0013,   200,    0],
'Bouche du Rhone' : [pcibf/3.6, 1.2,    44,   115,       47000,       51000, 0.0013,    20,    0],
'Vaucluse'        : [pcibf/3.6, 1.2,    76,   115,       24000,       28000, 0.0013,   100,    0],
'Var'             : [pcibf/3.6, 1.2,    60,   115,       27000,       27000, 0.0013,    60,    0],
'Hautes Alpes'    : [pcibf/3.6, 1.2,   100,   115,       15000,       21000, 0.0013,   160,    0],
'Alpes Hte Provence':[pcibf/3.6,1.2,    88,   115,       26000,       37000, 0.0013,   130,    0],
'Autres1'         : [pcibf/3.6, 1.2,   116,   115,       27000,       27000, 0.0013,   200,    0],
'Autres2'         : [pcibf/3.6, 1.2,   156,   115,       56000,       56000, 0.0013,   300,    0],
'Autres3'         : [pcibf/3.6, 1.2,   196,   115,       93000,       93000, 0.0013,   400,    0],

'rv1'             : [pcirv/3.6, 1.4,   0,     115,      313000,      313000, 0.0017,  1000,  0],

'br'              : [pcibr/3.6,   1,    12,   115,       85000,      240000, 0.0001,     0,    0]
})

boisfrais =   ['MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']
boisrecycle = ['br']
charbon =     ['charbon']
boistorrefie =['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =  ['rv1']

sechage =     boisfrais+residuvert
biomasse =    boisfrais+boisrecycle+boistorrefie+residuvert
#liste pour le bois brute broyé == biomasse - granulés(bois torrefies)
bois_brute =  boisfrais+boisrecycle+residuvert
#Création liste des valeurs de quota (dépassement ou pas) calculés
Quota=[]

#Création d'une liste liée à la localisation de la biomasse
nonregion=[]
region=[]
for c in boisfrais+boisrecycle+residuvert+charbon:
    if (mer[c]+route[c])>= 400:
        nonregion.append(c)
    else :
        region.append(c)

#Listes des points e l'approximation linéaires des prix RV
cout_vert=20*[0]
dispo_rv=np.array([0,1000,7000,22000,29000,52000,57000,143000,210000,313000])
prix_rv=np.array([0,4,7,10,16,25,31,46,61,76])
        
        
#------FONCTION DE PROFIT-----

def profit(c):
    return pci[c]*eff*vente[c] - achat[c]
#profit après séchage de la biomasse avec un pci de 5% humidité (spci)
def sprofit(c):
    return (spci/3.6)*eff*vente[c] - achat[c]


#------VARIABLES DECISIONNELLES RELLES-----

C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#variable de masse séchée,S, (après le séchage) et non séchée, NS, pour chaque année pour chaque combustible 
S=model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
NS=model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)


#-------VARIABLES DECISIONNELLES BINAIRES -----

#variables binaires d'achat de capacité de stockage modéré s50 ou grand s150
s50 = model.addVars (20,lb = 0, vtype = GRB.BINARY)
s150 = model.addVars (20,lb = 0, vtype = GRB.BINARY)
sec = model.addVars (20,lb = 0, vtype = GRB.BINARY)
#variable binaire de la capacité de stockage doublée ou non. Vaut 1 si le stockage double est rentable
stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
quot = model.addVar (lb = 0, vtype = GRB.BINARY)
#variable de masse séchée pour chaque année pour chaque combustible 
nr = model.addVars (combustible,lb = 0, vtype = GRB.BINARY)  

#----VARIABLES APPROXIMATION LINEAIRE-----

lambda_rv=model.addVars(10,20,vtype=GRB.CONTINUOUS,ub=1)
for i in range(20):
    model.addSOS(GRB.SOS_TYPE2,[lambda_rv[j,i] for j in range(10)])

prix_total_rv=dispo_rv*prix_rv

#-----CONTRAINTES------
#-----séchage
for i in range(durée):
    #il faut que la somme de la masse mise dans les séchoirs (avant séchage) à l'année i soit inférieur à la capcité de stockage mis en place les années précédentes
    model.addConstr(sum(eau[c]*S[c,i] for c in sechage) <= sum(s50[j]*50000+s150[j]*150000 for j in range(0,i+1)))
    for c in sechage:
    #contrainte de séchage 
    #je veux que la masse séchée, plus le poids d'eau perdu, plus la masse non séchée soit égale a la masse achetée
    ## CHANGER NS par C-S*(1-eau)
        model.addConstr(eau[c]*S[c,i]+NS[c,i]  == C[c,i] )
#Pas plus de 5 séchoirs, de quelconque capacité
model.addConstr(sum(s50[i] for i in range(durée))+sum(s150[i] for i in range(durée)) <= 5)

        
for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(sum(pci[c]*C[c,i] for c in combustible) == prod)
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-(ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert)))  >= 0)
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in bois_brute))<= 1500*365*(1+stock))
   
    #Avant 10 ans on peut jusqu'a 60% de region, et apres 100% région
    if i < 10:
            #je veux 60% de R sur l'ensemble de la biomasse soit R/C = 0,6 donc R - 0,6C = 0
            model.addConstr((sum(C[c,i] for c in region))  >= 0.6*(sum(C[c,i] for c in biomasse)))
    if i >= 10:
           model.addConstr((sum(C[c,i] for c in region))  >= (sum(C[c,i] for c in biomasse)))
           
    model.addConstr((sum(C[c,i] for c in region))+(sum(C[c,i] for c in nonregion))==(sum(C[c,i] for c in region+nonregion)))
    

    
    #valeur de disponibilité
    for c in combustible :
        if i < 10: #du coup on se retrouve < 2026
            model.addConstr(C[c,i] <= dispo1[c])
        elif i >= 10:
            model.addConstr(C[c,i] <= dispo2[c])
    
    #GES
    if i <5:
        Quota.append(80000-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))
    elif i >=5 and i <10:
        Quota.append(6000-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))
    elif i >=10 and i <15:
        Quota.append(4000-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))                                                             
    elif i >=15 :
        Quota.append(2000-quicksum(ges[c]*C[c,i] for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))
        #rajouter variabile binaire pour si pas de benef on le fait pas
        
        #Modélisation de la fonction linéaire par morceaux des résidus verts
        
    model.addConstr(quicksum(lambda_rv[j,i] for j in range(10))==1)
    model.addConstr(C['rv1',i]==quicksum(dispo_rv[j]*lambda_rv[j,i] for j in range(10)))
    cout_vert[i]=quicksum(prix_total_rv[j]*lambda_rv[j,i] for j in range(10))  
        

model.setObjective(quot*sum(5*Quota[i] for i in range(durée))
                   #Max du profit en prenant tous les combustibles
                   +sum(profit(c)*C[c,i] for c in combustible for i in range(durée))
                   
                   #on ne laisse pas le choix on optimise des la premiere année, ajout binaire pour choix année
                   +(sum(profit(c)*(NS[c,i]-C[c,i])+S[c,i]*sprofit(c) for c in sechage for i in range(durée))
                   -sum(s50[i] for i in range(durée))*sech50 -sum(s150[i] for i in range(durée))*sech150 )
                   
                   #Calcul les pertes liées à l'autoconsommation électrique pour le broyage
                   -sum(consobt*C[c,i]*vente[c] for c in boistorrefie+bois_brute for i in range(durée)) 
                   
                   #-sum(cout_vert[i] for i in range(durée))
                   
                   - CF - stock*invest,GRB.MAXIMIZE)

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

for i in range(durée):
    charbonn[i,0]=int(sum(C[c,i].x for c in charbon))/1000
    bt[i,0]=int(sum(C[c,i].x for c in boistorrefie))/1000
    br[i,0]=int(sum(C[c,i].x for c in boisrecycle))/1000
    rv[i,0]=int(sum(C[c,i].x for c in residuvert))/1000-int(sum(eau[c]*S[c,i].x for c in residuvert))/1000
    ss[i,0]=int(sum(eau[c]*S[c,i].x for c in sechage))/1000
    bf[i,0]=int(sum(C[c,i].x for c in boisfrais))/1000-int(sum(eau[c]*S[c,i].x for c in boisfrais))/1000
    bbb[i,0]=int(sum(C[c,i].x for c in biomasse))/1000
    rvs[i,0]=int(sum(S[c,i].x for c in residuvert))/1000
    
data = np.concatenate((charbonn,bt),axis=1)
data = np.concatenate((data,br),axis=1)
data = np.concatenate((data,rv),axis=1)
data = np.concatenate((data,rvs),axis=1)
data = np.concatenate((data,ss),axis=1)
data = np.concatenate((data,bf),axis=1)


comb = ['   Charbon','   BT','   BR','   RV','   RVS','   BS','   BF']
duree = []
for i in range(durée):
    duree.append(i+1)

df = df = pd.DataFrame(data=data,index=duree,columns=comb)
print(df)

"""""
-------AFFICHE LES MASSES DE COMBUSTIBLES ACHETEES ----
for c in combustible:
    print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")
"""


#------ TEST CALCUL DU QUOTA -----
quota=[]    
for i in range(20):
    if i <5:
        quota.append(80000-quicksum(ges[c]*C[c,i].x for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))
    elif i >=5 and i <10:
        quota.append(60000-quicksum(ges[c]*C[c,i].x for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))
    elif i >=10 and i <15:
        quota.append(40000-quicksum(ges[c]*C[c,i].x for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))                                                             
    elif i >=15 :
        quota.append(20000-quicksum(ges[c]*C[c,i].x for c in combustible)-quicksum(route[c]*0.016 for c in combustible)-quicksum(mer[c]*0.017 for c in combustible))
        #rajouter variabile binaire pour si pas de benef on le fait pas 
s=0
for i in quota:
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


#----TEST APPROVISIONNEMENT REGIONNAL-----
print('biomasse achetée',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in biomasse))/1000))
print('biomasse R',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in region))/1000))
print('biomasse NR',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in nonregion))/1000))
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
print('Capacité de séchage : ',(LinExpr.getValue(sum(s50[i] for i in range(20)))*50000+LinExpr.getValue(sum(s150[i] for i in range(20)))*150000)/1000)

#-----AFFICHAGE CAPACITE DE STOCKAGE------
if stock.x>=1:
    print('Investissement dans le stockage de bois : Oui')

"""
# TEST AFFICHAGE LAMBDA

for i in range(20):
    print('lambda',i,sum(lambda_rv[j,i].x for j in range(10)))
"""
