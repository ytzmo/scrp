import time
from scrapers import (
    goldman_sachs, jpmorgan, morgan_stanley, bofa,
    citi, barclays, hsbc, bnp_paribas, societe_generale, credit_agricole,
    euronext, natixis
)

scrapers = [
    ("Goldman Sachs", goldman_sachs),
    ("J.P. Morgan", jpmorgan),
    ("Morgan Stanley", morgan_stanley),
    ("Bank of America", bofa),
    ("Citi", citi),
    ("Barclays", barclays),
    ("HSBC", hsbc),
    ("BNP Paribas", bnp_paribas),
    ("Société Générale", societe_generale),
    ("Crédit Agricole", credit_agricole),
    ("Euronext", euronext),
    ("Natixis", natixis),
]

print("=== TEST DES 12 BANQUES ==================")
for name, module in scrapers:
    try:
        t0 = time.time()
        jobs = module.scrape()
        duration = time.time() - t0
        print(f"✅ {name:20}: {len(jobs)} offres trouvées en {duration:.1f}s")
    except Exception as e:
        print(f"❌ {name:20}: ERREUR -> {e}")
print("==========================================")
