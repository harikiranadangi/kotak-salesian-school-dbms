
CREATE TABLE IF NOT EXISTS daywise_fees_collection_2024_25 (
    "SNo" TEXT, 
    "RecieptNo" TEXT, 
    "Class" TEXT, 
    "AdmissionNo" TEXT, 
    "StudentName" TEXT, 
    "Date" TIMESTAMP WITHOUT TIME ZONE, 
    "ReceivedAmount" FLOAT, 
    "Remarks" TEXT
);



CREATE TABLE attendance_report_2024_25 (
    Date DATE NOT NULL,
    AdmissionNo VARCHAR(20) NOT NULL,
    ClassNo VARCHAR(10) NOT NULL,
    classId INT NOT NULL,
    branchId INT NOT NULL,
    AttendanceStatusId INT NOT NULL
);

CREATE TABLE IF NOT EXISTS class_table_2024_25 (
    ClassNo INT PRIMARY KEY,
    Class VARCHAR(50),
    classId INT,
    className VARCHAR(50),
    branchId INT,
    branchName VARCHAR(50)
);


SELECT pid, age(clock_timestamp(), query_start), usename, query
FROM pg_stat_activity
WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;

SELECT pid, age(clock_timestamp(), query_start), usename, query
FROM pg_stat_activity
WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;



CREATE TABLE IF NOT EXISTS fees_collection_2024_25 (
    SNo SERIAL PRIMARY KEY,
    AdmissionNo VARCHAR(20) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Total_Fees DECIMAL(10,2) NOT NULL DEFAULT 0,
    Total_Fee_Paid DECIMAL(10,2) NOT NULL DEFAULT 0,
    Discount_Concession DECIMAL(10,2) NOT NULL DEFAULT 0,
    Total_Due DECIMAL(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fee_concession_2024_25 (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    student_number VARCHAR(20) NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    discount_given NUMERIC(10,2) NOT NULL
);



SELECT * FROM fees_table_2024_25;

SELECT * FROM students_2024_25;

SELECT * FROM daywise_fees_collection_2024_25;

SELECT COUNT(*) FROM daywise_fees_collection_2024_25;

SELECT * FROM attendance_report_2024_25;

SELECT * FROM fees_report_2024_25;

SELECT * FROM fees_collection_2024_25;

SELECT * FROM fee_concession_2024_25;

SELECT column_name FROM information_schema.columns 
WHERE table_name = 'fees_collection_2024_25';










