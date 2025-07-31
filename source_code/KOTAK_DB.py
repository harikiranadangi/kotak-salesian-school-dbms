#!/usr/bin/env python
# coding: utf-8

# <h1 align="center"><b>KOTAK SALESIAN SCHOOL</b></h1>
# 

# <h2 align="center"><b>STUDENTS DATABASE MANAGEMENT</b></h2>

# ## **Import Required Libraries**

# In[1]:


import os
import datetime
import subprocess
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine, text
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy.exc import SQLAlchemyError
import urllib.parse


# ## **Backup Files Before running New**

# In[2]:


# * PostgreSQL Credentials
DB_USER = "postgres"
DB_PASSWORD = "Hari@123"
DB_NAME = "kotakschooldb"
DB_HOST = "localhost"
DB_PORT = "5432"
BACKUP_DIR = "D:/postgres_backups"  # * Backup directory

# * Full path to pg_dump (if needed)
PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"

# * Ensure the backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# * Generate a timestamp for the backup file
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = os.path.join(BACKUP_DIR, f"backup_{DB_NAME}_{timestamp}.sql")

# * Run pg_dump
try:
    result = subprocess.run(
        [
            PG_DUMP_PATH,  # Use full path if not in PATH
            "-U", DB_USER,
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-F", "c",
            "-b",
            "-v",
            "-f", backup_file,
            DB_NAME
        ],
        env={**os.environ, "PGPASSWORD": DB_PASSWORD},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # * Check for errors
    if result.returncode == 0:
        print(f"✅ Backup successful: {backup_file}")
    else:
        print(f"❌ Backup failed!\nError: {result.stderr}")

except FileNotFoundError:
    print(f"⚠️ pg_dump not found at {PG_DUMP_PATH}. Check PostgreSQL installation or system PATH.")

except Exception as e:
    print(f"⚠️ An unexpected error occurred: {e}")


# ## **Import Libraries & Define Credentials**

# In[3]:


# === CONFIG ===
GOOGLE_JSON_PATHS = {
    "2024-25": r"D:\GITHUB\kotak-school-dbms\google_api_keys\woven-solution-446513-f2-2024-25.json",
    "2025-26": r"D:\GITHUB\kotak-school-dbms\google_api_keys\woven-solution-446513-f2-2025-26.json",
}

GOOGLE_SHEET_TITLES = {
    "2024-25": "STUDENTS DETAILS 2024-25",
    "2025-26": "STUDENTS DETAILS 2025-26",
}

UNIQUE_KEY = "Adm No."

POSTGRES_CREDENTIALS = {
    "username": "postgres",
    "password": "Hari@123",
    "host": "localhost",
    "port": "5432",
    "database": "kotakschooldb",
}

TABLE_NAME1 = "students"
TABLE_NAME2 = "student_list"


# ## **Extract Data from Google Sheet**

# In[4]:


# === FETCH GOOGLE SHEET ===
def fetch_data(sheet_title, worksheet_name="Overall", json_path=None):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_title)
    sheet = spreadsheet.worksheet(worksheet_name)
    data = sheet.get_all_records(head=3)
    return pd.DataFrame(data)

# === CLEAN COLUMN NAMES ===
def clean_column_names(df):
    df.columns = df.columns.str.strip()
    return df


# In[5]:


# === MERGE AND TAG STATUS ===
def merge_and_tag():
    df_2024 = clean_column_names(fetch_data(GOOGLE_SHEET_TITLES["2024-25"], "Overall", GOOGLE_JSON_PATHS["2024-25"]))
    df_2025 = clean_column_names(fetch_data(GOOGLE_SHEET_TITLES["2025-26"], "Overall", GOOGLE_JSON_PATHS["2025-26"]))

    df_2024["academic_year"] = "2024-25"
    df_2025["academic_year"] = "2025-26"

    codes_2024 = set(df_2024[UNIQUE_KEY])
    codes_2025 = set(df_2025[UNIQUE_KEY])

    continuing = codes_2024.intersection(codes_2025)
    left = codes_2024 - codes_2025
    new = codes_2025 - codes_2024

    df_2024["status"] = df_2024[UNIQUE_KEY].apply(lambda x: "left" if x in left else "continuing")
    df_2025["status"] = df_2025[UNIQUE_KEY].apply(lambda x: "new" if x in new else "continuing")

    return pd.concat([df_2024, df_2025], ignore_index=True)


# In[6]:


def clean_data(df):
    df = df.copy()

    # ✨ Rename columns to match your database structure
    df.columns = [
        "sno", "adm_no", "name", "class", "gender", "mother_name", "father_name",
        "pen_number", "dob", "phone_no", "religion", "caste", "sub_caste",
        "second_lang", "remarks", "class_nos", "joined_year", "grades",
        "academic_year", "status"
    ]

    # Lowercase and strip spaces for consistency
    df.columns = df.columns.str.strip().str.lower()

    # 🗓️ Convert DOB to PostgreSQL-friendly format
    df["dob"] = pd.to_datetime(df["dob"], format="%d-%m-%Y", errors='coerce').dt.strftime("%Y-%m-%d")

    # 🔢 Convert joined_year to integer
    df["joined_year"] = pd.to_numeric(df["joined_year"], errors="coerce").astype("Int64")

    # 🧹 Remove optional junk column
    if "apaar_status" in df.columns:
        df.drop(columns=["apaar_status"], inplace=True)

    # Capitalize gender and reset S.No
    df["gender"] = df["gender"].str.upper()
    df["sno"] = range(1, len(df) + 1)

    # 🟢 Clean text fields
    df["adm_no"] = df["adm_no"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    df["academic_year"] = df["academic_year"].astype(str).str.strip()

    # Sort for visual clarity
    df = df.sort_values(by=["academic_year", "class_nos", "gender", "name"])

    # Prefer non-null mother/father names when dropping duplicates
    df_sorted = df.sort_values(
        by=["adm_no", "mother_name", "father_name"],
        ascending=[True, True, True],
        na_position='last'  # Non-null values come first
    )

    student_list_df = df_sorted.drop_duplicates(subset="adm_no", keep="first")[
        [
            "adm_no", "name", "gender", "mother_name", "father_name",
            "pen_number", "dob", "phone_no", "religion", "caste",
            "sub_caste", "second_lang", "remarks"
        ]
    ]


    students_df = df[
        [
            "adm_no", "class", "class_nos", "joined_year",
            "grades", "academic_year", "status"
        ]
    ]

    # 🧾 Save CSV for auditing
    student_list_df.to_csv(r"D:\GITHUB\kotak-school-dbms\output_data\student_list.csv", index=False)
    df.to_csv(r"D:\GITHUB\kotak-school-dbms\output_data\students_data.csv", index=False)

    print("✅ Cleaned and split data saved.")

    return student_list_df, students_df


# In[7]:


def update_database(df, table_name):
    import numpy as np
    password = urllib.parse.quote_plus(POSTGRES_CREDENTIALS["password"])
    engine = create_engine(
        f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
        f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}",
        echo=False
    )

    # Table creation logic
    table_create_sql = {
        "students": """
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                adm_no VARCHAR,
                class VARCHAR,
                class_nos VARCHAR,
                joined_year INT,
                grades VARCHAR,
                academic_year VARCHAR,
                status VARCHAR
            );
        """,
        "student_list": """
            CREATE TABLE IF NOT EXISTS student_list (
                adm_no VARCHAR PRIMARY KEY,
                name VARCHAR,
                gender VARCHAR,
                mother_name VARCHAR,
                father_name VARCHAR,
                pen_number VARCHAR,
                dob DATE,
                phone_no VARCHAR,
                religion VARCHAR,
                caste VARCHAR,
                sub_caste VARCHAR,
                second_lang VARCHAR,
                remarks TEXT
            );
        """
    }

    try:
        with engine.begin() as conn:
            # ✅ Create table if it does not exist
            if table_name in table_create_sql:
                conn.execute(text(table_create_sql[table_name]))
                print(f"📦 Table '{table_name}' created if it didn't exist.")

            # 🗑️ Truncate before insert
            conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
            print(f"🧹 Old records deleted from '{table_name}'.")

        df = df.replace({pd.NA: None, np.nan: None})
        print(f"⏳ Inserting data into '{table_name}'...")

        df.to_sql(name=table_name, con=engine, if_exists='append', index=False, method='multi', chunksize=500)

        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
            count = result.scalar()
            print(f"✅ Insert complete. 📊 Table '{table_name}' now contains {count} records.\n")

    except Exception as e:
        print(f"❌ Error updating table '{table_name}': {e}")


