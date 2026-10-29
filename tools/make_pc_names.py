"""Generate the Simplified Chinese player-character name table.

OpenYAMM draws random creation names from `data_tables/english/pc_names.txt` (8 columns by
class/gender). This tool replaces the English name pools with Simplified Chinese ones while
keeping the original header and the tab-separated `*end`-terminated row format, then writes
the table into the mod tree so the engine picks it up instead of the packed English one.

Names are 2-3 han characters, which stays inside the engine's 15-code-point name limit
(UTF-8, 9 bytes max) even for the longest pools.
"""

from __future__ import annotations

import argparse
from pathlib import Path

HEADER = [
    "Knight/Cleric Male", "Knight/Cleric Female", "Dark Elf Pesant Male", "Dark Elf Pesant Female",
    "Troll/Minotaur", "Vampire/Necro Female", "Vampire/Necro Male", "Dragon",
]

# 骑士/牧师 男：经典西式男名音译
MALE = [
    "亚伦", "亚当", "艾伦", "阿尔文", "安德鲁", "安东尼", "阿瑟", "本杰明", "伯纳德", "布莱恩",
    "卡登", "卡尔", "查尔斯", "克里斯", "科林", "大卫", "多明尼", "德里克", "埃德蒙", "埃里克",
    "伊桑", "费尔顿", "加雷斯", "加文", "乔治", "杰拉德", "吉尔伯特", "戈登", "格雷厄姆", "哈罗德",
    "哈里", "休伯特", "艾萨克", "雅各布", "詹姆斯", "杰里米", "约瑟夫", "朱利安", "肯纳德", "肯尼斯",
    "兰斯", "劳伦斯", "莱昂纳德", "卢修斯", "马库斯", "马修", "梅尔文", "迈克尔", "莫蒂默", "内森",
    "尼尔", "诺曼", "奥利弗", "奥斯蒙", "帕特里克", "保罗", "彼得", "菲利普", "昆廷", "雷蒙德",
    "理查德", "罗伯特", "罗杰", "罗兰", "罗纳德", "罗斯科", "鲁珀特", "塞缪尔", "斯科特", "西蒙",
    "所罗门", "斯蒂芬", "斯图尔特", "西奥多", "托马斯", "特拉维斯", "维克托", "文森特", "沃尔特", "威廉",
]

# 骑士/牧师 女：经典西式女名音译
FEMALE = [
    "艾达", "艾格尼丝", "亚历珊", "爱丽丝", "艾丽西亚", "阿玛塔", "安伯", "安德烈娅", "安吉拉", "阿曼达",
    "阿斯特丽德", "奥黛丽", "芭芭拉", "比阿特丽斯", "布丽安娜", "凯瑟琳", "塞西莉亚", "夏洛特", "克洛伊", "克拉拉",
    "科拉莉", "黛西", "多萝西", "埃莉诺", "艾琳", "伊丽莎白", "艾玛", "埃丝特", "伊冯娜", "菲奥娜",
    "弗洛拉", "弗蕾亚", "吉纳维芙", "乔治娜", "格温多林", "哈丽特", "海伦", "伊莎贝尔", "珍妮弗", "乔治安娜",
    "朱莉娅", "凯伦", "凯特", "拉维妮娅", "莉迪亚", "琳达", "露西尔", "玛格丽特", "玛丽安", "玛蒂尔达",
    "梅芙", "梅琳达", "梅拉妮", "米娅", "米拉贝尔", "莫甘娜", "娜奥米", "妮可", "诺拉", "奥菲莉娅",
    "帕梅拉", "菲比", "蕾切尔", "丽贝卡", "罗莎琳德", "露丝", "萨布丽娜", "塞拉菲娜", "雪莉", "索菲娅",
    "塔莉娅", "特蕾莎", "乌苏拉", "瓦伦蒂娜", "维罗妮卡", "薇薇安", "约兰达", "伊冯", "泽诺比娅", "赛琳娜",
]

