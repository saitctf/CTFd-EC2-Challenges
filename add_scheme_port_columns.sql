-- Add scheme and port columns to ec2_challenge table
-- Run this script to add the missing columns

USE ctfd;

-- Add scheme column
ALTER TABLE ec2_challenge ADD COLUMN scheme VARCHAR(10) DEFAULT NULL;

-- Add port column  
ALTER TABLE ec2_challenge ADD COLUMN port VARCHAR(10) DEFAULT NULL;

-- Verify the columns were added
DESCRIBE ec2_challenge;
