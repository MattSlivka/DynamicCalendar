CREATE TABLE users(
    id INT PRIMARY KEY,
    username VARCHAR(50),
    pass_hash VARCHAR(255),
    auth_ts TIMESTAMP
);
