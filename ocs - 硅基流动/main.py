from fastapi import FastAPI
import httpx
import uvicorn
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 轨迹流动（硅基流动）信息
SILICONFLOW_API_KEY = "aip-key"
MODEL_NAME = "模型名字"
BASE_URL = "https://api.siliconflow.cn/v1"

# 2. 启动本地服务
app = FastAPI(title="本地轨迹AI题库", version="1.0")


# 3. OCS请求接口
@app.get("/query")
async def query(title: str, options: str = "", type: str = ""):
    logger.info(f"收到题目请求: title={title}, options={options}, type={type}")
    try:
        # 拼接题目
        prompt = f"""
        题目：{title}
        选项：{options}
        你现在是一个严格的答题助手，只需要返回正确答案的选项字母（A/B/C/D），
        不要任何解释、不要多余文字、不要标点符号，只返回一个字母。
        """

        # 调用轨迹流动AI（修复：超时改成30秒）
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url=f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 10
                }
            )

        response.raise_for_status()
        res_json = response.json()
        logger.info(f"轨迹流动返回: {res_json}")

        answer = res_json["choices"][0]["message"]["content"].strip()
        logger.info(f"解析到的答案: {answer}")

        return {
            "code": 200,
            "data": {
                "answer": answer,
                "question": title,
                "ai": True
            }
        }

    except httpx.ConnectError:
        logger.error("无法连接到硅基流动API，请检查网络或代理设置")
        return {"code": 500, "msg": "无法连接到AI服务"}
    except httpx.ReadTimeout:
        logger.error("请求超时，硅基流动API响应过慢")
        return {"code": 500, "msg": "请求超时，请稍后重试"}
    except Exception as e:
        logger.error(f"处理请求出错: {str(e)}", exc_info=True)
        return {"code": 500, "msg": f"错误：{str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)