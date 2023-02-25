from tqdm import tqdm


__all__ = ["tqdm_callback"]

def tqdm_callback(description:str="Processing..."):
    """
    用于作为参数传入exp_parser.refine等函数的callback函数生成函数

    Params:
        description: 用于设置进度条前显示的说明文字
    """
    tqdm_obj=tqdm(desc=description)
    def __cb(c_dict):
        tqdm_obj.desc = c_dict["description"]
        tqdm_obj.total = c_dict["total"]
        tqdm_obj.n = c_dict["iternum"]
        tqdm_obj.display()  # 请用display()来刷新tqdm，这样进度条滚动会很丝滑
    return __cb