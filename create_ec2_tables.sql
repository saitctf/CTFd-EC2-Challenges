-- Manual SQL script to create EC2 plugin tables
-- Run this in your CTFd MySQL database

-- Create EC2Config table
CREATE TABLE IF NOT EXISTS `ec2_config` (
    `id` int NOT NULL AUTO_INCREMENT,
    `aws_access_key_id` varchar(20) DEFAULT NULL,
    `aws_secret_access_key` varchar(40) DEFAULT NULL,
    `region` varchar(32) DEFAULT NULL,
    `default_instance_type` varchar(32) DEFAULT NULL,
    `default_security_group` varchar(128) DEFAULT NULL,
    `default_key_name` varchar(128) DEFAULT NULL,
    `max_instance_time` int DEFAULT 1800,
    `auto_stop_enabled` tinyint(1) DEFAULT 1,
    PRIMARY KEY (`id`)
);

-- Create EC2ChallengeTracker table
CREATE TABLE IF NOT EXISTS `ec2_challenge_tracker` (
    `id` int NOT NULL AUTO_INCREMENT,
    `owner_id` varchar(64) DEFAULT NULL,
    `challenge_id` int DEFAULT NULL,
    `instance_id` varchar(128) DEFAULT NULL,
    `timestamp` int DEFAULT NULL,
    `revert_time` int DEFAULT NULL,
    `host` varchar(128) DEFAULT NULL,
    `flag` varchar(128) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_ec2_challenge_tracker_challenge_id` (`challenge_id`),
    KEY `ix_ec2_challenge_tracker_instance_id` (`instance_id`),
    KEY `ix_ec2_challenge_tracker_owner_id` (`owner_id`),
    KEY `ix_ec2_challenge_tracker_revert_time` (`revert_time`),
    KEY `ix_ec2_challenge_tracker_timestamp` (`timestamp`)
);

-- Create EC2Challenge table
CREATE TABLE IF NOT EXISTS `ec2_challenge` (
    `id` int NOT NULL,
    `ami_id` varchar(128) DEFAULT NULL,
    `instance_type` varchar(32) DEFAULT NULL,
    `security_group` varchar(128) DEFAULT NULL,
    `key_name` varchar(128) DEFAULT NULL,
    `subnet_id` varchar(128) DEFAULT NULL,
    `setup_script` text,
    `guide` text,
    `auto_stop_time` int DEFAULT 1800,
    PRIMARY KEY (`id`),
    KEY `ix_ec2_challenge_ami_id` (`ami_id`),
    CONSTRAINT `ec2_challenge_ibfk_1` FOREIGN KEY (`id`) REFERENCES `challenges` (`id`)
);

-- Create EC2History table
CREATE TABLE IF NOT EXISTS `ec2_history` (
    `id` int NOT NULL AUTO_INCREMENT,
    `user_id` int DEFAULT NULL,
    `instance_id` varchar(128) DEFAULT NULL,
    `challenge_id` int DEFAULT NULL,
    `start_time` int DEFAULT NULL,
    `end_time` int DEFAULT NULL,
    `solved` tinyint(1) DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `ix_ec2_history_id` (`id`)
);

-- Insert default EC2 config if it doesn't exist
INSERT IGNORE INTO `ec2_config` (`id`, `max_instance_time`, `auto_stop_enabled`) 
VALUES (1, 1800, 1);
