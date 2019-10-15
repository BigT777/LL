https://stackoverflow.com/questions/21422090/how-do-you-find-all-list-items-between-two-tags-with-beautifulsoup
for ul in soup.find_all('ul'):
    print 'ul start'
    for idx, li in enumerate(ul.findChildren('li')):
        if idx in range(3):
            print li

https://stackoverflow.com/questions/44723713/python-beautifulsoup-iterating-through-tags-and-attributes
rows = bs_table.find_all('tr')
for row in rows:
    cells = row.find_all(['td', 'th'])
    for cell in cells:
        print(cell.name, cell.attrs)

https://stackoverflow.com/questions/49092812/scraping-categories-and-subcategories-using-beautifulsoup
subcategory_links = []
for link in soup.find_all('a', class_='itemMenuName'):
    subcategory_links.append(link.get('href'))


for link in soup.find_all(["span","b"]):
    print(link)


МОЖНО ИСКАТЬ ЛИНКИ findall И ПОТОМ К НИМ ТАКЖЕ ОБРАЩАТЬСЯ ТЕМИ ЖЕ ФУНКЦИЯМИ findall
for link in soup.find_all(["span","b"]):
    classes = link.get('class')
    if classes and "def" in classes:
        print("DEFINITION", link.text.strip())
        
    if classes and "def-body" in classes:
        print("RUS_DEFIN", link.find("span", attrs = {'class':"trans"}).text.strip())
        for ex in link.find_all("span", attrs = {'class':"eg"}):
            print("ENG_DEFIN_EX", ex.text.strip())
        print("===")