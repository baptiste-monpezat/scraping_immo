import requests 
from bs4 import BeautifulSoup
from torrequest import TorRequest
import re
import random 
import time
import json
import sys


def tor_request(url):
    """
    Make a get request with Tor Proxy
    
    Args:
    - url (string) : url from which we want to fetch data  
    Return:
    response : Response from get request
    
    """
    
    tr = TorRequest(password="s6w81nh2")
    print(f"Scrapped {url} with Ip Address",tr.get("http://ipecho.net/plain").text)
    response = tr.get(url)
    tr.reset_identity()

    
    return response


def get_agents_information(agency_information_soup):
    """
    Collecting agents information from agency : name,job,mail,phone
    
    Args:
    agency_information_soup : BeautifulSoup object from agency page
    
    Return:
    agents_information_list : List of dict containing agent information from one agency
    
    """
    
    agents_information_list = []

    for div in agency_information_soup.find_all("div",{"class":"title"}):

        agent_information = div.getText().strip("").split("\n")
        
        try:
            name = agent_information[1].strip(" ")
        except:
            name = None
            
        try:
            job = agent_information[2].strip(" ")
        except:
            job = None

        agents_information_list.append({"name":name,"job":job,"mail":None,"tel":None})

    for index,obfuscated_email in enumerate(agency_information_soup.find_all("app-obfuscate-email")):

        email = obfuscated_email["email"]
        agents_information_list[index]["mail"] = email

    for index,slot in enumerate(agency_information_soup.find_all("div",{"slot":"content"},text=re.compile("^[0-9]*$"))):

        if slot.getText() != "":
            agents_information_list[index]["tel"] =  slot.getText()
            
            
    return agents_information_list


def get_ads_information(real_estate_ads_response):
    """
    Collecting ads information : title,name,price,list of pictures 
    
    Args: 
    real_estate_ads_response : reponse from ads api 

    Return: 
    ads_information_list : list of dict containing ad information
    
    """
    
    ads_information_list = []
    
    for real_estate_ads in real_estate_ads_response.json():
    
        title = real_estate_ads["title"]
        name = real_estate_ads["name"]
        price = real_estate_ads["price"]
        picture_urls_list = real_estate_ads["thumbnails"]

        for index,picture_url in enumerate(picture_urls_list):
            picture_urls_list[index] =  picture_url[:-8]
            
        ads_information_list.append({"title":title,"name":name,"price":price,"picture_urls_list":picture_urls_list})
        
    return ads_information_list


def get_all_information(agency):
    
    """
    Collecting agents and ads information for one agency
    
    Args:
    - agencie : dict containing general information about an agency : name, adress, zip_code, real_estate_agency_url
    
    Return:
    - scrapping_information_dict : dict containing the following information:
        real_estate_agency_name : Agency Name,
        real_estate_agency_address : Agency Adress,
        real_estate_agency_zip_code :  Agency Zipcode,
        real_estate_agency_city : Agency Location, 
        real_estate_agency_contact_name : Contact's name in agency
        real_estate_agency_contact_firstname :  Contact's firstname
        real_estate_agency_email : Contact's email
        real_estate_agency_phone : Contact's phone 
        agents_information_list : Information on Agency's employees
        ads_information_list : Ads' Information
    """


    real_estate_agency_id = agency["real_estate_agency_id"]
    real_estate_agency_immofacile_id = agency["real_estate_agency_reference"]
    real_estate_agency_url = agency["real_estate_agency_url"]
    url_agency = agency["url"]
    
    print(agency["real_estate_agency_name"])

    agents_information_list = None
    ads_information_list = None
    
    
    agency_information_response = tor_request(url_agency)
    agency_information_soup = BeautifulSoup(agency_information_response.content,'html.parser')

    agents_information_list = get_agents_information(agency_information_soup)

    real_estate_ads_api = f"https://www.stephaneplazaimmobilier.com/search/all?target=all&agency_id={real_estate_agency_id}&sort=&markers=true&limit=100000&page=0"
    real_estate_ads_response = tor_request(real_estate_ads_api)

    ads_information_list = get_ads_information(real_estate_ads_response)

    scrapping_information_dict = {
            "real_estate_agency_name" : agency["real_estate_agency_name"],
            "real_estate_agency_address" : agency["real_estate_agency_address"],
            "real_estate_agency_zip_code" : agency["real_estate_agency_zip_code"],
            "real_estate_agency_city" : agency["real_estate_agency_city"],
            "real_estate_agency_contact_name" : agency["real_estate_agency_contact_name"],
            "real_estate_agency_contact_firstname" : agency["real_estate_agency_contact_firstname"],
            "real_estate_agency_email" : agency["real_estate_agency_email"],
            "real_estate_agency_phone" : agency["real_estate_agency_phone"],
            "agents_information_list" : agents_information_list,
            "ads_information_list" : ads_information_list
        }
        
    return scrapping_information_dict



def scrapping_stephaneplazaimmobilier(nb_pages=1):
    
    """
    Loop through agencies from www.stephaneplazaimmobilier.com 
    Each API call is limited to 10 agencies
    
    Args:
    nb_pages (int): Pages' Number to scrap (10 agencies per page, 53 pages)
    

    Return:
    scrapping_information_list : List of dict containing all information 
    """

    scrapping_information_list = []
    start_time = time.time()

    for page in range(1,nb_pages+1):
        
        agencies_api = f"https://www.stephaneplazaimmobilier.com/agencies/search?page={page}&location="
        agencies_response = tor_request(agencies_api)
        agencies_json = agencies_response.json()
        
        for agency in agencies_json["agencies"]["data"]:
            
            scrapping_information_list.append(get_all_information(agency))

    
    elapsed_time = time.time() - start_time
    print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    
    return scrapping_information_list
        

if __name__ == "__main__":
    
    """
    Args: 
    nb_pages: Number of pages we want to scrap
    """

    nb_pages = int(sys.argv[1])
    scrapping_information_list = scrapping_stephaneplazaimmobilier(nb_pages)

    with open('scraping_test.json', 'w') as fp:
        json.dump(scrapping_information_list, fp,ensure_ascii=False)


        