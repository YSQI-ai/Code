-- ==========================================
-- 数据库初始化脚本：宿舍管理系统
-- ==========================================

-- 创建并使用数据库
CREATE DATABASE IF NOT EXISTS `宿舍管理系统` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `宿舍管理系统`;

-- 关闭外键检查以方便清理旧表（避免修改表结构时因旧表存在而报错）
SET FOREIGN_KEY_CHECKS = 0;

-- 清理可能存在的旧表
DROP TABLE IF EXISTS `Repair_Record`;
DROP TABLE IF EXISTS `Bed`;
DROP TABLE IF EXISTS `Room`;
DROP TABLE IF EXISTS `Student`;
DROP TABLE IF EXISTS `Dormitory_Building`;
DROP TABLE IF EXISTS `Administrator`;

-- 开启外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 1. 创建表结构
-- ==========================================

-- 1. 宿舍楼 (Dormitory Building)
CREATE TABLE `Dormitory_Building` (
    `BuildingNo` VARCHAR(20) PRIMARY KEY COMMENT '楼号',
    `BuildingName` VARCHAR(50) NOT NULL COMMENT '楼名',
    `TotalFloors` INT COMMENT '总楼层',
    `AdminNo` VARCHAR(20) COMMENT '管理员工号',
    `Phone` VARCHAR(20) COMMENT '联系电话'
) ENGINE=InnoDB COMMENT='宿舍楼信息';

-- 2. 学生 (Student)
CREATE TABLE `Student` (
    `Sno` VARCHAR(20) PRIMARY KEY COMMENT '学号',
    `Sname` VARCHAR(50) NOT NULL COMMENT '姓名',
    `Ssex` ENUM('男', '女') NOT NULL COMMENT '性别',
    `Dept` VARCHAR(100) COMMENT '院系',
    `Sclass` VARCHAR(50) COMMENT '班级',
    `Phone` VARCHAR(20) COMMENT '电话',
    `IDCard` VARCHAR(18) UNIQUE COMMENT '身份证号',
    `CheckInDate` DATE COMMENT '入住日期',
    `CheckOutDate` DATE COMMENT '退宿日期'
) ENGINE=InnoDB COMMENT='学生信息';

