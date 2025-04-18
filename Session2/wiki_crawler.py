import requests as rq
from bs4 import BeautifulSoup 
from tqdm import tqdm
import os

def _download_html(url: str) -> str:
 
    with rq.get(url, stream=True) as response:

        return response.text


def get_pages(soup):
    pages_used = {}

    soup = soup.find("div", {"id": "mw-pages"})
    soup = soup.find_all("li")
    
    pages = []
    for page in soup:
        wiki = page.find("a")['href']
    
        if wiki not in pages_used:
            page_name = rq.utils.unquote(wiki)
            pages.append(page_name)
            pages_used[wiki] = 1
    return pages
  

def extract_text_from_wikipedia(html_content=None, url=None):
    """
    Extract text from Wikipedia HTML content or URL.
    
    Args:
        html_content (str): Raw HTML content to parse
        url (str): Wikipedia article URL
        
    Returns:
        str: Extracted text content
    """
    # If URL provided, fetch the content
    if url:
        try:
            response = rq.get(url)
            response.raise_for_status()  # Raise exception for bad status codes
            html_content = response.text
        except rq.RequestException as e:
            raise Exception(f"Error fetching URL: {e}")
    
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove navigation elements
    for element in soup(['nav', 'script', 'style', 'footer']):
        element.decompose()

    # Remove unnecassary classes
    for class_name in ['navbox']:
        for element in soup.find_all(class_=class_name):
            element.decompose()
        
    # Extract text from paragraphs
    text = ''
    for paragraph in soup.find_all('p'):
        text += paragraph.get_text() + '\n\n'

    
    return soup.find('title').get_text(), text.strip()


def crawl_wiki_category(category: str, output_path: str, lang: str = "tr", pdf: bool = False):
    """
        Extract text from an entire Wikipedia category and write into a folder.
        Wikipedia categories are titles containing multiple articles like Search_algorithms for example
    
    Args:
        category (str): one of the category titles from https://en.wikipedia.org/wiki/Wikipedia:Contents/Categories or can be searched from https://en.wikipedia.org/w/index.php?search=&ns14=1
        output_path (str): local output path, function creates a folder in the working directory with that name
        lang (str): basically either tr for Turkish Vikipedi otherwise the English Wikipwdia
    """

    base_url = "https://tr.wikipedia.org" if lang == "tr" else "https://en.wikipedia.org"
    os.makedirs(output_path, exist_ok=True)
    category_url = base_url + "/wiki/Kategori:" if lang == "tr" else base_url + "/wiki/Category:"
    
    html = _download_html(category_url + category)
    soup = BeautifulSoup(html,'html.parser')
    wikies = get_pages(soup)

    if not pdf:
        for wiki in tqdm(wikies):
            url = base_url + wiki
            title, text = extract_text_from_wikipedia(url=url)
            with open(f"{output_path}/{title}.txt", "w") as f:
                f.write(text)

    else:
        os.makedirs(output_path + '/PDF/', exist_ok=True)
        for wiki in tqdm(wikies):
            title = wiki.split("/")[-1]
            url = base_url + '/api/rest_v1/page/pdf/' + title
            response = rq.get(url, headers = {"accept": "application/pdf"})
            with open(f'{output_path}/PDF/{title}.pdf','wb') as f:
                f.write(response.content)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Wikipedia Category Crawler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Example usage:
        python wiki_crawler.py -c "Search_algorithms" -o search-algorithms -l en
        python wiki_crawler.py --category "Avrupa_Yakası" --output avrupa-yakasi --pdf --language tr'''
    )
    
    parser.add_argument(
        '-c', '--category',
        required=True,
        help='Wikipedia category to crawl (e.g., "Search_algorithms", "Alacakaranlık_filmleri")'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output directory path within current working directory'
    )
    
    parser.add_argument(
        '-l', '--language',
        default='en',
        choices=['en', 'tr'],
        help='Wikipedia language (en or tr), used for configuring urls'
    )
    
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='Download articles as PDF instead of text'
    )
    
    args = parser.parse_args()
    
    try:
        crawl_wiki_category(
            category=args.category,
            output_path=args.output,
            lang=args.language,
            pdf=args.pdf
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())