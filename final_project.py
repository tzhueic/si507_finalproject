from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains API key
import sqlite3
import sys
import plotly.graph_objs as go

CACHE_BOOK_FILENAME = "google_books_cache.json"
CACHE_BOOK_DICT = {}
CACHE_WIKI_FILENAME = "wiki_cache.json"
CACHE_WIKI_DICT = {}
INSPIRED_TITLE_LIST = []

# FUNCTIONS
def get_google_books(search_term):
    '''Obtain API data from Google Books API with use of cache
    
    Parameters
    ----------
    search_term: string
        the search term inputted

    Returns
    -------
    dict
        results returned by API
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
    '''Extract required information from the Google Books API results,
    save as a list

    Parameters
    ----------
    record_dict: dict
        results returned by API
    search_term: string
        the search term inputted

    Returns
    -------
    list
        extracted information
    '''
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
    try:
        publishedDate = record_dict['volumeInfo']['publishedDate']
    except:
        publishedDate = "NA"
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


def get_wiki_results(author):
    '''Obtain API data from Wikipedia API with use of cache

    Parameters
    ----------
    author: string
        author's name

    Returns
    -------
    dict
        results returned by API
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


def create_wikiresult_record(record_dict, search_term):
    '''Extract required information from the Wikipedia API results,
    save as a list

    Parameters
    ----------
    record_dict: dict
        results returned by API
    search_term: string
        the search term inputted

    Returns
    -------
    list
        extracted information
    '''
    title = record_dict['title']
    url = record_dict['fullurl']
    searchTerm = search_term
    return [title, url, searchTerm]