# ## **Clean Extracted Data**

# In[8]:


if __name__ == "__main__":
    print("🚀 Starting full student import pipeline...\n")

    merged_df = merge_and_tag()
    student_list_df, students_df = clean_data(merged_df)

    # Update master (student_list) and academic (students) tables
    update_database(students_df, "students")
    update_database(student_list_df, "student_list")

    print("🎉 All done! Both 'student_list' and 'students' tables updated successfully.")


# <h2 align="center"><b>FEE REPORTS</b></h2>

# ## **Google Console Service Account: myschooldb@woven-solution-446513-f2.iam.gserviceaccount.com**

# ## **Import Necessary Libraries & Define Global Variables**

# In[9]:


# === CONFIG ===
GOOGLE_JSON_PATHS = {
    "2024-25": r"D:\GITHUB\kotak-school-dbms\google_api_keys\woven-solution-446513-f2-2024-25-fees.json",
    "2025-26": r"D:\GITHUB\kotak-school-dbms\google_api_keys\woven-solution-446513-f2-2025-26-fees.json"
}

GOOGLE_SHEET_TITLES = {
    "2024-25": "Fee Reports 2024-25",
    "2025-26": "Fee Reports 2025-26",
}

POSTGRES_CREDENTIALS = {
    "username": "postgres",
    "password": "Hari@123",
    "host": "localhost",
    "port": "5432",
    "database": "kotakschooldb",
}

TABLE_NAME = "fees_table"


# ## **Function for Fetching Data**

# In[10]:


# === FETCH GOOGLE SHEET ===
def fetch_data(sheet_title, worksheet_name="Overall Sheet", json_path=None):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_title)
    sheet = spreadsheet.worksheet(worksheet_name)
    data = sheet.get_all_records(head=3)
    return pd.DataFrame(data)

# === CLEAN COLUMN NAMES ===
def clean_column_names(df):
    df.columns = df.columns.str.strip()
    return df


# In[11]:


# === MERGE AND TAG STATUS ===
def merge_and_tag():
    df_2024 = clean_column_names(fetch_data(GOOGLE_SHEET_TITLES["2024-25"], "Overall Sheet", GOOGLE_JSON_PATHS["2024-25"]))
    df_2025 = clean_column_names(fetch_data(GOOGLE_SHEET_TITLES["2025-26"], "Overall Sheet", GOOGLE_JSON_PATHS["2025-26"]))

    df_2024["academic_year"] = "2024-25"
    df_2025["academic_year"] = "2025-26"

    return pd.concat([df_2024, df_2025], ignore_index=True)


# ## **Function for Cleaning Data**

# In[12]:


def clean_data(df):
    df = df[:-1][:-6]

    df.columns = ['SNo', 'STUDENT_NAME', 'ADM_NO', 'FB_NO', 'CLASS',
                  'Term1', 'Term2', 'Term3', 'Term4', 'Total_Fee_Paid',
                  'Discount_Concession', 'Total_Fee_Due', 'PermissionUpto',
                  'Fine', 'Payment_Status', 'ClassNo',"AcNo",'Concession_type', "staff_name", "academic_year"]

    df.columns = df.columns.str.strip().str.lower()

    # 🚫 Remove blank admission numbers
    df = df[df["adm_no"].astype(str).str.strip() != ""]
    df = df.dropna(subset=["adm_no"])
    # 🚫 Remove blank admission numbers
    df = df[df["student_name"].astype(str).str.strip() != ""]
    df = df.dropna(subset=["student_name"])

    columns_to_convert = ["term1", "term2", "term3", "term4", "total_fee_paid",
                          "discount_concession", "total_fee_due", "fine"]

    df[columns_to_convert] = df[columns_to_convert].apply(pd.to_numeric, errors='coerce').fillna(0)

    df = df.drop(columns=["acno", 'concession_type'])

    df["sno"] = range(1, len(df) + 1)

    df = df.sort_values(by=["sno"])

    df["total_fees"] = df["total_fee_paid"] + df["discount_concession"] + df["total_fee_due"]

    df = df.sort_values(by=["academic_year", "classno", "student_name"], ascending=[True, True, True])

    df.to_csv(r"D:\GITHUB\kotak-school-dbms\output_data\fees_report.csv", index=False)

    PaymentStatus = df[["payment_status"]].drop_duplicates().reset_index(drop=True)
    PaymentStatus["payment_status_id"] = range(1, len(PaymentStatus) + 1)
    PaymentStatus = PaymentStatus[["payment_status_id", "payment_status"]]
    PaymentStatus.to_csv(r"D:\GITHUB\kotak-school-dbms\output_data\payment_status_table.csv", index=False)
    print("✅ Payment Status Table created successfully.\n")

    df = pd.merge(df, PaymentStatus, on="payment_status", how="left")

    df.drop(columns=["permissionupto","payment_status"], inplace=True)

    df.columns = df.columns.str.lower().str.strip()

    return df


# ## **Function for Updating the Database**

# In[13]:


# PostgreSQL Connection Credentials
POSTGRES_CREDENTIALS = {
    "username": "postgres",
    "password": "Hari@123",
    "host": "localhost",
    "port": "5432",
    "database": "kotakschooldb",
}

# Encode password for URL safety
password = urllib.parse.quote(POSTGRES_CREDENTIALS["password"])

# Create Engine
engine = create_engine(f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
                       f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}")

def table_exists(table_name):
    """Check if table exists in PostgreSQL database"""
    check_query = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = '{table_name}'
    );
    """
    with engine.connect() as conn:
        result = conn.execute(text(check_query)).scalar()
    return result

def create_table():
    """Create table only if it does not exist"""
    table_name = "fees_table"

    if table_exists(table_name):
        print(f"✅ Table '{table_name}' already exists.")
        return

    create_table_query = """
    CREATE TABLE fees_table (
    sno SERIAL PRIMARY KEY,
    student_name TEXT NOT NULL,
    adm_no TEXT,
    fb_no TEXT,
    class TEXT,
    term1 NUMERIC DEFAULT 0,
    term2 NUMERIC DEFAULT 0,
    term3 NUMERIC DEFAULT 0,
    term4 NUMERIC DEFAULT 0,
    total_fee_paid NUMERIC DEFAULT 0,
    discount_concession NUMERIC DEFAULT 0,
    total_fee_due NUMERIC DEFAULT 0,
    fine NUMERIC DEFAULT 0,
    classno TEXT,
    staff_name TEXT,
    academic_year TEXT NOT NULL,
    total_fees INTEGER DEFAULT 0,
    payment_status_id INTEGER
);
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_query))
            print(f"✅ Table '{table_name}' created successfully.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")


