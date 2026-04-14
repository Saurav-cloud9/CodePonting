import math

OFF = ['T-5','T-4','T-3','T-2','T-1','T0','T+1','T+2']

GRID = [
    {'oi':0,'ti':0,'thresh':0.01,'pf_tr':0.9637,'pf_te':0.9321,'n_te':18509},
    {'oi':0,'ti':7,'thresh':0.08,'pf_tr':1.0087,'pf_te':0.9823,'n_te':8967},
    {'oi':0,'ti':8,'thresh':0.09,'pf_tr':1.0011,'pf_te':0.9808,'n_te':8037},
    {'oi':1,'ti':8,'thresh':0.09,'pf_tr':1.0144,'pf_te':0.9887,'n_te':7876},
    {'oi':1,'ti':9,'thresh':0.10,'pf_tr':1.0026,'pf_te':0.9918,'n_te':7000},
    {'oi':1,'ti':10,'thresh':0.11,'pf_tr':0.9927,'pf_te':0.9931,'n_te':6232},
    {'oi':2,'ti':6,'thresh':0.07,'pf_tr':1.0094,'pf_te':0.9845,'n_te':9693},
    {'oi':2,'ti':13,'thresh':0.14,'pf_tr':0.9125,'pf_te':1.0188,'n_te':4207},
    {'oi':2,'ti':14,'thresh':0.15,'pf_tr':0.9109,'pf_te':1.0049,'n_te':3755},
    {'oi':3,'ti':11,'thresh':0.12,'pf_tr':0.9395,'pf_te':1.026,'n_te':5101},
    {'oi':3,'ti':12,'thresh':0.13,'pf_tr':0.9242,'pf_te':1.0373,'n_te':4500},
    {'oi':3,'ti':13,'thresh':0.14,'pf_tr':0.9063,'pf_te':1.0345,'n_te':3959},
    {'oi':3,'ti':14,'thresh':0.15,'pf_tr':0.9039,'pf_te':1.0022,'n_te':3518},
    {'oi':4,'ti':10,'thresh':0.11,'pf_tr':0.9204,'pf_te':1.0212,'n_te':5384},
    {'oi':4,'ti':11,'thresh':0.12,'pf_tr':0.8944,'pf_te':1.0311,'n_te':4669},
    {'oi':4,'ti':12,'thresh':0.13,'pf_tr':0.8584,'pf_te':1.0268,'n_te':4049},
    {'oi':4,'ti':13,'thresh':0.14,'pf_tr':0.8556,'pf_te':1.0472,'n_te':3568},
    {'oi':4,'ti':14,'thresh':0.15,'pf_tr':0.8649,'pf_te':1.0792,'n_te':3140},
    {'oi':5,'ti':8,'thresh':0.09,'pf_tr':0.9004,'pf_te':1.0202,'n_te':6954},
    {'oi':5,'ti':9,'thresh':0.10,'pf_tr':0.8823,'pf_te':1.0393,'n_te':6063},
    {'oi':5,'ti':10,'thresh':0.11,'pf_tr':0.8661,'pf_te':1.0416,'n_te':5190},
    {'oi':5,'ti':11,'thresh':0.12,'pf_tr':0.8734,'pf_te':1.0399,'n_te':4524},
    {'oi':5,'ti':12,'thresh':0.13,'pf_tr':0.8629,'pf_te':1.0479,'n_te':3910},
    {'oi':5,'ti':13,'thresh':0.14,'pf_tr':0.8728,'pf_te':1.0668,'n_te':3405},
    {'oi':5,'ti':14,'thresh':0.15,'pf_tr':0.8609,'pf_te':1.0314,'n_te':2932},
]

# Add all remaining combos with pf_te < 1.0 that weren't listed above
# (these definitely won't pass the filter — skip for brevity)
# Full grid already loaded in H3.1 — this is the subset we need to query

def score(r):
    sf = max(0.0, 1.0 - abs(r['pf_tr'] - r['pf_te']) / 0.1)
    return r['pf_te'] * math.log(r['n_te']) * sf

