import re
import sys

import requests
import lxml.html
import rdflib
from urllib.parse import unquote

PREFIX = "http://en.wikipedia.org"
ontology_Prefix = 'http://example.org/'

countries = []
countriesNames = []
primeMinisters = set()
populations = set()
g = rdflib.Graph()

president_of_country = rdflib.URIRef(ontology_Prefix + "president_of_country")
prime_minister_of_country = rdflib.URIRef(ontology_Prefix + "prime_minister_of_country")
population_of_country = rdflib.URIRef(ontology_Prefix + "population_of_country")
capital_of_country = rdflib.URIRef(ontology_Prefix + "capital_of_country")
area_of_country = rdflib.URIRef(ontology_Prefix + "area_of_country")
government_of_country = rdflib.URIRef(ontology_Prefix + "government_of_country")
birth_day_of_person = rdflib.URIRef(ontology_Prefix + "birth_day_of_person")
birth_place_of_person = rdflib.URIRef(ontology_Prefix + "birth_place_of_person")
driving_side_of_country = rdflib.URIRef(ontology_Prefix + "driving_side_of_country")


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
    presURL = doc.xpath("((//table[contains(./@class,'infobox')])[1]//tr[.//th//text()='President']/td//a)[1]/@href")

    # option 2 - partial path:
    #    ref = doc.xpath("//tr[.//text()='President']/td//a/@href")
    return presURL