# In[14]:


import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def update_database(df):
    password = urllib.parse.quote(POSTGRES_CREDENTIALS["password"])
    engine = create_engine(
        f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
        f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}"
    )

    try:
        with engine.begin() as conn:
            # ✅ Truncate existing table and reset serial ID
            conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY CASCADE;"))
            print(f"✅ All records from the '{TABLE_NAME}' table have been deleted.\n")

            # ✅ Add UNIQUE constraint on 'admissionno' (if it doesn't exist)
            conn.execute(text(f"""
                DO $$ 
                BEGIN 
                    -- Drop old constraint if exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = '{TABLE_NAME}' AND constraint_name = 'unique_admissionno'
                    ) THEN
                        ALTER TABLE {TABLE_NAME} DROP CONSTRAINT unique_admissionno;
                    END IF;

                    -- Add new composite unique constraint if not exists
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = '{TABLE_NAME}' AND constraint_name = 'unique_adm_year'
                    ) THEN
                        ALTER TABLE {TABLE_NAME} ADD CONSTRAINT unique_adm_year UNIQUE ("adm_no", "academic_year");
                    END IF;
                END $$;
            """))

            print(f"✅ Unique constraint on 'admissionno' ensured in the '{TABLE_NAME}' table.\n")

        print("✅ Table cleared. Proceeding with data insertion...\n")

        # ✅ Normalize column names
        df.columns = df.columns.str.lower()

        # ✅ Drop generated or unneeded columns
        if "totalfees" in df.columns:
            df = df.drop(columns=["totalfees"])
            print("✅ 'totalfees' column removed before insertion (generated column).\n")

        # ✅ Insert data in chunks
        df.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )

        print(f"✅ {len(df)} records successfully inserted into '{TABLE_NAME}'.\n")

    except SQLAlchemyError as e:
        print(f"❌ An error occurred during database update: {e}")


# ## **Main Execution Block**

# In[15]:


if __name__ == "__main__":
    # * Merge and tag both years
    combined_df = merge_and_tag()
    print("✅ Raw data merged from both years.\n")

    # * Clean and process the merged data
    cleaned_df = clean_data(combined_df)
    print("✅ Data cleaned and transformed successfully.\n")
    print("✅ Final columns are:\n", cleaned_df.columns.to_list())

    # * Create table if it does not exist
    create_table()
    print("\n✅ Table check/creation complete.\n")

    # * Drop duplicates by adm_no + year before insert
    cleaned_df = cleaned_df.drop_duplicates(subset=["adm_no", "academic_year"])
    print(f"✅ Deduplicated. Final records to upload: {len(cleaned_df)}\n")

    # * Upload data using safe insertion
    update_database(cleaned_df)


# <h2 align="center"><b>DAY WISE REPORTS</b></h2>

# ## **Import Required Libraries**

# In[16]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine, text


# ## **Define Login Credentials and MySQL Credentials**

# In[17]:


# * 🔹 Login Credentials
login_url = "https://app.myskoolcom.tech/kotak_vizag/login"
urls_with_years = [
    ("https://app.myskoolcom.tech/kotak_vizag/office_fee/fee_reports_day_wise_receipt_wise_print?academic_years_id=1", "2024-25"),
    ("https://app.myskoolcom.tech/kotak_vizag/office_fee/fee_reports_day_wise_receipt_wise_print?academic_years_id=7", "2025-26"),
]

credentials = {
    "uname": "harikiran",
    "psw": "812551"
}

POSTGRES_CREDENTIALS = {
    "username": "postgres",
    "password": "Hari@123",
    "host": "localhost",
    "port": "5432",
    "database": "kotakschooldb",
}

TABLE_NAME = "daywise_fees_collection"


# ## **Define Functions for Each Step**

# In[18]:


def login_to_website():
    session = requests.Session()
    login_response = session.post(login_url, data=credentials)

    if "Invalid" in login_response.text:
        print("❌ Login failed! Check credentials.\n")
        return None
    else:
        print("✅ Login successful!\n")
        return session


# ## **Function to Fetch Fee Report Page**

# In[19]:


def fetch_fee_report_page(session, data_url):
    response = session.get(data_url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    return table


# ## **Function to Extract Data from Table**

# In[20]:


def extract_data_from_table(table):
    rows = []
    for tr in table.find_all("tr"):
        cols = [td.text.strip() for td in tr.find_all("td")]
        if cols:
            rows.append(cols)

    if not rows:
        raise ValueError("No rows found in table")

    num_cols = len(rows[0])

    if num_cols == 12:
        header_row = [
            "SNo", "RecieptNo", "Class", "AdmissionNo", "StudentName", 
            "Date", "-", "Abacus / Vediic Maths", "TERM FEE", "TERM FEE2", 
            "ReceivedAmount", "Remarks"
        ]
    elif num_cols == 11:
        header_row = [
            "SNo", "RecieptNo", "Class", "AdmissionNo", "StudentName", 
            "Date", "-", "Abacus / Vediic Maths", "TERM FEE", 
            "ReceivedAmount", "Remarks"
        ]
    else:
        raise ValueError(f"⚠️ Unexpected number of columns: {num_cols}")

    df = pd.DataFrame(rows, columns=header_row)
    return df


# ## **Function to Clean Data**

# In[21]:


def clean_and_tag_data(df, academic_year):
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
    df['AdmissionNo'] = df['AdmissionNo'].astype(str)
    df["Class"] = df["Class"].str.replace("/", " - ")
    df["ReceivedAmount"] = pd.to_numeric(df["ReceivedAmount"], errors="coerce")
    df["academic_year"] = academic_year  # Add academic year tag

    # Apply "TERM" row slicing only for 2024-25
    if academic_year == "2024-25":
        term_index = df[df["SNo"].str.contains("TERM", na=False)].index
        if not term_index.empty:
            df = df.iloc[:term_index[0]]

    # Safely drop any of these columns only if they exist
    cols_to_drop = ["-", "Abacus / Vediic Maths", "TERM FEE", "TERM FEE2"]

    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors="ignore")

    df = df.dropna(subset=["Date" ])

    df

    return df


# ## **Function to Update Database**

# In[22]:


def update_database(df):
    password = urllib.parse.quote(POSTGRES_CREDENTIALS["password"])
    engine = create_engine(
        f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
        f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}"
    )

    # Define SQL table creation (only if not exists)
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        "SNo" TEXT,
        "RecieptNo" TEXT,
        "Class" TEXT,
        "AdmissionNo" TEXT,
        "StudentName" TEXT,
        "Date" DATE,
        "ReceivedAmount" NUMERIC,
        "Remarks" TEXT,
        "academic_year" TEXT
    );
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))  # ✅ Ensure table exists

            conn.execute(text("BEGIN;"))
            conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME};"))
            conn.execute(text("COMMIT;"))
            print(f"✅ Table '{TABLE_NAME}' ensured and truncated.\n")

            # ✅ Insert DataFrame
            df.to_sql(name=TABLE_NAME, con=engine, if_exists='append', index=False, method="multi", chunksize=1000)
            print(f"✅ {len(df)} records inserted into '{TABLE_NAME}' successfully.\n")
    except Exception as e:
        print(f"⚠️ Error inserting data: {e}")


