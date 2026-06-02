# 🚗 基于Hermes Agent的车载智能维保与故障诊断系统

## 项目简介

本项目实现了一个面向汽修场景的AI Agent系统，基于Hermes-3大模型和Function Calling能力，集成OBD-II故障码查询、维修手册检索和故障推理引擎，实现从故障码读取到维修建议生成的端到端智能诊断流程。

## 核心特性

- **自然语言交互**：技师可用口语描述故障现象，Agent自动理解并调用工具链
- **OBD-II故障码智能解析**：不仅翻译故障码，还进行多码关联分析
- **维修手册RAG检索**：基于向量检索的维修知识库查询
- **故障推理引擎**：综合多个数据源进行根因分析
- **Function Calling**：Hermes-3原生tool_call支持，可靠的工具调用

## 系统架构

```
用户输入(自然语言)
      |
      v
+------------------+
|   Hermes Agent   |  <-- Ollama本地部署
+------------------+
      |
      v (Function Calling)
+-----+-----+-----+
|     |     |     |
v     v     v     v
OBD   维修   故障   费用
查询  手册   推理   估算
工具  RAG   引擎   工具
```

## 环境要求

- Python 3.10+
- Ollama (已安装并运行 hermes3:8b-q4_K_M 模型)
- 8GB+ 显存 (使用量化模型可降至4GB)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置Ollama模型

```bash
# 拉取Hermes-3量化模型
ollama pull hermes3:8b-q4_K_M

# 确认模型可用
ollama list
```

### 3. 修改配置

编辑 `config.yaml` 中的模型地址和参数。

### 4. 运行Agent

```bash
python agent.py
```

## 文件结构

```
car-llm-demo/
├── README.md              # 项目说明文档
├── config.yaml            # Agent配置文件
├── agent.py               # 主Agent程序
├── obd_tools.py           # OBD故障码工具函数
├── prompt_templates.py    # 系统提示词模板
└── requirements.txt       # Python依赖
```

## 使用示例

```
> 车子怠速不稳，有时候会熄火，仪表盘亮了发动机故障灯

🔍 正在分析您描述的故障现象...
🔧 调用工具: search_by_symptom("怠速不稳", "熄火", "发动机故障灯")

诊断结果:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
可能的故障码: P0505 (怠速控制系统故障)
关联故障: P0171 (系统过稀)
严重程度: 中等

建议检查顺序:
1. 检查怠速控制阀是否积碳卡滞
2. 检查进气管路是否漏气
3. 检测MAF传感器读数
4. 检查节气门体清洁度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 大模型 | Hermes-3 8B Q4_K_M | 本地量化部署，支持Function Calling |
| 推理引擎 | Ollama | 本地模型管理与推理服务 |
| Agent框架 | 自研 | 基于Hermes tool_call协议的轻量Agent |
| 知识库 | 本地JSON | OBD故障码数据库(可扩展为向量库) |
| 开发语言 | Python 3.10+ | 异步架构，类型注解 |

## 扩展计划

- [ ] 集成真实OBD-II硬件接口 (ELM327)
- [ ] 接入向量数据库 (Milvus/Chroma) 存储维修手册
- [ ] 添加TTS语音输出，支持免手操作
- [ ] 部署到车载边缘设备 (Jetson/高通8295)
- [ ] 支持多品牌车型的故障码数据库

## 许可证

MIT License

## 作者

刘思思 - liusisi.ai@outlook.com