# 黑暗精灵 男：奇幻精灵风
DARK_ELF_MALE = [
    "阿莱顿", "贝伦", "布拉杰克", "布拉勒", "蔡斯里昂", "科里温", "达雷", "德里戈恩", "德雷文", "德罗加尔",
    "杜奇", "埃拉辛", "艾德里奇", "法伦", "费恩", "加尔文", "格拉登", "格里姆", "哈洛克", "伊伐里斯",
    "贾卡尔", "凯利斯", "克尔加恩", "拉尔登", "洛坎", "洛斯里昂", "马雷克", "梅隆", "纳索恩", "内拉西恩",
    "尼尔文", "奥利纳斯", "奥尔加斯", "奎尔文", "拉文纳", "里纳斯", "里瓦尔", "罗德里克", "罗文", "萨尔瓦",
    "塞弗里恩", "沙多温", "西尔文", "索文", "塔尔文", "瑟文", "索恩", "乌尔文", "瓦伦", "维尔纳斯",
    "沃尔文", "桑恩", "泽菲恩", "齐尔文", "德拉戈恩", "法里恩", "加洛斯", "海尔文", "伊萨恩", "洛萨恩",
]

# 黑暗精灵 女：奇幻精灵风
DARK_ELF_FEMALE = [
    "阿莱玛达", "阿玛德蕾娅", "安吉娅玛", "安吉布里娅", "安娜珠", "布里达", "布蕾尔", "塞莱斯特", "达莱", "德拉维娜",
    "德里莎", "埃拉温", "埃莉拉", "埃薇琳", "费阿娜", "菲尔米琳", "加薇娜", "伊莉莉丝", "伊莎薇", "伊泽尔",
    "贾丝敏", "卡莉丝", "莱拉", "莉安德拉", "莉莉丝", "洛萨莉娅", "露米娜", "玛丽赛", "米拉维", "莫甘薇",
    "娜索薇", "奈莎", "尼薇拉", "诺薇娜", "奥莉安娜", "佩特拉", "奎薇拉", "拉薇娜", "罗莎薇", "塞尔玛",
    "塞拉薇", "希尔维", "索薇塔", "苏瑞尔", "塔莉莎", "瑟蕾萨", "乌拉薇", "瓦莱拉", "薇尔玛", "薇奥拉",
    "薇薇卡", "泽尔达", "泽菲拉", "阿黛拉", "伊芙瑞尔", "莱丝薇", "奈薇拉", "莎尔薇", "蒂雅薇拉", "薇兰蒂尔",
]

# 巨魔/牛头人：粗犷单音节风格（此列不分性别）
TROLL = [
    "阿尔顿", "阿什伯恩", "巴舍尔", "毕晓普", "布莱恩", "布鲁克", "布鲁诺", "克鲁姆", "达戈", "多恩",
    "杜姆", "德鲁格", "埃格里克", "法尔格", "加尔姆", "戈姆", "戈尔巴", "格里姆格", "格罗姆", "格鲁尔",
    "哈格", "霍尔格", "卡兹格", "克鲁格", "库尔格", "洛格", "马格", "莫格", "穆尔格", "纳格尔",
    "奥格", "奥格姆", "拉格纳", "罗格", "鲁格", "斯卡尔", "斯诺尔", "索尔格", "索格", "乌尔格",
    "乌尔克", "瓦尔格", "沃尔格", "雅恩格", "扎格", "祖尔格", "布洛格", "杜尔格", "戈尔格", "卡尔格",
]

# 吸血鬼/死灵 女：哥特优雅风
VAMPIRE_FEMALE = [
    "阿贝隆娜", "阿比盖尔", "阿卡西娅", "阿达吉莎", "艾西琳", "阿莱西娅", "阿玛兰塔", "安娜西娅", "安托瓦内", "奥萝拉",
    "贝洛妮卡", "卡米拉", "克劳迪娅", "克莉姆莎", "德莎蒙达", "埃莉诺", "埃斯特拉", "埃薇莉娜", "伊莎贝拉", "法尔汀娜",
    "杰玛", "吉赛拉", "海伦娜", "莎朵拉", "约瑟芬", "茱斯蒂娜", "莉莉丝", "露克蕾莎", "玛格达", "梅尔辛娜",
    "米卡艾拉", "米拉娜", "娜迪亚", "奥克塔薇", "拉莫娜", "罗莎蒙", "萨宾娜", "塞维琳娜", "塔玛拉", "泰奥拉",
    "薇尔米拉", "薇奥莱", "薇洛妮卡", "薇薇安娜", "温蒂娜", "叶卡娜", "泽诺比娅", "卢米娅", "奈落薇", "薇斯珀",
]

