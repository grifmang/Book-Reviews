CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL
);


CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    book_id INTEGER REFERENCES books,
    rating SMALLINT NOT NULL CONSTRAINT Invalid_Rating CHECK (rating <=5 AND rating>=1),
    comment VARCHAR
);