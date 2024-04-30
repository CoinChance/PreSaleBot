-- init.sql


-- CREATE DATABASE presalebot;

-- USE presalebot


CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) UNIQUE,
    name VARCHAR(255), 
    symbol VARCHAR(255),
    web VARCHAR(255),
    twitter VARCHAR(255),
    telegram VARCHAR(255),
    token_address VARCHAR(255),
    supply VARCHAR(255),           -- 1,000,000,000
    chain VARCHAR(255),
    soft_cap VARCHAR(255),
    start_time VARCHAR(255),   -- 2024-04-03 18:00:00 (UTC)
    end_time VARCHAR(255),     -- 2024-04-03 18:00:00 (UTC)
    lockup_time VARCHAR(255),   -- 120 days after pool ends
    rate VARCHAR(255),  -- 1 SOL = 155,411.3105 $BOOB
    raised VARCHAR(255),    -- 2,687.3787 SOL (2687.38%)
    scrap_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

