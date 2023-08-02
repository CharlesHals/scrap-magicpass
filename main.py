import requests
import json
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd

class MagicPass():
    def __init__(self):
        self.baseUrl = "https://www.magicpass.ch"
    def getAllData(self,sourced=False):
        print("--- START MAGICPASS UPDATE --- SOURCED: " + str(sourced))
        if sourced:            
            dictData = json.load(open("sourced/MagicPass_getAllData.txt"))
        else:
            URL = self.baseUrl
            response = requests.get(URL+ "/en/stations/", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'},timeout=5)
            print(response.content)
            soup = BeautifulSoup(response.content, "html.parser")
            response.close()
            stationBloc = soup.find_all("div", class_="card-body")
            dictData = {}
            for stationData in stationBloc:
                dictDataSub = {}
                
                stationTitle = stationData.find("h2", class_="card-title")    
                dictDataSub["station_name"] = stationTitle.find("a")["title"]
                dictDataSub["station_link"] = URL + stationTitle.find("a")["href"]
                
                dictDataSub["station_canton"] = stationData.find("time").text
                dictDataSub["station_season"] = stationData.find("small").text
                dictData[dictDataSub["station_name"]] = dictDataSub
                dictDataSub.update(self.getStationIndividualData(dictDataSub["station_link"]))
                
            f = open("sourced/MagicPass_getAllData.txt", "w")
            f.write(json.dumps(dictData))
            f.close()
        return dictData
    def getStationIndividualData(self,URL):
        #URL = "https://www.magicpass.ch/en/ski-resorts/aeschiallmend-1805"
        dictDataSub = {}
        response = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'},timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        response.close()
        stationAllInfo = soup.find_all("div", class_="resorts-conditions-numbers-txt")
        for stationInfo in stationAllInfo:
            infoName = stationInfo.find('span')
            infoName.extract()
            dictDataSub[infoName.text.strip()] = stationInfo.text.strip()
        
        contactBloc = soup.find("h2", string=lambda text: "Contact").parent
        i=0
        for contactData in contactBloc.childGenerator():
            if i==2:
                dictDataSub["station_address"] = contactData.text.strip()
            elif i==4:
                dictDataSub["station_phone"] = contactData.text.strip()
            i=i+1
            
        i=0
        for contactData in contactBloc.find_all("a"):
            if i==0:
                dictDataSub["station_mail"] = contactData["title"]
            elif i==1:
                dictDataSub["station_website"] = contactData["href"]
            elif contactData["href"][:13] == "https://snow.":
                urlSnowConditions = contactData["href"]
                if urlSnowConditions.find("https://snow.myswitzerland.com") == -1:
                    dictDataSub["station_snowconditions"] = ""  
                elif urlSnowConditions.find("bulletin_enneigement") != -1:
                    dictDataSub["station_snowconditions"] = urlSnowConditions.rsplit("/",3)[0] + "/snow_reports/" + urlSnowConditions.rsplit("/",3)[3] #Switch to english page          
                elif urlSnowConditions.find("schneebericht") != -1:
                    dictDataSub["station_snowconditions"] = urlSnowConditions.replace("schneebericht","snow_reports")
                else:            
                    dictDataSub["station_snowconditions"] = urlSnowConditions    
            i=i+1
        return dictDataSub
#%%   
class SnowConditions():
    def __init__(self):
        pass
    def addSnowConditionsToDict(self, dictDataMagicPass="", sourced=False):
        print("--- START SNOW CONDITIONS UPDATE --- SOURCED: " + str(sourced))
        if sourced:
            dictDataMagicPass = json.load(open("sourced/SnowConditions_addSnowConditionsToDict.txt"))
        else:
            for key, dictDataSub in dictDataMagicPass.items():
                try:
                    URL = dictDataSub["station_snowconditions"]
                    dictDataMagicPass[key].update(self.getStationIndividualData(URL))
                except:
                    pass
            f = open("sourced/SnowConditions_addSnowConditionsToDict.txt", "w")
            f.write(json.dumps(dictDataMagicPass))
            f.close()
        return dictDataMagicPass
                    
    def getStationIndividualData(self, URL):
        #URL = "https://snow.myswitzerland.com/snow_reports/aeschi-aeschiried-101/"
        dictDataSub = {}
        response = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'},timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        response.close()
        summaryAccordion = soup.find_all("article", class_="SummaryAccordion")
        for accordion in summaryAccordion:
            accordionName = accordion.find("h3").text.strip()
            dictDataSub[accordionName] = accordion.find("div", class_="SummaryAccordion--summary").text.strip()
            try:
                tableDetails = accordion.find("tbody").find_all("tr")
                for detail in tableDetails:
                    detailName = detail.find("th").text.strip()
                    dictDataSub[accordionName + "_" + detailName] = detail.find("td").text.strip()
            except:
                pass    
        listAdditionalInfoToGet = ["articlesection-u20",
                                    "articlesection-u21",
                                    "articlesection-tickets",
                                    ]        
        for sectionId in listAdditionalInfoToGet:
            additionalInfoData = soup.find("div", {"id":sectionId})
            sectionName = additionalInfoData.find("h2", class_="ArticleSection--title").text.strip()
            additionalInfoDetails = additionalInfoData.find("tbody").find_all("tr") 
            for detail in additionalInfoDetails:
                detailName = detail.find("th").text.strip()
                dictDataSub[sectionName + "_" + detailName] = detail.find("td").text.strip()
        return dictDataSub
#%%
class googleAPI():
    def __init__(self):
        self.api_key ='AIzaSyCB6b2e_GzRN8UNxR0Ms7CUERuvqcNXLBc'        
    def addAllDistanceToDict(self,start_address, dictData):
        print("--- START GOOGLE UPDATE ---")
        #start_address="Route d'Oron 11, 1010 Lausanne"
        for key, dictDataSub in dictData.items():
            try:
                dictData[key].update(googleAPI().DistanceMatrix(start_address,dictDataSub["station_address"]))
            except:
                dictDataError={
                    "google_distance_km" : -999,
                    "google_duration_min" : -999
                    }
                dictData[key].update(dictDataError)
        return dictData
        
    def DistanceMatrix(self,start_address,destination_adress):
        #start_address="Route d'Oron 11, 1010 Lausanne"
        #destination_adress = "Chem. du Crépon 32, 1815 Montreux"

        api_key = self.api_key
        source = urllib.parse.quote(start_address)
        dest = urllib.parse.quote(destination_adress)
        url ='https://maps.googleapis.com/maps/api/distancematrix/json?'
        response = requests.get(url + 
                         '&destinations=' + dest +
                         '&origins=' + source +
                         '&key=' + api_key)
        
        dictResponse = response.json()
        
        dictDataGoogleApi={}
        dictDataGoogleApi["google_distance_km"] = dictResponse["rows"][0]["elements"][0]["distance"]["value"] / 1000
        dictDataGoogleApi["google_duration_min"] = dictResponse["rows"][0]["elements"][0]["duration"]["value"] / 60
        return dictDataGoogleApi
#%%
class MagicPassMeteoProject():
    def __init__(self):
        pass
    def updateData(self,data_to_update, sourced=False):
        if sourced:
            dictData = json.load(open("sourced/MagicPassMeteoProject_ExtractAll.txt"))
        else:
            if data_to_update == "all":
                dictData = MagicPass().getAllData(sourced=False)
                dictData = SnowConditions().addSnowConditionsToDict(dictData, sourced=False)
                dictData = googleAPI().addAllDistanceToDict("Route d'Oron 11, 1010 Lausanne",dictData)
            elif data_to_update == "snowconditions_googledistance":
                dictData = MagicPass().getAllData(sourced=True)
                dictData = SnowConditions().addSnowConditionsToDict(dictData, sourced=False)
                dictData = googleAPI().addAllDistanceToDict("Route d'Oron 11, 1010 Lausanne",dictData)
            elif data_to_update == "googledistance":                
                dictData = SnowConditions().addSnowConditionsToDict(sourced=True)
                dictData = googleAPI().addAllDistanceToDict("Route d'Oron 11, 1010 Lausanne",dictData)
            f = open("sourced/MagicPassMeteoProject_ExtractAll.txt", "w")
            f.write(json.dumps(dictData))
            f.close()
        return dictData
#%%
dictData = MagicPassMeteoProject().updateData(data_to_update="all", sourced=False)
dfData = pd.DataFrame.from_dict(dictData, orient="index")
dfData.to_excel("Magicpass.xlsx", sheet_name="Alldata")
