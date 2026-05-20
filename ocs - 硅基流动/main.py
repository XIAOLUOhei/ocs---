import httpx
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 你的硅基流动配置
SILICONFLOW_API_KEY = "sk-qytibunnzsjrpqbpjwffowaqsstrhfwvwoxiwfmucbkcqtnh"  # 替换成你自己的Key
MODEL_NAME = "THUDM/GLM-Z1-9B-0414"
BASE_URL = "https://api.siliconflow.cn/v1"

app = FastAPI(title="本地轨迹AI题库", version="1.0")


@app.get("/query")
async def query(title: str, options: str = "", type: str = ""):
    logger.info(f"收到题目请求: title={title}, options={options}, type={type}")

    # 构建prompt，强制AI只返回选项字母
    prompt = f"""
    题目：{title}
    选项：{options}
    请只回答正确选项的字母（A/B/C/D），不要任何解释、标点或多余文字，只返回一个大写字母。
    """

    try:
        # 调用硅基流动API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()

            # 提取答案并清理（确保只保留字母）
            raw_answer = result["choices"][0]["message"]["content"].strip()
            # 用正则提取字母，避免AI返回多余内容
            import re
            answer = re.search(r"[A-D]", raw_answer.upper()).group()
            logger.info(f"解析到的答案: {answer}")

            # 【关键】严格按照OCS要求的格式返回数据
            return {
                "code": 200,
                "data": {
                    "answer": answer
                }
            }

    except Exception as e:
        logger.error(f"请求失败: {str(e)}", exc_info=True)
        return {
            "code": 500,
            "data": {
                "answer": None
            }
        }


if __name__ == "__main__":
    import uvicorn

    # 确保端口是8000，和OCS配置里的url一致
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
