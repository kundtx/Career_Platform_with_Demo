DROP DATABASE IF EXISTS CAREER_dev;
CREATE DATABASE CAREER_dev;

use CAREER_dev;

DROP TABLE IF EXISTS person;
CREATE TABLE person(    
        person_uuid VARCHAR(255) PRIMARY KEY COMMENT '人员UUID (数据中心A00)',
        person_name VARCHAR(255) DEFAULT NULL COMMENT '人员姓名',
        person_namepinyin VARCHAR(255) DEFAULT NULL COMMENT '人员姓名拼音首字母',
        person_gender CHAR(32) COMMENT '性别{1:男, 2:女}',
        person_minzu CHAR(32) COMMENT '民族',
        person_origo VARCHAR(255) COMMENT '籍贯',
        person_birthplace VARCHAR(255) COMMENT '出生地',
        person_photo VARCHAR(255) COMMENT '照片路径',
        edu_ft varchar(255) COMMENT '最高全日制教育学历',
        edu_ft_school varchar(255) COMMENT '最高全日制教育学校',
        edu_pt varchar(255) COMMENT '最高在职教育学历',
        edu_pt_school varchar(255) COMMENT '最高在职教育学校',
        time_birth DATE COMMENT '生日',
        time_joinparty DATE COMMENT '入党时间',
        time_startwork DATE COMMENT '工作时间',
        cur_position VARCHAR(255) COMMENT '现任职位',
        cur_adminrank VARCHAR(255) COMMENT '现任行政级别'
        ) DEFAULT CHARSET=UTF8, COMMENT '人员基本信息表';

DROP TABLE IF EXISTS person_relative;
CREATE TABLE person_relative(
        relative_id VARCHAR(255) PRIMARY KEY COMMENT '亲属主键 (数据中心A36.recordid) ',
        relative_name VARCHAR(255) COMMENT '亲属姓名',
        relative_birthday DATE COMMENT '亲属生日',
        relative_type VARCHAR(255) COMMENT '称谓代码 (数据中心A3604B, 码表GB4761) ',
        relative_uuid VARCHAR(255) COMMENT '亲属的person_uuid (该亲属在person表中时本字段才有值) ',
        person_uuid VARCHAR(255) COMMENT '亲属所属人员的person_uuid',
        time_update datetime(0) NULL,
        INDEX (person_uuid)
        ) DEFAULT CHARSET=UTF8, COMMENT '人员亲属表';

DROP TABLE IF EXISTS exp;
CREATE TABLE exp(
        exp_uuid VARCHAR(255) COMMENT '经历在数据中心的UUID (数据中心A16表主键)',
        exp_splitnum INT DEFAULT 0 COMMENT '编号, 代表本条记录是对应经历原文从1开始的第几个兼职拆分结果. 若没被rebuild处理过则为0',
        PRIMARY KEY (exp_uuid, exp_splitnum) COMMENT '温馨提示: (exp_uuid, exp_splitnum)才是本系统内经历的唯一id',
        exp_ordernum INT COMMENT '编号，代表本记录是对应人员的第几条经历',
        text_ TEXT COMMENT '经历文本 (温馨提示: 是text_不是text, 后面有下划线_)',
        text_token TEXT COMMENT '经历文本的NER token',
        text_raw TEXT COMMENT '经历原文',
        text_rawpinyin TEXT COMMENT '经历原文 (首字母拼音 ) ',
        text_rawrefine TEXT COMMENT '经历原文 (兼职拆分标记前 ) ',
        text_rawsplit TEXT COMMENT '经历原文 (兼职拆分标记后 ) ',
        text_rawtoken TEXT COMMENT '经历原文 (segment后)',
        time_start DATE COMMENT '经历开始日期',
        time_end DATE COMMENT '经历结束日期',
        adminrank VARCHAR(255) NULL COMMENT '经历的行政级别',
        person_uuid VARCHAR(255) COMMENT '经历所属人员UUID',
        INDEX (person_uuid),
        INDEX (exp_uuid)
        ) DEFAULT CHARSET=UTF8, COMMENT '经历表';

