USE schooldb;

SHOW INDEXES FROM students_2024_25;

ALTER TABLE students_2024_25 DROP INDEX existing_index_name;

ALTER TABLE students_2024_25 DROP INDEX AdmissionNo;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_2;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_3;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_4;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_5;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_6;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_7;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_8;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_9;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_10;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_11;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_12;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_13;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_14;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_15;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_16;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_17;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_18;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_19;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_20;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_21;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_22;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_23;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_24;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_25;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_26;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_27;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_28;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_29;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_30;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_31;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_32;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_33;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_34;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_35;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_36;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_37;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_38;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_39;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_40;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_41;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_42;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_43;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_44;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_45;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_46;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_47;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_48;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_49;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_50;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_51;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_52;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_53;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_54;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_55;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_56;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_57;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_58;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_59;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_60;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_61;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_62;					
ALTER TABLE students_2024_25 DROP INDEX AdmissionNo_63;					

SHOW INDEX FROM students_2024_25;

ALTER TABLE students_2024_25 ADD UNIQUE (AdmissionNo);

SELECT DISTINCT index_name 
FROM information_schema.statistics 
WHERE table_name = 'students_2024_25';



