## Book Review Site

Install requirements
```
pip install -r requirements.txt
```

Configure GoodReads API and OAuth credentials
[GoodReads API](https://www.goodreads.com/api) - 
[Google OAuth](https://developers.google.com/identity/protocols/OpenIDConnect)

# import.py
Connects to database. Creates books table with id(PK), title, author, year and ISBN. Opens books.csv and iterates over each line, importing the data into books table.

# application.py Modules

## API
Navigate to /api/[isbn]
Function will return json object from database containing Title, Author, Year, ISBN. Included will be Review Count and Average Rating from GoodReads.

## Books
Navigate to / or /index or /books
Search using ISBN, Title or Author. Results will be redirected to /search. Empty values are caught and dealt with. As are invalid ISBN's.

## Search
Search will display search results from database in table form. Title will be displayed in link format. If clicked, it will redirect to /details along with ISBN.

## Details
Details will display a formatted page containing details of the book clicked in search. Data displayed is Title, Author, Description, Year, Book Image, Ratings Count, Average Rating, and Reviews. There is also a link to /post to post a review.

## Post
Post will display a form to rate book with stars, and leave a text based review. Which will be saved by user and book in database.

## Login Tools
Login, Register, Logout, and Change Password are available.
Navigation will change links accordingly based on login status.

