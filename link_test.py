import sys
from scrapers import (
    goldman_sachs, jpmorgan, morgan_stanley, bofa, citi,
    barclays, hsbc, bnp_paribas, societe_generale, credit_agricole
)

scrapers = [
    goldman_sachs, jpmorgan, morgan_stanley, bofa, citi,
    barclays, hsbc, bnp_paribas, societe_generale, credit_agricole
]

print("=== DEBUT DU TEST DE LIENS ===\n")

for s in scrapers:
    try:
        print(f"Scraping {s.BANK_NAME}...")
        jobs = s.scrape()
        print(f"  -> Total trouvé : {len(jobs)}")
        
        # Affiche jusqu'à 2 offres
        for i, j in enumerate(jobs[:2]):
            print(f"  [{i+1}] {j['title']}")
            print(f"      {j['url']}")
        print()
    except Exception as e:
        print(f"  Erreur : {e}\n")

print("=== FIN DU TEST ===")
