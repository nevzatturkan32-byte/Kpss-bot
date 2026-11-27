for link_etiketi in soup.find_all("a", href=True):
            baslik = link_etiketi.get_text(strip=True)
            href = link_etiketi["href"]

            if len(baslik) < 15:
                continue

            tam_link = href if href.startswith("http") else f"https://www.resmigazete.gov.tr/{href.lstrip('/')}"

            # Sadece resmi devlet (.gov.tr) ilan linklerini al
            if ".gov.tr" not in 
