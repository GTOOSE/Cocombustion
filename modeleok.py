# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 15:37:06 2020

@author: guillaume.falandry
"""

from gurobipy import *

CF = 10050000        #cout fixe en euros O&M liés à la capacité de la centrale
eff = 0.38            #efficacité énergétique
prod = 990000/eff
ratiocmin = 0.1      # ratio carbone dans le LFC
durée = 20


Couts_Var = ['CV1', 'CV2']
Investissements = ['Stockage', 'Séchage']


combustible, pci, achat, vente, dispo1, dispo2, ges = multidict({
        'charbon':  [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Caroline-du-Sud': [25/3.6,75,4000000,GRB.INFINITY,30000,1,1],
        'Brésil': [25/3.6,75,43.2,GRB.INFINITY,30000,11,],
        'Québec': [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Canada Pacifique': [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Portugal' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Russie': [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'MA' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Cévennes30' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Cévennes48' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'Cévennes07': [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'rv1' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'rv2' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'rv3' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'rv4' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'rv5' : [25/3.6,75,43.2,GRB.INFINITY,30000,1,1],
        'br': [25/3.6,75,43.2,GRB.INFINITY,30000,1,1]
})

boisfrais = ['MA','Cévennes30','Cévennes48','Cévennes07']
boisrecycle = ['br']
charbon = ['charbon']
boistorrefie = ['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =['rv1','rv2','rv3','rv4','rv5']
 
def profit(c):
    return pci[c]*eff*vente[c] - achat[c]


def dispo_bio (provenance, année):
    return dispo [provenance] if année <= 5 else dispo2 [provenance]


model = Model('COCOmbustion')
model.modelSense = GRB.MAXIMIZE



#Variale masse des combustibles
C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)

        
#Variales investissement stockage

stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
investment = model.addVar (lb = 0, vtype = GRB.CONTINUOUS)

#variables incorporation biomasse
X1=model.addVar(vtype=GRB.BINARY)
cout_variable_incorp=model.addVar(lb=215/3600*prod,ub=430/3600*prod)


for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(quicksum(pci[c]*C[c,i] for c in combustible) == prod)
    
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert))  >= 0)
    
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)) <= 1500*365*(1+stock))
    
    #Conditionne les couts variables de biomasse
    model.addConstr(0.5*sum(C[c,i] for c in combustible)>=sum(C[c,i] for c in combustible)-C['charbon',i]-300000000*X1)
    
    
model.setObjective(quicksum(profit(c)*C[c,i] for c in combustible for i in range(20))- CF-cout_variable_incorp*X1,GRB.MAXIMIZE)

model.optimize()

print('------OPTI ECONOMIQUE ---------')
print()
Obj=model.getObjective()
Opti=Obj.getValue()
print(X1.x)
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")
for c in combustible:
    print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")