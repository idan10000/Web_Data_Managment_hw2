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

    return [result + " km squared"]


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
    if birthURL in countriesNames:  # need to actually init the countriesNames with the proper names
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
    name = name.replace('"', '')
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
        # for country1 in ['/wiki/Israel']:
        prime_minister, population, capital, area, gov, president = getAlldataByCountry(country1)
        countryOntology = prepareStrToOntology(country1)
        if len(prime_minister) > 0:
            prime_minister_name = prime_minister[0]
            prime_minister_name = prime_minister_name[6:]  # remove wiki
            prime_minister_name.replace(" ", "_")
            primeMinisters.add(prime_minister_name)
            prime_ministerOntology = prepareStrToOntology(prime_minister_name)
            g.add((prime_ministerOntology, prime_minister_of_country, countryOntology))
            bDay = getPersonBirthday(PREFIX + "/wiki" + prime_minister_name)
            if len(bDay) > 0:
                bDay1 = bDay[0]
                bdayOntolgy = prepareStrToOntology(bDay1)
                g.add((bdayOntolgy, birth_day_of_person, prime_minister_name))
            bPlace = getPersonBirthPlace(PREFIX + "/wiki" + prime_minister_name)
            if len(bPlace) > 0:
                bPlace1 = bPlace[0]
                bPlaceOntology = prepareStrToOntology(bPlace1)
                g.add((bPlaceOntology, birth_place_of_person, prime_minister_name))

        if len(president) > 0:
            president_name = president[0]
            president_name = president_name[6:]  # remove wiki
            president_name.replace(" ", "_")
            presidents.add(president_name)
            presidentOntology = prepareStrToOntology(president_name)
            g.add((presidentOntology, president_of_country, countryOntology))
            bDay = getPersonBirthday(PREFIX + "/wiki" + president_name)
            if len(bDay) > 0:
                bDay1 = bDay[0]
                bdayOntolgy = prepareStrToOntology(bDay1)
                g.add((bdayOntolgy, birth_day_of_person, president_name))
            bPlace = getPersonBirthPlace(PREFIX + "/wiki" + president_name)
            if len(bPlace) > 0:
                bPlace1 = bPlace[0]
                bPlaceOntology = prepareStrToOntology(bPlace1)
                g.add((bPlaceOntology, birth_place_of_person, president_name))

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


def queryGraph(q):
    res = list(g.query(q))
    if len(res) == 0:
        return []
    output = []
    for item in res:
        output.append(str(item[0])[19:].replace("_"," "))
    return output


# question to sparql

def whoIsQuestion(question):
    if question.find("president") != -1:
        country = question.split()[-1]
        q = "select * where {?a <http://example.org/president_of_country> <http://example.org/" + country + ">}"
        res = queryGraph(q)

    elif question.find("prime minister") != -1:
        country = question.split()[-1]
        q = "select * where {?a <http://example.org/prime_minister_of_country> <http://example.org/" + country + ">}"
        res = queryGraph(q)

    else:
        name = question[7:].replace(" ", "_")
        q = "select * where " \
            "{<http://example.org/" + name + "> <http://example.org/president_of_country> ?x}"
        res = queryGraph(q)
        if len(res) == 0:
            q = "select * where " \
                "{<http://example.org/" + name + "> <http://example.org/prime_minister_of_country> ?x}"
            res = queryGraph(q)





def whatIsQuestion(question):
    country = question.split()[-1]
    if question.find("population of") != -1:
        subject = "population_of_country"
    elif question.find("area of") != -1:
        subject = "area_of_country"
    elif question.find("form of government") != -1:
        subject = "government_of_country"
    elif question.find("is the capital of") != -1:
        subject = "capital_of_country"
    q = "select * where  {?x<http://example.org/" + subject + "> <http://example.org/" + country + ">}"
    res = queryGraph(q)



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

# s = (questionToSparql("What is the population of Israel?"))
# print(getCountryArea(PREFIX+"/wiki/Austria"))

# print(s)
"""""
g = rdflib.Graph()
g.parse("graph.nt", format="nt")
query_list_result = g.query(s)
print(list(query_list_result))
"""""
# print(getCountryArea(PREFIX+"/wiki/China"))
# createOntology()

# q = "select ?x where " \
#     "{ ?x <http://example.org/prime_minister_of_country>  <http://example.org/India> " \
#     "}"
# x = g1.query(q)
# print(list(x))
g.parse("ontology.nt", format="nt")
q = questionToSparql("Who is Joe Biden")
print(q)
