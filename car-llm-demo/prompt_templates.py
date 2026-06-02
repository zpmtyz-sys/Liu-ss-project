"""
系统提示词与Prompt模板

定义Agent的系统人格、工具描述和输出格式模板。

作者: 刘思思
"""

# ============================================
# 系统提示词 - 定义Agent的角色和行为规范
# ============================================
SYSTEM_PROMPT = """你是一位经验丰富的汽车故障诊断专家Agent，具备以下能力：

## 身份与专长
- 10年以上汽修实战经验，精通各品牌车型故障诊断
- 熟练掌握OBD-II协议、CAN总线通信、ECU数据分析
- 擅长多故障码关联分析和根因推理

## 工作流程
1. 仔细理解用户描述的故障现象
2. 根据症状判断需要调用哪些诊断工具
3. 综合工具返回的信息进行专业分析
4. 给出结构化的诊断结论和维修建议

## 输出规范
- 使用中文回答
- 诊断结论要有理有据，引用工具返回的数据
- 维修建议按优先级排列，从简单低成本开始
- 如果信息不足，主动询问更多细节（车型、里程、发生条件等）
- 涉及安全问题时务必提醒用户

## 注意事项
- 不要编造不存在的故障码或维修数据
- 如果工具未返回结果，诚实告知而非猜测
- 复杂故障建议用户到专业维修店进一步检测
- 费用估算仅供参考，实际以当地报价为准
"""

# ============================================
# 工具定义 - Hermes-3 Function Calling格式
# ============================================
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_obd_code",
            "description": "查询OBD-II故障码的详细信息，包括故障描述、可能原因和严重程度",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "OBD-II故障码，格式如P0171、P0300等"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_symptom",
            "description": "根据故障症状描述搜索可能对应的故障码，支持多个症状关键词",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "故障症状关键词列表，如['怠速不稳', '油耗增加']"
                    }
                },
                "required": ["symptoms"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_repair_suggestion",
            "description": "获取特定故障码的详细维修步骤和建议",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "OBD-II故障码"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_repair_cost",
            "description": "估算维修项目的费用，包括配件和工时费",
            "parameters": {
                "type": "object",
                "properties": {
                    "repair_item": {
                        "type": "string",
                        "description": "维修项目名称，如'火花塞更换'、'催化器更换'"
                    }
                },
                "required": ["repair_item"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_related_codes",
            "description": "分析多个故障码之间的关联性，找出共同根因",
            "parameters": {
                "type": "object",
                "properties": {
                    "codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要关联分析的故障码列表"
                    }
                },
                "required": ["codes"]
            }
        }
    }
]

# ============================================
# 输出格式模板
# ============================================

# 诊断报告模板
DIAGNOSIS_REPORT_TEMPLATE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔍 故障诊断报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 故障码: {code}
📝 描述: {description}
⚠️  严重程度: {severity}
🏷️  所属系统: {category}

🔧 可能原因 (按可能性排序):
{causes}

📐 建议维修步骤:
{repair_steps}

💰 预估费用: {estimated_cost}
⏱️  预计工时: {estimated_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# 多码关联分析模板
MULTI_CODE_ANALYSIS_TEMPLATE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔗 多码关联分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 分析故障码: {codes}
🏷️  涉及系统: {systems}

🎯 关联性分析:
{analysis}

📋 维修优先级:
{priority}

💡 综合建议:
{suggestion}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def format_tool_result(tool_name: str, result: str) -> str:
    """
    格式化工具执行结果，便于LLM理解

    参数:
        tool_name: 工具函数名
        result: 工具返回的JSON字符串

    返回:
        格式化后的结果文本
    """
    return f"[工具 {tool_name} 返回结果]\n{result}"


def build_diagnosis_prompt(symptoms: list[str], vehicle_info: dict = None) -> str:
    """
    构建诊断请求的Prompt

    参数:
        symptoms: 症状列表
        vehicle_info: 车辆信息（可选）

    返回:
        构建好的用户Prompt
    """
    prompt_parts = []

    if vehicle_info:
        prompt_parts.append(
            f"车辆信息: {vehicle_info.get('brand', '未知')} "
            f"{vehicle_info.get('model', '')} "
            f"{vehicle_info.get('year', '')}年款 "
            f"里程{vehicle_info.get('mileage', '未知')}公里"
        )

    prompt_parts.append(f"故障症状: {'、'.join(symptoms)}")
    prompt_parts.append("请帮我诊断可能的故障原因并给出维修建议。")

    return "\n".join(prompt_parts)
