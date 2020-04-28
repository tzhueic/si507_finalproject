# SI 507 Final Project

This program allows users to search for books in Google Books with the search term they input. Different presentation options are availabel. For users with no specific terms in mind, they can be inspired by the titles of the best books of 2020 recommended by Elle. If the users are interested in a book and would like to learn more about the author, they can perform a search with the author’s name as the keyword. The top 10 relevant results on Wikipedia will be returned.

## Getting Started

To run the program on your local machine, you will need to obtain set-ups mentioned below in advance.

### Special Requirements

You need to obtain an API key for Google Books API on https://developers.google.com/books.<br>
Save the key to an independent file called "secrets.py" in the same directory where the program code is saved.<br>
<br>
In this program, data collected from APIs will be stored to a database.<br>
You also need to create a database called "finalproject.sqlite" in the same directory before running the program.

### Required Packages

The program utilizes Beautiful Soup, requests, sqlite3, and plotly.<br>
You need to install the packages if they are not available on your local machine.

## Interaction Instruction

You can run and interact with the program in the command line interface.

### Program Capabilities

* Users will be asked to input a search term, this can be anything from a book’s name, a category, to other keywords. The program will return 25 related books information retrieved from Google Books.
* For users with no specific terms in mind, they can choose to be inspired by the titles of the best books of 2020 recommended by Elle. The title of the 27 books will be printed as a number list in the console. The program will use the title selected by the users as the search term and return 25 related books information retrieved from Google Books. 
* To help the users visualize the results, users can choose to display the data in the following two ways. The chosen visualization will be displayed in the browser.
    * A bar graph that groups the results by category.
    * A scatter plot of the average rating and ratings count of each result.
* If the users are interested in learning more about the author of a book, they can perform a search with the author’s name as the keyword. The top 10 relevant results on Wikipedia will be returned. The title and URL of the page will be presented in a table format in the console. Users can visit the corresponding Wikipedia page by clicking on the URL directly.

## Author

* **Melody Chang** - *Initial work* - [tzhueic](https://github.com/tzhueic)
