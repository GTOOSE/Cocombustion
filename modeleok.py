

from gurobipy import *


model = Model('COCOmbustion')
model.modelSense = GRB.MAXIMIZE
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
s1 = model.addVars (20,lb = 0, vtype = GRB.BINARY)
s2 = model.addVars (20,lb = 0, vtype = GRB.BINARY)
s3 = model.addVars (20,lb = 0, vtype = GRB.BINARY)

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

combustible, pci, achat, vente, dispo1, dispo2, ges = multidict({
        'charbon':  [2/3.6,75,43.2,GRB.INFINITY,GRB.INFINITY,3],
        'Caroline-du-Sud': [pcibt/3.6,190,115,700000,700000,0.0017],
        'Brésil': [pcibt/3.6,170,115,600000,600000,0.0017],
        'Québec': [pcibt/3.6,180,115,450000,450000,0.0017],
        'Canada Pacifique': [pcibt/3.6,250,115,1000000,1000000,0.0017],
        'Portugal' : [pcibt/3.6,240,115,350000,350000,0.0017],
        'Russie': [pcibt/3.6,300,115,600000,600000,0.0017],
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


C = model.addVars (combustible, 20, lb =0, vtype= GRB.CONTINUOUS)

        

stock = model.addVar (lb = 0, vtype = GRB.BINARY)   
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
quot = model.addVar (lb = 0, vtype = GRB.BINARY)
#Vaut 1 si le carbone devient un bénéfice, 0 sinon. Inséré dans objectif
quot = model.addVar (lb = 0, vtype = GRB.BINARY)

L=100000000

for i in range(durée):
    #Assure la production énergétique pour chaque année i
    model.addConstr(quicksum(pci[c]*C[c,i] for c in combustible) == prod)
    
    #Assure les 10% de charbon pour chaque année i 
    model.addConstr((1-ratiocmin)*(sum(C[c,i] for c in charbon))-(ratiocmin*(sum(C[c,i] for c in boisfrais)+sum(C[c,i] for c in boisrecycle)+sum(C[c,i] for c in boistorrefie)+sum(C[c,i] for c in residuvert)))  >= 0)
    
    #Assure le stockage pour chaque jour i/365
    model.addConstr((sum(C[c,i] for c in boisrecycle))+(sum(C[c,i] for c in boistorrefie)) + (sum(C[c,i] for c in residuvert)) <= 1500*365*(1+stock))
    
    #contrainte sur les masse de biomasse pour le sechage 
    model.addConstr(s1[i]+s2[i]+s3[i] == 1)
    
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
        
        
#masse bois frais et résidus verts
m1=(quicksum(C[c,i] for c in boisfrais for i in range(20)))+(quicksum(C[c,i] for c in residuvert for i in range(20)))
#50kt possible par le sechage 1
m2=50000
m3=150000

pcibf1=18-21*0.4
pcibf2=18-21*0.05
pcibf3=18-21*0.05

#benef sans le sechage
benef1 = m1*pcibf1
#benef avec sechage
benef2 = m2*pcibf2+(m1-m2)*pcibf1-300
benef3 = m3*pcibf3+(m1-m3)*pcibf1-600




model.setObjective((s2[i]*benef1+s1[i]*benef2+s3[i]*benef3)+quot*sum(5*Quota[i] for i in range(20))+quicksum(profit(c)*C[c,i] for c in combustible for i in range(20))-quicksum(profit(c)*C[c,i] for c in boisfrais for i in range(20))- CF - stock*invest,GRB.MAXIMIZE)

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
s11=0
s22=0
s33=0
for i in range(20):
    s11 = s11+s1[i]
    s22 = s22+s2[i]
    s33 = s33+s3[i]

print(LinExpr.getValue(s11))
print(LinExpr.getValue(s22))
print(LinExpr.getValue(s33))



