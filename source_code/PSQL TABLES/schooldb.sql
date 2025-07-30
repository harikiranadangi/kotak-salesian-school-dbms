CREATE DATABASE schooldb;

USE schooldb;

CREATE TABLE students_2024_25 (
    SNo INT ,
    AdmissionNo VARCHAR(50) UNIQUE NOT NULL,
    STUDENT_NAME VARCHAR(255) NOT NULL,
    Class VARCHAR(50) NOT NULL,
    Gender ENUM('Male', 'Female') NOT NULL,
    MotherName VARCHAR(255),
    FatherName VARCHAR(255),
    PenNo VARCHAR(50),
    DOB DATE NOT NULL,
    Mobile VARCHAR(30) NOT NULL,
    Religion VARCHAR(50),
    Caste VARCHAR(50),
    SubCaste VARCHAR(50),
    IIndLang VARCHAR(50),
    Remarks TEXT,
    ClassNo INT NOT NULL,
    JoinedYear YEAR 
);

DROP TABLE students_2024_25;

SELECT * FROM students_2024_25 ORDER BY SNo;


CREATE TABLE fees_table_2024_25 (
	SNo INT,
    ADM_NO VARCHAR(10) PRIMARY KEY,
    STUDENT_NAME VARCHAR(100) NOT NULL,
    FB_NO VARCHAR(10),
    CLASS VARCHAR(10),
    TotalFees INT NOT NULL,
    Term1 INT DEFAULT 0,
    Term2 INT DEFAULT 0,
    Term3 INT DEFAULT 0,
    Term4 INT DEFAULT 0,
    TotalFeePaid INT DEFAULT 0,
    Discount_Concession INT DEFAULT 0,
    TotalFeeDue INT DEFAULT 0,
    Fine INT DEFAULT 0,
    PaymentStatusId INT,
    ClassNo INT
);

DROP TABLE fees_table_2024_25;

SELECT * FROM fees_table_2024_25;

CREATE TABLE daywise_fees_collection_2024_25 (
    SNo INT ,
    RecieptNo VARCHAR(50) UNIQUE NOT NULL,
    Class VARCHAR(50) NOT NULL,
    AdmissionNo VARCHAR(50) NOT NULL,
    StudentName VARCHAR(255) NOT NULL,
    Date DATE NOT NULL,
    ReceivedAmount DECIMAL(10,2) NOT NULL,
    Remarks TEXT
);


SELECT * FROM daywise_fees_collection_2024_25;

CREATE TABLE attendance_report_2024_25 (
    SNo INT PRIMARY KEY AUTO_INCREMENT,
    Date DATE NOT NULL,
    AdmissionNo VARCHAR(50) NOT NULL,
    ClassNo INT NOT NULL,
    classId INT NOT NULL,
    branchId INT NOT NULL,
    AttendanceStatusId INT NOT NULL
);

ALTER TABLE attendance_report DROP INDEX `AdmissionNo`;
ALTER TABLE attendance_report ADD UNIQUE (`Date`, `AdmissionNo`);

SELECT * FROM attendance_report_2024_25 ORDER BY SNo DESC;

CREATE TABLE fees_collection_2024_25 (
    SNo INT ,
    AdmissionNo VARCHAR(50) NOT NULL,
    Name VARCHAR(255) NOT NULL,
    Total_Fees DECIMAL(10,2) NOT NULL,
    Total_Fee_Paid DECIMAL(10,2) NOT NULL,
    Discount_Concession DECIMAL(10,2) DEFAULT 0.00,
    Total_Due DECIMAL(10,2) NOT NULL
);

SELECT * FROM fees_collection_2024_25 ORDER BY SNo DESC;

CREATE TABLE fee_concession_2024_25 (
    id INT ,
    date DATE NOT NULL,
    student_number VARCHAR(50) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    discount_given DECIMAL(10,2) NOT NULL
);

DROP TABLE fee_concession_2024_25;

SELECT * FROM fee_concession_2024_25;


CREATE TABLE students (
	SNo INT,
    AdmissionNo VARCHAR(10) PRIMARY KEY,
    STUDENT_NAME VARCHAR(255),
    Class VARCHAR(50),
    Gender VARCHAR(10),
    MotherName VARCHAR(255),
    FatherName VARCHAR(255),
    PenNo VARCHAR(50),
    DOB DATE,
    Mobile VARCHAR(50),
    Religion VARCHAR(20),
    Caste VARCHAR(10),
    SubCaste VARCHAR(20),
    `IIndLang` VARCHAR(20),
    Remarks TEXT,
    ClassNo INT,
    JoinedYear TEXT
);

CREATE TABLE fees_collection (
    SNo INT ,
    AdmissionNo VARCHAR(20) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Total_Fees INT NOT NULL,
    Total_Fee_Paid INT NOT NULL,
    Discount_Concession INT NOT NULL,
    Total_Due INT NOT NULL
);


-- DESCRIBING TABLES

DESCRIBE fees_table;

DESCRIBE attendance_report;

DESCRIBE students;

DESCRIBE class_table_2024_25;

-- DROPPING TABLES

DROP TABLE fees_table;

DROP TABLE attendance_report;

DROP TABLE students;

DROP TABLE class_table;

-- FEES TABLE

SELECT * FROM students;

SELECT * FROM class_table_2024_25;

SELECT COUNT(*) FROM students;

SELECT * FROM fees_table ORDER BY SNo;

SELECT ClassNo,Class,COUNT(*) AS Strength FROM fees_table GROUP BY ClassNo,CLASS ORDER BY ClassNo DESC ;

SELECT * FROM fees_table WHERE PaymentStatus="Not Paid";

-- DAY WISE REPORTS

SELECT * FROM daywise_fees_collection WHERE AdmissionNo="14940";

SELECT count(*) FROM daywise_fees_collection;

SELECT * FROM attendance_report WHERE AttendanceStatus = "Present" ;

SELECT * FROM attendance_report WHERE Date = curdate() - 1 AND AttendanceStatus = "Absent" ORDER BY ClassNo;

SELECT * FROM attendance_report ;

SELECT Date, count(*) AS Students FROM attendance_report GROUP BY Date ORDER BY Students ASC;

SELECT COUNT(DISTINCT Date) AS UniqueDates FROM attendance_report;


SELECT COUNT(*) FROM attendance_report;

-- Student Info



SELECT * FROM students ORDER BY SNo, ClassNo ASC;

SELECT COUNT(*) FROM students;

SHOW CREATE TABLE attendance_report;

