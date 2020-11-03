#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 14:24:26 2020

@author: guillaumefalandry
"""


from gurobipy import *
import numpy as np

CF = 10050000        #cout fixe en euros O&M liés à la capacité de la centrale
eff = 0.38            #efficacité énergétique
prod = 990000/eff
ratiocmin = 0.1      # ratio carbone dans le LFC
durée = 20
pcibt=15.96
pcibf=13
pcibr=12

Couts_Var = ['CV1', 'CV2']
Investissements = ['Stockage', 'Séchage']

combustible, pci, achat, vente, dispo1, dispo2, ges, route, mer = multidict({
         'charbon':  [2/3.6,75,43.2,GRB.INFINITY,GRB.INFINITY,3, 0, 0],
         'Caroline-du-Sud': [pcibt/3.6,190,115,700000,700000,0.0017, 250, 7000],
         'Brésil': [pcibt/3.6,170,115,600000,600000,0.0017, 1000, 8500],
         'Québec': [pcibt/3.6,180,115,450000,450000,0.0017, 500, 5000],
         'Canada Pacifique': [pcibt/3.6,250,115,1000000,1000000,0.0017, 800, 16500],
         'Portugal' : [pcibt/3.6,240,115,350000,350000,0.0017, 1700, 0],
         'Russie': [pcibt/3.6,300,115,600000,600000,0.0017, 3000, 0],
         'MA' : [pcibf/3.6,128,115,18000,21000,0.0013, 230, 0],
         'Cévennes30' : [pcibf/3.6,120,115,21000,43000,0.0013, 210, 0],
         'Cévennes48' : [pcibf/3.6,128,115,12000,75000,0.0013, 230, 0],
         'Cévennes07': [pcibf/3.6,116,115,47000,56000,0.0013, 200, 0],
         'Bouche du Rhone': [pcibf/3.6,44,115,47000,51000,0.0013, 20, 0],
         'Vaucluse': [pcibf/3.6,76,115,24000,28000,0.0013, 100, 0],
         'Var': [pcibf/3.6,60,115,27000,27000,0.0013, 60, 0],
         'Hautes Alpes': [pcibf/3.6,100,115,15000,21000,0.0013, 160, 0],
         'Alpes Hte Provence': [pcibf/3.6,88,115,26000,37000,0.0013, 130, 0],
         'Autres1': [pcibf/3.6,116,115,27000,27000,0.0013, 200, 0],
         'Autres2': [pcibf/3.6,156,115,56000,56000,0.0013, 300, 0],
         'Autres3': [pcibf/3.6,196,115,93000,93000,0.0013, 400, 0],
         'rv1' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0017, 10, 0],
         'rv2' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0017, 20, 0],
         'rv3' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0001, 30, 0],
         'rv4' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0001, 50, 0],
         'rv5' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0001, 80, 0],
         'br': [pcibr/3.6,12,115,85000,240000,0.0001, 0, 0]
 })

dispo_rv=np.array([1000,7000,22000,29000,52000,57000,143000,210000,313000])
prix_rv=np.array([4,7,10,16,25,31,46,61,76])


boisfrais = ['MA','Cévennes30','Cévennes48','Cévennes07']
boisrecycle = ['br']
charbon = ['charbon']
boistorrefie = ['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =['rv1','rv2','rv3','rv4','rv5']

biomasse = [boistorrefie, residuvert, boisfrais]
def profit(c):
     return pci[c]*eff*vente[c] - achat[c]


def dispo_bio (provenance, année):
     return dispo [provenance] if année <= 5 else dispo2 [provenance]
 


model = Model('COCOmbustion')
model.modelSense = GRB.MAXIMIZE



#Variale masse des combustibles
C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#masse régionnale de biomasse achetée
R = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#Variales investissement stockage

stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
investment = model.addVar (lb = 0, vtype = GRB.CONTINUOUS)

#variables incorporation biomasse
X1=model.addVar(vtype=GRB.BINARY)
cout_variable_incorp=model.addVar(lb=215/3600*prod,ub=430/3600*prod)

#variables séchage

nombre_petit_secheur=model.addVars(20,lb=0,vtype = GRB.INTEGER)
nombre_petit_secheur_achete=model.addVars(20,lb=0,vtype = GRB.INTEGER)
nombre_gros_secheur=model.addVars(20,lb=0,vtype = GRB.INTEGER)
nombre_gros_secheur_achete=model.addVars(20,lb=0,vtype = GRB.INTEGER)
X2=model.addVar(vtype=GRB.BINARY)
périmètre = model.addVar (vtype = GRB.BINARY)

# variables pour les résidus verts
lambda_rv=model.addVars(9,20,lb=0,ub=1,vtype=GRB.CONTINUOUS)
for i in range(20):
    model.addSOS(GRB.SOS_TYPE2,[lambda_rv[j,i] for j in range(9)])

prix_total_rv=dispo_rv*prix_rv


quota=[]


for i in range(durée):
     #Assure la production énergétique pour chaque année i
     model.addConstr(quicksum(pci[c]*C[c,i] for c in combustible) == prod)

     #Assure les 10% de charbon pour chaque année i 
     model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert))>= 0)

     #Assure le stockage pour chaque jour i/365
     model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)) <= 1500*365*(1+stock))

     #Conditionne les couts variables de biomasse
     model.addConstr(0.5*sum(C[c,i] for c in combustible)>=sum(C[c,i] for c in combustible)-C['charbon',i]-300000000*X1)

     for r in biomasse:
         if i < 10:
             model.addConstr ((route [r]  + mer [r]) <= 400 (1-périmètre))
             model.addConstr(R[c,i]*périmètre >= 0.6*C[c,i])


    

    #contraintes ges

     if i<5:
         quota.append(80000-quicksum(ges[c]*C[c,i] for c in combustible))
     if i>=5 and i<10:
         quota.append(60000-quicksum(ges[c]*C[c,i] for c in combustible))
     if i>=10 and i<15:
         quota.append(40000-quicksum(ges[c]*C[c,i] for c in combustible))
     if i>=15:
         quota.append(20000-quicksum(ges[c]*C[c,i] for c in combustible))
     #contraintes sur les secheurs
     """nombre_petit_secheur[i+1]=nombre_petit_secheur[i]+nombre_petit_secheur_achete[i]
     nombre_gros_secheur[i+1]=nombre_gros_secheur[i]+nombre_gros_secheur_achete[i]
     model.addConstr(nombre_petit_secheur[i]+nombre_gros_secheur[i]<=5)
     model.addConstr((quicksum(C[c,i] for c in boisfrais_sec)<=3000000000000-300000000000*(1-X2)))
"""
    #contrainte résidus vert
     model.addConstr(quicksum(lambda_rv[j,i] for j in range(9))==1)
     model.addConstr(C[c,i] for c in residuvert==quicksum(dispo_rv['j']*lambda_rv[j,i] for j in range(9)))
     cout_vert[i]=quicksum(prix_total_rv['j']*lambda_rv[j,i] for j in range(9))
     
model.setObjective(5*sum(quota[i] for i in range(20))+quicksum(profit(c)*C[c,i] for c in combustible for i in range(20))- CF-cout_variable_incorp*X1-X2*quicksum(nombre_gros_secheur[i]*600000+nombre_petit_secheur[i]*300000 for i in range(20)),GRB.MAXIMIZE)

model.optimize()

print('------OPTI ECONOMIQUE ---------')
print()
Obj=model.getObjective()
Opti=Obj.getValue()
print(X1.x)
print(X2.x)


print(nombre_petit_secheur[i].x for i in range(20))
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")
for c in combustible:
      print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")
