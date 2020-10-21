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
        'charbon':  [25,75,43.2,GRB.INFINITY,30000,3],
        'Caroline-du-Sud': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Brésil': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Québec': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Canada Pacifique': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Portugal' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Russie': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'MA' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Cévennes30' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Cévennes48' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'Cévennes07': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'rv1' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'rv2' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'rv3' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'rv4' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'rv5' : [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'br': [25/3.6,75,43.2,GRB.INFINITY,30000,10**(-6)],
        'MAseche':[16.95,75,43.2,GRB.INFINITY,30000,10**(-6)],
})

boisfrais = ['MA','Cévennes30','Cévennes48','Cévennes07']
boisrecycle = ['br']
charbon = ['charbon']
boistorrefie = ['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =['rv1','rv2','rv3','rv4','rv5']
boisfrais_sec=['MAseche']
 
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

#variables séchage

nombre_petit_secheur=model.addVars(20,lb=0,vtype = GRB.INTEGER)
nombre_petit_secheur_achete=model.addVars(20,lb=0,vtype = GRB.INTEGER)
nombre_gros_secheur=model.addVars(20,lb=0,vtype = GRB.INTEGER)
nombre_gros_secheur_achete=model.addVars(20,lb=0,vtype = GRB.INTEGER)
X2=model.addVar(vtype=GRB.BINARY)




quota=[]
    

for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(quicksum(pci[c]*C[c,i] for c in combustible) == prod)
    
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert)+sum(C[c,i] for c in boisfrais_sec))  >= 0)
    
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)+(sum(C[c,i] for c in boisfrais_sec))) <= 1500*365*(1+stock))
    
    #Conditionne les couts variables de biomasse
    model.addConstr(0.5*sum(C[c,i] for c in combustible)>=sum(C[c,i] for c in combustible)-C['charbon',i]-300000000*X1)
    
    
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
    nombre_petit_secheur[i+1]=nombre_petit_secheur[i]+nombre_petit_secheur_achete[i]
    nombre_gros_secheur[i+1]=nombre_gros_secheur[i]+nombre_gros_secheur_achete[i]
    model.addConstr(nombre_petit_secheur[i]+nombre_gros_secheur[i]<=5)
    model.addConstr((quicksum(C[c,i] for c in boisfrais_sec)<=3000000000000-300000000000*(1-X2)))
    
    
    
    
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
    