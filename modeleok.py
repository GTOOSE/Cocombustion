from gurobipy import *



model = Model('COCOmbustion')
model.modelSense = GRB.MAXIMIZE
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif


CF = 10050000        #cout fixe en euros O&M liés à la capacité de la centrale
eff = 0.38            #efficacité énergétique
prod = 990000/eff
ratiocmin = 0.1      # ratio carbone dans le LFC
durée = 20
Quota=[]
pcibr = 18-21*0.2
pcibf = 18-21*0.4
pcibt = 18
pcirv = 25
pcic= 25
spci=18-21*0.05
invest = 50000

combustible,               pci, eau, achat, vente,      dispo1,       dispo2,   ges, route, mer= multidict({
'charbon'         : [pcic/3.6,   1,    75,  43.2,GRB.INFINITY,GRB.INFINITY,      3,     0,  0],
'Caroline-du-Sud' : [pcibt/3.6,   1,   190,   115,           0,      700000, 0.0017,   400,  0],
'Brésil'          : [pcibt/3.6,   1,   170,   115,           0,      600000, 0.0017,     0,  0],
 'Québec'         : [pcibt/3.6,   1,   180,   115,           0,      450000, 0.0017,     0,  0],
'Canada Pacifique': [pcibt/3.6,   1,   250,   115,           0,     1000000, 0.0017,     0,  0],
'Portugal'        : [pcibt/3.6,   1,   240,   115,           0,      350000, 0.0017,     0,  0],
'Russie'          : [pcibt/3.6,   1,   300,   115,           0,      600000, 0.0017,     0,  0],
'MA'              : [pcibf/3.6, 1.2,   128,   115,       18000,       21000, 0.0013,     0,  0],
'Cévennes30'      : [pcibf/3.6, 1.2,   120,   115,       21000,       43000, 0.0013,     0,  0],
'Cévennes48'      : [pcibf/3.6 ,1.2,   128,   115,       12000,       75000, 0.0013,   400,  0],
'Cévennes07'      : [pcibf/3.6, 1.2,   116,   115,       47000,       56000, 0.0013,  3000,  0],
'Bouche du Rhone' : [pcibf/3.6, 1.2,    44,   115,       47000,       51000, 0.0013,     0,  0],
'Vaucluse'        : [pcibf/3.6, 1.2,    76,   115,       24000,       28000, 0.0013,     0,  0],
'Var'             : [pcibf/3.6, 1.2,    60,   115,       27000,       27000, 0.0013,     0,  0],
'Hautes Alpes'    : [pcibf/3.6, 1.2,   100,   115,       15000,       21000, 0.0013,     0,  0],
'Alpes Hte Provence':[pcibf/3.6,1.2,    88,   115,       26000,       37000, 0.0013,     0,  0],
'Autres1'         : [pcibf/3.6, 1.2,   116,   115,       27000,       27000, 0.0013,     0,  0],
'Autres2'         : [pcibf/3.6, 1.2,   156,   115,       56000,       56000, 0.0013,     0,  0],
'Autres3'         : [pcibf/3.6, 1.2,   196,   115,       93000,       93000, 0.0013,     0,  0],
'rv1'             : [pcirv/3.6, 1.4,   115,  43.2,GRB.INFINITY,       30000, 0.0017,  1000,  0],
'rv2'             : [pcirv/3.6, 1.4,   115,  43.2,GRB.INFINITY,       30000, 0.0017,    40,  0],
'rv3'             : [pcirv/3.6, 1.4,   115,  43.2,GRB.INFINITY,       30000, 0.0001,     0,  0],
'rv4'             : [pcirv/3.6, 1.4,   115,  43.2,GRB.INFINITY,       30000, 0.0001,     0,  0],
'rv5'             : [pcirv/3.6, 1.4,   115,  43.2,GRB.INFINITY,       30000, 0.0001,     0,  0],
'br'              : [pcibr/3.6,   1,    12,   115,       85000,      240000, 0.0001,     0,  0]
})

