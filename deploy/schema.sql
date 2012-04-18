-- To create the database:
--   CREATE DATABASE doodle;
--   GRANT ALL PRIVILEGES ON doodle.* TO 'doodle'@'localhost' IDENTIFIED BY 'doodle';
--
-- To reload the tables:
--   mysql --user=doodle --password=doodle --database=doodle < schema.sql

SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";

DROP TABLE IF EXISTS saved;
DROP TABLE IF EXISTS online;
DROP TABLE IF EXISTS user_like;
DROP TABLE IF EXISTS room_user;
DROP TABLE IF EXISTS topic;
DROP TABLE IF EXISTS room;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS userintopic;

CREATE TABLE user
(
    id VARCHAR(128) NOT NULL,
    url INT NOT NULL AUTO_INCREMENT,
    site VARCHAR(32),
    site_id VARCHAR(32),
    access_key VARCHAR(256),
    access_secret VARCHAR(256),
    name VARCHAR(256),
    icon VARCHAR(512),
    intro TEXT,
    email VARCHAR(256),
    password VARCHAR(256),
    created DATETIME,
    role INT,
    PRIMARY KEY (`id`),
    KEY `url` (`url`)
) AUTO_INCREMENT=100000;

CREATE TABLE room
(
    `id` INT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(512),
    `intro` TEXT,
    `password` VARCHAR(32),
    `likes` INT,
    `views` INT,
    `savedid` INT,
    `created` DATETIME,
    PRIMARY KEY (`id`),
    KEY `created` (`created`),
    KEY `likes` (`likes`),
    KEY `views` (`views`)
) AUTO_INCREMENT=100000;

CREATE TABLE room_user
(
    `id` INT NOT NULL AUTO_INCREMENT,
    `uid` VARCHAR(128),
    `name` VARCHAR(256),
    `icon` VARCHAR(512),
    `url` INT,
    `rid` INT,
    `role` INT,
    PRIMARY KEY (`id`),
    KEY `FK_room_user_room` (`rid`),
    CONSTRAINT `FK_room_user_room` FOREIGN KEY (`rid`) REFERENCES `room` (`id`)
);

CREATE TABLE user_like
(
    `id` INT NOT NULL AUTO_INCREMENT,
    `uid` VARCHAR(128),
    `rid` INT,
    PRIMARY KEY (`id`),
    KEY `uid` (`uid`),
    KEY `rid` (`rid`)
);

CREATE TABLE topic
(
    id INT NOT NULL AUTO_INCREMENT,
    tid INT,
    uid VARCHAR(128),
    url INT,
    name VARCHAR(256),
    icon VARCHAR(512),
    title VARCHAR(512),
    content TEXT,
    created DATETIME,
    view_count INT,
    reply_count INT,
    reply_uid VARCHAR(128),
    reply_url INT,
    reply_icon VARCHAR(512),
    reply_name VARCHAR(256),
    replied DATETIME,
    PRIMARY KEY (`id`),
    KEY `tid` (`tid`),
    KEY `uid` (`uid`),
    KEY `created` (`created`),
    KEY `replied` (`replied`),
    KEY `reply_count` (`reply_count`)
) AUTO_INCREMENT=100000;

CREATE TABLE userintopic
(
    uid VARCHAR(128),
    url INT,
    name VARCHAR(256),
    icon VARCHAR(512),
    time DATETIME,
    PRIMARY KEY (`uid`),
    KEY `time` (`time`)
);

CREATE TABLE online
(
    id INT NOT NULL AUTO_INCREMENT,
    rid INT,
    uid VARCHAR(128),
    url INT,
    name VARCHAR(256),
    icon VARCHAR(512),
    PRIMARY KEY (`id`),
    KEY `uid` (`uid`),
    KEY `FK_online_room` (`rid`),
    CONSTRAINT `FK_online_room` FOREIGN KEY (`rid`) REFERENCES `room` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE saved
(
    id INT NOT NULL AUTO_INCREMENT,
    rid INT,
    uid VARCHAR(128),
    file MEDIUMBLOB,
    created DATETIME,
    PRIMARY KEY (`id`),
    KEY `created` (`created`),
    KEY `FK_saved_room` (`rid`),
    CONSTRAINT `FK_saved_room` FOREIGN KEY (`rid`) REFERENCES `room` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION    
);