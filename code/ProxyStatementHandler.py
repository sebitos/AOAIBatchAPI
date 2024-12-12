import requests
import pandas as pd
import json
class ProxyStatementHandler:
    def __init__(self, symbol):
        self.symbol = symbol
        self.headers = {'User-Agent': "dmp442@nyu.edu"}
        self.CIK_url = "https://www.sec.gov/files/company_tickers.json"
    def get_CIK(self):
        CIK = requests.get(
            self.CIK_url,
            headers=self.headers
        )

        # Convert the dictionary to Pandas Dataframe
        CIK_data = pd.DataFrame.from_dict(CIK.json(),orient='index')

        # Dictionary to dataframe
        CIK_data = pd.DataFrame.from_dict(CIK.json(),orient='index')

        # If missing, add the leading zeros to the CIK to conform to Edgar syntax
        CIK_data['cik_str'] = CIK_data['cik_str'].astype(
                                str).str.zfill(10)
        return CIK_data
    def get_proxy_stmt(self,ticker_symbol,CIK_data):
        cik = None
        if ticker_symbol in CIK_data['ticker'].values:
            # Use .loc to retrieve the 'cik_str' value corresponding to the TickerSymbol
            cik = CIK_data.loc[CIK_data['ticker'] == ticker_symbol, 'cik_str'].values[0]
        if not cik is None:
            print(cik)
        else:
            print(f'TickerSymbol {ticker_symbol} not found in the DataFrame.')
        # Request filing metadata
        filingMetadata = requests.get(
            f'https://data.sec.gov/submissions/CIK{cik}.json',
            headers=self.headers
            )
        filing_metadata_json = filingMetadata.json()
        # Retrieves a dictioanry with keys to the filing for the specified CIK
        #print(filingMetadata.json().keys())
        filingMetadata.json()['filings']
        filingMetadata.json()['filings'].keys()
        filingMetadata.json()['filings']['recent']
        filingMetadata.json()['filings']['recent'].keys()

        # Create a pd dataframe of the company filings and their accession number
        allForms = pd.DataFrame.from_dict(
                    filingMetadata.json()['filings']['recent']
                    )
        # Create a new dataframe sorted just for proxies also known as form DEF 14A
        proxies = allForms[allForms['form'] == 'DEF 14A']

        # Within the proxies df add another column of accessionnumbner with special characters removed
        proxies['accessionNumberSpecial'] = proxies['accessionNumber'].replace('[^a-zA-Z0-9]', '', regex=True)
        proxies['Access_Link'] = proxies['accessionNumberSpecial'] + '/' +proxies['accessionNumber'] 

        # Create a the proxy's link to the txt file
        ProxyLink = 'https://www.sec.gov/Archives/edgar/data/'+cik+'/'+proxies['accessionNumberSpecial'].iloc[0] +'/index.json'
        
        #+proxies['Access_Link'].iloc[0]+'.json'

       # print("ProxyLink:", ProxyLink)

        content = requests.get(ProxyLink,headers=self.headers)

        txt_content = json.loads(content.text)
        proxy_htm = ""
        proxy_url = ""
        item_list = txt_content['directory']['item']
        for item in item_list:
            if self.check_for_proxy_match(item,ticker_symbol):
                proxy_url = 'https://www.sec.gov/Archives/edgar/data/'+cik+'/'+proxies['accessionNumberSpecial'].iloc[0]+"/"+item['name'] 
                print("Proxy URL: ",proxy_url)
                proxy_htm = requests.get(proxy_url,headers=self.headers).text
                break
        
        return proxy_htm
    def check_for_proxy_match(self,item,ticker_symbol):
        ticker_symbol_lower = ticker_symbol.lower()
        if "R1.htm" in item['name'] or "R2.htm" in item['name'] or ".html" in item['name']:
            return False
        if 'def14a' in item['name'] and '.htm' in item['name']:
            return True
        elif ticker_symbol_lower in item['name'] and '.htm' in item['name']:
            return True
        elif ".htm" in item['name']:
            return True
        return False