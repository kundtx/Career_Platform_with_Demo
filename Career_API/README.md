# Career API Documentation

### Export API

| API名称                                  | 说明      |
|:---------------------------------------|:--------|
| [/export_user_data](#export_user_data) | 导出用户信息  |
| [/export_json_tree](#export_json_tree) | 导出组织机构树 |

### Query API

| API名称                                                            | 说明           |
|:-----------------------------------------------------------------|:-------------|
| [/name_fuzzy_matching](#name_fuzzy_matching)                     | 用户姓名拼音模糊查询   |
| [/exp_fuzzy_matching](#exp_fuzzy_matching)                       | 用户经历拼音模糊查询   |
| [/query_individual_relationship](#query_individual_relationship) | 查询用户同乡校友亲属信息 |
| [/query_social_relationship](#query_social_relationship)         | 查询用户前任继任同事信息 |
| [/generate_label_map](#generate_label_map)                       | 查询用户标签信息     |

### Functional API

| 地址                                           | 说明     |
|:---------------------------------------------|:-------|
| [/parse_strings](#parse_strings)             | 分词工具   |
| [/classify_strings](#classify_strings)       | 分类工具   |

### Info API

| 地址                                         | 说明            |
|:-------------------------------------------|:--------------|
| [/get_database_stats](#get_database_stats) | 获取本系统数据库的统计信息 |

# API详情

+ ## <span id="export_user_data">/export_user_data</span>

### Request parameters

|     名称      | 必填  |        类型        | 说明      |
|:-----------:|:---:|:----------------:|:--------|
| list_of_uid |  是  | str or List[str] | 用户uid列表 |

##### Request method

POST

##### Request sample

```json
{
  "list_of_uid": [
    "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8",
    "8D66AC3E-F379-3F46-B615-646607868F50"
  ]
}
```

### Response specification

|        名称         |     类型     | 说明                     |
|:-----------------:|:----------:|:-----------------------|
|      result       | List[Dict] | 结果数据列表                 |
|      +uname       |    str     | 姓名                     |
|      +gender      |    str     | 性别                     |
|     +birthday     |    str     | 出生年月                   |
|      +nation      |    str     | 民族                     |
|      +origo       |    str     | 籍贯                     |
|    +birthplace    |    str     | 出生地                    |
|     +t_party      |    str     | 入党时间                   |
|      +t_job       |    str     | 参加工作时间                 |
|  +ft_edu_career   |    str     | 全日制教育                  |
|  +ft_edu_school   |    str     | 毕业院校及专业                |
|  +pt_edu_career   |    str     | 在职教育                   |
|  +pt_edu_school   |    str     | 毕业院校及专业                |
| +current_position |    str     | 现任职务                   |
|     +img_path     |    str     | 头像路径                   |
|       +data       | List[Dict] | 用户全部经历列表               |
|      ++batch      |    null    | 保留字段                   |
|      ++label      |    str     | 经历对应的标签信息              |
|      ++level      |    Dict    | 经历的职级信息{"职位": 持续时间（月）} |
|       ++loc       |    null    | 保留字段                   |
|      ++misc       |    null    | 保留字段                   |
|       ++occ       |    null    | 保留字段                   |
|       ++raw       |    str     | 兼职修复后文本                |
|    ++raw_data     |    str     | 原始文本                   |
|  ++raw_processed  |    str     | 处理后文本                  |
|   ++raw_pinyin    |    str     | 经历原始文本拼音首字母            |
|       ++rid       |    int     | 经历的编号（本系统内部）           |
|      ++rkey       |    int     | 经历的编号（数据中心A16主键）       |
|       ++seg       |    str     | 经历的分词信息                |
|      ++time       |    str     | 经历的持续时间                |
|       ++uid       |    int     | 经历所属的用户uid             |

##### Response sample

```json
{
  "result": [
    {
      "data": [
        {
          "batch": null,
          "label": "深圳市外1,一般院校,学生",
          "level": "{'null': 35}",
          "loc": "",
          "misc": "",
          "occ": "",
          "raw": "CC市AA专科学校BB专业学生",
          "raw_data": "1979.08—1982.07 CC市AA专科学校BB专业学生",
          "raw_processed": "1979.08—1982.07 CC市AA专科学校BB专业学生",
          "rid": 0,
          "seg": "CC市L A专科学校O BB专业S 学生P ",
          "time": "1979.08—1982.07",
          "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8"
        },
        {
          "batch": null,
          "label": "深圳市外1,基层工作",
          "level": "{'null': 50}",
          "loc": "",
          "misc": "",
          "occ": "",
          "raw": "DD省EE县农业局干部",
          "raw_data": "1982.07—1986.09 DD省EE县农业局干部",
          "raw_processed": "1982.07—1986.09 DD省EE县农业局干部",
          "rid": 1,
          "seg": "省L E县L 农业局O 干部P ",
          "time": "1982.07—1986.09",
          "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8"
        }
      ],
      "name": "张三"
    },
    {
      "data": [
        {
          "batch": null,
          "label": "一般院校,经济金融,财务,深圳市外1,学生",
          "level": "{'null': 46}",
          "loc": "",
          "misc": "",
          "occ": "",
          "raw": "AA经济管理学院企业管理专业本科学校",
          "raw_data": "1989.09—1993.07 AA经济管理学院企业管理专业本科学校",
          "raw_processed": "1989.09—1993.07 AA经济管理学院企业管理专业本科学校",
          "rid": 0,
          "seg": "AA经济管理学院O 企业管理专业S 本科学校P ",
          "time": "1989.09—1993.07",
          "uid": "8D66AC3E-F379-3F46-B615-646607868F50"
        },
        {
          "batch": null,
          "label": "深圳市外1,财务",
          "level": "{'null': 22}",
          "loc": "",
          "misc": "",
          "occ": "",
          "raw": "BB省金属材料总公司驻CC交易所期货交易员",
          "raw_data": "1993.05—1995.03 BB省金属材料总公司驻CC交易所期货交易员",
          "raw_processed": "1993.05—1995.03 BB省金属材料总公司驻CC交易所期货交易员",
          "rid": 1,
          "seg": "BB省L 金属材料总公司O 驻CC交易所S 期货交易员P ",
          "time": "1993.05—1995.03",
          "uid": "8D66AC3E-F379-3F46-B615-646607868F50"
        }
      ],
      "name": "李四"
    }
  ]
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code | msg              | 说明                                     |
|:----------:|:-----------------|:---------------------------------------|
|     -1     | list_of_name字段错误 | 请求中没有list_of_name字段或list_of_name字段无法解析 |
|     -2     | 无此用户             | list_of_name中存在非法用户（数据库找不到该用户）         |

---

* ## <span id="export_json_tree">/export_json_tree</span>

##### Request method

GET

### Return specification

详见[开发说明](开发说明.docx)

##### Return sample

详见[octree_temp.json](octree_temp.json)

---

* ## <span id="name_fuzzy_matching">/name_fuzzy_matching</span>

### Request parameters

|    名称     | 必填  | 类型  | 说明                 |
|:---------:|:---:|:---:|:-------------------|
| condition |  是  | str | 姓名模糊查询关键字/关键字拼音首字母 |

##### Request method

GET 或 POST

##### Request sample

```json
{
  "condition": "zs"
}
```

or

```json
{
  "condition": "张三"
}
```

### Response specification

|   名称   |     类型     | 说明     |
|:------:|:----------:|:-------|
| result | List[Dict] | 查询结果列表 |
|  +uid  |    str     | 用户uid  |
| +uname |    str     | 用户姓名   |

##### Response sample

```json
{
  "result": [
    {
      "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8",
      "uname": "张三"
    },
    {
      "uid": "E0946CDB-5763-3C20-9729-7A54DA1B7A14",
      "uname": "张三毛"
    }
  ]
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code | msg           | 说明                               |
|:----------:|:--------------|:---------------------------------|
|     -1     | condition字段错误 | 请求中没有condition字段或condition字段无法解析 |
|     -2     | 无此用户          | 数据库找不到这样的用户                      |

---

* ## <span id="exp_fuzzy_matching">/exp_fuzzy_matching</span>

### Request parameters

|    名称     | 必填  | 类型  |         说明         |
|:---------:|:---:|:---:|:------------------:|
| condition |  是  | str | 经历模糊查询关键字/关键字拼音首字母 |

##### Request method

GET 或 POST

##### Request sample

```json
{
  "condition": "jyj"
}
```

or

```json
{
  "condition": "教育局"
}
```

### Return specification

|   名称   |     类型     | 说明      |
|:------:|:----------:|:--------|
| result | List[Dict] | 查询结果列表  |
|  +raw  |    str     | 原始经历文本  |
|  +rid  |    int     | 解析后经历编号 |
|  +uid  |    int     | 用户uid   |
| +uname |    str     | 用户姓名    |

##### Return sample

```json
{
  "result": [
    {
      "raw": "1994.11—1997.01 AA市BB区教育局勤工俭学基建",
      "rid": 2,
      "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8",
      "uname": "张三"
    },
    {
      "raw": "1997.01—2004.10 AA市BB区教育局行政办公室科员",
      "rid": 3,
      "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8",
      "uname": "张三"
    },
    {
      "raw": "1997.01—2004.10 AA市BB区教育局行政办公室科员|副主任",
      "rid": 4,
      "uid": "E0946CDB-5763-3C20-9729-7A54DA1B7A14",
      "uname": "李四"
    }
  ]
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code | msg           | 说明                               |
|:----------:|:--------------|:---------------------------------|
|     -1     | condition字段错误 | 请求中没有condition字段或condition字段无法解析 |
|     -2     | 无此经历          | 数据库找不到这样的经历                      |

* ## <span id="query_individual_relationship">/query_individual_relationship</span>

### Request parameters

|  名称  | 必填  |       类型       |                  说明                  |
|:----:|:---:|:--------------:|:------------------------------------:|
| uid  |  是  |   int or str   |                用户uid                 |
| type |  否  | int, str, list | 查询的关系类型{0=同乡, 1=校友, 2=亲属}, 不填则查询所有类型 |

##### Request method

GET 或 POST

##### Request sample

```json
{
  "uid": "AAFFEE88-1234-5678-9ABC-88889999AAAA",
  "type": 0
}
```

### Return specification

|   名称   |     类型     | 说明                            |
|:------:|:----------:|:------------------------------|
| result | List[Dict] | 查询结果列表                        |
|  +uid  |    str     | 用户uid                         |
| +uname |    str     | 用户姓名                          |
| +type  |    str     | 和被查询用户的关系类型{0=同乡, 1=校友, 2=亲属} |

##### Return sample

```json
{
  "result": [
    {
      "type": "1",
      "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8",
      "uname": "张三"
    },
    {
      "type": "1",
      "uid": "E0946CDB-5763-3C20-9729-7A54DA1B7A14",
      "uname": "李四"
    }
  ]
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code | msg     | 说明                   |
|:----------:|:--------|:---------------------|
|     -1     | uid字段错误 | 请求中没有uid字段或uid字段无法解析 |
|     -2     | 无结果     | 找不到该用户的同乡、校友或亲属关系    |

* ## <span id="query_social_relationship">/query_social_relationship</span>

### Request parameters

| 名称  | 必填  |       类型       |                  说明                   |
|:---:|:---:|:--------------:|:-------------------------------------:|
| uid |  是  |   int or str   |                 用户uid                 |
| rid |  否  | int, str, list | 经历编号，若填写则查询该特定经历对应工作关系，若不填则查询用户全部工作关系 |

##### Request method

GET 或 POST

##### Request sample

```json
{
  "uid": "AAFFEE88-1234-5678-9ABC-88889999AAAA",
  "rid": 3
}
```

### Response specification

|    名称     |     类型     | 说明                             |
|:---------:|:----------:|:-------------------------------|
|  result   | List[Dict] | 查询结果列表                         |
|   +rid    |    int     | 关系对应经历编号                       |
|   +data   | List[Dict] | 关系信息                           |
| +interval |    str     | 关系持续时间                         |
|   ++raw   |    str     | 关系对应经历原始文本                     |
|  ++type   |    str     | 关系类型{0=前任，1=继任，2=同事，3=上级，4=下级} |
|   ++uid   |    int     | 关系对应用户uid                      |
|  ++uname  |    str     | 关系对应姓名                         |

##### Response sample

```json
{
  "result": [
    {
      "rid": 3,
      "data": [
        {
          "interval": "1997.01—2004.10",
          "raw": "1997.01—2004.10 AA市BB区教育局行政办公室科员",
          "type": "1",
          "uid": "6BCB4F2B-2837-3F62-BD0E-89ADF7CF71D8",
          "uname": "张三"
        },
        {
          "interval": "1990.05—1998.07",
          "raw": "1990.05—1998.07 AA市BB区教育局行政办公室科员",
          "type": "1",
          "uid": "E0946CDB-5763-3C20-9729-7A54DA1B7A14",
          "uname": "李四"
        }
      ]
    }
  ]
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code | msg           | 说明                                 |
|:----------:|:--------------|:-----------------------------------|
|     -1     | uid字段或rid字段错误 | 请求中没有uid字段或没有rid字段/uid字段或rid字段无法解析 |
|     -2     | 无结果           | 找不到该用户的前任、继任或同事关系                  |
|     -3     | 无此经历          | 找不到该用户或该用户没有请求中rid指定的经历            |

---

* ## <span id="generate_label_map">/generate_label_map</span>

### Request parameters

| 名称  | 必选  | 类型  | 说明    |
|:---:|:---:|:---:|:------|
| uid |  是  | str | 用户uid |

##### Request method

GET 或 POST

##### Request sample

```json
{
  "uid": "AAFFEE88-1234-5678-9ABC-88889999AAAA"
}
```

### Return specification

|    名称     |     类型     | 说明       |
|:---------:|:----------:|:---------|
|  result   | List[Dict] | 查询结果列表   |
| +<具体标签名称> | List[str]] | 该标签的持续时间 |

##### Return sample

```json
{
  "result": {
    "一般院校": [
      [
        "Mon, 31 Aug 1987 16:00:00 GMT",
        "Sun, 30 Jun 1991 16:00:00 GMT"
      ]
    ],
    "国企事业单位": [
      [
        "Sun, 29 Feb 2004 16:00:00 GMT",
        "Fri, 30 Sep 2011 16:00:00 GMT"
      ],
      [
        "Sun, 29 Feb 2004 16:00:00 GMT",
        "Fri, 30 Sep 2011 16:00:00 GMT"
      ]
    ],
    "学生": [
      [
        "Mon, 31 Aug 1987 16:00:00 GMT",
        "Sun, 30 Jun 1991 16:00:00 GMT"
      ]
    ]
  }
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code | msg     | 说明                   |
|:----------:|:--------|:---------------------|
|     -1     | uid字段错误 | 请求中缺少uid字段或uid字段无法解析 |
|     -2     | 无此用户    | 找不到该用户               |

* ## <span id="parse_strings">/parse_strings</span>

### Request parameters

|     名称      | 必填  |    类型     | 说明          |
|:-----------:|:---:|:---------:|:------------|
| list_of_txt |  是  | List[str] | 需要解析的经历文本列表 |

##### Request method

POST

##### Request sample

```json
{
  "list_of_txt": [
    "深圳市深圳职业技术学院软件工程专业学生",
    "广东省梅州市农业局干部",
    "梅州市教育局局长兼书记"
  ]
}
```

### Return specification

|   名称   |       类型        | 说明                    |
|:------:|:---------------:|:----------------------|
| result | List[List[str]] | 经历解析结果（每一个List对应一个输入） |

##### Return sample

```json
{
  "result": [
    [
      "深圳市L 深圳职业技术学院O 软件工程专业S 学生P "
    ],
    [
      "梅州市L 农业局O 干部P "
    ],
    [
      "梅州市L 教育局O 局长P ",
      "梅州市L 教育局O 书记P "
    ]
  ]
}
```

##### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code |       msg       | 说明                                   |
|:----------:|:---------------:|:-------------------------------------|
|     -1     | list_of_txt字段错误 | 请求中没有list_of_txt字段或list_of_txt字段无法解析 |

---

* ## <span id="classify_strings">/classify_strings</span>

### Request parameters

|     名称      | 必填  |        类型        | 说明                                              |
|:-----------:|:---:|:----------------:|:------------------------------------------------|
| list_of_txt |  是  |    List[str]     | 需分类的经历文本列表                                      |
|   method    |  否  | str or List[str] | 方法（当前可用：bert、exp、kg，可同时使用多种方法，不填写时默认使用bert+exp） |

##### Request method

POST

##### Request sample

```json
{
  "list_of_txt": [
    "深圳市深圳职业技术学院软件工程专业学生",
    "广东省梅州市农业局干部",
    "梅州市教育局局长兼书记"
  ],
  "method": [
    "bert",
    "exp"
  ]
}
```

### Response specification

|    名称    |       类型        | 说明                  |
|:--------:|:---------------:|:--------------------|
|  result  | List[List[str]] | 分类结果（每一个List对应一个输入） |

##### Response sample

```json
{
  "result": [
    [
      "学生",
      "一般院校",
      "深圳市外1"
    ],
    [
      "深圳市外1"
    ],
    [
      "教育",
      "深圳市外1"
    ]
  ]
}
```

### Error Message

##### 系统级错误

| 错误代码 |   返回msg    | 详细描述   |
|:----:|:----------:|:-------|
| 400  | 系统错误，请稍候再试 | 请求参数有误 |
| 404  | 系统错误，请稍候再试 | 资源未找到  |
| 500  | 系统错误，请稍候再试 | 服务器错误  |

##### 业务级错误

| error_code |          msg           | 说明                                          |
|:----------:|:----------------------:|:--------------------------------------------|
|     -1     | list_of_txt/method字段错误 | 请求中没有list_of_txt字段或list_of_txt/method字段无法解析 |
|     -2     |        无此method        | 不存在请求中method指定的的模型                          |

* ## <span id="get_database_stats">/get_database_stats</span>

### Request parameters

无参数

##### Request method

GET

### Response specification

|          名称          | 类型  | 说明                                 |
|:--------------------:|:---:|:-----------------------------------|
|    nodeCount_Leaf    | int | 组织架构树中的职位节点数                       |
|    nodeCount_Node    | int | 组织架构树总节点数                          |
|  nodeCount_YearUser  | int | 关系网络中的经历节点数量                       |
|     relCount_Col     | int | 关系网络中的同事关系数量                       |
|    relCount_Rank     | int | 关系网络中的上下级关系数量                      |
|   rowCount_expRaw    | int | 本系统数据库中存储的经历原始数据（从数据中心A16相关表获取）条目数 |
|  rowCount_expParsed  | int | 本系统数据库中存储的算法解析后的经历条目数              |
|   rowCount_userNum   | int | 本系统数据库中存储的的人员条目数                   |
|  num_knowledgeGraph  | int | 本系统数据库中存储的知识图谱数量                   |
|  nodeAttNum_OCtree   | int | 组织机构树中节点的属性数量                      |
| nodeAttNum_SocialNet | int | 关系网络中节点的属性数量                       |

##### Response sample

```json
{
  "nodeAttNum_OCtree": 4,
  "nodeAttNum_SocialNet": 5,
  "nodeCount_Leaf": 2450,
  "nodeCount_Node": 5300,
  "nodeCount_YearUser": 2665,
  "num_knowledgeGraph": 2,
  "relCount_Col": 106,
  "relCount_Rank": 16,
  "rowCount_expParsed": 2665,
  "rowCount_expRaw": 2069,
  "rowCount_userNum": 180
}
```