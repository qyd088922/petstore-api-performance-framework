# 无头模式运行：功能测试 + 性能压测
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 默认执行一键编排的功能测试与报告汇总；压测通过 CI 覆盖 CMD
CMD ["python", "run_all.py", "func"]