# In[23]:


def main():
    session = login_to_website()
    if session is None:
        return

    all_dfs = []

    for url, year in urls_with_years:
        print(f"📄 Fetching data for academic year: {year}")
        table = fetch_fee_report_page(session, url)

        if table:
            df = extract_data_from_table(table)
            print(df.info())

            df = clean_and_tag_data(df, year)
            print(f"✅ Data extracted for year {year} with {len(df)} records.\n")


            print(df.info())
            print(df.head())
            df.to_csv(fr"D:\GITHUB\kotak-school-dbms\output_data\fee_collection_{year}.csv", index=False)
            all_dfs.append(df)
        else:
            print(f"❌ Table not found for year {year}!")

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        final_df.to_csv(r"D:\GITHUB\kotak-school-dbms\output_data\merged_fee_collection.csv", index=False)
        print("✅ Data saved to merged_fee_collection.csv\n")

        update_database(final_df)
        print("✅ Columns:\n", final_df.columns)
        print(f"✅ Total {len(final_df)} records entered into database.")
    else:
        print("❌ No data to process!")


# ## **Run the Main Function**

# In[24]:


# * Run the main function
main()


# <h2 align="center"><b>ATTENDANCE REPORT</b></h2>

# ## **Import Libraries**

# In[25]:


# import os
# import time
# import pandas as pd
# from datetime import datetime, timedelta
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager


# ## **Login to Website**

# In[26]:


# # ✅ Config
# login_url = "https://app.myskoolcom.tech/kotak_vizag/login"
# attendance_url = "https://app.myskoolcom.tech/kotak_vizag/admin/attedance_grid"

# credentials = {
#     "uname": "harikiran",
#     "psw": "812551"
# }

# download_folder = r"D:\GITHUB\kotak-school-dbms\source_data\Attendance Reports"
# merged_output_path = os.path.join(download_folder, "MergedAttendance_2025_26.csv")

# academic_ranges = {
#     "2025-26": ("2025-06-16", datetime.today().strftime("%Y-%m-%d"))
#     # "2025-26": ("2025-06-16", datetime.today().strftime("%Y-%m-%d"))
# }


# In[27]:


# # ✅ Setup Chrome Driver
# chrome_options = webdriver.ChromeOptions()
# prefs = {"download.default_directory": download_folder}
# chrome_options.add_experimental_option("prefs", prefs)
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
# wait = WebDriverWait(driver, 10)

# # ✅ Functions
# def login():
#     driver.get(login_url)
#     wait.until(EC.presence_of_element_located((By.NAME, "uname"))).send_keys(credentials["uname"])
#     driver.find_element(By.NAME, "psw").send_keys(credentials["psw"])
#     driver.find_element(By.NAME, "psw").send_keys(Keys.RETURN)
#     print("✅ Logged in successfully!")
#     time.sleep(5)

# def set_date_range(start, end):
#     driver.get(attendance_url)
#     time.sleep(2)
#     from_date_input = wait.until(EC.presence_of_element_located((By.ID, "from_attendance_date")))
#     driver.execute_script("arguments[0].removeAttribute('readonly')", from_date_input)
#     from_date_input.clear()
#     from_date_input.send_keys(start)

#     to_date_input = wait.until(EC.presence_of_element_located((By.ID, "to_attendance_date")))
#     driver.execute_script("arguments[0].removeAttribute('readonly')", to_date_input)
#     to_date_input.clear()
#     to_date_input.send_keys(end)

#     print(f"✅ Date range set: {start} to {end}")

# def download_csv(filename):
#     try:
#         if os.path.exists(filename):
#             os.remove(filename)
#         download_button = wait.until(EC.element_to_be_clickable((By.ID, "smaplecsv")))
#         download_button.click()
#         time.sleep(8)
#         downloaded = sorted(
#             [f for f in os.listdir(download_folder) if f.endswith(".csv")],
#             key=lambda x: os.path.getctime(os.path.join(download_folder, x)),
#             reverse=True
#         )[0]
#         os.rename(os.path.join(download_folder, downloaded), filename)
#         print(f"✅ Downloaded and renamed to: {filename}")
#     except Exception as e:
#         print(f"❌ Error downloading file: {e}")

# def date_batches(start, end, months=1):
#     start_date = datetime.strptime(start, "%Y-%m-%d")
#     end_date = datetime.strptime(end, "%Y-%m-%d")
#     while start_date < end_date:
#         batch_end = min(start_date + timedelta(days=30 * months), end_date)
#         yield (start_date.strftime("%Y-%m-%d"), batch_end.strftime("%Y-%m-%d"))
#         start_date = batch_end + timedelta(days=1)

# def merge_csvs(folder, output_file, year_filter="2025-26"):
#     all_csvs = [
#         os.path.join(folder, f)
#         for f in os.listdir(folder)
#         if f.endswith(".csv") and year_filter in f
#     ]

#     merged_df = pd.DataFrame()

#     for f in all_csvs:
#         try:
#             df = pd.read_csv(f, low_memory=False)
#             if "Students Number" in df.columns:
#                 # Merge logic: remove duplicates by date + student number
#                 df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#                 df = df.dropna(subset=["Date", "Students Number"])

#                 # Merge with deduplication
#                 if not merged_df.empty:
#                     merged_df = pd.concat([merged_df, df], ignore_index=True)
#                     merged_df.drop_duplicates(subset=["Date", "Students Number"], keep="last", inplace=True)
#                 else:
#                     merged_df = df
#                 print(f"🔄 Merged file (with Students Number): {os.path.basename(f)}")
#             else:
#                 # Append directly if "Students Number" not found
#                 merged_df = pd.concat([merged_df, df], ignore_index=True)
#                 print(f"➕ Appended file (no Students Number): {os.path.basename(f)}")
#         except Exception as e:
#             print(f"❌ Error reading file {f}: {e}")

#     merged_df.to_csv(output_file, index=False)
#     print(f"✅ Final merged file saved: {output_file}")

#     # ✅ MAIN Execution
# login()

# # ✅ MAIN Execution
# login()

# for year, (start, end) in academic_ranges.items():
#     print(f"\n📅 Downloading attendance for {year}")
#     for i, (s, e) in enumerate(date_batches(start, end)):
#         s_fmt = datetime.strptime(s, "%Y-%m-%d")
#         e_fmt = datetime.strptime(e, "%Y-%m-%d")
#         filename = f"Attendance_{year}_{s_fmt.strftime('%b')}_{e_fmt.strftime('%b')}.csv"
#         filepath = os.path.join(download_folder, filename)
#         set_date_range(s_fmt.strftime("%Y-%m-%d"), e_fmt.strftime("%Y-%m-%d"))
#         download_csv(filepath)

# # ❌ No merging now – only individual files will be downloaded and renamed
# # merge_csvs(download_folder, merged_output_path, year_filter="2025-26")

# driver.quit()
# print("✅ All attendance downloads complete – individual files saved!")


# ## **📌 Step 1: Import Libraries**

# In[28]:


# import pandas as pd
# from sqlalchemy import create_engine
# import logging
# import numpy as np
# import urllib
# import logging
# import traceback
# from datetime import datetime

# # * Configure logging
# logging.basicConfig(filename=r"D:\GITHUB\kotak-school-dbms\output_data\attendance_report.log", level=logging.ERROR, 
#                     format="%(asctime)s - %(levelname)s - %(message)s")


# ## **📌 Step 2: Define PostgreSQl Credentials & Table Name**

