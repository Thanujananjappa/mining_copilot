-- =========================================
-- Create Database
-- =========================================
CREATE DATABASE IF NOT EXISTS mining_data;
USE mining_data;

-- =========================================
-- Equipment Status Table
-- =========================================
CREATE TABLE IF NOT EXISTS equipment_status (
    id VARCHAR(50) PRIMARY KEY,
    equipment_name VARCHAR(100) NOT NULL,
    status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
    date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    duration_minutes INT DEFAULT 0,
    alert ENUM('Yes','No') DEFAULT 'No',
    reason VARCHAR(255),
    issue VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_equipment_name (equipment_name),
    INDEX idx_date (date),
    INDEX idx_alert (alert)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Load CSV into equipment_status
LOAD DATA INFILE '/path/to/equipment_status_logs_rows.csv'
INTO TABLE equipment_status
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, equipment_name, status, date, start_time, end_time, duration_minutes, alert, reason, issue, comment, created_at);

-- =========================================
-- Production By Date Table (Shift-wise)
-- =========================================
CREATE TABLE IF NOT EXISTS production_by_date (
    Date DATE PRIMARY KEY,
    Excavator INT,
    Dumper INT,
    Total_Trips INT,
    Qty_m3 DECIMAL(12,2),
    Excavator_1 INT,
    Dumper_1 INT,
    Total_Trips_1 INT,
    Qty_m3_1 DECIMAL(12,2),
    Excavator_2 INT,
    Dumper_2 INT,
    Total_Trips_2 INT,
    Qty_m3_2 DECIMAL(12,2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOAD DATA INFILE '/path/to/mines_production_data_by_date.csv'
INTO TABLE production_by_date
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(Date, Excavator, Dumper, Total_Trips, Qty_m3, Excavator_1, Dumper_1, Total_Trips_1, Qty_m3_1, Excavator_2, Dumper_2, Total_Trips_2, Qty_m3_2);

-- =========================================
-- Trip Details Table
-- =========================================
CREATE TABLE IF NOT EXISTS trip_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Date DATE NOT NULL,
    Source VARCHAR(255),
    Destination VARCHAR(255),
    Specification VARCHAR(100),
    Asset_Name VARCHAR(100),
    Operator VARCHAR(100),
    Production DECIMAL(10,2) DEFAULT 0,
    Total INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (Date),
    INDEX idx_asset (Asset_Name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOAD DATA INFILE '/path/to/mines_production_data_by_date_by_equipment.csv'
INTO TABLE trip_details
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(Date, Source, Destination, Specification, Asset_Name, Operator, Production, Total);

-- =========================================
-- Create User and Permissions
-- =========================================
CREATE USER IF NOT EXISTS 'mining_user'@'%' IDENTIFIED BY 'miningpass';
GRANT ALL PRIVILEGES ON mining_data.* TO 'mining_user'@'%';
FLUSH PRIVILEGES;

