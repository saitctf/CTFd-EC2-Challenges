-- Add missing columns to ec2_challenge table
-- Run this in your CTFd MySQL database

-- Check what columns currently exist
-- DESCRIBE ec2_challenge;

-- Add missing columns to ec2_challenge table
ALTER TABLE `ec2_challenge` 
ADD COLUMN IF NOT EXISTS `ami_id` varchar(128) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS `instance_type` varchar(32) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS `security_group` varchar(128) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS `key_name` varchar(128) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS `subnet_id` varchar(128) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS `setup_script` text,
ADD COLUMN IF NOT EXISTS `guide` text,
ADD COLUMN IF NOT EXISTS `auto_stop_time` int DEFAULT 1800;

-- Add index for ami_id if it doesn't exist
CREATE INDEX IF NOT EXISTS `ix_ec2_challenge_ami_id` ON `ec2_challenge` (`ami_id`);

-- Verify the table structure
-- DESCRIBE ec2_challenge;
