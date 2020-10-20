"""@author: guillaume.thomas, sophie.chlela, guillaume.falandry
"""
from gurobipy import *


gdispo = 700000
coutfixeg = 100000
ff = 0.38
prod = 990000/eff
ratiocmin = 0.1



provenance_g, prix_g, cout_fixe_g, dispo_g, mer_g, route_g, ges_variable_g=multidict({
    'g_caro': [190,100,700,7000,250,0.015*10**(-3)*7000+(0.09*10**(-3))*250],
    'g_bresil': [170,120,600,8500,1000,0.015*10**(-3)*8500+0.09*10**(-3)*1000],
    'g_quebec': [180,110,450,5000,500,0.015*10**(-3)*5000+0.09*10**(-3)*500],
    'g_canada': [250,100,1000,16500,800,0.015*10**(-3)*16500+0.09*10**(-3)*800],
    'g_portugal': [240,5,350,0,1700,0.09*10**(-3)*1700],
    'g_russie': [300,6,600,0,3000,0.09*10**(-3)*3000],
    })
provenance_bf, prix, dispo_pre2025, dispo_pre2025,route,ges_variable_bf=multidict({
    'aigual': [128,18,21,230,],
    'cevennes 30': [120,21,43,210,0.16*10**(-3)*210],
    'cevennes 48': [128,12,75,230,0.16*10**(-3)*230],
    'cevennes 07 ': [116,8,56,200,0.16*10**(-3)*200],
    'bouches du rhone': [44,47,51,20,0.16*10**(-3)*20],
    'vaucluse': [76,24,28,100,0.16*10**(-3)*100],
    'var': [60,27,27,60,0.16*10**(-3)*60],
    'hautes alpes': [100,15,21,160,0.16*10**(-3)*160],
    'alpes hte pv': [88,26,37,130,0.16*10**(-3)*130],
    'autres 1': [116,27,27,200,0.16*10**(-3)*200],
    'autres 2': [156,56,56,300,0.16*10**(-3)*300],
    'autres 3': [196,93,93,400,0.16*10**(-3)*400],
    })
combustible, pci, achat, vente, ges_prod, ges_variable = multidict({
        'c':  [25/3.6, 75, 43.2,3],
        'g': [18/3.6, 190, 750,1.7*10**(-3)],
        'g_caro': [18/3.6, 190, 75,1.7*10**(-3),0.015*10**(-3)*mer_g['g_caro']+(0.09*10**(-3))*route_g['g_caro']],
        'g_bresil': [18/3.6, 170, 75,1.7*10**(-3),0.015*10**(-3)*mer_g['g_bresil']+(0.09*10**(-3))*route_g['g_bresil']],
        'g_quebec': [18/3.6, 180, 75,1.7*10**(-3),0.015*10**(-3)*mer_g['g_quebec']+(0.09*10**(-3))*route_g['g_quebec']],
        'g_canada': [18/3.6, 250, 75,1.7*10**(-3),0.015*10**(-3)*mer_g['g_canada']+(0.09*10**(-3))*route_g['g_canada']],
        'g_portugal': [18/3.6, 240, 75,1.7*10**(-3),0.015*10**(-3)*mer_g['g_portugal']+(0.09*10**(-3))*route_g['g_portugal']],
        'g_russie': [18/3.6, 300, 75,1.7*10**(-3),0.015*10**(-3)*mer_g['g_russie']+(0.09*10**(-3))*route_g['g_russie']],
        'aigual':[18/3.6,128,75,1.3*10**(-3),0.16*10**(-3)*route['aigual']],
        'cevennes 30':[18/3.6,120,75,1.3*10**(-3),0.16*10**(-3)*route['cevennes 30']],
        'cevennes 48':[18/3.6,128,75,1.3*10**(-3),0.16*10**(-3)*route['cevennes 48']],
        'cevennes 07 ':[18/3.6,116,75,1.3*10**(-3),0.16*10**(-3)*route['cevennes 07 ']],
        'bouches du rhone':[18/3.6,44,75,1.3*10**(-3),0.16*10**(-3)*route['bouches du rhone']],
        'vaucluse':[18/3.6,76,75,1.3*10**(-3),0.16*10**(-3)*route['vaucluse']],
        'var':[18/3.6,60,75,1.3*10**(-3),0.16*10**(-3)*route['var']],
        'hautes alpes':[18/3.6,100,75,1.3*10**(-3),0.16*10**(-3)*route['hautes alpes']],
        'alpes hte pv':[18/3.6,88,75,1.3*10**(-3),0.16*10**(-3)*route['alpes hte pv']],
        'autres 1':[18/3.6,116,75,1.3*10**(-3),0.16*10**(-3)*route['autres 1']],
        'autres 2':[18/3.6,156,75,1.3*10**(-3),0.16*10**(-3)*route['autres 2']],
        'autres 3':[18/3.6,196,75,1.3*10**(-3),0.16*10**(-3)*route['autres 3']],
        
})

def profit(c):
    return pci[c]*eff*vente[c] - achat[c]


def ges(c):
    return ges_prod(c)+ges_variable[c]

coco = Model('COCOmbustion')
coco.modelSense = GRB.MAXIMIZE
X = coco.addVars(combustible, 20, lb=0, vtype=GRB.CONTINUOUS)
X1 = (lb=0,vtype=GRB.BINARY)
F_X1=(lb=215*prod,ub=430*prod)
Quota=[]


    

for i in range(20):
    
    coco.addConstr(quicksum(pci[c]*X[c,i] for c in combustible) == prod)
    coco.addConstr((1-ratiocmin)*X['c',i] - ratiocmin*X['g',i] >= 0)
    coco.addConstr(X['g',i] - gdispo <= 0)
    coco.addConstr(0.5*(sum(X[c,i]) for c in combustible)<=X['b',i]-300000*X1)
    coco.addConstr(F_X1>=215'ETotale'+'ETotale'(430-215)*X1)
    if i <5:
        coco.addConstr(quicksum(ges[c]*X[c,i] for c in combustible))<=80000 
        
    elif i >=5 and i <10
        coco.addConstr(quicksum(ges[c]*X[c,i] for c in combustible))<=60000 
        Quota.append(80000-quicksum(ges[c]*X[c,i] for c in combustible)
    elif i >=10 and i <15:
        coco.addConstr(quicksum(ges[c]*X[c,i] for c in combustible))<=40000
        Quota.append(80000-quicksum(ges[c]*X[c,i] for c in combustible)                                                                  
    elif i >=15 :
        coco.addConstr(quicksum(ges[c]*X[c,i] for c in combustible))<=20000 
        Quota.append(80000-quicksum(ges[c]*X[c,i] for c in combustible)
                                                                     
                                                                     
                                                                     
coco.setObjective(sum(5*Quota[i] for i in range(20))+quicksum(profit(c)*X[c,i] for c in combustible for i in range(20)) - coutfixeg,
                  GRB.MAXIMIZE)

        
coco.optimize()


print('------OPTI ECONOMIQUE ---------')
print()

Obj=coco.getObjective()
Opti=Obj.getValue()
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")



