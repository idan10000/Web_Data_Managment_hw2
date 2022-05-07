import requests
import lxml.html

PREFIX = "http://en.wikipedia.org"
countries = []
countriesNames = []

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

    return area


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


def createOntology():
    pass


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


if __name__ == '__main__':
    print(len(getAllCountryRefs("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")))
    print(getCountryPrimeMinister("https://en.wikipedia.org/wiki/Russia"))
    countries = getAllCountryRefs("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")
    urls = []
    for country in countries:
        urls.append(f"{PREFIX}{country}")

    areas = []
    presidents = []
    testPresidents = []
    for url in urls:
        presidents.append(getCountryCapital(url))
        testPresidents.append(testFunc(url))

    print(len([x for x in presidents if not len(x) == 0]))
    print(len([x for x in testPresidents if not len(x) == 0]))
    print([(presidents[i], testPresidents[i]) for i in range(len(presidents)) if len(presidents[i]) != len(testPresidents[i])])
    print("temp")