# In[29]:


# # * MySQL Credentials
# POSTGRES_CREDENTIALS = {
#     "username": "postgres",
#     "password": "Hari@123",
#     "host": "localhost",
#     "port": "5432",
#     "database": "kotakschooldb",
# }
# TABLE_NAME = "attendance_report"


# ## **📌 Step 3: Load and Clean Data**

# In[30]:


# def load_and_clean_data(file1, file2, file3, file4=None, file5=None):
#     # Load DataFrames
#     dfs = [pd.read_csv(f) for f in [file1, file2, file3, file4, file5] if f is not None]

#     # Clean column names
#     for i in range(len(dfs)):
#         dfs[i].columns = dfs[i].columns.str.strip().str.replace('"', '', regex=False)

#     # Ensure unique columns before merge to avoid suffix collision
#     base_df = dfs[0]

#     for df in dfs[1:]:
#         # Remove columns from df that would cause _x/_y clashes (except 'Students Number')
#         conflict_cols = [col for col in df.columns if col in base_df.columns and col != 'Students Number']
#         df = df.drop(columns=conflict_cols, errors='ignore')

#         # Merge safely
#         base_df = base_df.merge(df, on="Students Number", how="outer")

#     df = base_df

#     # Merge fields like Name, Class if duplicated from earlier columns
#     for field in ['Name', 'Class']:
#         col_x, col_y = f"{field}_x", f"{field}_y"
#         if col_x in df.columns and col_y in df.columns:
#             df[field] = df[col_x].combine_first(df[col_y])
#             df.drop([col_x, col_y], axis=1, inplace=True)
#         elif col_x in df.columns:
#             df[field] = df.pop(col_x)
#         elif col_y in df.columns:
#             df[field] = df.pop(col_y)

#     # Drop any remaining _x/_y suffix columns
#     df = df.drop(columns=[col for col in df.columns if col.endswith('_x') or col.endswith('_y')], errors='ignore')

#     # Rename key identifier
#     df = df.rename(columns={"Students Number": "AdmissionNo"})

#     # Drop unnecessary columns
#     drop_cols = ['Present Days', 'Absent Days', 'Toral Working Days']
#     df = df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore')

#     # Reorder columns
#     key_cols = ['AdmissionNo', 'Name', 'Class']
#     other_cols = [col for col in df.columns if col not in key_cols]
#     df = df[key_cols + other_cols]

#     return df


# # **📌 Step 4: Process Attendance Data**

# In[31]:


# from datetime import datetime
# import numpy as np
# import pandas as pd

# def process_attendance_data(df):
#     # * Step 1: Clean AdmissionNo (remove 786 and purely alphabetical ones)
#     df = df[~(df["AdmissionNo"].astype(str) == "786") & ~df["AdmissionNo"].astype(str).str.match(r"^[a-zA-Z]+$")].copy()

#     # * Step 2: Clean Class name (remove ICSE wrapper)
#     df["Class"] = df["Class"].astype(str).str.replace(r"ICSE \((.*?)\)", r"\1", regex=True)

#     # * Step 3: Load class info with academic year
#     student_df = pd.read_csv(r"D:\GITHUB\kotak-school-dbms\output_data\fees_report.csv")[["adm_no", "academic_year", "class"]]
#     print("✅ Students Before Merging\n", len(df["AdmissionNo"].unique()))
#     df = df[df["AdmissionNo"].isin(student_df["adm_no"])]
#     print("✅ Students After Merging\n", len(df["AdmissionNo"].unique()))

#     # * Step 4: Unpivot attendance columns to Date-wise rows
#     df_unpivot = pd.melt(df, id_vars=["AdmissionNo", "Name", "Class"], var_name="Date", value_name="AttendanceStatus")
#     df_unpivot["Date"] = pd.to_datetime(df_unpivot["Date"], format='%d.%m.%Y', errors='coerce')

#     # * Step 5: Remove invalid past records for new students
#     numeric_mask = df_unpivot["AdmissionNo"].str.isnumeric()
#     df_unpivot.loc[numeric_mask, "adm_no_int"] = df_unpivot.loc[numeric_mask, "AdmissionNo"].astype(int)
#     df_unpivot = df_unpivot[
#         ~((df_unpivot["Date"] < datetime(2024, 4, 1)) & (df_unpivot["adm_no_int"] > 17165))
#     ]
#     df_unpivot.drop(columns=["adm_no_int"], inplace=True)

#     df_unpivot["id"] = range(1, len(df_unpivot) + 1)

#     if df_unpivot["Date"].isna().sum() > 0:
#         print("⚠️ Warning: Some Date values were invalid and converted to NaT.")

#     df_unpivot = df_unpivot.sort_values("Date", ascending=False).reset_index(drop=True)

#     # * Step 6: Mark "Not Joined"
#     first_attendance_dates = df_unpivot[df_unpivot['AttendanceStatus'].notna()].groupby('AdmissionNo')['Date'].min()
#     df_unpivot['AttendanceStatus'] = df_unpivot.apply(
#         lambda row: "Not Joined" if row['Date'] < first_attendance_dates.get(row['AdmissionNo'], row['Date']) else row['AttendanceStatus'],
#         axis=1
#     )

#     # * Step 7: Prioritize and deduplicate attendance
#     priority_map = {'P': 2, 'A': 1, 'H': 3, 'Not Joined': 4, 'TC': 5}
#     df_unpivot['Priority'] = df_unpivot["AttendanceStatus"].map(priority_map)
#     df_unpivot = df_unpivot.sort_values(by=['AdmissionNo', 'Date', 'Priority']) \
#                            .drop_duplicates(subset=['AdmissionNo', 'Date'], keep='first') \
#                            .drop(columns=['Priority'])

#     # * Step 8: Clean Class + Standardize AttendanceStatus
#     df_unpivot['Class'] = df_unpivot['Class'].str.replace("Pre KG - ", "Pre KG")
#     df_unpivot["AttendanceStatus"] = df_unpivot["AttendanceStatus"].replace({
#         'P': "Present", 'A': "Absent", 'H': "Holiday"
#     })
#     df_unpivot.sort_values(by=['Date'], ascending=False, inplace=True)

#     # * Step 9: Assign academic year from Date
#     df_unpivot['academic_year'] = df_unpivot['Date'].apply(
#         lambda d: "2024-25" if pd.Timestamp("2024-07-17") <= d <= pd.Timestamp("2025-03-31")
#         else "2025-26" if pd.Timestamp("2025-06-16") <= d <= pd.Timestamp(datetime.today().date())
#         else ""
#     )

#     # * Step 10: Assign ClassNo by academic year
#     student_df["adm_no"] = student_df["adm_no"].astype(str)
#     lookup_2024 = student_df[student_df["academic_year"] == "2024-25"]
#     lookup_2025 = student_df[student_df["academic_year"] == "2025-26"]

#     lookup_map_2024 = {row["adm_no"]: row["class"] for _, row in lookup_2024.iterrows()}
#     lookup_map_2025 = {row["adm_no"]: row["class"] for _, row in lookup_2025.iterrows()}

