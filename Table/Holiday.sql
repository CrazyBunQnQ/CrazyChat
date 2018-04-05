-- auto-generated definition
CREATE TABLE Holiday
(
  Id         INT AUTO_INCREMENT
    PRIMARY KEY,
  Name       VARCHAR(200)              NULL
  COMMENT '节日名称',
  Date       VARCHAR(4)                NOT NULL
  COMMENT '日期(MMdd)',
  Lunar      INT(1) DEFAULT '0'        NOT NULL
  COMMENT '0:非农历
	1:农历',
  Correction VARCHAR(50)               NULL
  COMMENT '非固定日期修正：
	2w+7(第二个星期日)',
  Country    VARCHAR(200) DEFAULT '中国' NULL
  COMMENT '所属国家',
  Province   VARCHAR(100)              NULL
  COMMENT '省份',
  City       VARCHAR(200)              NULL
  COMMENT '所属城市',
  Wish       VARCHAR(255)              NULL
)
  COMMENT '节日'
  ENGINE = InnoDB;

