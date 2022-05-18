import re

import requests
import lxml.html
import rdflib
from urllib.parse import unquote

PREFIX = "http://en.wikipedia.org"
ontology_Prefix = 'http://example.org/'

countries = []
countriesNames = []
primeMinisters = set()
presidents = set()
g = rdflib.Graph()

president_of_country = rdflib.URIRef(ontology_Prefix + "president_of_country")
prime_minister_of_country = rdflib.URIRef(ontology_Prefix + "prime_minister_of_country")
population_of_country = rdflib.URIRef(ontology_Prefix + "population_of_country")
capital_of_country = rdflib.URIRef(ontology_Prefix + "capital_of_country")
area_of_country = rdflib.URIRef(ontology_Prefix + "area_of_country")
government_of_country = rdflib.URIRef(ontology_Prefix + "government_of_country")
birth_day_of_person = rdflib.URIRef(ontology_Prefix + "birth_day_of_person")
birth_place_of_person = rdflib.URIRef(ontology_Prefix + "birth_place_of_person")



def getAllCountryRefs(url):
    countryRefs = []
    r = requests.get(url)
    doc = lxml.html.fromstring(r.content)
    refs = doc.xpath("//table/tbody/tr/td[1]//span[@class='flagicon']/following-sibling::a[1]/@href")
    return refs