#     class_mapping = {
#         "Pre KG": 1, "LKG - A": 2, "LKG - B": 3, "UKG - A": 4, "UKG - B": 5, "UKG - C": 6,
#         "I - A": 7, "I - B": 8, "I - C": 9, "I - D": 10,
#         "II - A": 11, "II - B": 12, "II - C": 13, "II - D": 14,
#         "III - A": 15, "III - B": 16, "III - C": 17, "III - D": 18,
#         "IV - A": 19, "IV - B": 20, "IV - C": 21, "IV - D": 22,
#         "V - A": 23, "V - B": 24, "V - C": 25, "V - D": 26,
#         "VI - A": 27, "VI - B": 28, "VI - C": 29, "VI - D": 30,
#         "VII - A": 31, "VII - B": 32, "VII - C": 33, "VII - D": 34,
#         "VIII - A": 35, "VIII - B": 36, "VIII - C": 37, "VIII - D": 38,
#         "IX - A": 39, "IX - B": 40, "IX - C": 41,
#         "X - A": 42, "X - B": 43, "X - C": 44
#     }

#     def get_class_no_2024(adm_no):
#         class_name = lookup_map_2024.get(str(adm_no), "")
#         return class_mapping.get(class_name, np.nan)

#     def get_class_no_2025(adm_no):
#         class_name = lookup_map_2025.get(str(adm_no), "")
#         return class_mapping.get(class_name, np.nan)

#     df_2024 = df_unpivot[df_unpivot["academic_year"] == "2024-25"].copy()
#     df_2025 = df_unpivot[df_unpivot["academic_year"] == "2025-26"].copy()

#     valid_adm_nos_2025 = set(lookup_map_2025.keys())
#     df_2025 = df_2025[df_2025["AdmissionNo"].astype(str).isin(valid_adm_nos_2025)].copy()

#     df_2024["ClassNo"] = df_2024["AdmissionNo"].apply(get_class_no_2024)
#     df_2025["ClassNo"] = df_2025["AdmissionNo"].apply(get_class_no_2025)

#     df_unpivot = pd.concat([df_2024, df_2025], ignore_index=True)
#     df_unpivot["ClassNo"] = df_unpivot["ClassNo"].fillna(0).astype(int)

#     # * Step 11: Grade level (classId)
#     grade_mapping = [
#         ("Pre KG", 1), ("LKG", 2), ("UKG", 3),
#         ("I", 4), ("II", 5), ("III", 6), ("IV", 7), ("V", 8),
#         ("VI", 9), ("VII", 10), ("VIII", 11), ("IX", 12), ("X", 13)
#     ]
#     conditions = [df_unpivot['Class'].str.contains(fr"\b{k}\b", na=False, regex=True) for k, _ in grade_mapping]
#     choices = [v for _, v in grade_mapping]
#     df_unpivot['classId'] = np.select(conditions, choices, default=0).astype(int)

#     # * Step 12: AttendanceStatusId
#     AttendanceStatus_mapping = [("Absent", 1), ("Present", 2), ("Not Joined", 3), ("Holiday", 4)]
#     conditions = [df_unpivot['AttendanceStatus'].str.contains(k, na=False) for k, _ in AttendanceStatus_mapping]
#     choices = [v for _, v in AttendanceStatus_mapping]
#     df_unpivot['AttendanceStatusId'] = np.select(conditions, choices, default=0).astype(int)

#     # * Step 13: BranchId
#     branch_mapping = [
#         ('Pre KG', 1), ('LKG', 1), ('UKG', 1),
#         ('I', 2), ('II', 2), ('III', 2), ('IV', 2), ('V', 2),
#         ('VI', 3), ('VII', 3), ('VIII', 3), ('IX', 3), ('X', 3)
#     ]
#     conditions = [df_unpivot['Class'].str.contains(fr"\b{k}\b", na=False, regex=True) for k, _ in branch_mapping]
#     choices = [v for _, v in branch_mapping]
#     df_unpivot['branchId'] = np.select(conditions, choices, default=0).astype(int)

#     # ✅ Final output
#     df_unpivot = df_unpivot[[
#         "id", "Date", "AdmissionNo", "ClassNo", "classId", "branchId", "AttendanceStatusId", "academic_year"
#     ]]
#     df_unpivot.columns = [c.lower() for c in df_unpivot.columns]

#     print(f"✅ Processed data with {len(df_unpivot)} rows.")
#     print(f"✅ Columns are:\n {df_unpivot.columns}")
#     return df_unpivot


# ## **📌 Step 5: Insert Data into PostgreSQL**

# In[32]:


# from sqlalchemy import text

# def ensure_table_exists():
#     create_table_sql = f"""
#     CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
#         id SERIAL PRIMARY KEY,
#         date DATE,
#         admissionno TEXT,
#         classno INTEGER,
#         classid INTEGER,
#         branchid INTEGER,
#         attendancestatusid INTEGER,
#         academic_year TEXT NOT NULL
#     );
#     """
#     try:
#         with engine.begin() as connection:  # ✅ ensures DDL is committed
#             connection.execute(text(create_table_sql))
#         print(f"✅ Table '{TABLE_NAME}' ensured.")
#     except Exception as e:
#         print(f"❌ Failed to create or check table '{TABLE_NAME}': {e}")


# In[33]:


# # Create database engine
# password = urllib.parse.quote(POSTGRES_CREDENTIALS["password"])
# engine = create_engine(
#     f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
#     f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}"
# )

# def update_database(df):
#     """Use PostgreSQL COPY for ultra-fast data insertion."""
#     csv_path = (r"D:\GITHUB\kotak-school-dbms\output_data\attendance_report.csv")

#     # ✅ Ensure column names are lowercase to match table definition
#     df.columns = [c.lower() for c in df.columns]

#     # ✅ Save DataFrame to CSV
#     df.to_csv(csv_path, index=False, header=False)

#     try:
#         conn = engine.raw_connection()
#         cursor = conn.cursor()

#         print(f"🔄 Truncating table: {TABLE_NAME}")
#         cursor.execute(f"TRUNCATE TABLE {TABLE_NAME};")
#         conn.commit()

#         with open(csv_path, "r") as f:
#             cursor.copy_from(f, TABLE_NAME, sep=",")  # ✅ lowercase and unquoted

#         conn.commit()
#         cursor.close()
#         conn.close()

#         print(f"✅ Data copied to '{TABLE_NAME}' using COPY command!")

#     except Exception as e:
#         print(f"❌ COPY failed: {e}")
#         logging.error(traceback.format_exc())


# ## **📌 Step 6: Run the Full Pipeline**

# In[34]:


# def main():
#     file1 = r"D:\GITHUB\kotak-school-dbms\source_data\Attendance Reports\AttendanceReportUptoSeptember_2024_25.csv"
#     file2 = r"D:\GITHUB\kotak-school-dbms\source_data\Attendance Reports\AttendanceOctoberToDecember_2024_25.csv"
#     file3 = r"D:\GITHUB\kotak-school-dbms\source_data\Attendance Reports\AttendanceUptoMarch_2024_25.csv"
#     file4 = r"D:\GITHUB\kotak-school-dbms\source_data\Attendance Reports\Attendance_2025-26_Jun_Jul.csv"
#     file5 = r"D:\GITHUB\kotak-school-dbms\source_data\Attendance Reports\Attendance_2025-26_Jul_Jul.csv"
#     output_file = r"D:\GITHUB\kotak-school-dbms\output_data\attendance_report.csv"

#     try:
#         print("Loading and cleaning data...\n")
#         df = load_and_clean_data(file1, file2, file3, file4, file5)
#         print(f"✅ Data loaded with {df.shape[0]} rows.\n")

