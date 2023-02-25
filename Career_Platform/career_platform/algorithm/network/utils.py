'''
functions used in CTree class func
'''
import pandas as pd
import pickle
import os


def set_node_time(nid, startTime, endTime, restore_node_interval):
    if nid not in restore_node_interval:
        restore_node_interval[nid] = (startTime, endTime)
    else:
        start, end = restore_node_interval[nid]
        if startTime < start:
            start = startTime
        if endTime > end:
            end = endTime
        restore_node_interval[nid] = (start, end)


def time_overlap(year, entry_time):
    startTime, endTime = entry_time.split('—')
    startTime = int(startTime[:4])
    endTime = int(endTime[:4])
    if startTime <= int(year) <= endTime:  # non overlap
        return True
    else:
        return False


def coincident_interval(ia, ib, min_year, max_year):
    sa, ea = ia
    sb, eb = ib
    sa = max(min_year, float(sa))
    ea = min(max_year, float(ea))
    sb = max(min_year, float(sb))
    eb = min(max_year, float(eb))
    if ea <= sb or eb <= sa:
        return []
    return [format(max(sa, sb), '.2f'), format(min(ea, eb), '.2f')]


def user_pair(resume_la, resume_lb, start, end):
    """  """
    results = []
    for ra in resume_la:
        eid_a, uid_a, interval_as, interval_ae = ra
        for rb in resume_lb:
            eid_b, uid_b, interval_bs, interval_be = rb
            co_period = coincident_interval((interval_as, interval_ae),
                                            (interval_bs, interval_be),
                                            min_year=start,
                                            max_year=end)
            if uid_a == uid_b or co_period == []:
                continue
            else:
                results.append((eid_a, eid_b, co_period))
    return results


def get_rank_dict(path=os.path.join(os.path.dirname(__file__), "./data/rank.xlsx")):
    rank_excel = pd.read_excel(path)
    rank_dict = {"null": -1}
    for id, row in rank_excel.iterrows():
        rank = row["等级"]
        name = row.tolist()[1:]
        name_altered = [i.replace("'", "").split("、") for i in name if not pd.isna(i)]
        for i in name_altered:
            if type(i) == list:
                for j in i:
                    rank_dict[j] = rank
            else:
                rank_dict[i] = rank
    return rank_dict


def remove_zero_month_rank(dit):
    return {k: v for k, v in dit.items() if v > 0}


def user_pair_with_rank(resume_la, resume_lb, rank_record, start, end):
    results = []
    for eid_a, uid_a, interval_as, interval_ae in resume_la:
        a_rank = remove_zero_month_rank(rank_record[eid_a])
        a_interval_rank = split_interval_by_rank((interval_as, interval_ae), a_rank)
        for eid_b, uid_b, interval_bs, interval_be in resume_lb:
            if uid_a == uid_b:
                continue
            b_rank = remove_zero_month_rank(rank_record[eid_b])
            b_interval_rank = split_interval_by_rank((interval_bs, interval_be), b_rank)
            for i in a_interval_rank:
                for j in b_interval_rank:
                    co_period = coincident_interval(i[0], j[0], min_year=start, max_year=end)
                    if co_period != []:
                        results.append((eid_a, eid_b, i[1], j[1], co_period))
    return results


def split_interval_by_rank(interval, rank):
    """
    # interval : (1993.08,2002.11)
    # rank :  {'正科级': 40, '正处级': 0, '副处级': 72}
    # output : [['1993.08—1996.12', '正科级'], ['1996.12—2002.11', '副处级']]
    """
    results = []
    period_start, period_end = interval
    # t_start = datetime.datetime.strptime(period_start, "%Y.%m")
    # t_end = datetime.datetime.strptime(period_end, "%Y.%m")
    # split_flag = t_start
    split_flag = float(period_start)
    count = 1
    for k, v in rank.items():
        year, month = str(split_flag).split('.')
        month_delta = v + int(month)
        if count == len(rank.keys()) and count > 1:
            month_delta -= 1
        div, mod = divmod(month_delta, 12)
        if mod < 1:
            mod = 12
            div -= 1
        split_flag_cur = int(year) + div + mod * 0.01
        results.append([[format(split_flag, '.2f'), format(split_flag_cur, '.2f')], k])
        split_flag = split_flag_cur
        count += 1
    # print(results)
    return results


def load_tree(tree_path="./octree_temp.pkl"):
    with open(tree_path, 'rb') as f:
        tree = pickle.load(f)
    return tree