def getCountryPresident(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    # option 1 - full path:
    presURL = doc.xpath("(//table[contains(./@class,'infobox')]//tr[.//th//text()='President']/td//a)[1]/@href")

    # option 2 - partial path:
    #    ref = doc.xpath("//tr[.//text()='President']/td//a/@href")
    return presURL


def getCountryPrimeMinister(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    primURL = doc.xpath("(//table[contains(./@class,'infobox')]//tr[.//th//text()='Prime Minister']/td//a)[1]/@href")
    return primURL


def getCountryGovernment(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    govForms = doc.xpath("//table[contains(./@class,'infobox')]//tr[.//text()='Government']/td//a/@title")
    return govForms

def getCountryDrivingSide(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    drivingSide = doc.xpath("(//table[contains(./@class,'infobox')]//tr[.//th//text()='Driving side']/td//text())[1]")
    return drivingSide


def getCountryCapital(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    primURL = doc.xpath("(//table[contains(./@class,'infobox')]//tr[.//text()='Capital']/td//a)[1]/@href")
    if len(primURL) > 0:
        if 'wiki' not in primURL[0]:
            return []
    return primURL


def getCountryPopulation(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    population = doc.xpath(
        "(//table[contains(./@class,'infobox')]//tr[.//text()='Population']/following-sibling::tr[1]/td//text()[.!='\n'])[1]")
    return population


def getCountryArea(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    area = doc.xpath(
        "(//table[contains(./@class,'infobox')]//tr[contains(.//text(),'Area')]/following-sibling::tr[1]/td//text()[.!='\n'])[1]")
    strrinArea = area[0]
   # area = re.split("–-/", strrinArea)
    result = ""
    for c in strrinArea:
        if c.isdigit() or c == ",":
            result += c
        else:
            break

    return [result +" km squared"]

def getPersonBirthday(personURL):
    r = requests.get(personURL)
    doc = lxml.html.fromstring(r.content)
    primURL = doc.xpath("//table[contains(./@class,'infobox')]//span[./@class='bday']/text()")
    return primURL


def getPersonBirthPlace(personURL):
    r = requests.get(personURL)
    doc = lxml.html.fromstring(r.content)
    birthURLS = doc.xpath("//table[contains(./@class,'infobox')]//tr[.//text()='Born']/td//a")
    for url in birthURLS:
        if url in countries:
            return [url]
    birthURL = doc.xpath("//table[contains(./@class,'infobox')]//tr[.//text()='Born']/td/text()[last()]")
    if birthURL in countriesNames: # need to actually init the countriesNames with the proper names
        return birthURL
    else:
        return []


def getAlldataByCountry(country):
    population = getCountryPopulation(PREFIX + country)
    president = getCountryPresident(PREFIX + country)
    primeMinister = getCountryPrimeMinister(PREFIX + country)
    area = getCountryArea(PREFIX + country)
    capital = getCountryCapital(PREFIX + country)
    gov = getCountryGovernment(PREFIX + country)
    return primeMinister, population, capital, area, gov, president


def prepareStrToOntology(name):
    name = name.strip()
    if name.find("/wiki") != -1:
        name = name[6:]
    name = unquote(name)
    name = name.replace(" ", "_")
    name = name.replace('"','')
    name = ontology_Prefix + name
    name = unquote(name)
    i = name.find('(')
    if i >= 0:
        name = name[:i]
        name = name.strip()
    ont = rdflib.URIRef(name)
    return ont


def createOntology():
    allCountries = getAllCountryRefs("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")
    for country1 in allCountries:
        prime_minister, population, capital, area, gov, president = getAlldataByCountry(country1)
        countryOntology = prepareStrToOntology(country1)
        if len(prime_minister) > 0:
            prime_minister_name = prime_minister[0]
            prime_minister_name = prime_minister_name[6:]  # remove wiki
            prime_minister_name.replace(" ", "_")
            primeMinisters.add(prime_minister_name)
            prime_ministerOntology = prepareStrToOntology(prime_minister_name)
            g.add((prime_ministerOntology, prime_minister_of_country, countryOntology))
            bDay = getPersonBirthday(PREFIX +"/wiki"+prime_minister_name)
            bDay1 = bDay[0]
            bPlace = getPersonBirthPlace(PREFIX +"/wiki"+prime_minister_name)
            bPlace1 = bPlace[0]
            bdayOntolgy = prepareStrToOntology(bDay1)
            g.add((bdayOntolgy, birth_day_of_person, countryOntology))
            bPlaceOntology = prepareStrToOntology(bPlace1)
            g.add((bPlaceOntology, birth_place_of_person, countryOntology))


        if len(president) > 0:
            president_name = president[0]
            president_name = president_name[6:]  # remove wiki
            president_name.replace(" ", "_")
            presidents.add(president_name)
            presidentOntology = prepareStrToOntology(president_name)
            g.add((presidentOntology, prime_minister_of_country, countryOntology))
            bDay = getPersonBirthday(PREFIX + "/wiki" + president_name)
            bDay1 = bDay[0]
            bPlace = getPersonBirthPlace(PREFIX + "/wiki" + president_name)
            bPlace1 = bPlace[0]
            bdayOntolgy = prepareStrToOntology(bDay1)
            g.add((bdayOntolgy, birth_day_of_person, countryOntology))
            bPlaceOntology = prepareStrToOntology(bPlace1)
            g.add((bPlaceOntology, birth_place_of_person, countryOntology))

        populationString = population[0]
        populationAntology = prepareStrToOntology(populationString)
        g.add((populationAntology, population_of_country, countryOntology))
        areaString = area[0]
        areaAntology = prepareStrToOntology(areaString)
        g.add((areaAntology, area_of_country, countryOntology))

        for capital1 in capital:
            capitalAntology = prepareStrToOntology(capital1)
            g.add((capitalAntology, capital_of_country, countryOntology))
        for formOfGov in gov:
            govOntology = prepareStrToOntology(formOfGov)
            g.add((govOntology, government_of_country, countryOntology))




        g.serialize("ontology.nt", format="nt")

#question to sparql

def whoIsQuestion(question):
    if question.find("president") != -1:
        headOfCountry = "president_of_country"
        country = question[24:-1]
        """
        q = "select ?x where "\
                "{ ?x <http://example.org/" + headOfCountry + "> ?x ."\
            " ?x <http://example.org/" + country + ">?x }"
            """
        return "select ?a where {<http://example.org/" + headOfCountry + "><http://example.org/" + country + "> ?a.}"

        return q

    elif question.find("prime minister") != -1:
        headOfCountry = "prime_minister_of_country"
        country = question[29:-1]
        return "select * where {<http://example.org/" + headOfCountry + "> <http://example.org/" + country + "> ?a.}"

    else:
        name = question[7:-1]


def whatIsQuestion(question):
    if question.find("population of") != -1:
        country = question[26:-1]
        subject = "population_of_country"
    elif question.find("area of") != -1:
        country = question[20:-1]
        subject = "area_of_country"
    elif question.find("form of government") != -1:
        country = question[34:-1]
        subject = "government_of_country"
    elif question.find("is the capital of") != -1:
        country = question[23:-1]
        subject = "capital_of_country"
    return "select * where  {<http://example.org/" + subject + "> <http://example.org/" + country + "> ?x.}"


def whenQuestion(question):
    if question.find("president") != -1:
        pass


def questionToSparql(question):

    # who is question
    if question.find("Who is") != -1:
        return whoIsQuestion(question)
    # what is question
    if question.find("What is") != -1:
        return whatIsQuestion(question)
    if question.find("When") != -1:
        return whenQuestion(question)


# //*[@id="mw-content-text"]/div[1]/table[1]/tbody/tr[32]/td/a[3]
# //*[@id="mw-content-text"]/div[1]/table[2]/tbody/tr[45]/td/text()[3]
#
# def crawl(url, visited):
#     urls = []
#     r = requests.get(url)
#     doc = lxml.html.fromstring(r.content)
#     print(url)
#
#     hrefs = doc.xpath("//table/tbody/tr/td[1]/span//a/@href")
#     hrefs = hrefs[:MAX_LINKS_PER_PAGE]
#     for t in hrefs:
#         if t in visited:
#             continue
#
#         print(f"---- {t}")
#         if len(visited) < MAX_PAGES:
#             urls.append(f"{PREFIX}{t}")
#             visited.add(t)
#
#     for next_url in urls:
#         crawl(next_url, visited)


# def main():
#     visited = set()
#     crawl("", visited)

def testFunc(url):
    r = requests.get(url)
    country_html = lxml.html.fromstring(r.content)
    infobox = country_html.xpath("(//table[contains(./@class, 'infobox')])[1]")[0]
    capital = infobox.xpath("tbody/tr[./th[text()='Capital']]/td/a/@href")
    if len(capital) > 0:
        capital = capital[0].rsplit("/", 1)[1].replace('_', ' ')
    if len(capital) == 0:
        capital = infobox.xpath("tbody/tr[./th[text()='Capital']]/td/text()")
    if len(capital) == 0:
        capital = infobox.xpath("tbody/tr[./th[text()='Capital']]/td/div/ul/li/a/text()")
    # if len(capital)>0:
    #   capital = infobox.xpath("tbody/tr[./th[text()='Capital']]/td/div/ul/li[2]/a/text()")
    if len(capital) == 0:
        capital = infobox.xpath("tbody/tr[./th[text()='Capital']]/td/text()")
    if len(capital) > 0:
        if 'none' in str(capital[0]).lower():
            capital = []
    return capital


if __name__ == '__main11__':
    print(len(getAllCountryRefs("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")))
    print(getCountryDrivingSide("https://en.wikipedia.org/wiki/Russia"))
    countries = getAllCountryRefs("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")
    urls = []
    for country in countries:
        urls.append(f"{PREFIX}{country}")

    areas = []
    presidents = []
    testPresidents = []
    for url in urls:
        presidents.append(getCountryDrivingSide(url))
        # testPresidents.append(testFunc(url))

    print(len([x for x in presidents if not len(x) == 0]))
    # print(len([x for x in testPresidents if not len(x) == 0]))
    # print([(presidents[i], testPresidents[i]) for i in range(len(presidents)) if len(presidents[i]) != len(testPresidents[i])])
    print("temp")



s = (questionToSparql("Who is the prime minister of Israel?"))
#print(getCountryPrimeMinister(PREFIX+"/wiki/The_Bahamas"))
print(s)

g = rdflib.Graph()
g.parse("ontology.nt", format="nt")
query_list_result = g.query(s)
print(list(query_list_result))
print(getPersonBirthday(PREFIX+"/wiki/Joe_Biden" ))
#print(getCountryArea(PREFIX+"/wiki/China"))
#print(prepareStrToOntology(PREFIX+"/wiki/China"))
createOntology()
print(presidents)
