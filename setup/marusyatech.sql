DROP DATABASE IF EXISTS `marusyatech`;
CREATE DATABASE `marusyatech`;
USE `marusyatech`;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `UserId` varchar(64) NOT NULL COMMENT 'Уникальный user id',
  `Name` text DEFAULT NULL COMMENT 'Имя пользователя',
  `Room` text DEFAULT NULL COMMENT 'Имя комнаты',
  `ChangeTime` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`UserId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Пользователи Маруси';

LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES ('11c5d2e04b28077d3b2a385b8c332b2f3f261fab10e88b539512e68ccd80a294','Тагир','комната Тагир','2020-09-27 21:34:48'),('4d23459a0b789cdc17701ac58c82491c0828a56a431aa1d9e1f4f35c21974e53','Михаил','комната Михаил','2020-09-27 21:34:48'),('53a8a43a97c8498659b1623b2cc601eecc7358f9ae124b8880f2e431ce716a23','Товарищ','комната Михаил','2020-09-27 21:34:48'),('78d1c6916ba593c48881d20668a7574b565baa9541d2c7cd74fe5808074e3646','Анатолий','комната Федя и Толя','2020-09-27 21:34:48');
UNLOCK TABLES;
