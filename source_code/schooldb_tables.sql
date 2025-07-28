BEGIN;

rollback;

-- Drop unified tables if they exist
DROP TABLE IF EXISTS public.attendance_report CASCADE;
DROP TABLE IF EXISTS public.fees_table CASCADE;
DROP TABLE IF EXISTS public.fees_collection CASCADE;
DROP TABLE IF EXISTS public.fee_concession CASCADE;
DROP TABLE IF EXISTS public.fees_report CASCADE;
DROP TABLE IF EXISTS public.daywise_fees_collection CASCADE;
DROP TABLE IF EXISTS public.students CASCADE;
DROP TABLE IF EXISTS public.class_table CASCADE;

-- Class Table
CREATE TABLE public.class_table (
    classno SERIAL PRIMARY KEY,
    class VARCHAR(50),
    classid INTEGER,
    classname VARCHAR(50),
    branchid INTEGER,
    branchname VARCHAR(50),
    academic_year VARCHAR(10) NOT NULL
);

CREATE TABLE public.students (
    sno SERIAL PRIMARY KEY,
    adm_no VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    class VARCHAR(20),
    gender VARCHAR(10),
    mother_name VARCHAR(100),
    father_name VARCHAR(100),
    pen_number VARCHAR(50),
    dob DATE,
    phone_no VARCHAR(25),
    religion VARCHAR(50),
    caste VARCHAR(50),
    sub_caste VARCHAR(50),
    second_lang VARCHAR(50),
    remarks TEXT,
    class_nos INTEGER,
    joined_year INTEGER,
    grades VARCHAR(10),
    academic_year VARCHAR(10) NOT NULL,
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE (adm_no, academic_year)  -- ✅ No comma here
);

-- Attendance Report
CREATE TABLE public.attendance_report (
    id SERIAL,
    date DATE NOT NULL,
    admissionno VARCHAR(20) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    classno INTEGER NOT NULL,
    classid INTEGER NOT NULL,
    branchid INTEGER NOT NULL,
    attendancestatusid INTEGER NOT NULL,
    PRIMARY KEY (date, admissionno, academic_year),
    FOREIGN KEY (admissionno, academic_year) REFERENCES public.students(admissionno, academic_year) ON DELETE CASCADE,
    FOREIGN KEY (classno) REFERENCES public.class_table(classno) ON DELETE SET NULL
);

-- Fees Table
CREATE TABLE public.fees_table (
    sno SERIAL,
    student_name VARCHAR(100),
    adm_no VARCHAR(20),
    fb_no VARCHAR(20),
    class VARCHAR(20),
    term1 NUMERIC(10, 2) DEFAULT 0,
    term2 NUMERIC(10, 2) DEFAULT 0,
    term3 NUMERIC(10, 2) DEFAULT 0,
    term4 NUMERIC(10, 2) DEFAULT 0,
    totalfeepaid NUMERIC(10, 2) DEFAULT 0,
    discount_concession NUMERIC(10, 2) DEFAULT 0,
    totalfeedue NUMERIC(10, 2) DEFAULT 0,
    fine NUMERIC(10, 2) DEFAULT 0,
    classno INTEGER,
    totalfees NUMERIC(10, 2) GENERATED ALWAYS AS (totalfeepaid + discount_concession + totalfeedue) STORED,
    paymentstatusid INTEGER,
    academic_year VARCHAR(10) NOT NULL,
    PRIMARY KEY (adm_no, academic_year),
    FOREIGN KEY (adm_no, academic_year) REFERENCES public.students(admissionno, academic_year) ON DELETE CASCADE,
    FOREIGN KEY (classno) REFERENCES public.class_table(classno) ON DELETE SET NULL
);

-- Fees Collection
CREATE TABLE public.fees_collection (
    admissionno VARCHAR(20),
    academic_year VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    total_fees NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total_fee_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
    discount_concession NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total_due NUMERIC(10, 2) NOT NULL DEFAULT 0,
    PRIMARY KEY (admissionno, academic_year),
    FOREIGN KEY (admissionno, academic_year) REFERENCES public.students(admissionno, academic_year) ON DELETE CASCADE
);

-- Fee Concession
CREATE TABLE public.fee_concession (
    id SERIAL,
    student_number VARCHAR(20),
    academic_year VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    discount_given NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (student_number, date, academic_year),
    FOREIGN KEY (student_number, academic_year) REFERENCES public.students(admissionno, academic_year) ON DELETE CASCADE
);

-- Fees Report
CREATE TABLE public.fees_report (
    admissionno VARCHAR(20),
    academic_year VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    total_fees NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total_fee_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
    discount_concession NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total_due NUMERIC(10, 2) NOT NULL DEFAULT 0,
    PRIMARY KEY (admissionno, academic_year),
    FOREIGN KEY (admissionno, academic_year) REFERENCES public.students(admissionno, academic_year) ON DELETE CASCADE
);

-- Daywise Fees Collection
CREATE TABLE public.daywise_fees_collection (
    "AdmissionNo" TEXT,
    academic_year VARCHAR(10) NOT NULL,
    "SNo" TEXT,
    "RecieptNo" TEXT,
    "Class" TEXT,
    "StudentName" TEXT,
    "Date" TIMESTAMP,
    "ReceivedAmount" DOUBLE PRECISION,
    "Remarks" TEXT,
    PRIMARY KEY ("SNo", academic_year)
);

COMMIT;