def build_inspired_titles_list():
    '''Scrape the titles from the page

    Parameters
    ----------
    none

    Returns
    -------
    list
        title of each book on the page
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
    '''Create two tables in the database to store data
    obtained from APIs

    Parameters
    ----------
    none

    Returns
    -------
    none
    '''
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()

    drop_books = '''
        DROP TABLE IF EXISTS "Books";
    '''

    create_books = '''
        CREATE TABLE IF NOT EXISTS "Books" (
            "Title"         TEXT NOT NULL,
            "Subtitle"      TEXT NOT NULL,
            "Author"        TEXT NOT NULL,
            "PublishedDate" TEXT NOT NULL,
            "Category"      TEXT NOT NULL,
            "Price"         TEXT NOT NULL,
            "AverageRating" REAL NOT NULL,
            "RatingCount"   INT NOT NULL,
            "Keyword"       TEXT NOT NULL,
            PRIMARY KEY (Title, PublishedDate)
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
    '''Insert records retrieved from Google Books API
    into the Books table in the database

    Parameters
    ----------
    record_list: list
        extracted information
    
    Returns
    -------
    none
    '''
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    insert_books = '''
        INSERT INTO Books
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    cur.execute(insert_books, record_list)
    conn.commit()


def insert_record_to_wikiresults(record_list):
    '''Insert records retrieved from Wikipedia API
    into the WikiResults table in the database

    Parameters
    ----------
    record_list: list
        extracted information
    
    Returns
    -------
    none
    '''
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
    none
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(cache_filename,"w")
    fw.write(dumped_json_cache)
    fw.close()


def print_inspired_list():
    '''Prints titles in INSPITED_TITLE_LIST as a numbered list

    Parameters
    ----------
    none

    Returns
    -------
    none
    '''
    i = 1
    for title in INSPIRED_TITLE_LIST:
        print(f"{i}. {title}")
        i += 1


def extract_book_from_database(user_input):
    '''Extracts relevant records from the Books table in database

    Parameters
    ----------
    user_input: string
        the search term inputted
    
    Returns
    -------
    list
        a list of tuples that contains the extracted records
    '''
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    query = f'''
    SELECT Title, Subtitle, Author, PublishedDate
    FROM Books
    WHERE Keyword = '{user_input}'
    '''     
    results = cur.execute(query).fetchall()
    conn.close()
    return results


def display_book_results(results):
    '''Displays results in the predefined format

    Parameters
    ----------
    results: list
        extracted records from the database
    
    Returns
    -------
    none
    '''
    i = 1
    for book in results:
        print(f"{i}. {book[0]}- {book[1]}:{book[2]} ({book[3]})", end='\n')
        i += 1


def extract_wikiresult_from_database(author):
    '''Extracts relevant records from the WikiResults table in database

    Parameters
    ----------
    author: string
        the author's name
    
    Returns
    -------
    list
        a list of tuples that contains the extracted records
    '''
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    query = f'''
    SELECT Title, Url
    FROM WikiResults
    WHERE SearchTerm = '{author}'
    '''     
    results = cur.execute(query).fetchall()
    conn.close()
    return results


def display_wiki_results(results):
    '''Displays results in the predefined format

    Parameters
    ----------
    results: list
        extracted records from the database
    
    Returns
    -------
    none
    '''
    max_title = 0
    for result in results:
        if len(result[0]) > max_title:
            max_title = len(result[0])
    print(f"{'Title':<{max_title+2}}{'URL':<}")
    for result in results:    
        print(f"{result[0]:<{max_title+2}}{result[1]:<}")


def display_visualize_options():
    '''Prints the visualization options menu

    Parameters
    ----------
    none

    Returns
    -------
    none
    '''
    print(f"*****")
    print(f"1. Bar chart: results by category")
    print(f"2. Scatter Plot: average rating and ratings count")
    print(f"*****")


def count_books_category(user_input):
    '''Extracts categories and counts of relevant records
    from the database

    Parameters
    ----------
    user_input: string
        the search term inputted
        to filter relevant records from database

    Returns
    -------
    list
        a list of tuples that contains the extracted records
    '''
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    query = f'''
    SELECT Category, COUNT(*)
    FROM Books
    WHERE Keyword = '{user_input}'
    GROUP BY Category
    '''     
    results = cur.execute(query).fetchall()
    conn.close()
    return results


def plot_category_barchart(results):
    '''Presents barplot that groups results by category

    Parameters
    ----------
    results: list
        extracted information from the database

    Returns
    -------
    none
    '''
    xvals = []
    yvals = []
    
    for result in results:
        xvals.append(result[0])
        yvals.append(result[1])

    bar_data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title="Book Search Results by Category")
    fig = go.Figure(data=bar_data, layout=basic_layout)
    fig.show()


def get_ratings_info(user_input):
    '''Extracts average ratings and rating counts 
    of relevant records from the database

    Parameters
    ----------
    user_input: string
        the search term inputted
        to filter relevant records from database

    Returns
    -------
    list
        a list of tuples that contains the extracted records
    '''
    conn = sqlite3.connect("finalproject.sqlite")
    cur = conn.cursor()
    query = f'''
    SELECT AverageRating, RatingCount, Title
    FROM Books
    WHERE Keyword = '{user_input}'
    '''     
    results = cur.execute(query).fetchall()
    conn.close()
    return results


def plot_rating_scatter(results):
    '''Presents scatter plot for average ratings and rating counts

    Parameters
    ----------
    results: list
        extracted information from the database

    Returns
    -------
    none
    '''
    xvals = []
    yvals = []
    hovertext = []
    
    for result in results:
        xvals.append(result[0])
        yvals.append(result[1])
        hovertext.append(result[2])
    
    scatter_data = go.Scatter(
        x=xvals, 
        y=yvals,
        hovertext = hovertext,
        mode='markers')
    basic_layout = go.Layout(
        title="Average Rating and Rating Count",
        xaxis_title="Average Rating",
        yaxis_title="Rating Count")
    fig = go.Figure(data=scatter_data, layout=basic_layout)
    fig.show()


def search_for_books(resp):
    '''Conducts search through Google Books API,saves the 
    results to database, extracts relevant records from the 
    database, and displays the results in console

    Parameters
    ----------
    resp: string
        the search term inputted

    Returns
    -------
    list
        a list of tuples that contains the extracted records
    '''
    book_result = get_google_books(resp)
    for result in book_result['items']:
        record = create_book_record(result, resp)
        insert_record_to_books(record)
    book_results = extract_book_from_database(resp)
    display_book_results(book_results)

    return book_results


def search_on_wiki(book_results, resp_wiki):
    '''Conducts search through Wikipedia API,saves the results 
    to database, extracts relevant records from the database, 
    and displays the results in console

    Parameters
    ----------
    book_results: list
        extracted results of books information
    resp_wiki: string
        the selected author as search term
    
    Returns
    -------
    none
    '''
    author = book_results[int(resp_wiki)-1][2]
    wiki_result = get_wiki_results(author)
    for result in wiki_result['pages'].values():
        try:
            record = create_wikiresult_record(result, author)
            insert_record_to_wikiresults(record)
        except:
            pass
    results = extract_wikiresult_from_database(author)
    display_wiki_results(results) 


def interactive_program():
    '''Allows a user to interactively input commands, present 
    the results in the console, and visualize the results 
    with different plots

    Parameters
    ----------
    none

    Returns
    -------
    none
    '''
    #load cache
    CACHE_BOOK_DICT = load_cache(CACHE_BOOK_FILENAME)
    CACHE_WIKI_DICT = load_cache(CACHE_WIKI_FILENAME)

    #load inspired titles list
    build_inspired_titles_list()

    #Create tables in database
    create_database()

    while True:
        resp = input(f"Enter a search term, 'inspired' to get inspired by recommended books, or 'exit' to quit:")
        if resp == 'inspired':
            print_inspired_list()
            resp_title = input(f"Enter a corresponding number to search with the title:")
            if int(resp_title) < 1:
                print(f"Invalid input.")
                continue
            else:
                try:
                    title = INSPIRED_TITLE_LIST[int(resp_title)-1]
                    book_results = search_for_books(title)
                    while True:
                        resp_plot = input(f"Do you want to visualize the results, enter 'yes' or 'no':")
                        if resp_plot == 'yes':
                            display_visualize_options()
                            while True:
                                resp_plot = input(f"Which type of visualization do you want to choose, enter '1', '2', or 'no' to skip:")
                                if resp_plot == '1':
                                    category_results = count_books_category(title)
                                    plot_category_barchart(category_results)
                                    while True:
                                        resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                        if resp_wiki == 'exit':
                                            sys.exit()
                                        elif resp_wiki == 'back':
                                            break
                                        elif int(resp_wiki) < 1:
                                            print(f"Invalid Input. Enter an existing number.")
                                            continue
                                        else:
                                            try:
                                                search_on_wiki(book_results, resp_wiki)
                                            except:
                                                print(f"Invalid Input. Enter an existing number.")
                                                continue
                                elif resp_plot == '2':
                                    rating_results = get_ratings_info(title)
                                    plot_rating_scatter(rating_results)
                                    while True:
                                        resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                        if resp_wiki == 'exit':
                                            sys.exit()
                                        elif resp_wiki == 'back':
                                            break
                                        elif int(resp_wiki) < 1:
                                            print(f"Invalid Input. Enter an existing number.")
                                            continue
                                        else:
                                            try:
                                                search_on_wiki(book_results, resp_wiki)
                                            except:
                                                print(f"Invalid Input. Enter an existing number.")
                                                continue
                                elif resp_plot == 'no':
                                    while True:
                                        resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                        if resp_wiki == 'exit':
                                            sys.exit()
                                        elif resp_wiki == 'back':
                                            break
                                        elif int(resp_wiki) < 1:
                                            print(f"Invalid Input. Enter an existing number.")
                                            continue
                                        else:
                                            try:
                                                search_on_wiki(book_results, resp_wiki)
                                            except:
                                                print(f"Invalid Input. Enter an existing number.")
                                                continue
                                else:
                                    print(f"Invalid input. Enter '1', '2', or 'no'.")
                                    continue
                                break
                        elif resp_plot == 'no':
                            while True:
                                resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                if resp_wiki == 'exit':
                                    sys.exit()
                                elif resp_wiki == 'back':
                                    break
                                elif int(resp_wiki) < 1:
                                    print(f"Invalid Input. Enter an existing number.")
                                    continue
                                else:
                                    try:
                                        search_on_wiki(book_results, resp_wiki) 
                                    except:
                                        print(f"Invalid Input. Enter an existing number.")
                                        continue
                        else:
                            print(f"Invalid input. Enter 'yes' or 'no'.")
                            continue
                        break
                except SystemExit:
                    sys.exit()
                except:
                    print(f"Invalid Input. Enter an existing number.")
                    continue
        elif resp == 'exit':
            break
        else:
            book_results = search_for_books(resp)
            while True:
                resp_plot = input(f"Do you want to visualize the results, enter 'yes' or 'no':")
                if resp_plot == 'yes':
                    display_visualize_options()
                    while True:
                        resp_plot = input(f"Which type of visualization do you want to choose, enter '1', '2', or 'no' to skip:")
                        if resp_plot == '1':
                            category_results = count_books_category(resp)
                            plot_category_barchart(category_results)
                            while True:
                                resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                if resp_wiki == 'exit':
                                    sys.exit()
                                elif resp_wiki == 'back':
                                    break
                                elif int(resp_wiki) < 1:
                                    print(f"Invalid Input. Enter an existing number.")
                                    continue
                                else:
                                    try:
                                        search_on_wiki(book_results, resp_wiki)
                                    except:
                                        print(f"Invalid Input. Enter an existing number.")
                                        continue
                        elif resp_plot == '2':
                            rating_results = get_ratings_info(resp)
                            plot_rating_scatter(rating_results)
                            while True:
                                resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                if resp_wiki == 'exit':
                                    sys.exit()
                                elif resp_wiki == 'back':
                                    break
                                elif int(resp_wiki) < 1:
                                    print(f"Invalid Input. Enter an existing number.")
                                    continue
                                else:
                                    try:
                                        search_on_wiki(book_results, resp_wiki)
                                    except:
                                        print(f"Invalid Input. Enter an existing number.")
                                        continue
                        elif resp_plot == 'no':
                            while True:
                                resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                                if resp_wiki == 'exit':
                                    sys.exit()
                                elif resp_wiki == 'back':
                                    break
                                elif int(resp_wiki) < 1:
                                    print(f"Invalid Input. Enter an existing number.")
                                    continue
                                else:
                                    try:
                                        search_on_wiki(book_results, resp_wiki)
                                    except:
                                        print(f"Invalid Input. Enter an existing number.")
                                        continue
                        else:
                            print(f"Invalid input. Enter '1', '2', or 'no'.")
                            continue
                        break
                elif resp_plot == 'no':
                    while True:
                        resp_wiki = input(f"Enter a corresponding number to learn more about the author, 'back' for new search, or 'exit' to quit:")
                        if resp_wiki == 'exit':
                            sys.exit()
                        elif resp_wiki == 'back':
                            break
                        elif int(resp_wiki) < 1:
                            print(f"Invalid Input. Enter an existing number.")
                            continue
                        else:
                            try:
                                search_on_wiki(book_results, resp_wiki) 
                            except:
                                print(f"Invalid Input. Enter an existing number.")
                                continue
                else:
                    print(f"Invalid input. Enter 'yes' or 'no'.")
                    continue
                break


# MAIN PROGRAM
if __name__ == "__main__":
    interactive_program()
    