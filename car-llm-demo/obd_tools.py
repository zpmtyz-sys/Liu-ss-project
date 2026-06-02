"""
OBD-II故障码工具集

提供故障码查询、症状搜索、维修建议和费用估算等功能。
这些函数通过Agent的Function Calling机制被调用。

作者: 刘思思
"""

from typing import Optional


# ============================================
# OBD-II故障码数据库
# 实际生产环境中应使用数据库存储，此处用字典演示
# ============================================
OBD_DATABASE = {
    "P0171": {
        "code": "P0171",
        "description": "系统过稀 (Bank 1)",
        "category": "燃油系统",
        "severity": "中等",
        "symptoms": ["怠速不稳", "加速无力", "油耗增加", "发动机故障灯亮"],
        "possible_causes": [
            "进气管路漏气（真空管老化、进气歧管垫片损坏）",
            "MAF空气流量传感器脏污或故障",
            "燃油压力不足（油泵衰减、滤清器堵塞）",
            "氧传感器读数偏差",
            "喷油器雾化不良"
        ],
        "repair_steps": [
            "使用烟雾机检测进气系统漏气点",
            "清洗或更换MAF传感器",
            "测量燃油压力（正常值：250-350kPa）",
            "检查前氧传感器波形",
            "清洗喷油器或进行流量测试"
        ],
        "related_codes": ["P0174", "P0300", "P0130"]
    },
    "P0300": {
        "code": "P0300",
        "description": "检测到随机/多缸失火",
        "category": "点火系统",
        "severity": "高",
        "symptoms": ["发动机抖动", "加速顿挫", "动力下降", "排气异味"],
        "possible_causes": [
            "火花塞磨损或间隙异常",
            "点火线圈故障",
            "燃油喷射器堵塞",
            "气缸压缩压力不足",
            "正时链条/皮带跳齿"
        ],
        "repair_steps": [
            "读取冻结帧数据确认失火条件",
            "检查各缸火花塞状态（正常间隙0.8-1.1mm）",
            "逐缸断缸测试定位故障缸",
            "测量点火线圈初/次级电阻",
            "进行气缸压缩测试（正常值：1000-1400kPa）"
        ],
        "related_codes": ["P0301", "P0302", "P0303", "P0304"]
    },
    "P0420": {
        "code": "P0420",
        "description": "催化转化器效率低于阈值 (Bank 1)",
        "category": "排放系统",
        "severity": "中等",
        "symptoms": ["尾气异味", "油耗增加", "动力轻微下降", "年检排放不合格"],
        "possible_causes": [
            "催化器老化失效（超过16万公里）",
            "长期混合气过浓导致催化器中毒",
            "后氧传感器性能下降",
            "排气泄漏导致读数异常",
            "发动机机油消耗过大污染催化器"
        ],
        "repair_steps": [
            "对比前后氧传感器波形（后氧应相对平稳）",
            "检测催化器入口与出口温差（正常差值>50度）",
            "排除排气系统泄漏",
            "检查机油消耗情况",
            "必要时更换催化转化器"
        ],
        "related_codes": ["P0171", "P0172", "P0430"]
    },
    "P0505": {
        "code": "P0505",
        "description": "怠速控制系统故障",
        "category": "进气系统",
        "severity": "中等",
        "symptoms": ["怠速不稳", "怠速过高", "怠速过低", "偶尔熄火"],
        "possible_causes": [
            "怠速控制阀（IACV）积碳卡滞",
            "节气门体脏污",
            "节气门位置传感器故障",
            "进气系统漏气",
            "ECU怠速学习值异常"
        ],
        "repair_steps": [
            "清洗怠速控制阀和节气门体",
            "检测IACV控制信号（占空比信号）",
            "测量节气门位置传感器电压（怠速时0.45-0.55V）",
            "检查进气管路密封性",
            "执行ECU怠速学习复位程序"
        ],
        "related_codes": ["P0506", "P0507", "P0171"]
    },
    "P0128": {
        "code": "P0128",
        "description": "冷却液恒温器温度低于调节温度",
        "category": "冷却系统",
        "severity": "低",
        "symptoms": ["暖车时间长", "暖风效果差", "油耗略增", "水温表偏低"],
        "possible_causes": [
            "节温器卡在开启位置",
            "冷却液温度传感器读数偏低",
            "冷却液不足或存在气锁",
            "散热风扇持续运转",
            "节温器密封不良"
        ],
        "repair_steps": [
            "检查冷却液液位和状态",
            "观察暖车过程水温变化曲线",
            "测量冷却液温度传感器电阻值（80度时约330欧姆）",
            "检查节温器开启温度（正常82-95度）",
            "必要时更换节温器"
        ],
        "related_codes": ["P0125", "P0115", "P0116"]
    },
    "P0172": {
        "code": "P0172",
        "description": "系统过浓 (Bank 1)",
        "category": "燃油系统",
        "severity": "中等",
        "symptoms": ["油耗明显增加", "排气发黑", "火花塞积碳", "怠速不稳"],
        "possible_causes": [
            "MAF传感器读数偏高",
            "燃油压力过高（调压器故障）",
            "喷油器泄漏（关闭不严）",
            "EVAP碳罐电磁阀常开",
            "冷却液温度传感器读数偏低（ECU误判冷车加浓）"
        ],
        "repair_steps": [
            "读取实时数据流中的燃油修正值",
            "检查MAF传感器读数是否偏高",
            "测量燃油压力和保持压力",
            "检查喷油器密封性（滴漏测试）",
            "检测EVAP系统各电磁阀状态"
        ],
        "related_codes": ["P0171", "P0175", "P0420"]
    }
}