def getCountryPrimeMinister(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    primURL = doc.xpath(
        "((//table[contains(./@class,'infobox')])[1]//tr[.//th//text()='Prime Minister']/td//a)[1]/@href")
    return primURL


def getCountryGovernment(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    govForms = doc.xpath("(//table[contains(./@class,'infobox')])[1]//tr[.//text()='Government']/td//a/@title")
    return govForms


def getCountryDrivingSide(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    drivingSide = doc.xpath(
        "((//table[contains(./@class,'infobox')])[1]//tr[.//th//text()='Driving side']/td//text())[1]")
    return drivingSide


def getCountryCapital(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    primURL = doc.xpath("((//table[contains(./@class,'infobox')])[1]//tr[.//text()='Capital']/td//a)[1]/@href")
    if len(primURL) > 0:
        if 'wiki' not in primURL[0]:
            return []
    return primURL


def getCountryPopulation(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    population = doc.xpath(
        "((//table[contains(./@class,'infobox')])[1]//tr[.//text()='Population']/following-sibling::tr[1]/td//text()[.!='\n'])[1]")
    return population


def getCountryArea(countryURL):
    r = requests.get(countryURL)
    doc = lxml.html.fromstring(r.content)
    area = doc.xpath(
        "((//table[contains(./@class,'infobox')])[1]//tr[contains(./th//text(),'Area')]/following-sibling::tr[1]/td//text()[.!='\n'])[1]")
    strrinArea = area[0]
    # area = re.split("–-/", strrinArea)
    result = ""
    for c in strrinArea:
        if c.isdigit() or c == "," or c == ".":
            result += c
        else:
            break

    return [result + " km squared"]


def getPersonBirthday(personURL):
    r = requests.get(personURL)
    doc = lxml.html.fromstring(r.content)
    primURL = doc.xpath("(//table[contains(./@class,'infobox')])[1]//span[./@class='bday']/text()")
    return primURL


def getPersonBirthPlace(personURL):
    r = requests.get(personURL)
    doc = lxml.html.fromstring(r.content)
    birthURLS = doc.xpath("(//table[contains(./@class,'infobox')])[1]//tr[.//text()='Born']/td//a/@href")
    for url in birthURLS:
        if url in countries:
            return [url]
    birthString = doc.xpath("(//table[contains(./@class,'infobox')])[1]//tr[.//text()='Born']/td//text()")
    if len(birthString) == 0:
        return []
    for place in birthString:
        birthPlace = re.sub(r'[^a-zA-Z]', '', place)
        if birthPlace in countriesNames:  # need to actually init the countriesNames with the proper names
            return [f"/wiki/{birthPlace}"]

    return []


def getAlldataByCountry(country):
    population = getCountryPopulation(PREFIX + country)
    president = getCountryPresident(PREFIX + country)
    primeMinister = getCountryPrimeMinister(PREFIX + country)
    area = getCountryArea(PREFIX + country)
    capital = getCountryCapital(PREFIX + country)
    gov = getCountryGovernment(PREFIX + country)
    drive = getCountryDrivingSide(PREFIX + country)
    return primeMinister, population, capital, area, gov, president, drive


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
    global countries
    countries = getAllCountryRefs("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")
    for country1 in countries:
        countriesNames.append(country1[6:])

    for country1 in countries:
        # for country1 in ['/wiki/Solomon_Islands']:
        prime_minister, population, capital, area, gov, president, drive = getAlldataByCountry(country1)
        countryOntology = prepareStrToOntology(country1)
        if len(prime_minister) > 0:
            prime_minister_name = prime_minister[0]
            prime_minister_name = prime_minister_name[6:]  # remove wiki
            prime_minister_name.replace(" ", "_")
            primeMinisters.add(prime_minister_name)
            prime_ministerOntology = prepareStrToOntology(prime_minister_name)
            g.add((prime_ministerOntology, prime_minister_of_country, countryOntology))
            bDay = getPersonBirthday(PREFIX + "/wiki/" + prime_minister_name)
            if len(bDay) > 0:
                bDay1 = bDay[0]
                bdayOntolgy = prepareStrToOntology(bDay1)
                g.add((bdayOntolgy, birth_day_of_person, prime_ministerOntology))
            bPlace = getPersonBirthPlace(PREFIX + "/wiki/" + prime_minister_name)
            if len(bPlace) > 0:
                bPlace1 = bPlace[0]
                bPlaceOntology = prepareStrToOntology(bPlace1)
                g.add((bPlaceOntology, birth_place_of_person, prime_ministerOntology))

        if len(president) > 0:
            president_name = president[0]
            president_name = president_name[6:]  # remove wiki
            president_name.replace(" ", "_")
            populations.add(president_name)
            presidentOntology = prepareStrToOntology(president_name)
            g.add((presidentOntology, president_of_country, countryOntology))
            bDay = getPersonBirthday(PREFIX + "/wiki/" + president_name)
            if len(bDay) > 0:
                bDay1 = bDay[0]
                bdayOntolgy = prepareStrToOntology(bDay1)
                g.add((bdayOntolgy, birth_day_of_person, presidentOntology))
            bPlace = getPersonBirthPlace(PREFIX + "/wiki/" + president_name)
            if len(bPlace) > 0:
                bPlace1 = bPlace[0]
                bPlaceOntology = prepareStrToOntology(bPlace1)
                g.add((bPlaceOntology, birth_place_of_person, presidentOntology))

        populationString = population[0]
        populationAntology = prepareStrToOntology(populationString)
        g.add((populationAntology, population_of_country, countryOntology))
        areaString = area[0]
        areaAntology = prepareStrToOntology(areaString)
        g.add((areaAntology, area_of_country, countryOntology))
        if len(drive) > 0:
            driveString = drive[0]
            driveOntology = prepareStrToOntology(driveString)
            g.add((driveOntology, driving_side_of_country, countryOntology))

        for capital1 in capital:
            capitalAntology = prepareStrToOntology(capital1)
            g.add((capitalAntology, capital_of_country, countryOntology))
        for formOfGov in gov:
            govOntology = prepareStrToOntology(formOfGov)
            g.add((govOntology, government_of_country, countryOntology))

    g.serialize("ontology.nt", format="nt")


def queryGraphList(q):
    res = list(g.query(q))
    print(res)
    if len(res) == 0:
        return []
    output = []
    for item in res:
        output.append(str(item[0])[19:].replace("_", " "))
    return output


def queryGraph(q):
    res = list(g.query(q))

    if len(res) == 0:
        return []
    output = []
    for item in res:
        output.append(str(item[0])[19:].replace("_", " "))
    return output


# question to sparql

def whoIsQuestion(question):
    if question.find("president") != -1:
        country = question[24:-1].replace(" ", "_")
        q = "select * where {?a <http://example.org/president_of_country> <http://example.org/" + country + ">}"
        res = queryGraph(q)
        resultString = ""
    elif question.find("prime minister") != -1:
        country = question[29:-1].replace(" ", "_")
        q = "select * where {?a <http://example.org/prime_minister_of_country> <http://example.org/" + country + ">}"
        res = queryGraph(q)
        resultString = ""

    else:
        name = question[7:-1].replace(" ", "_")
        q = "select * where " \
            "{<http://example.org/" + name + "> <http://example.org/president_of_country> ?x}"
        res = queryGraph(q)
        resultString = "President of "
        if len(res) == 0:
            q = "select * where " \
                "{<http://example.org/" + name + "> <http://example.org/prime_minister_of_country> ?x}"
            res = queryGraph(q)
            resultString = "Prime minister of "
    res = sorted(res)
    for item in res:
        resultString += item + ", "
    return resultString[:-2]


def whatIsQuestion(question):
    if question.find("population of") != -1:
        country = question[26:-1].replace(" ", "_")
        subject = "population_of_country"
    elif question.find("area of") != -1:
        country = question[20:-1].replace(" ", "_")
        subject = "area_of_country"
    elif question.find("form of government") != -1:
        country = question[34:-1].replace(" ", "_")
        subject = "government_of_country"
    elif question.find("is the capital of") != -1:
        country = question[23:-1].replace(" ", "_")
        subject = "capital_of_country"
    q = "select * where  {?x <http://example.org/" + subject + "> <http://example.org/" + country + ">}"
    res = queryGraph(q)
    res = sorted(res)
    resultString = ""
    for item in res:
        resultString += item + ", "
    return resultString[:-2]


def whenQuestion(question):
    if question.find("president") != -1:
        country = question[26:-6]
        country = country.replace(" ", "_")

        q = "select ?y where {" \
            "?x <http://example.org/president_of_country> <http://example.org/" + country + "> ." \
                                                                                            "?y <http://example.org/birth_day_of_person> ?x}"
        res = queryGraph(q)
    else:
        country = question[31:-6]
        country = country.replace(" ", "_")

        q = "select ?y where {" \
            "?x <http://example.org/prime_minister_of_country> <http://example.org/" + country + "> ." \
                                                                                                 "?y <http://example.org/birth_day_of_person> ?x}"
        res = queryGraph(q)

    res.sort()
    resString = ""
    for i in range(len(res)):
        resString += res[i]
    return resString


def whereQuestion(question):
    if question.find("president") != -1:
        country = question[27:-6]
        country = country.replace(" ", "_")
        q = "select ?y where {" \
            "?x <http://example.org/president_of_country> <http://example.org/" + country + "> ." \
                                                                                            "?y <http://example.org/birth_place_of_person> ?x}"
        res = queryGraph(q)
        resString = ""
        res.sort()
        for i in range(len(res)):
            resString += res[i]
        return resString
    else:
        country = question[32:-6]
        country = country.replace(" ", "_")
        q = "select ?y where {" \
            "?x <http://example.org/prime_minister_of_country> <http://example.org/" + country + "> ." \
                                                                                                 "?y <http://example.org/birth_place_of_person> ?x}"
        res = queryGraph(q)
        resString = ""
        res.sort()
        for i in range(len(res)):
            resString += res[i]
        return resString


def howQuestion(question):
    if question.find("also") != -1:
        form1, form2 = question.split("are also")
        form1 = (form1.split("?")[0]).split()
        form1 = "_".join(form1[2:])
        form2 = (form2.split("?")[0]).split()
        form2 = "_".join(form2)
        q = "select * where {  <" + ontology_Prefix + form1 + "> <http://example.org/government_of_country> ?x. " \
            + " <" + ontology_Prefix + form2 + "> <http://example.org/government_of_country> ?x. }"

        res = queryGraph(q)
        return len(res)
    elif question.find("born") != -1:
        place = question[33:-1]
        place = f"<{ontology_Prefix}{place}>"
        print(place)
        q = "select ?e where { " + place + " <http://example.org/birth_place_of_person> ?e. " \
                                          "?e <http://example.org/president_of_country> ?z}"
        res = queryGraph(q)
        return len(res)


def ListQuestion(question):
    name = (question.split("?")[0]).split(" ")
    name = "_".join(name[9:])
    q = "select ?x where { ?e <http://example.org/capital_of_country> ?x FILTER(regex(lcase(str(?e)),\"" + \
        str(name).lower() + "\"))}"
    res = queryGraph(q)
    res.sort()
    return res


def ourQuestion(question):
    country = question[30:-1].replace(" ", "_")
    q = "select ?a where {?a <http://example.org/driving_side_of_country> <http://example.org/" + country + ">}"
    res = queryGraph(q)
    if res:
        if res[0][0] == 'l':
            return "left"
        return "right"
    return ""


def questionToSparql(question):
    # who is question
    if question.find("Who is") != -1:
        return whoIsQuestion(question)
    # what is question
    if question.find("What is") != -1:
        return whatIsQuestion(question)
    if question.find("When") != -1:
        return whenQuestion(question)
    if question.find("Where") != -1:
        return whereQuestion(question)
    if question.find("How") != -1:
        return howQuestion(question)
    if question.find("List") != -1:
        return ListQuestion(question)
    if question.find("which") != -1:
        return ourQuestion(question)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == "question":
        g.parse("ontology.nt", format="nt")
        question = sys.argv[2]
        print(questionToSparql(question))
    else:
        createOntology()
