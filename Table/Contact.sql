-- auto-generated definition
CREATE TABLE Contact
(
  ContactId    INT AUTO_INCREMENT,
  NickName     VARCHAR(100)       NOT NULL
  COMMENT '昵称',
  RemarkName   VARCHAR(100)       NOT NULL
  COMMENT '备注'
    PRIMARY KEY,
  RealNickName VARCHAR(100)       NULL
  COMMENT '称呼',
  Sex          INT(1) DEFAULT '0' NOT NULL
  COMMENT '账号性别',
  RealSex      INT(1)             NULL
  COMMENT '真实性别',
  Province     VARCHAR(20)        NULL
  COMMENT '所在省份',
  City         VARCHAR(20)        NULL
  COMMENT '所在城市',
  Alias        VARCHAR(20)        NULL,
  IsOwner      INT(1) DEFAULT '0' NOT NULL
  COMMENT '是否是自己',
  CONSTRAINT Tag_ContactId_uindex
  UNIQUE (ContactId),
  CONSTRAINT Tag_RemarkName_uindex
  UNIQUE (RemarkName)
)
  COMMENT '好友标签'
  ENGINE = InnoDB;