# 维修费用参考（单位：元）
REPAIR_COST_DATABASE = {
    "火花塞更换": {"parts": 120, "labor": 80, "time_hours": 0.5},
    "点火线圈更换": {"parts": 280, "labor": 120, "time_hours": 0.8},
    "MAF传感器清洗": {"parts": 30, "labor": 60, "time_hours": 0.3},
    "MAF传感器更换": {"parts": 450, "labor": 80, "time_hours": 0.5},
    "节气门清洗": {"parts": 40, "labor": 100, "time_hours": 0.5},
    "怠速控制阀清洗": {"parts": 30, "labor": 80, "time_hours": 0.4},
    "氧传感器更换": {"parts": 350, "labor": 120, "time_hours": 0.8},
    "催化器更换": {"parts": 2500, "labor": 300, "time_hours": 2.0},
    "节温器更换": {"parts": 80, "labor": 200, "time_hours": 1.5},
    "喷油器清洗": {"parts": 60, "labor": 150, "time_hours": 1.0},
    "进气管路检修": {"parts": 50, "labor": 100, "time_hours": 0.8},
}


class OBDToolkit:
    """
    OBD-II诊断工具集

    提供给Agent的Function Calling工具函数集合。
    每个方法对应一个可被LLM调用的工具。
    """

    def lookup_obd_code(self, code: str) -> dict:
        """
        查询OBD-II故障码详细信息

        参数:
            code: OBD-II故障码（如"P0171"）

        返回:
            故障码详细信息字典
        """
        code = code.upper().strip()

        if code in OBD_DATABASE:
            return {
                "status": "found",
                "data": OBD_DATABASE[code]
            }
        else:
            # 尝试模糊匹配
            prefix = code[:2]
            suggestions = [k for k in OBD_DATABASE if k.startswith(prefix)]
            return {
                "status": "not_found",
                "message": f"未找到故障码 {code}",
                "suggestions": suggestions if suggestions else "无相近故障码"
            }

    def search_by_symptom(self, *symptoms: str) -> dict:
        """
        根据故障症状搜索可能的故障码

        参数:
            symptoms: 一个或多个症状描述关键词

        返回:
            匹配的故障码列表及匹配度
        """
        results = []

        for code, info in OBD_DATABASE.items():
            match_count = 0
            matched_symptoms = []

            for symptom in symptoms:
                for db_symptom in info["symptoms"]:
                    if symptom in db_symptom or db_symptom in symptom:
                        match_count += 1
                        matched_symptoms.append(db_symptom)
                        break

            if match_count > 0:
                results.append({
                    "code": code,
                    "description": info["description"],
                    "severity": info["severity"],
                    "match_score": match_count / len(symptoms),
                    "matched_symptoms": matched_symptoms
                })

        # 按匹配度排序
        results.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "status": "success",
            "query_symptoms": list(symptoms),
            "results": results[:5],  # 返回前5个最匹配的结果
            "total_matches": len(results)
        }

    def get_repair_suggestion(self, code: str) -> dict:
        """
        获取故障码对应的维修建议

        参数:
            code: OBD-II故障码

        返回:
            维修步骤和建议
        """
        code = code.upper().strip()

        if code not in OBD_DATABASE:
            return {"status": "error", "message": f"未找到故障码 {code} 的维修信息"}

        info = OBD_DATABASE[code]
        return {
            "status": "success",
            "code": code,
            "description": info["description"],
            "severity": info["severity"],
            "possible_causes": info["possible_causes"],
            "repair_steps": info["repair_steps"],
            "note": "建议按照列出的顺序逐步检查，从简单低成本项目开始排除"
        }

    def estimate_repair_cost(self, repair_item: str) -> dict:
        """
        估算维修费用

        参数:
            repair_item: 维修项目名称（如"火花塞更换"）

        返回:
            费用明细
        """
        # 精确匹配
        if repair_item in REPAIR_COST_DATABASE:
            cost = REPAIR_COST_DATABASE[repair_item]
            total = cost["parts"] + cost["labor"]
            return {
                "status": "success",
                "item": repair_item,
                "parts_cost": f"{cost['parts']}元",
                "labor_cost": f"{cost['labor']}元",
                "total_cost": f"{total}元",
                "estimated_time": f"{cost['time_hours']}小时",
                "note": "价格为参考值，实际费用因地区和车型有所不同"
            }

        # 模糊匹配
        matches = [k for k in REPAIR_COST_DATABASE if repair_item in k or k in repair_item]
        if matches:
            return {
                "status": "partial_match",
                "message": f"未精确匹配到 '{repair_item}'",
                "similar_items": matches
            }

        return {
            "status": "not_found",
            "message": f"暂无 '{repair_item}' 的费用参考数据",
            "available_items": list(REPAIR_COST_DATABASE.keys())
        }

    def analyze_related_codes(self, codes: list[str]) -> dict:
        """
        分析多个故障码之间的关联性

        参数:
            codes: 故障码列表

        返回:
            关联分析结果
        """
        codes = [c.upper().strip() for c in codes]
        found_codes = {c: OBD_DATABASE[c] for c in codes if c in OBD_DATABASE}
        not_found = [c for c in codes if c not in OBD_DATABASE]

        if not found_codes:
            return {"status": "error", "message": "未找到任何有效故障码"}

        # 分析关联性
        all_categories = set()
        all_causes = []
        common_symptoms = []

        for code, info in found_codes.items():
            all_categories.add(info["category"])
            all_causes.extend(info["possible_causes"])

        # 查找共同原因（出现在多个故障码中的原因关键词）
        cause_keywords = {}
        for cause in all_causes:
            for keyword in ["MAF", "漏气", "传感器", "燃油", "点火", "催化"]:
                if keyword in cause:
                    cause_keywords[keyword] = cause_keywords.get(keyword, 0) + 1

        # 找出高频关联原因
        common_causes = [k for k, v in cause_keywords.items() if v >= 2]

        # 确定建议维修优先级
        severity_order = {"高": 1, "中等": 2, "低": 3}
        priority_codes = sorted(
            found_codes.items(),
            key=lambda x: severity_order.get(x[1]["severity"], 4)
        )

        return {
            "status": "success",
            "analyzed_codes": list(found_codes.keys()),
            "not_found_codes": not_found,
            "involved_systems": list(all_categories),
            "common_root_causes": common_causes if common_causes else ["未发现明显关联原因"],
            "repair_priority": [
                {"code": code, "description": info["description"], "severity": info["severity"]}
                for code, info in priority_codes
            ],
            "analysis_note": "多个故障码同时出现时，应优先排查共同原因，避免重复维修"
        }
