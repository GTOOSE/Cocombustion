

from gurobipy import *

CF = 10050000        #cout fixe en euros O&M liés à la capacité de la centrale
eff = 0.38            #efficacité énergétique
prod = 990000/eff
ratiocmin = 0.1      # ratio carbone dans le LFC
durée = 20
Quota=[]
pcibf = 8-21*0.2
pcirv = 8 - 21*0.4
pcibr = 8 - 21*0.05
invest = 50000

combustible, pci, achat, vente, dispo1, dispo2, ges = multidict({
        'charbon':  [25/3.6,75,43.2,GRB.INFINITY,GRB.INFINITY,3],
        'Caroline-du-Sud': [18/3.6,190,115,700000,700000,0.0017],
        'Brésil': [18/3.6,170,115,600000,600000,0.0017],
        'Québec': [18/3.6,180,115,450000,450000,0.0017],
        'Canada Pacifique': [18/3.6,250,115,1000000,1000000,0.0017],
        'Portugal' : [18/3.6,240,115,350000,350000,0.0017],
        'Russie': [18/3.6,300,115,600000,600000,0.0017],
        'MA' : [pcibf/3.6,128,115,18000,21000,0.0013],
        'Cévennes30' : [pcibf/3.6,120,115,21000,43000,0.0013],
        'Cévennes48' : [pcibf/3.6,128,115,12000,75000,0.0013],
        'Cévennes07': [pcibf/3.6,116,115,47000,56000,0.0013],
        'Bouche du Rhone': [pcibf/3.6,44,115,47000,51000,0.0013],
        'Vaucluse': [pcibf/3.6,76,115,24000,28000,0.0013],
        'Var': [pcibf/3.6,60,115,27000,27000,0.0013],
        'Hautes Alpes': [pcibf/3.6,100,115,15000,21000,0.0013],
        'Alpes Hte Provence': [pcibf/3.6,88,115,26000,37000,0.0013],
        'Autres1': [pcibf/3.6,116,115,27000,27000,0.0013],
        'Autres2': [pcibf/3.6,156,115,56000,56000,0.0013],
        'Autres3': [pcibf/3.6,196,115,93000,93000,0.0013],
        'rv1' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0017],
        'rv2' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0017],
        'rv3' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0001],
        'rv4' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0001],
        'rv5' : [25/3.6,115,43.2,GRB.INFINITY,30000,0.0001],
        'br': [pcibr/3.6,12,115,85000,240000,0.0001]
})

boisfrais = ['MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']
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

C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)

        

stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
investment = model.addVar (lb = 0, vtype = GRB.CONTINUOUS)

for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(quicksum(pci[c]*C[c,i] for c in combustible) == prod)
    
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-(ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert)))  >= 0)
    
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)) <= 1500*365*(1+stock))
    
    #GES
    if i <5:
        model.addConstr(quicksum(ges[c]*C[c,i] for c in combustible)<=800000 )
        Quota.append(800000-quicksum(ges[c]*C[c,i] for c in combustible))
        
    elif i >=5 and i <10:
        model.addConstr(quicksum(ges[c]*C[c,i] for c in combustible)<=600000) 
        Quota.append(600000-quicksum(ges[c]*C[c,i] for c in combustible))
                         
    elif i >=10 and i <15:
        model.addConstr(quicksum(ges[c]*C[c,i] for c in combustible)<=400000)
        Quota.append(400000-quicksum(ges[c]*C[c,i] for c in combustible)     )                                                             
    elif i >=15 :
        model.addConstr(quicksum(ges[c]*C[c,i] for c in combustible)<=200000 )
        Quota.append(200000-quicksum(ges[c]*C[c,i] for c in combustible))

model.setObjective(sum(5*Quota[i] for i in range(20))+quicksum(profit(c)*C[c,i] for c in combustible for i in range(20))- CF - stock*invest,GRB.MAXIMIZE)

model.optimize()

print('------OPTI ECONOMIQUE ---------')
print()
Obj=model.getObjective()
Opti=Obj.getValue()
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")

for c in combustible:
    print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")



