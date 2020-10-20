# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 17:43:42 2020

@author: Sof
"""

from gurobipy import *

CF = 10050000        #cout fixe en euros O&M liés à la capacité de la centrale
EE = 0.38            #efficacité énergétique
Prod = 990000/EE
ratiocmin = 0.1      # ratio carbone dans le LFC
durée = 20


Couts_Var = ['CV1', 'CV2']
Investissements = ['Stockage', 'Séchage']



charbon, PCI, achat, vente, dispo, GES = multidict({
        'charbon':  [25/3.6, 75, 43.2, GRB.INFINITY, 30000]})


bois_torréfiés, PCI, achat, cout_fixe, dispo, dispo2, mer, route, vente, GES_Prod, GES_Trans = multidict ({
    'Caroline-du-Sud': [18/3.6, 190, 100, 700, 700, 7000, 250, 115, 1.7, 0.015],
    'Brésil': [18/3.6, 170, 120, 600, 600, 8500, 1000, 115, 1.7, 0.015],
    'Québec': [18/3.6, 180, 110, 450, 450, 5000, 500, 115, 1.7, 0.015],
    'Canada Pacifique': [18/3.6, 250, 100, 1000, 1000, 16500, 800, 115, 1.7, 0.015],
    'Portugal' : [18/3.6, 240, 5, 350, 350, 0, 1700, 115, 1.7, 0.015],
    'Russie': [18/3.6, 300, 6, 600, 600, 0, 3000, 115, 1.7, 0.015]})

bois_frais, PCI, achat, dispo, dispo2, route, vente, GES_Prod, GES_Trans = multidict ({
    'MA' : [13.8/3.6, 128, 18, 21, 230, 115, 1.3, 0.16],
    'Cévennes30' : [13.8/3.6, 120, 21, 43, 210, 115, 1.3, 0.16],
    'Cévennes48' : [13.8/3.6, 128, 12, 75, 230, 115, 1.3, 0.16],
    'Cévennes07': [13.8/3.6, 116, 8, 56, 200, 115, 1.3, 0.16]})

résidus_verts, PCI, achat, dispo, dispo2, route, vente, GES_prod, GES_Trans = multidict ({
    'rv1' : [9.6/3.6, 4, 1, 1, 10, 115, 0.1, 0.16],
    'rv2' : [9.6/3.6, 7, 7, 7, 20, 115, 0.1, 0.16],
    'rv3' : [9.6/3.6, 10, 22, 22, 30, 115, 0.1, 0.16],
    'rv4' : [9.6/3.6, 16, 29, 29, 50, 115, 0.1, 0.16],
    'rv5' : [9.6/3.6, 25, 52, 52, 80, 115, 0.1, 0.16]})

bois_recyclé, PCI, achat, dispo, dispo2, vente, GES = multidict ({
    'br': [16.95/3.6, 12, 85, 240, 115, 10000]})

combustible = [charbon, bois_torréfiés, bois_frais, bois_recyclé, résidus_verts]
    
 
print (combustible)
def profit(c):
    return PCI[c]*eff*vente[c] - achat[c]

def dispo_bio (provenance, année):
    return dispo [provenance] if année <= 5 else dispo2 [provenance]


model = Model('COCOmbustion')
model.modelSense = GRB.MAXIMIZE




        X1 = model.addVars (charbon, 20, lb =0,  ub = dispo [c], vtype= GRB.CONTINUOUS)
  
        X2  = model.addVars (bois_torréfiés, 20, lb =0, ub = dispo_bio (t, i), vtype = GRB.CONTINUOUS)
   
        X3 = model.addVar (bois_frais, 20, lb =0, ub = dispo_bio (f, i), vtype = GRB.CONTINUOUS)
 
        X4 = model.addVar (résidus_verts, 20, lb = 0, ub = dispo_bio (v, i), vtype = GRB.CONTINUOUS)
   
        X5  = model.addVar (bois_recyclé, 20, lb = 0, ub = dispo_bio (r, i), vtype = GRB.CONTINUOUS)
        

    
x_invest = model.addVar(lb=0, vtype = GRB.BINARY) 
x_stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
investment = model.addVar (lb = 0, vtype = GRB.CONTINUOUS)

for i in range(durée):
    
    model.addConstr((PCI[c]*X1[c,i] for c in charbon) 
                             + (PCI [t]*X2[t, i] for t in bois_torréfiés)
                             + (PCI[f]*X3[f,i] for f in bois_frais)
                             + (PCI[v]* X4[v,i] for v in résidus_verts)
                             + (PCI [r]* X5[r, i] for r in bois_recyclé)
                             == prod)
    
    model.addConstr((1-ratiocmin)*X1[charbon,i] - ratiocmin*(X2[bois_torréfiés,i]+ X3[bois_frais,i]
                                                             + X4[bois_recylé,i] + X5[résidus_verts,i]) >= 0)
    
  
    model.addConstr ((x_invest >= 1))
    
    model.addConstr((x_ivest*ivestment >= 500000))
    
    model.addConstr((x_invest + 1)*X3[bois_frais,i]+ X4[bois_recylé,i] + X5[résidus_verts,i] <= 1500*365)
    
model.setObjective(quicksum(profit(c)*X[c,i] for c in combustible for i in range(20)) - coutfixeg - investment,
                  GRB.MAXIMIZE)