#         print("Processing attendance data...\n")
#         df_unpivot = process_attendance_data(df)
#         df_unpivot.to_csv(output_file, index=False)
#         print(f"✅ Processed data with {df_unpivot.shape[0]} rows.\n")
#         print("✅ Columns are:\n", df_unpivot.columns)
#         print(max(df_unpivot["date"]))
#         print((df_unpivot.head()))

#         print("Updating database...\n")
#         ensure_table_exists()
#         update_database(df_unpivot)
#         print("✅ Data updated successfully!\n")

#         print("✅ Attendance report processing completed successfully!\n")
#         print(f"✅ No of Rows: {df_unpivot.shape[0]}\n")

#     except Exception as e:
#         print(f"❌ An unexpected error occurred. Error: {e}\n")
#         logging.error(f"❌ Unexpected error: {e}\n")


# # * Run the script
# main()


# <h2 align="center"><b>Class Table</b></h2>

# In[35]:


# import pandas as pd
# from sqlalchemy import create_engine, text

# POSTGRES_CREDENTIALS = {
#     "username": "postgres",
#     "password": "Hari@123",
#     "host": "localhost",
#     "port": "5432",
#     "database": "kotakschooldb",
# }
# TABLE_NAME = "class_table"


# In[36]:


# df = pd.read_csv(r"D:\GITHUB\kotak-school-dbms\output_data\class_section_grade_table.csv")
# # df["ClassNo"] = df["ClassNo"].astype(int)
# df.head()


# In[37]:


# df.columns


# In[38]:


# import time
# import traceback
# import logging
# import pandas as pd
# import urllib
# import io
# from sqlalchemy import create_engine, text
# from sqlalchemy.exc import OperationalError

# # Retry settings
# MAX_RETRIES = 3
# RETRY_DELAY = 5  # Seconds

# def bulk_insert_postgres(df, conn, table_name):
#     """Fast bulk insert using PostgreSQL COPY command."""
#     with conn.connection.cursor() as cur:
#         output = io.StringIO()
#         df.to_csv(output, sep="\t", index=False, header=False)
#         output.seek(0)
#         cur.copy_from(output, table_name, sep="\t", null="NULL")
#         conn.connection.commit()

# def update_database(df):
#     """Insert attendance data into PostgreSQL database with retry logic."""
#     password = urllib.parse.quote(POSTGRES_CREDENTIALS["password"])
#     engine = create_engine(f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
#                            f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}")

#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             print(f"🔄 Attempt {attempt}: Connecting to database {POSTGRES_CREDENTIALS['database']} at {POSTGRES_CREDENTIALS['host']}...")
#             with engine.begin() as conn:
#                 print(f"✅ Connection established.")

#                 # Create Table if it does not exist
#                 print(f"Checking if table '{TABLE_NAME}' exists...")

#                 # Truncate the table before inserting data
#                 print(f"Truncating existing table: {TABLE_NAME}")
#                 conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME} CASCADE;"))

#                 print(f"Deleting data from {TABLE_NAME} table...")
#                 conn.execute(text(f"DELETE FROM {TABLE_NAME};"))


#                 # Fast Bulk Insert
#                 print(f"Inserting data into {TABLE_NAME} table...")
#                 bulk_insert_postgres(df, conn, TABLE_NAME)

#                 print(f"✅ Data successfully inserted into '{TABLE_NAME}' table.")
#                 return  # Exit function if successful

#         except OperationalError as e:
#             print(f"❌ OperationalError: {e}")
#             logging.error(f"❌ OperationalError: {e}")
#             logging.error("Error Traceback:\n" + traceback.format_exc())

#             if attempt < MAX_RETRIES:
#                 print(f"🔄 Retrying in {RETRY_DELAY} seconds...")
#                 time.sleep(RETRY_DELAY)
#             else:
#                 print("❌ Max retries reached. Could not update the database.")
#                 logging.error("❌ Max retries reached. Could not update the database.")
#                 return


# In[39]:


# update_database(df)


# <h2 align="center"><b>FEE COLLECTION REPORT 2024-25</b></h2>

# ## **Import Required Libraries**

# In[40]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
import numpy as np
import logging
from sqlalchemy import create_engine, text


# In[41]:


# 📌 Logging
logging.basicConfig(filename="fee_collection_merge.log", level=logging.ERROR)

# 🔐 Credentials & URLs
login_url = "https://app.myskoolcom.tech/kotak_vizag/login"
credentials = {"uname": "harikiran", "psw": "812551"}
urls = {
    "2024_25": "https://app.myskoolcom.tech/kotak_vizag/office_fee/fee_consolidate_report_print?&from=2024-04-01&academic_years_id=7&status=1&imageField=Search",
    "2025_26": "https://app.myskoolcom.tech/kotak_vizag/office_fee/fee_consolidate_report_print?&from=2025-04-01&academic_years_id=1&status=1&imageField=Search"
}

# 🛠️ PostgreSQL Config
POSTGRES_CREDENTIALS = {
    "username": "postgres",
    "password": "Hari@123",
    "host": "localhost",
    "port": "5432",
    "database": "kotakschooldb",
}
TABLE_NAME = "fees_collection"


# In[42]:


# 🔌 Create Engine
def get_engine():
    password = urllib.parse.quote(POSTGRES_CREDENTIALS["password"])
    return create_engine(
        f"postgresql+psycopg2://{POSTGRES_CREDENTIALS['username']}:{password}"
        f"@{POSTGRES_CREDENTIALS['host']}:{POSTGRES_CREDENTIALS['port']}/{POSTGRES_CREDENTIALS['database']}"
    )

# 🔑 Login
def login_to_website():
    session = requests.Session()
    response = session.post(login_url, data=credentials)
    if "Invalid" in response.text:
        print("❌ Login failed!")
        return None
    print("✅ Login successful!")
    return session


# In[43]:


# 🧾 Convert HTML table to DataFrame
def table_to_dataframe(table):
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = [[td.get_text(strip=True) for td in tr.find_all("td")] for tr in table.find_all("tr")[1:]]
    return pd.DataFrame(rows, columns=headers) if rows else None