DROP TABLE IF EXISTS relationship;
CREATE TABLE relationship(    
        rel_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '关系记录id',
        rel_type INT COMMENT '关系类型',
        person_uuid_from VARCHAR(255) COMMENT '关系所属的人员UUID',
        person_uuid_to VARCHAR(255) COMMENT '关系指向的人员UUID',
        exp_uuid_from VARCHAR(255) DEFAULT NULL COMMENT '关系所属的经历UUID, 与经历无关则为NULL',
        exp_uuid_to VARCHAR(255) DEFAULT NULL COMMENT '关系指向的经历UUID, 与经历无关则为NULL',
        time_start DATE DEFAULT NULL COMMENT '关系开始日期',
        time_end DATE DEFAULT NULL COMMENT '关系结束日期',
        rel_info VARCHAR(255) COMMENT '关系附加信息',
        INDEX (person_uuid_from),
        INDEX (exp_uuid_from),
        UNIQUE KEY (rel_type, exp_uuid_from, exp_uuid_to),
        UNIQUE KEY (rel_type, person_uuid_from, person_uuid_to)
        ) DEFAULT CHARSET=UTF8, COMMENT '关系表';
-- [rel_type关系类型代码对照]
-- 1: 工作关系{101:前任, 102:继任, 103:同事, 104:上级, 105:下级}
-- 2: 个人关系{201:同乡, 202:校友, 203:亲属关系}

DROP TABLE IF EXISTS label;
CREATE TABLE label(
        label_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '标签id',
        label_code VARCHAR(255) COMMENT '标签代码',
        label_text VARCHAR(255) COMMENT '标签文本',
        label_category INT COMMENT '标签类别',
        label_source INT COMMENT '标签来源',
        label_info VARCHAR(255) COMMENT '标签附加信息',
        person_uuid VARCHAR(255) COMMENT '标签所属人员UUID',
        exp_uuid VARCHAR(255) DEFAULT NULL COMMENT '标签对应经历UUID, 标签来源非经历时为空值',
        eval_uuid VARCHAR(255) DEFAULT NULL COMMENT '标签对应评价材料UUID, 标签来源非评价材料时为空值',
        time_start DATE DEFAULT NULL COMMENT '标签开始日期',
        time_end DATE DEFAULT NULL COMMENT '标签结束日期',
        INDEX (person_uuid),
        INDEX (exp_uuid),
        INDEX (eval_uuid)
        ) DEFAULT CHARSET=UTF8, COMMENT '人员标签表';
-- [label_category标签类别代码对照]
-- 1: 客观标签
-- 2: 评价标签
-- [label_source标签来源代码对照]
-- 1: 个人信息{100: 其他, 101: 教育信息}
-- 2: 经历信息{200: 其他, 201: 规则分类器, 202: Bert分类器}
-- 3: 评价材料{300: 其他, 301: 模糊匹配分类器}
-- [label_info值意义]
-- label_category=2时, label_info值为该标签在评价文本中的出现次数

DROP TABLE IF EXISTS evaluation;
CREATE TABLE evaluation(
        eval_uuid VARCHAR(255) PRIMARY KEY COMMENT '评价UUID',
        person_uuid VARCHAR(255) COMMENT '人员UUID (数据中心A00)',
        eval_text TEXT COMMENT '评价文本',
        eval_deficiency TEXT COMMENT '主要不足',
        eval_source VARCHAR(255) COMMENT '评价来源',
        eval_memo VARCHAR(255) COMMENT '评价备注',
        time_start DATE DEFAULT NULL COMMENT '评价时间',
        time_create DATE DEFAULT NULL COMMENT '评价创建时间',
        time_update DATE DEFAULT NULL COMMENT '评价更新时间',
        ordernum INT COMMENT '排序序号',
        effective VARCHAR(6) COMMENT '是否有效{0:无效,1:有效}',
        ismatch VARCHAR(6) COMMENT '是否匹配{1:匹配,2:不匹配}',
        INDEX (person_uuid)
        ) DEFAULT CHARSET=UTF8, COMMENT '人员评价表';
-- [effective 是否有效代码对照]
-- 0: 无效
-- 1: 有效
-- [ismatch 是否匹配代码对照]
-- 1: 匹配
-- 2: 不匹配