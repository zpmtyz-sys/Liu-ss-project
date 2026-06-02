"""
车载智能维保与故障诊断Agent

基于Hermes-3大模型的Function Calling能力，实现OBD故障码查询、
维修手册检索和故障推理的端到端智能诊断系统。

作者: 刘思思
邮箱: liusisi.ai@outlook.com
"""

import json
import re
import logging
from typing import Optional

import yaml
import requests

from obd_tools import OBDToolkit
from prompt_templates import SYSTEM_PROMPT, TOOL_DEFINITIONS, format_tool_result

# ============================================
# 日志配置
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CarAgent")


class CarDiagnosticAgent:
    """
    车载智能诊断Agent

    核心功能:
    1. 接收用户自然语言描述的故障现象
    2. 通过Function Calling调用诊断工具
    3. 综合多个工具返回结果进行推理
    4. 生成结构化的诊断报告和维修建议
    """

    def __init__(self, config_path: str = "config.yaml"):
        """初始化Agent，加载配置和工具"""
        # 加载配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # 初始化Ollama连接参数
        self.base_url = self.config["ollama"]["base_url"]
        self.model = self.config["ollama"]["model"]
        self.options = self.config["ollama"]["options"]

        # 初始化工具集
        self.toolkit = OBDToolkit()

        # 对话历史管理
        self.conversation_history: list[dict] = []
        self.max_turns = self.config["agent"]["history"]["max_turns"]
        self.max_tool_calls = self.config["agent"]["max_tool_calls"]

        # 注册可用工具（Function Calling映射表）
        self.available_tools = {
            "lookup_obd_code": self.toolkit.lookup_obd_code,
            "search_by_symptom": self.toolkit.search_by_symptom,
            "get_repair_suggestion": self.toolkit.get_repair_suggestion,
            "estimate_repair_cost": self.toolkit.estimate_repair_cost,
            "analyze_related_codes": self.toolkit.analyze_related_codes,
        }

        logger.info(f"Agent初始化完成 | 模型: {self.model} | 工具数: {len(self.available_tools)}")

    def _call_ollama(self, messages: list[dict]) -> dict:
        """
        调用Ollama API进行推理

        参数:
            messages: 对话消息列表，格式兼容OpenAI Chat API

        返回:
            模型响应字典
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": self.options,
            # Hermes-3 Function Calling需要在此声明可用工具
            "tools": TOOL_DEFINITIONS,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.config["agent"]["timeout"]
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Ollama请求超时")
            return {"message": {"content": "抱歉，模型响应超时，请稍后重试。"}}
        except requests.exceptions.ConnectionError:
            logger.error("无法连接Ollama服务，请确认服务已启动")
            return {"message": {"content": "无法连接模型服务，请检查Ollama是否已启动。"}}

    def _parse_tool_calls(self, response: dict) -> Optional[list[dict]]:
        """
        解析模型响应中的工具调用请求

        Hermes-3的tool_call格式:
        {
            "tool_calls": [
                {
                    "function": {
                        "name": "lookup_obd_code",
                        "arguments": {"code": "P0171"}
                    }
                }
            ]
        }
        """
        message = response.get("message", {})
        tool_calls = message.get("tool_calls")

        if tool_calls:
            return tool_calls

        # 兼容处理：某些情况下tool_call可能嵌入在content中
        content = message.get("content", "")
        if "<tool_call>" in content:
            try:
                # 提取<tool_call>标签内的JSON
                match = re.search(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
                if match:
                    tool_data = json.loads(match.group(1))
                    return [{"function": tool_data}]
            except json.JSONDecodeError:
                logger.warning("解析嵌入式tool_call失败")

        return None

    def _execute_tool(self, tool_call: dict) -> str:
        """
        执行单个工具调用

        参数:
            tool_call: 工具调用描述字典

        返回:
            工具执行结果的字符串表示
        """
        function_info = tool_call.get("function", {})
        func_name = function_info.get("name", "")
        arguments = function_info.get("arguments", {})

        # 如果arguments是字符串，尝试解析为JSON
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return f"参数解析错误: {arguments}"

        logger.info(f"执行工具: {func_name}({arguments})")

        # 查找并执行工具函数
        if func_name in self.available_tools:
            try:
                result = self.available_tools[func_name](**arguments)
                return json.dumps(result, ensure_ascii=False, indent=2)
            except TypeError as e:
                return f"工具参数错误: {str(e)}"
            except Exception as e:
                return f"工具执行异常: {str(e)}"
        else:
            return f"未知工具: {func_name}"

    def chat(self, user_input: str) -> str:
        """
        处理用户输入，执行Agent循环

        Agent循环流程:
        1. 将用户输入加入对话历史
        2. 调用LLM获取响应
        3. 如果LLM请求工具调用，执行工具并将结果返回给LLM
        4. 重复步骤2-3直到LLM给出最终回答
        5. 返回最终回答给用户

        参数:
            user_input: 用户输入的自然语言文本

        返回:
            Agent的最终回答
        """
        # 添加用户消息到历史
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # 构建完整的消息列表（包含系统提示）
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + self.conversation_history

        # Agent循环：允许多次工具调用
        tool_call_count = 0

        while tool_call_count < self.max_tool_calls:
            # 调用LLM
            response = self._call_ollama(messages)
            message = response.get("message", {})

            # 检查是否有工具调用请求
            tool_calls = self._parse_tool_calls(response)

            if tool_calls is None:
                # 没有工具调用，LLM直接给出回答
                final_answer = message.get("content", "抱歉，我无法理解您的问题。")
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                return final_answer

            # 有工具调用，逐个执行
            for tool_call in tool_calls:
                tool_call_count += 1
                func_name = tool_call.get("function", {}).get("name", "unknown")

                # 执行工具
                tool_result = self._execute_tool(tool_call)

                # 将工具调用和结果加入消息历史
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": format_tool_result(func_name, tool_result)
                })

                logger.info(f"工具调用 {tool_call_count}/{self.max_tool_calls}: {func_name}")

        # 超过最大工具调用次数，强制生成回答
        logger.warning("达到最大工具调用次数限制")
        response = self._call_ollama(messages + [
            {"role": "system", "content": "请基于已有信息直接给出诊断结论。"}
        ])
        final_answer = response.get("message", {}).get("content", "诊断信息收集完成，请查看上述工具返回结果。")

        self.conversation_history.append({
            "role": "assistant",
            "content": final_answer
        })
        return final_answer

    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history.clear()
        logger.info("对话历史已重置")


def main():
    """
    主函数：启动交互式诊断Agent

    支持的命令:
    - 输入故障描述进行诊断
    - 输入 /reset 重置对话
    - 输入 /quit 退出程序
    """
    print("=" * 60)
    print("  🚗 车载智能维保与故障诊断系统 v1.0")
    print("  基于 Hermes-3 Agent + Function Calling")
    print("=" * 60)
    print()
    print("  输入故障描述开始诊断，输入 /quit 退出")
    print("  输入 /reset 重置对话历史")
    print()

    # 初始化Agent
    try:
        agent = CarDiagnosticAgent()
    except FileNotFoundError:
        print("错误: 未找到配置文件 config.yaml")
        print("请确认在正确的目录下运行程序")
        return
    except Exception as e:
        print(f"Agent初始化失败: {e}")
        return

    # 交互循环
    while True:
        try:
            user_input = input("\n🔧 请描述故障现象 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("感谢使用，再见！")
            break

        if user_input == "/reset":
            agent.reset_conversation()
            print("对话已重置，请重新描述故障。")
            continue

        # 调用Agent处理
        print("\n🤖 正在分析...")
        response = agent.chat(user_input)
        print(f"\n{response}")


if __name__ == "__main__":
    main()
