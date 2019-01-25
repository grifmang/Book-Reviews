from sqlalchemy import create_engine
import os
import csv
from sqlalchemy.orm import scoped_session, sessionmaker

DATABASE_URL = os.environ['DATABASE_URL']

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():

    file_open = open('books.csv', 'r')
    reader = csv.reader(file_open, delimiter=',')
    next(reader)

    db.execute("CREATE TABLE IF NOT EXISTS books ("
                    "isbn VARCHAR PRIMARY KEY NOT NULL,"
                    "title VARCHAR NOT NULL,"
                    "author VARCHAR NOT NULL,"
                    "year INTEGER NOT NULL);")

    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})

    db.commit()
    file_open.close()
    db.close()

if __name__ == "__main__":
    main()