-- 3. 管理员 (Administrator)
CREATE TABLE `Administrator` (
    `AdminNo` VARCHAR(20) PRIMARY KEY COMMENT '工号',
    `Aname` VARCHAR(50) NOT NULL COMMENT '姓名',
    `Asex` ENUM('男', '女') COMMENT '性别',
    `Phone` VARCHAR(20) COMMENT '电话',
    `BuildingNo` VARCHAR(20) COMMENT '所属楼栋',
    `Role` VARCHAR(30) COMMENT '角色权限',
    FOREIGN KEY (`BuildingNo`) REFERENCES `Dormitory_Building`(`BuildingNo`) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='管理员信息';

-- 为宿舍楼表添加管理员的外键约束
ALTER TABLE `Dormitory_Building` 
ADD CONSTRAINT `FK_Building_Admin` 
FOREIGN KEY (`AdminNo`) REFERENCES `Administrator`(`AdminNo`) ON DELETE SET NULL;

-- 4. 宿舍房间 (Room)
CREATE TABLE `Room` (
    `RoomNo` VARCHAR(20) NOT NULL COMMENT '房间号',
    `BuildingNo` VARCHAR(20) NOT NULL COMMENT '楼号',
    `RoomType` VARCHAR(30) COMMENT '房间类型',
    `BedCount` INT DEFAULT 4 COMMENT '床位数',
    `OccupiedCount` INT DEFAULT 0 COMMENT '已住人数',
    `Floor` INT COMMENT '所在楼层',
    `Status` VARCHAR(20) DEFAULT '正常' COMMENT '当前状态',
    PRIMARY KEY (`RoomNo`, `BuildingNo`),
    FOREIGN KEY (`BuildingNo`) REFERENCES `Dormitory_Building`(`BuildingNo`) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='宿舍房间信息';

-- 5. 床位 (Bed)
CREATE TABLE `Bed` (
    `BedNo` VARCHAR(20) NOT NULL COMMENT '床位号',
    `RoomNo` VARCHAR(20) NOT NULL COMMENT '房间号',
    `BuildingNo` VARCHAR(20) NOT NULL COMMENT '楼号',
    `IsAvailable` BOOLEAN DEFAULT TRUE COMMENT '是否空闲',
    `Sno` VARCHAR(20) UNIQUE COMMENT '对应入住学生学号',
    PRIMARY KEY (`BedNo`, `RoomNo`, `BuildingNo`),
    FOREIGN KEY (`RoomNo`, `BuildingNo`) REFERENCES `Room`(`RoomNo`, `BuildingNo`) ON DELETE CASCADE,
    FOREIGN KEY (`Sno`) REFERENCES `Student`(`Sno`) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='床位信息';

-- 6. 报修记录 (Repair Record)
-- 注意：这里的 RepairID 改为了 VARCHAR(20)，之前版本中由于表已存在可能没有更新成功
CREATE TABLE `Repair_Record` (
    `RepairID` VARCHAR(20) PRIMARY KEY COMMENT '报修单号',
    `Sno` VARCHAR(20) COMMENT '报修学生学号',
    `Description` TEXT NOT NULL COMMENT '故障描述',
    `SubmitTime` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    `Status` VARCHAR(20) DEFAULT '待处理' COMMENT '处理状态',
    `Result` TEXT COMMENT '处理结果',
    `AdminNo` VARCHAR(20) COMMENT '处理人工号',
    FOREIGN KEY (`Sno`) REFERENCES `Student`(`Sno`) ON DELETE SET NULL,
    FOREIGN KEY (`AdminNo`) REFERENCES `Administrator`(`AdminNo`) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='报修记录信息';

-- ==========================================
-- 2. 插入测试数据
-- ==========================================

-- 1. 插入宿舍楼信息 (先不设置管理员，避免外键死锁)
INSERT INTO `Dormitory_Building` (`BuildingNo`, `BuildingName`, `TotalFloors`, `AdminNo`, `Phone`) VALUES
('B01', '南苑1栋 (男生宿舍)', 6, NULL, '010-88880001'),
('B02', '北苑2栋 (女生宿舍)', 6, NULL, '010-88880002');

-- 2. 插入管理员信息
-- 注意：张主管的所属楼栋在图中为“全部”，但在数据库外键约束下只能填具体楼号或 NULL。此处使用 NULL 代表统管。
INSERT INTO `Administrator` (`AdminNo`, `Aname`, `Asex`, `Phone`, `BuildingNo`, `Role`) VALUES
('ADM001', '王建国', '男', '13800000001', 'B01', '楼管'),
('ADM002', '李素珍', '女', '13900000002', 'B02', '楼管'),
('ADM003', '张主管', '男', '13700000003', NULL, '超级管理员');

-- 更新宿舍楼信息的管理员关联
UPDATE `Dormitory_Building` SET `AdminNo` = 'ADM001' WHERE `BuildingNo` = 'B01';
UPDATE `Dormitory_Building` SET `AdminNo` = 'ADM002' WHERE `BuildingNo` = 'B02';

-- 3. 插入宿舍房间信息
INSERT INTO `Room` (`BuildingNo`, `RoomNo`, `RoomType`, `BedCount`, `OccupiedCount`, `Floor`, `Status`) VALUES
('B01', '101', '四人间', 4, 2, 1, '正常'),
('B01', '102', '四人间', 4, 0, 1, '维修中'),
('B02', '201', '双人间', 2, 1, 2, '正常');

-- 4. 插入学生信息
INSERT INTO `Student` (`Sno`, `Sname`, `Ssex`, `Dept`, `Sclass`, `Phone`, `IDCard`, `CheckInDate`, `CheckOutDate`) VALUES
('20230101', '张三', '男', '计算机学院', '计科2301', '13111111111', '11010520050101XXXX', '2023-09-01', NULL),
('20230102', '李四', '男', '计算机学院', '计科2301', '13222222222', '11010520050202XXXX', '2023-09-01', NULL),
('20230201', '王语嫣', '女', '外国语学院', '英语2302', '13333333333', '11010520050303XXXX', '2023-09-02', NULL),
('20220105', '赵六', '男', '计算机学院', '计科2201', '13444444444', '11010520040404XXXX', '2022-09-01', '2024-01-15');

-- 5. 插入床位信息
INSERT INTO `Bed` (`BuildingNo`, `RoomNo`, `BedNo`, `IsAvailable`, `Sno`) VALUES
('B01', '101', '1', FALSE, '20230101'),
('B01', '101', '2', FALSE, '20230102'),
('B01', '101', '3', TRUE, NULL),
('B01', '101', '4', TRUE, NULL),
('B02', '201', '1', FALSE, '20230201'),
('B02', '201', '2', TRUE, NULL);

-- 6. 插入报修记录
INSERT INTO `Repair_Record` (`RepairID`, `Sno`, `Description`, `SubmitTime`, `Status`, `Result`, `AdminNo`) VALUES
('REP20240501001', '20230101', 'B01-101空调漏水', '2024-05-01 09:30:00', '已处理', '更换冷凝水管', 'ADM001'),
('REP20240502002', '20230201', 'B02-201门锁损坏', '2024-05-02 14:15:00', '待处理', NULL, NULL),
('REP20240505003', '20230102', 'B01-101一号床电灯不亮', '2024-05-05 20:00:00', '处理中', '正在采购灯管', 'ADM001');

-- ==========================================
-- 测试查询
-- ==========================================
SELECT * FROM `Student`;

SELECT * FROM `Dormitory_Building`;