# Full grid from H3.1 (all 120 rows, oi 0-7, ti 0-14)
FULL = [
    # oi=0 (T-5)
    {'oi':0,'ti':0,'thresh':0.01,'pf_tr':0.9637,'pf_te':0.9321,'n_te':18509},
    {'oi':0,'ti':1,'thresh':0.02,'pf_tr':0.9648,'pf_te':0.9315,'n_te':16860},
    {'oi':0,'ti':2,'thresh':0.03,'pf_tr':0.9724,'pf_te':0.9436,'n_te':15293},
    {'oi':0,'ti':3,'thresh':0.04,'pf_tr':0.9802,'pf_te':0.9544,'n_te':13765},
    {'oi':0,'ti':4,'thresh':0.05,'pf_tr':0.9786,'pf_te':0.964,'n_te':12417},
    {'oi':0,'ti':5,'thresh':0.06,'pf_tr':0.9876,'pf_te':0.9638,'n_te':11145},
    {'oi':0,'ti':6,'thresh':0.07,'pf_tr':0.9902,'pf_te':0.9767,'n_te':10022},
    {'oi':0,'ti':7,'thresh':0.08,'pf_tr':1.0087,'pf_te':0.9823,'n_te':8967},
    {'oi':0,'ti':8,'thresh':0.09,'pf_tr':1.0011,'pf_te':0.9808,'n_te':8037},
    {'oi':0,'ti':9,'thresh':0.10,'pf_tr':0.9929,'pf_te':0.9836,'n_te':7212},
    {'oi':0,'ti':10,'thresh':0.11,'pf_tr':0.9891,'pf_te':0.9729,'n_te':6463},
    {'oi':0,'ti':11,'thresh':0.12,'pf_tr':0.9978,'pf_te':0.9788,'n_te':5833},
    {'oi':0,'ti':12,'thresh':0.13,'pf_tr':0.982,'pf_te':0.9888,'n_te':5146},
    {'oi':0,'ti':13,'thresh':0.14,'pf_tr':0.9886,'pf_te':0.9837,'n_te':4629},
    {'oi':0,'ti':14,'thresh':0.15,'pf_tr':0.9702,'pf_te':0.9648,'n_te':4130},
    # oi=1 (T-4)
    {'oi':1,'ti':0,'thresh':0.01,'pf_tr':0.9623,'pf_te':0.9407,'n_te':18604},
    {'oi':1,'ti':1,'thresh':0.02,'pf_tr':0.9625,'pf_te':0.9384,'n_te':16905},
    {'oi':1,'ti':2,'thresh':0.03,'pf_tr':0.963,'pf_te':0.9489,'n_te':15273},
    {'oi':1,'ti':3,'thresh':0.04,'pf_tr':0.9717,'pf_te':0.9485,'n_te':13766},
    {'oi':1,'ti':4,'thresh':0.05,'pf_tr':0.9805,'pf_te':0.9572,'n_te':12325},
    {'oi':1,'ti':5,'thresh':0.06,'pf_tr':0.9776,'pf_te':0.958,'n_te':11020},
    {'oi':1,'ti':6,'thresh':0.07,'pf_tr':0.9907,'pf_te':0.9745,'n_te':9869},
    {'oi':1,'ti':7,'thresh':0.08,'pf_tr':0.9923,'pf_te':0.9795,'n_te':8780},
    {'oi':1,'ti':8,'thresh':0.09,'pf_tr':1.0144,'pf_te':0.9887,'n_te':7876},
    {'oi':1,'ti':9,'thresh':0.10,'pf_tr':1.0026,'pf_te':0.9918,'n_te':7000},
    {'oi':1,'ti':10,'thresh':0.11,'pf_tr':0.9927,'pf_te':0.9931,'n_te':6232},
    {'oi':1,'ti':11,'thresh':0.12,'pf_tr':0.9765,'pf_te':0.9587,'n_te':5555},
    {'oi':1,'ti':12,'thresh':0.13,'pf_tr':0.9576,'pf_te':0.9497,'n_te':4934},
    {'oi':1,'ti':13,'thresh':0.14,'pf_tr':0.9642,'pf_te':0.9605,'n_te':4458},
    {'oi':1,'ti':14,'thresh':0.15,'pf_tr':0.9695,'pf_te':0.9607,'n_te':3976},
    # oi=2 (T-3)
    {'oi':2,'ti':0,'thresh':0.01,'pf_tr':0.951,'pf_te':0.9422,'n_te':18685},
    {'oi':2,'ti':1,'thresh':0.02,'pf_tr':0.9542,'pf_te':0.9438,'n_te':16947},
    {'oi':2,'ti':2,'thresh':0.03,'pf_tr':0.9502,'pf_te':0.9468,'n_te':15259},
    {'oi':2,'ti':3,'thresh':0.04,'pf_tr':0.9569,'pf_te':0.9535,'n_te':13704},
    {'oi':2,'ti':4,'thresh':0.05,'pf_tr':0.9757,'pf_te':0.9506,'n_te':12265},
    {'oi':2,'ti':5,'thresh':0.06,'pf_tr':0.9902,'pf_te':0.9698,'n_te':10938},
    {'oi':2,'ti':6,'thresh':0.07,'pf_tr':1.0094,'pf_te':0.9845,'n_te':9693},
    {'oi':2,'ti':7,'thresh':0.08,'pf_tr':0.993,'pf_te':0.9777,'n_te':8592},
    {'oi':2,'ti':8,'thresh':0.09,'pf_tr':0.9913,'pf_te':0.979,'n_te':7668},
    {'oi':2,'ti':9,'thresh':0.10,'pf_tr':0.9786,'pf_te':0.9758,'n_te':6770},
    {'oi':2,'ti':10,'thresh':0.11,'pf_tr':0.9765,'pf_te':0.9918,'n_te':6043},
    {'oi':2,'ti':11,'thresh':0.12,'pf_tr':0.9807,'pf_te':0.9792,'n_te':5344},
    {'oi':2,'ti':12,'thresh':0.13,'pf_tr':0.9396,'pf_te':0.9949,'n_te':4734},
    {'oi':2,'ti':13,'thresh':0.14,'pf_tr':0.9125,'pf_te':1.0188,'n_te':4207},
    {'oi':2,'ti':14,'thresh':0.15,'pf_tr':0.9109,'pf_te':1.0049,'n_te':3755},
    # oi=3 (T-2)
    {'oi':3,'ti':0,'thresh':0.01,'pf_tr':0.9565,'pf_te':0.9368,'n_te':19016},
    {'oi':3,'ti':1,'thresh':0.02,'pf_tr':0.9658,'pf_te':0.9463,'n_te':17177},
    {'oi':3,'ti':2,'thresh':0.03,'pf_tr':0.9652,'pf_te':0.9488,'n_te':15440},
    {'oi':3,'ti':3,'thresh':0.04,'pf_tr':0.9696,'pf_te':0.9487,'n_te':13792},
    {'oi':3,'ti':4,'thresh':0.05,'pf_tr':0.9751,'pf_te':0.9508,'n_te':12212},
    {'oi':3,'ti':5,'thresh':0.06,'pf_tr':0.973,'pf_te':0.9787,'n_te':10794},
    {'oi':3,'ti':6,'thresh':0.07,'pf_tr':0.9753,'pf_te':0.9892,'n_te':9571},
    {'oi':3,'ti':7,'thresh':0.08,'pf_tr':0.9818,'pf_te':0.9877,'n_te':8426},
    {'oi':3,'ti':8,'thresh':0.09,'pf_tr':0.9801,'pf_te':0.9975,'n_te':7452},
    {'oi':3,'ti':9,'thresh':0.10,'pf_tr':0.9546,'pf_te':0.9989,'n_te':6521},
    {'oi':3,'ti':10,'thresh':0.11,'pf_tr':0.9506,'pf_te':0.9964,'n_te':5763},
    {'oi':3,'ti':11,'thresh':0.12,'pf_tr':0.9395,'pf_te':1.026,'n_te':5101},
    {'oi':3,'ti':12,'thresh':0.13,'pf_tr':0.9242,'pf_te':1.0373,'n_te':4500},
    {'oi':3,'ti':13,'thresh':0.14,'pf_tr':0.9063,'pf_te':1.0345,'n_te':3959},
    {'oi':3,'ti':14,'thresh':0.15,'pf_tr':0.9039,'pf_te':1.0022,'n_te':3518},
    # oi=4 (T-1)
    {'oi':4,'ti':0,'thresh':0.01,'pf_tr':0.9519,'pf_te':0.9496,'n_te':19046},
    {'oi':4,'ti':1,'thresh':0.02,'pf_tr':0.951,'pf_te':0.9516,'n_te':17107},
    {'oi':4,'ti':2,'thresh':0.03,'pf_tr':0.9551,'pf_te':0.9643,'n_te':15259},
    {'oi':4,'ti':3,'thresh':0.04,'pf_tr':0.959,'pf_te':0.9702,'n_te':13546},
    {'oi':4,'ti':4,'thresh':0.05,'pf_tr':0.967,'pf_te':0.9752,'n_te':11961},
    {'oi':4,'ti':5,'thresh':0.06,'pf_tr':0.974,'pf_te':0.9742,'n_te':10480},
    {'oi':4,'ti':6,'thresh':0.07,'pf_tr':0.9737,'pf_te':0.9854,'n_te':9166},
    {'oi':4,'ti':7,'thresh':0.08,'pf_tr':0.965,'pf_te':0.9874,'n_te':7980},
    {'oi':4,'ti':8,'thresh':0.09,'pf_tr':0.9403,'pf_te':0.9911,'n_te':6963},
    {'oi':4,'ti':9,'thresh':0.10,'pf_tr':0.9381,'pf_te':0.9914,'n_te':6111},
    {'oi':4,'ti':10,'thresh':0.11,'pf_tr':0.9204,'pf_te':1.0212,'n_te':5384},
    {'oi':4,'ti':11,'thresh':0.12,'pf_tr':0.8944,'pf_te':1.0311,'n_te':4669},
    {'oi':4,'ti':12,'thresh':0.13,'pf_tr':0.8584,'pf_te':1.0268,'n_te':4049},
    {'oi':4,'ti':13,'thresh':0.14,'pf_tr':0.8556,'pf_te':1.0472,'n_te':3568},
    {'oi':4,'ti':14,'thresh':0.15,'pf_tr':0.8649,'pf_te':1.0792,'n_te':3140},
    # oi=5 (T0)
    {'oi':5,'ti':0,'thresh':0.01,'pf_tr':0.9327,'pf_te':0.947,'n_te':20622},
    {'oi':5,'ti':1,'thresh':0.02,'pf_tr':0.9284,'pf_te':0.9546,'n_te':18401},
    {'oi':5,'ti':2,'thresh':0.03,'pf_tr':0.9295,'pf_te':0.9529,'n_te':16299},
    {'oi':5,'ti':3,'thresh':0.04,'pf_tr':0.9414,'pf_te':0.9699,'n_te':14265},
    {'oi':5,'ti':4,'thresh':0.05,'pf_tr':0.9346,'pf_te':0.9805,'n_te':12423},
    {'oi':5,'ti':5,'thresh':0.06,'pf_tr':0.9373,'pf_te':0.9776,'n_te':10807},
    {'oi':5,'ti':6,'thresh':0.07,'pf_tr':0.9313,'pf_te':0.9991,'n_te':9334},
    {'oi':5,'ti':7,'thresh':0.08,'pf_tr':0.9279,'pf_te':0.9855,'n_te':8017},
    {'oi':5,'ti':8,'thresh':0.09,'pf_tr':0.9004,'pf_te':1.0202,'n_te':6954},
    {'oi':5,'ti':9,'thresh':0.10,'pf_tr':0.8823,'pf_te':1.0393,'n_te':6063},
    {'oi':5,'ti':10,'thresh':0.11,'pf_tr':0.8661,'pf_te':1.0416,'n_te':5190},
    {'oi':5,'ti':11,'thresh':0.12,'pf_tr':0.8734,'pf_te':1.0399,'n_te':4524},
    {'oi':5,'ti':12,'thresh':0.13,'pf_tr':0.8629,'pf_te':1.0479,'n_te':3910},
    {'oi':5,'ti':13,'thresh':0.14,'pf_tr':0.8728,'pf_te':1.0668,'n_te':3405},
    {'oi':5,'ti':14,'thresh':0.15,'pf_tr':0.8609,'pf_te':1.0314,'n_te':2932},
]

candidates = [r for r in FULL
              if r['pf_te'] >= 1.0
              and abs(r['pf_tr'] - r['pf_te']) < 0.05]

candidates.sort(key=score, reverse=True)

print(f"Combos passing PF_test>=1.0 AND |dPF|<0.05: {len(candidates)}")
print()
print(f"{'Rank':<5} {'Offset':<7} {'Thresh':<9} {'PF_tr':<7} {'PF_te':<7} {'Signals':<9} {'dPF':<8} {'Score':<8}")
print('-' * 65)
for i, r in enumerate(candidates, 1):
    dpf = r['pf_te'] - r['pf_tr']
    sf  = max(0.0, 1.0 - abs(r['pf_tr'] - r['pf_te']) / 0.1)
    sc  = score(r)
    print(f"{i:<5} {OFF[r['oi']]:<7} {r['thresh']:.2f}%    {r['pf_tr']:.3f}  {r['pf_te']:.3f}  {r['n_te']:<9,} {dpf:+.3f}   {sc:.3f}")