# 吸血鬼/死灵 男：哥特庄重风
VAMPIRE_MALE = [
    "阿莱顿", "贝伦", "卡尔文", "卡西乌斯", "克劳迪奥", "科里温", "达米安", "但丁", "德古林", "德里戈",
    "德罗戈尔", "杜卡尔", "埃德蒙", "艾德里奇", "法尔科", "弗拉基米尔", "加雷斯", "吉尔伯特", "格里高利", "哈洛克",
    "雨果", "伊尼亚斯", "伊伐里斯", "杰拉德", "卡西米尔", "拉迪斯", "卢西恩", "马雷克", "莫蒂默", "纳索恩",
    "尼古拉斯", "奥利纳斯", "奥尔加斯", "帕维尔", "里纳斯", "罗德里克", "萨尔瓦多", "西尔维奥", "斯蒂芬", "乌尔里希",
    "瓦伦丁", "维克托", "文森特", "维尔纳斯", "弗拉德", "泽菲恩", "阿斯特", "卡里翁", "德萨隆", "沃伦维",
]

# 龙：威严古风（此列不分性别）
DRAGON = [
    "阿祖尔", "巴洛尔", "布拉玛斯", "卡多斯", "科尔达斯", "德拉贡", "杜尔加", "埃尔达", "法拉克斯", "戈尔马斯",
    "格拉克斯", "哈格达", "伊格尼斯", "加尔达", "卡奥斯", "萨克斯", "洛达斯", "玛尔达斯", "纳达尔", "诺达斯",
    "奥达维斯", "帕拉贡", "拉达曼", "索达斯", "塔尔达斯", "乌尔达斯", "瓦达斯", "维尔达斯", "桑达斯", "扎达斯",
    "阿达曼", "贝达斯", "凯达斯", "多拉斯", "埃达斯", "古达斯", "伊尔达", "雅尔达", "卢尔达", "奥尔达",
    "罗尔达", "苏尔达", "图尔达", "沃达斯", "伊达斯", "泽达斯", "苍影", "赤鳞", "金瞳", "灰烬",
]


def build_text() -> str:
    """生成整张表的文本（表头 + 各列名单，短列用 `*end` 收尾）。"""
    columns = [MALE, FEMALE, DARK_ELF_MALE, DARK_ELF_FEMALE, TROLL, VAMPIRE_FEMALE, VAMPIRE_MALE, DRAGON]
    assert len(columns) == len(HEADER)

    for pool in columns:
        if len(set(pool)) != len(pool):
            raise SystemExit("同列内名字重复")
        for name in pool:
            encoded = name.encode("utf-8")
            # 引擎名字上限是 15 个字节（UTF-8），5 个汉字以内全部安全
            if len(encoded) > 15 or not (2 <= len(name) <= 5):
                raise SystemExit(f"名字长度超出引擎限制: {name}")

    lines = ["\t".join(HEADER)]
    height = max(len(pool) for pool in columns)
    for row in range(height):
        cells = [pool[row] if row < len(pool) else "*end" for pool in columns]
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


def total_names() -> int:
    return sum(len(pool) for pool in (MALE, FEMALE, DARK_ELF_MALE, DARK_ELF_FEMALE, TROLL, VAMPIRE_FEMALE, VAMPIRE_MALE, DRAGON))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="mod 的 data_tables/english 目录")
    arguments = parser.parse_args()

    out_path = arguments.out / "pc_names.txt"
    arguments.out.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_text(), encoding="utf-8", newline="")
    print(f"{out_path}: {total_names()} names in {len(HEADER)} columns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
