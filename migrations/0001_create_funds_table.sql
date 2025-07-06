CREATE TABLE IF NOT EXISTS funds (
    fund_id VARCHAR(10) PRIMARY KEY,
    fund_name VARCHAR(100),
    fund_manager VARCHAR(255),
    tier VARCHAR(10),
    scheme VARCHAR(10)
);
