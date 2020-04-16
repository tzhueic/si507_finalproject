
from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains API key
import sqlite3

CACHE_BOOK_FILENAME = "google_books_cache.json"
CACHE_BOOK_DICT = {}
CACHE_WIKI_FILENAME = "wiki_cache.json"
CACHE_WIKI_DICT = {}
INSPIRED_TITLE_LIST = []


def get_google_books(search_term):
    '''Obtain API data from Google Books API with use of cache
    
    Parameters
    ----------
    search_term: string

    
    Returns
    -------
    dict

    '''
    if search_term in CACHE_BOOK_DICT.keys():
        return CACHE_BOOK_DICT[search_term]
    else:
        base_url = 'https://www.googleapis.com/books/v1/volumes?'
        params = {
            "key": secrets.GOOGLE_API_KEY,
            "q": search_term,
            "printType": "books",
            "maxResults": 25
        }
        response = requests.get(base_url, params)
        CACHE_BOOK_DICT[search_term] = response.json()
        save_cache(CACHE_BOOK_DICT, CACHE_BOOK_FILENAME)
        return CACHE_BOOK_DICT[search_term]

def create_book_record(record_dict, search_term):
    record = []
    keyword = search_term
    #get title
    title = record_dict['volumeInfo']['title']
    #get subtitle
    try:
        subtitle = record_dict['volumeInfo']['subtitle']
    except:
        subtitle = "No subtitle"
    #get author (first author)
    try:
        author = record_dict['volumeInfo']['authors'][0]
    except:
        author = "No author"
    #get publish date
    publishedDate = record_dict['volumeInfo']['publishedDate']
    #get category
    try:
        category = record_dict['volumeInfo']['categories'][0]
    except:
        category = "No category"
    #get price
    try:
        price = record_dict['saleInfo']['listPrice']['amount']
    except:
        price = "NA"
    #get average rating
    try:
        averageRating = record_dict['volumeInfo']['averageRating']
    except:
        averageRating = 0
    #get rating count
    try:
        ratingCount = record_dict['volumeInfo']['ratingsCount']
    except:
        ratingCount = 0
    
    return [title, subtitle, author, publishedDate, category, price, averageRating, ratingCount, keyword]


def create_wikiresult_record(record_dict, search_term):
    title = record_dict['title']
    url = record_dict['fullurl']
    searchTerm = search_term
    return [title, url, searchTerm]


def get_wiki_results(author):
    '''Obtain API data from Wikipedia API with use of cache

    Parameters
    ----------
    author: string

    Returns
    -------
    dict

    '''
    if author in CACHE_WIKI_DICT.keys():
        return CACHE_WIKI_DICT[author]
    else:
        base_url = 'https://en.wikipedia.org/w/api.php'
        params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": author,
                "prop": "info",
                "inprop": "url"
            }
        response = requests.Session().get(url=base_url, params=params)
        CACHE_WIKI_DICT[author] = response.json()['query']
        save_cache(CACHE_WIKI_DICT, CACHE_WIKI_FILENAME)
        return CACHE_WIKI_DICT[author]


def build_inspired_titles_list():
    ''' 
    Parameters
    ----------
    None

    Returns
    -------
    dict
        
    '''
    title_list = []
    base_url = 'https://www.elle.com/culture/books/g29954140/best-books-2020/'

    if not INSPIRED_TITLE_LIST:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        menu = soup.find_all(class_='listicle-slide-hed-text')
        for book in menu:
            INSPIRED_TITLE_LIST.append(book.find('i').text)
        
    return INSPIRED_TITLE_LIST


def create_database():
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()

    drop_books = '''
        DROP TABLE IF EXISTS "Books";
    '''

    create_books = '''
        CREATE TABLE IF NOT EXISTS "Books" (
            "Title"         TEXT PRIMARY KEY,
            "Subtitle"      TEXT NOT NULL,
            "Author"        TEXT NOT NULL,
            "PublishedDate" TEXT NOT NULL,
            "Category"      TEXT NOT NULL,
            "Price"         TEXT NOT NULL,
            "AverageRating" REAL NOT NULL,
            "RatingCount"   INT NOT NULL,
            "Keyword"       TEXT NOT NULL
        );
    '''

    drop_wikiresults = '''
        DROP TABLE IF EXISTS "WikiResults";
    '''

    create_wikiresults = '''
        CREATE TABLE IF NOT EXISTS "WikiResults" (
            "Title"       TEXT PRIMARY KEY,
            "Url"         TEXT NOT NULL,
            "SearchTerm"  TEXT NOT NULL
        );
    '''
    cur.execute(drop_books)
    cur.execute(create_books)
    cur.execute(drop_wikiresults)
    cur.execute(create_wikiresults)

    conn.commit()


def insert_record_to_books(record_list):
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    insert_books = '''
        INSERT INTO Books
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    cur.execute(insert_books, record_list)
    conn.commit()


def insert_record_to_wikiresults(record_list):
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    insert_wikiresults = '''
        INSERT INTO WikiResults
        VALUES (?, ?, ?)
    '''
    cur.execute(insert_wikiresults, record_list)
    conn.commit()


def load_cache(cache_filename):
    '''Opens the cache file if it exists and loads the JSON into dictionary.
    If the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    cache_filename: string
        The name of the cache file
    
    Returns
    -------
    dict
        The opened cache
    '''
    try:
        cache_file = open(cache_filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict, cache_filename):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    cache_filename: string
        The name of the cache file
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(cache_filename,"w")
    fw.write(dumped_json_cache)
    fw.close()


def interactive_program():
    pass


if __name__ == "__main__":
    #load cache
    CACHE_BOOK_DICT = load_cache(CACHE_BOOK_FILENAME)
    CACHE_WIKI_DICT = load_cache(CACHE_WIKI_FILENAME)

    #load inspired titles list
    build_inspired_titles_list()

    #Create tables in database
    create_database()

    #test cache for Google Books
    book_result = get_google_books('magic')

    #test inserting book record to database
    for result in book_result['items']:
        record = create_book_record(result, 'magic')
        insert_record_to_books(record)

    #test cache for Wikipedia
    wiki_result = get_wiki_results('Stephen King')

    #test inserting wiki result record to database
    for result in wiki_result['pages'].values():
        record = create_wikiresult_record(result, 'Stephen King')
        insert_record_to_wikiresults(record)

