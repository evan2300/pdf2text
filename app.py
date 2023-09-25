import os
import random
import shutil
import string
import traceback
from typing import Generic, TypeVar
from typing import Optional

import uvicorn
from fastapi import FastAPI, UploadFile, File, Query, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from pydantic import Field
from pydantic.generics import GenericModel

from config import *
from smart_pdf import SmartPdf

app = FastAPI(
    title="文件转换接口文档",
    version="0.0.1",
    description="pdf文件转换接口文档",
    docs_url="/converter/docs",
    openapi_url="/converter/openapi.json",
)


DataType = TypeVar("DataType", bound=BaseModel)


class BaseResponse(GenericModel, Generic[DataType]):
    code: int = Field(0, description="成功时返回0，失败时返回非0数值", examples=[0])
    message: Optional[str] = Field(None, description="成功时返回ok，失败时返回错误原因", examples=["ok"])
    data: Optional[DataType] = None


class ConvertResult(BaseModel):
    text: str = Field(description="转换后的文本", examples=["pdf文件转换后的文本"])


class ErrorResponse(BaseModel):
    code: int = Field(10001, description="10001 验证错误， 99999 系统错误", examples=[10001])
    message: Optional[str] = Field(None, description="具体错误原因", examples=["必须提供带转换的文件字段"])


def ok(data):
    response_data = {
        "code": 0,
        "message": "ok",
        "data": data
    }

    return response_data


def error(code, message):
    response_data = {
        "code": code,
        "message": message,
    }

    return response_data


def generate_random_filename() -> str:
    """生成一个随机的文件名"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(10))


def save_pdf(file) -> str:
    """保存pdf到文件并返回文件名"""
    filename = "upload/" + generate_random_filename() + ".pdf"
    with open(filename, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return filename


@app.exception_handler(RequestValidationError)  # 重写请求验证异常处理器
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求参数验证异常
    :param request: 请求头信息
    :param exc: 异常对象
    :return:
    """
    # 日志记录异常详细上下文
    print(f"全局异常：{request.method}URL{request.url}Headers:{request.headers}{traceback.format_exc()}")
    error_object = error(10001, str(exec))
    return error_object


@app.post("/converter/api/v1/pdf/text", summary="pdf转换为文本", description="将pdf文件转换为text，支持正常pdf、图像pdf、字体嵌入pdf等",
          tags=["pdf文件转换接口"],
          response_model=BaseResponse[ConvertResult],
          responses={
              200: {"description": "响应成功"},
              422: {"description": "验证错误", "model": ErrorResponse},
              500: {"description": "系统错误", "model": ErrorResponse, "content": {
                  "application/json": {
                      "example": {"code": 99999, "message": "系统故障"}
                  }
                }}})
async def pdf_to_text(file: UploadFile = File(...), detect_zone: bool = Query(False, description="是否进行区域检测"),
                      detect_sections: bool = Query(False, description="是否进行章节检测")):
    print(detect_zone)
    print(detect_sections)
    # 将上传的信息保存到文件

    pdf_filename = save_pdf(file)

    pdf = SmartPdf(pdf_filename)
    text = pdf.extract_text()

    # 删除临时文件
    try:
        os.remove(pdf_filename)
    except:
        print("无法删除：" + pdf_filename)

    convert_result = ConvertResult(text=text, structure_result="")
    response_data = ok(convert_result)
    return response_data


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=server_port)
