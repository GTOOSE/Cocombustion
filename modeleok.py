

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
pcibr = 1-21*0.2
pcibf = 1-21*0.4
pcibt = 1
invest = 50000

combustible, pci,eau, achat, vente, dispo1, dispo2, ges= multidict({
        'charbon':  [2/3.6,1,75,43.2,GRB.INFINITY,GRB.INFINITY,3],
        'Caroline-du-Sud': [pcibt/3.6,1,190,115,0,700000,0.0017],
        'Brésil': [pcibt/3.6,1,170,115,0,600000,0.0017],
        'Québec': [pcibt/3.6,1,180,115,0,450000,0.0017],
        'Canada Pacifique': [pcibt/3.6,1,250,115,0,1000000,0.0017],
        'Portugal' : [pcibt/3.6,1,240,115,0,350000,0.0017],
        'Russie': [pcibt/3.6,1,300,115,0,600000,0.0017],
        'MA' : [pcibf/3.6,1.2,128,115,18000,21000,0.0013],
        'Cévennes30' : [pcibf/3.6,1.2,120,115,21000,43000,0.0013],
        'Cévennes48' : [pcibf/3.6,1.2,128,115,12000,75000,0.0013],
        'Cévennes07': [pcibf/3.6,1.2,116,115,47000,56000,0.0013],
        'Bouche du Rhone': [pcibf/3.6,1.2,44,115,47000,51000,0.0013],
        'Vaucluse': [pcibf/3.6,1.2,76,115,24000,28000,0.0013],
        'Var': [pcibf/3.6,1.2,60,115,27000,27000,0.0013],
        'Hautes Alpes': [pcibf/3.6,1.2,100,115,15000,21000,0.0013],
        'Alpes Hte Provence': [pcibf/3.6,1.2,88,115,26000,37000,0.0013],
        'Autres1': [pcibf/3.6,1.2,116,115,27000,27000,0.0013],
        'Autres2': [pcibf/3.6,1.2,156,115,56000,56000,0.0013],
        'Autres3': [pcibf/3.6,1.2,196,115,93000,93000,0.0013],
        'rv1' : [25/3.6,1.4,115,43.2,GRB.INFINITY,30000,0.0017],
        'rv2' : [25/3.6,1.4,115,43.2,GRB.INFINITY,30000,0.0017],
        'rv3' : [25/3.6,1.4,115,43.2,GRB.INFINITY,30000,0.0001],
        'rv4' : [25/3.6,1.4,115,43.2,GRB.INFINITY,30000,0.0001],
        'rv5' : [25/3.6,1.4,115,43.2,GRB.INFINITY,30000,0.0001],
        'br': [pcibr/3.6,1,12,115,85000,240000,0.0001]
})

boisfrais = ['MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']
boisrecycle = ['br']
charbon = ['charbon']
boistorrefie = ['Caroline-du-Sud','Brésil','Québec','Canada Pacifique','Portugal','Russie']
residuvert =['rv1','rv2','rv3','rv4','rv5']
sechage =  ['rv1','rv2','rv3','rv4','rv5','MA','Cévennes30','Cévennes48','Cévennes07','Bouche du Rhone','Vaucluse','Var','Hautes Alpes','Alpes Hte Provence','Autres1','Autres2','Autres3']

spci=18-21*0.05

def profit(c):
    return pci[c]*eff*vente[c] - achat[c]
def sprofit(c):
    return spci*eff*vente[c] - achat[c]

def dispo_bio (provenance, année):
    return dispo [provenance] if année <= 5 else dispo2 [provenance]

C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#variable de masse séchée (après le séchage) pour chaque année pour chaque combustible 
S=model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)
#variable de masse non séchée (avant le séchage) pour chaque année pour chaque combustible 
NS=model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)

stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
quot = model.addVar (lb = 0, vtype = GRB.BINARY)
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
quot = model.addVar (lb = 0, vtype = GRB.BINARY)
#variable de masse séchée pour chaque année pour chaque combustible 

for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(sum(pci[c]*C[c,i] for c in combustible) == prod)
    
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-(ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert)))  >= 0)
    
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)) <= 1500*365*(1+stock))
    #je veux pas plus de 150000kt dès la première année 
    model.addConstr(sum(1.2*S[c,i] for c in sechage) <= 150000)
        
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
                  
                   +quicksum(profit(c)*C[c,i] for c in combustible for i in range(20))
                   
                   +quicksum(profit(c)*NS[c,i] for c in sechage for i in range(20))+quicksum((-eau[c]*profit(c)+sprofit(c))*S[c,i] for c in sechage for i in range(20)) 
                   
                   - CF - stock*invest,GRB.MAXIMIZE)

model.optimize()

print('------OPTI ECONOMIQUE ---------')
print()
Obj=model.getObjective()
Opti=Obj.getValue()
print(f"Sur 20 ans le bénéfice est de : {Opti:.0f} euros")

for c in combustible:
    print(c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")

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

for c in sechage:
    print('masse achetée',c, int((sum(C[c,i].x for i in range(20)))/1000),"Kt")
    print('masse séchée',c, int((sum(S[c,i].x for i in range(20)))/1000),"Kt")
    print('masse NON séchée',c, int((sum(NS[c,i].x for i in range(20)))/1000),"Kt")
    print()
    


print('-----recap')
print('masse  achetée', int((sum(C[c,i].x for i in range(20) for c in sechage))/1000),"Kt")    
print('masse  séchée', int((1.2*sum(S[c,i].x for i in range(20) for c in boisfrais)/1000)+1.4*sum(S[c,i].x for i in range(20) for c in residuvert)/1000),"Kt")
print('masse NON séchée', int((sum(NS[c,i].x for i in range(20) for c in sechage))/1000),"Kt")