boisfrais = ['MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']
boisrecycle = ['br']
charbon = ['charbon']
boistorrefie = ['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =['rv1','rv2','rv3','rv4','rv5']
sechage =  ['rv1','rv2','rv3','rv4','rv5','MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']
biomasse = ['MA','Cévennes30','Cévennes48','Cévennes07','br','Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie','rv1','rv2','rv3','rv4','rv5']
nonregion=[]
region=[]
for c in biomasse:
    if (mer[c]+route[c])>= 400:
        nonregion.append(c)
    else :
        region.append(c)
#------FONCTION DE PROFIT-----

def profit(c):
    return pci[c]*eff*vente[c] - achat[c]
#profit après séchage de la biomasse avec un pci de 5% humidité (spci)
def sprofit(c):
    return spci*eff*vente[c] - achat[c]


#------VARIABLES DECISIONNELLES RELLES-----

C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#variable de masse séchée,S, (après le séchage) et non séchée, NS, pour chaque année pour chaque combustible 
S=model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
NS=model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#masse régionnale R ou non régionnale NR de biomasse achetée
R = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
NR = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)

#-------VARIABLES DECISIONNELLES BINAIRES -----

#variables binaires d'achat de capacité de stockage modéré s50 ou grand s150
s50 = model.addVars (20,lb = 0, vtype = GRB.BINARY)
s150 = model.addVars (20,lb = 0, vtype = GRB.BINARY)
#variable binaire de la capacité de stockage doublée ou non. Vaut 1 si le stockage double est rentable
stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
quot = model.addVar (lb = 0, vtype = GRB.BINARY)
#variable de masse séchée pour chaque année pour chaque combustible 
nr = model.addVars (combustible,lb = 0, vtype = GRB.BINARY)  

#-----CONTRAINTES------

#Pas plus de 5 séchoirs, de quelconque capacité
model.addConstr(sum(s50[i] for i in range(durée))+sum(s150[i] for i in range(durée)) <= 5)

for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(sum(pci[c]*C[c,i] for c in combustible) == prod)
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-(ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert)))  >= 0)
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)) <= 1500*365*(1+stock))
   
    #il faut que la somme de la masse séchée à l'année i soit inférieur à la capcité de stockage mis en place les années précédentes
    model.addConstr(sum(eau[c]*S[c,i] for c in combustible) <= sum(s50[j] for j in range(0,i-1))*50000+sum(s150[j] for j in range(0,i-1))*150000)
    
    if i < 10:
            #je veux 60% de R sur l'ensemble de la biomasse soit R/C = 0,6 donc R - 0,6C = 0
            model.addConstr((sum(C[c,i] for c in region))  <= 0.6*(sum(C[c,i] for c in biomasse)))
    if i > 10:
           model.addConstr((sum(C[c,i] for c in region))  >= (sum(C[c,i] for c in biomasse)))
           
    model.addConstr((sum(C[c,i] for c in region))+(sum(C[c,i] for c in nonregion))==(sum(C[c,i] for c in biomasse)))
    
    for c in sechage:
    #contrainte de séchage 
    #je veux que la masse séchée, plus le poids d'eau perdu, plus la masse non séchée soit égale a la masse achetée
    ## CHANGER NS par C-S*(1-eau)
        model.addConstr(eau[c]*S[c,i]+NS[c,i]  == C[c,i] )
    
    #valeur de disponibilité
    for c in combustible :
        if i < 10: #du coup on se retrouve < 2026
            model.addConstr(C[c,i] <= dispo1[c])
        elif i > 10:
            model.addConstr(C[c,i] <= dispo2[c])
        
    #GES
    if i <5:
        Quota.append(80000-quicksum(ges[c]*C[c,i] for c in combustible))
    elif i >=5 and i <10:
        Quota.append(6000-quicksum(ges[c]*C[c,i] for c in combustible))
    elif i >=10 and i <15:
        Quota.append(4000-quicksum(ges[c]*C[c,i] for c in combustible))                                                             
    elif i >=15 :
        Quota.append(2000-quicksum(ges[c]*C[c,i] for c in combustible))
        #rajouter variabile binaire pour si pas de benef on le fait pas
        

