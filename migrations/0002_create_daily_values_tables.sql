CREATE TABLE IF NOT EXISTS fund_daily_values (
    fund_id VARCHAR(10),
    date DATE,
    nav DECIMAL(10, 4),
    PRIMARY KEY (fund_id, date),
    FOREIGN KEY (fund_id) REFERENCES funds(fund_id) ON DELETE SET NULL
);
