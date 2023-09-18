import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://theevilliouschronicles.fandom.com'

def get_urls_from_page(soup):
    """
    Fetch all links from a page.
    """
    urls = []

    for li in soup.select('li.allpagesredirect a'):
        urls.append(BASE_URL + li['href'])

    return urls

def get_next_page_url(soup):
    """
    Fetch URL for the next page of links.
    """
    divs = soup.find_all('div', class_='mw-allpages-nav')
    
    for div in divs:
        next_page_anchor = div.find('a', string=lambda t: t and "Next page" in t)

    if next_page_anchor:
        return BASE_URL + next_page_anchor['href']
    
    return None

def get_all_urls(start_page_url, prev_urls):
    """
    Recursively scrape all pages for links.
    """
    all_urls = prev_urls
    current_page_url = start_page_url

    while current_page_url:
        response = requests.get(current_page_url)
        response.raise_for_status()
 
        soup = BeautifulSoup(response.content, 'html.parser')

        # Fetch links from the current page
        urls = get_urls_from_page(soup)
        all_urls.extend(urls)

        next_page_url = get_next_page_url(soup)
        
        if next_page_url != None:
            return(get_all_urls(next_page_url, all_urls))
        else:
            return(all_urls)

start_page_url = 'https://theevilliouschronicles.fandom.com/wiki/Special:AllPages'
all_urls = get_all_urls(start_page_url, [])
print(all_urls)

with open('data/links.txt', 'w') as f:
    f.writelines('\n'.join(all_urls))