model.setObjective(quot*sum(5*Quota[i] for i in range(20))
                  
                   +sum(profit(c)*C[c,i] for c in combustible for i in range(20))
                   
                   +sum(profit(c)*C[c,i] for c in region)+sum(profit(c)*C[c,i] for c in nonregion)-sum(profit(c)*C[c,i] for c in biomasse)
                   
                   +quicksum(profit(c)*NS[c,i] for c in sechage for i in range(20))+quicksum((-eau[c]*profit(c)+sprofit(c))*S[c,i] for c in sechage for i in range(20)) -sum(s50[i] for i in range(20))*300000 -sum(s150[i] for i in range(20))*600000
                   
                   - CF - stock*invest,GRB.MAXIMIZE)

model.optimize()

print('------OPTI ECONOMIQUE ---------')
print()
Obj=model.getObjective()
Opti=Obj.getValue()
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")

"""
-------AFFICHE LES MASSES DE COMBUSTIBLES ACHETEES ----
for c in combustible:
    print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")
"""

"""
------ TEST CALCUL DU QUOTA -----
quota=[]    
for i in range(20):
    if i <5:
        quota.append(80000-quicksum(ges[c]*C[c,i].x for c in combustible))
    elif i >=5 and i <10:
        quota.append(60000-quicksum(ges[c]*C[c,i].x for c in combustible))
    elif i >=10 and i <15:
        quota.append(40000-quicksum(ges[c]*C[c,i].x for c in combustible))                                                             
    elif i >=15 :
        quota.append(20000-quicksum(ges[c]*C[c,i].x for c in combustible))
        #rajouter variabile binaire pour si pas de benef on le fait pas 
s=0
for i in quota:
    s=s+i
print('valeur de quota', LinExpr.getValue(s))
print('quot : variable de prise en compte quota carbone', quot.x)
"""

"""
-----TEST AFFICHAGE DES MASSES SECHEES OU NON / COMBUSTIBLES -----
for c in sechage:
    print('masse achetée',c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")
    print('masse séchée',c, int((sum(S[c,i].x for i in range(20)))/1000),"Kt")
    print('masse NON séchée',c, int((sum(NS[c,i].x for i in range(20)))/1000),"Kt")
    print()"""


"""
-----TEST AFFICHAGE DES MASSES SECHEES OU NON / TOTAL -----
print('-----recap')
print('masse  achetée', int((sum(C[c,i].x for i in range(20) for c in sechage))/1000),"Kt")    
print('masse  séchée', int((1.2*sum(S[c,i].x for i in range(20) for c in boisfrais)/1000)+1.4*sum(S[c,i].x for i in range(20) for c in residuvert)/1000),"Kt")
print('masse NON séchée', int((sum(NS[c,i].x for i in range(20) for c in sechage))/1000),"Kt")
"""
print('biomasse achetée',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in biomasse))/1000))
print('biomasse R',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in region))/1000))
print('biomasse NR',int(LinExpr.getValue(sum(C[c,i] for i in range(20) for c in nonregion))/1000))

for c in biomasse :
    print(c,nr[c].x)

  
for i in range(durée):
    print()
    print(i,'ans')
    if sum(C[c,i].x for c in biomasse) != 0:
        print(sum(C[c,i].x for c in region)/sum(C[c,i].x for c in biomasse))

"""
------TEST AFFICHAGE DES CAPACITES DE STOCKAGE------
for i in range(durée):
    print(s50[i])
    print(s150[i])
#capacité totale de sechage sur les 20ans
print(LinExpr.getValue(sum(s50[i] for i in range(20)))*50000+LinExpr.getValue(sum(s150[i] for i in range(20)))*150000)
"""