import career_platform as CP
import os
import json

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "demo/sample_data/")
RUN_ENV = "dev"

# 初始化数据库
CP.persistent.utils.init_CareerDB()

# 1. 获取CAREER数据库Mapper ===========================================================================================
cem = CP.persistent.mapper.CareerDBExperienceMapper()           # 经历
cpm = CP.persistent.mapper.CareerDBPersonMapper()               # 人员
clm = CP.persistent.mapper.CareerDBLabelMapper()                # 标签
c_rltv_m = CP.persistent.mapper.CareerDBRelativeMapper()        # 亲属
c_rshp_m = CP.persistent.mapper.CareerDBRelationshipMapper()    # 关系
c_eval_m = CP.persistent.mapper.CareerDBEvaluationMapper()      # 评价


# 2. 获取数据源的Mapper并全量导入/更新数据到CAREER数据库 =================================================================
if RUN_ENV == "dev":
    # 开发环境：用demo/sample_data/中的样例数据
    jem = CP.persistent.mapper.JsonExperienceMapper()
    jpm = CP.persistent.mapper.JsonPersonMapper()
    j_eval_m = CP.persistent.mapper.JsonEvaluationMapper()

    # 读取数据并保存到CAREER
    cem.save(replace_by="person_uuid", exp_list=jem.getAll(SAMPLE_DATA_FOLDER + "sample_data_exp.json"))
    cpm.save(person_list=jpm.getAll(SAMPLE_DATA_FOLDER + "sample_data_person.json"))
    c_eval_m.save(replace_by="person_uuid", eval_list=j_eval_m.getAll(SAMPLE_DATA_FOLDER + "sample_data_evaluation.json"))

elif RUN_ENV == "prod":
    # 生产环境：用数据中心数据
    dem = CP.persistent.mapper.DatacenterExperienceMapper()
    dpm = CP.persistent.mapper.DatacenterPersonMapper()
    drm = CP.persistent.mapper.DatacenterRelativeMapper()
    d_eval_m = CP.persistent.mapper.DatacenterEvaluationMapper()

    # 读取数据并保存到CAREER数据库
    cem.save(replace_by="person_uuid", exp_list=dem.getAll())
    cpm.save(person_list=dpm.getAll())
    c_rltv_m.save(relative_list=drm.getAll())
    c_eval_m.save(replace_by="person_uuid", eval_list=d_eval_m.getAll())


# 3. 数据处理、计算、保存 ===============================================================================================

# 处理人员信息数据, 并写回到数据库
person_list = cpm.getAll()
person_list = CP.algorithm.person_parser.recover_school_name(person_list=person_list, in_position=True, callback=CP.algorithm.tqdm_callback())
cpm.save(person_list=person_list)
del person_list

# 用姓名生日匹配亲属person_uuid并写回数据库
relative_list = c_rltv_m.getAll()
relative_list = CP.algorithm.person_parser.match_rel_A00(rel_list=relative_list, in_position=True, callback=CP.algorithm.tqdm_callback())
c_rltv_m.save(relative_list=relative_list)

# 处理经历数据, 并回写到数据库
exp_list = cem.getAll()
exp_list = CP.algorithm.exp_parser.refine(exp_list, in_position=True, callback=CP.algorithm.tqdm_callback())
exp_list = CP.algorithm.exp_parser.segment(exp_list, in_position=True, callback=CP.algorithm.tqdm_callback())
exp_list = CP.algorithm.exp_parser.rebuild(exp_list, callback=CP.algorithm.tqdm_callback())
cem.save(replace_by="exp_uuid", exp_list=exp_list)
del exp_list

# 用处理过的经历数据预测Label, 并保存Label
label_list = CP.algorithm.label.label_exp(exp_list=cem.getAll())
clm.save(replace_by="exp_uuid", label_list=label_list)

# 用干部评价数据预测Label, 并保存Label
label_list = CP.algorithm.label.label_eval(eval_list=c_eval_m.getAll(), callback=CP.algorithm.utils.tqdm_callback())
clm.save(replace_by="eval_uuid", label_list=label_list)
del label_list

# 用经历和人员数据生成组织机构树、在neo4j中计算出关系网络等

octree = CP.algorithm.network.octree(exp_list=cem.getAll(), person_list=cpm.getAll())

# 把octree保存为json文件
del octree['users']
with open('./octree_temp.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(octree, ensure_ascii=False, indent=4))

# 导出并保存亲属、校友、同乡关系
person_list = cpm.getAll()
relative_list = c_rltv_m.getAll()
rel_relshp_list = CP.algorithm.person_parser.export_rel_relationship(rel_list=relative_list, callback=CP.algorithm.utils.tqdm_callback())
alum_relshp_list = CP.algorithm.person_parser.export_alumni_relationship(person_list, callback=CP.algorithm.utils.tqdm_callback())
tx_relshp_list = CP.algorithm.person_parser.export_tx_relationship(person_list, callback=CP.algorithm.utils.tqdm_callback())
c_rshp_m.save(replace_by="person_uuid", relationship_list=tx_relshp_list+rel_relshp_list+alum_relshp_list)
del person_list, relative_list, rel_relshp_list, alum_relshp_list, tx_relshp_list

# 把neo4j和nid2resumes.json里的Relationship都导出, 并保存到数据库
rel_list_neo4j = CP.algorithm.network.export_neo4j_relationship(callback=CP.algorithm.utils.tqdm_callback())
rel_list_nid2r = CP.algorithm.network.export_nid2resumes_relationship(callback=CP.algorithm.utils.tqdm_callback())
c_rshp_m.save(replace_by="exp_uuid", relationship_list=rel_list_neo4j + rel_list_nid2r)
del rel_list_neo4j, rel_list_nid2r

# 亲属关系计算保存
# 更新亲属的UUID 通过姓名与生日得到person表中的uuid
size = c_rltv_m.updateRelativeUuid()
# 分析并保存亲属关系
rela_list = CP.algorithm.person_parser.export_relativeship(callback=CP.algorithm.tqdm_callback())
c_rshp_m.save(replace_by="id", relationship_list=rela_list)
del rela_list