# 📥 Fetch fee table from a given URL
def fetch_fee_table(session, url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", class_="b-t")
    all_data = []

    for table in tables:
        df = table_to_dataframe(table)
        if df is not None:
            all_data.append(df)

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


# 🧹 Clean data
def clean_data(df, academic_year):
    df = df[~df.iloc[:, 0].astype(str).str.startswith("Total", na=False)].copy()
    df["Admin No."] = df["Admin No."].astype(str)

    df.columns = ['SNo', 'AdmissionNo', 'Name', 'Abacus1', 'TermFee1',
                  'Total_Fees', 'Abacus2', 'TermFee2',
                  'Total_Fee_Paid', 'Discount_Concession', 'Total_Due']

    numeric_columns = ["Total_Fees", "Total_Fee_Paid", "Discount_Concession", "Total_Due"]
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(",", "").replace(["", "None", "nan", "NaN", np.nan], 0)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df = df.drop(columns=["SNo", "Abacus1", "Abacus2", "TermFee1", "TermFee2"])
    df["academic_year"] = academic_year  # Add source year column
    return df


# In[44]:


from sqlalchemy import text

def ensure_fees_collection_table(engine):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS fees_collection (
        id SERIAL PRIMARY KEY,
        admissionno TEXT,
        name TEXT,
        total_fees INTEGER,
        total_fee_paid INTEGER,
        discount_concession INTEGER,
        total_due INTEGER,
        academic_year TEXT
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
        print("✅ Table 'fees_collection' ensured.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")


# In[45]:


# 🛢️ Insert into PostgreSQL
def update_database(df, table_name):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            print(f"⚠️ Deleting old records from '{table_name}'...")
            conn.execute(text(f"DELETE FROM {table_name};"))
            print(f"✅ Table '{table_name}' cleared.")
        df.columns = df.columns.str.lower()
        print(f"📥 Inserting {len(df)} rows...")
        df.to_sql(name=table_name, con=engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print(f"✅ Inserted into '{table_name}' successfully.")
    except Exception as e:
        print(f"❌ Error inserting: {e}")
        logging.error(f"Database insert error: {e}")
    finally:
        engine.dispose()


# In[46]:


# 🚀 Main Logic
def main():
    session = login_to_website()
    if session is None:
        return

    merged_df = pd.DataFrame()

    for year, url in urls.items():
        print(f"\n🔄 Fetching data for {year}...")
        raw_df = fetch_fee_table(session, url)
        if raw_df.empty:
            print(f"❌ No data for {year}!")
            continue
        clean_df = clean_data(raw_df, academic_year=year)
        merged_df = pd.concat([merged_df, clean_df], ignore_index=True)

    if merged_df.empty:
        print("❌ No data collected from any year!")
        return

    # Save CSV (optional)
    merged_df.to_csv("merged_fee_collection.csv", index=False)
    print("📁 Saved to merged_fee_collection.csv")

    # Ensure table exists
    engine = get_engine()
    ensure_fees_collection_table(engine)
    print("✅ Fees collection table ensured.")
    # Push to DB
    update_database(merged_df, TABLE_NAME)
    print(f"✅ All done! Total records: {len(merged_df)}")

if __name__ == "__main__":
    main()


# <h2 align="center"><b>FEE CONCESSION REPORT</b></h2>

# In[47]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
import logging
from datetime import date
from sqlalchemy import create_engine, text

# ------------------ Configuration ------------------
login_url = "https://app.myskoolcom.tech/kotak_vizag/login"
data_url_2024_25 = "https://app.myskoolcom.tech/kotak_vizag/office_fee/fee_discounts_report_receipt_wise_print?&academic_years_id=1"
data_url_2025_26 = "https://app.myskoolcom.tech/kotak_vizag/office_fee/fee_discounts_report_receipt_wise_print?&academic_years_id=7"

credentials = {
    "uname": "harikiran",
    "psw": "812551"
}

POSTGRES_CREDENTIALS = {
    "username": "postgres",
    "password": "Hari@123",
    "host": "localhost",
    "port": "5432",
    "database": "kotakschooldb",
}

TABLE_NAME = "fee_concession_report"
OUTPUT_PATH = r"D:\GITHUB\kotak-school-dbms\output_data\fee_concession_report.csv"


# In[48]:


# ------------------ Login Function ------------------
def login_to_website():
    session = requests.Session()
    login_response = session.post(login_url, data=credentials)

    if login_response.status_code != 200:
        print("❌ Login request failed! Server error.\n")
        return None

    soup = BeautifulSoup(login_response.text, "html.parser")
    if soup.find("div", class_="alert-danger"):
        print("❌ Login failed! Check credentials.\n")
        return None

    print("✅ Login successful!\n")
    return session


# In[49]:


# ------------------ Fetch Table Data ------------------
def fetch_all_concession_tables(session, data_url):
    response = session.get(data_url)
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table", class_="table_view")
    if not tables:
        print("❌ No fee tables found! The page structure may have changed.")
        return None

    all_data = []
    for table in tables:
        df = table_to_dataframe(table)
        if df is not None:
            all_data.append(df)

    if not all_data:
        print("❌ No data extracted from tables.")
        return None

    return pd.concat(all_data, ignore_index=True)


# In[50]:


# ------------------ HTML Table to DataFrame ------------------
def table_to_dataframe(table):
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    if len(headers) > 8:
        headers = headers[:8]

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) >= 8:
            rows.append(cells[:8])

    return pd.DataFrame(rows, columns=headers) if rows else None


# In[51]:


# ------------------ Clean DataFrame ------------------
def clean_data(df):
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.lower()
    df = df.dropna(subset=["student_number"])
    df["student_number"] = df["student_number"].astype(str).str.strip()
    df["discount_given"] = pd.to_numeric(df["discount_given"], errors="coerce").fillna(0.00)
    df.drop(columns=['receipt_no', 'fee_name', 'fee_amount', 'total_due_amount'], errors="ignore", inplace=True)
    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), errors="coerce").dt.date
    df = df.dropna(subset=["date"])

    df["id"] = range(1, len(df) + 1)

    # Ensure academic_year is kept if present
    cols = ['id', 'date', 'student_number', 'student_name', 'discount_given']
    if "academic_year" in df.columns:
        cols.append("academic_year")

    df = df[cols]
    df.reset_index(drop=True, inplace=True)
    return df


# In[52]:


def update_database(df: pd.DataFrame, table_name: str, postgres_credentials: dict):
    password = urllib.parse.quote(postgres_credentials["password"])
    engine = create_engine(
        f"postgresql+psycopg2://{postgres_credentials['username']}:{password}"
        f"@{postgres_credentials['host']}:{postgres_credentials['port']}/{postgres_credentials['database']}"
    )

    try:
        with engine.begin() as conn:
            print(f"🔄 Connecting to database {postgres_credentials['database']}...")

            # ✅ Create table if not exists
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    date DATE,
                    student_number VARCHAR(20),
                    student_name TEXT,
                    discount_given NUMERIC(10, 2),
                    academic_year VARCHAR(10)
                );
            """))
            print(f"✅ Ensured '{table_name}' table exists.")

            # 🔄 Clear existing records
            print(f"⚠️ Deleting existing records from: {table_name}")
            conn.execute(text(f"DELETE FROM {table_name};"))
            print(f"✅ Table '{table_name}' cleared.\n")

        # 📥 Insert Data
        print(f"📥 Inserting data into {table_name} table...")
        df.to_sql(name=table_name, con=engine, if_exists="append", index=False, method="multi", chunksize=1000)
        print(f"✅ Data successfully inserted into '{table_name}' table.\n")

    except Exception as e:
        logging.error(f"❌ Error updating database: {e}", exc_info=True)
        print(f"❌ Error occurred while updating database: {e}")

    finally:
        engine.dispose()


# In[53]:


def main():
    session = login_to_website()
    if session is None:
        return

    df_2024_25 = fetch_all_concession_tables(session, data_url_2024_25)
    df_2025_26 = fetch_all_concession_tables(session, data_url_2025_26)

    if df_2024_25 is None or df_2025_26 is None:
        print("❌ Could not fetch data for one or both academic years.")
        return

    df_2024_25["academic_year"] = "2024-25"
    df_2025_26["academic_year"] = "2025-26"

    merged_df = pd.concat([df_2024_25, df_2025_26], ignore_index=True)

    print("✅ Data extracted successfully! Cleaning data...\n")
    cleaned_df = clean_data(merged_df)

    output_file = r"D:\\GITHUB\\kotak-school-dbms\\output_data\\fee_concession_report_combined.csv"
    cleaned_df.to_csv(output_file, index=False)
    print(cleaned_df.columns)
    print(f"✅ Data saved to '{output_file}'\n")

    update_database(cleaned_df, TABLE_NAME, POSTGRES_CREDENTIALS)
    print(f"✅ {len(cleaned_df)} records entered into the database")

    print(cleaned_df.to_string())


# In[54]:


# ------------------ Run Script ------------------
if __name__ == "__main__":
    main()

