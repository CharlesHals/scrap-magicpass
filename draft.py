import requests
import json
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd

def googleDistanceMatrix(start_address,destination_adress):
    #start_address="Route d'Oron 11, 1010 Lausanne"
    #destination_adress = "Chem. du Crépon 32, 1815 Montreux"
    # enter your api key here
    api_key ='AIzaSyCB6b2e_GzRN8UNxR0Ms7CUERuvqcNXLBc'  
    # Take source as input
    source = urllib.parse.quote(start_address)  
    # Take destination as input
    dest = urllib.parse.quote(destination_adress)
    # url variable store url 
    url ='https://maps.googleapis.com/maps/api/distancematrix/json?'

    # Get method of requests module
    # return response object
    response = requests.get(url + 
                     '&destinations=' + dest +
                     '&origins=' + source +
                     '&key=' + api_key)
                         
    # json method of response object
    # return json format result
    dictResponse = response.json()
    
    dictDataGoogleApi={}
    dictDataGoogleApi["google_distance_km"] = dictResponse["rows"][0]["elements"][0]["distance"]["value"] / 1000
    dictDataGoogleApi["google_duration_min"] = dictResponse["rows"][0]["elements"][0]["duration"]["value"] / 60
    return dictDataGoogleApi

start_address="Route d'Oron 11, 1010 Lausanne"
dictData = json.load(open("allMagicPassData.txt"))

for key, dictDataSub in dictData.items():
    print(dictDataSub["station_address"])
    try:
        dictData[key].update(googleDistanceMatrix(start_address,dictDataSub["station_address"]))
    except:
        dictDataError={
            "google_distance_km" : -999,
            "google_duration_min" : -999
            }
        dictData[key].update(dictDataError)

dfAllData = pd.DataFrame.from_dict(dictData, orient="index")

