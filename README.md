# pdf2text

一个将pdf自动转换成text文件的工具，主要支持中文。支持嵌入字体的自动识别和纯图像pdf。

features:
* 转换pdf文件到text
* 对嵌入的字体采用单独识别每个文字的策略
* 使用paddleocr转换纯图像pdf

改进计划：
* 提高文字识别效率
* 实现文本的自动纠错

使用：
* 安装环境
  pip install -r requirements.txt

* 两种使用方式
*  api使用
	python app.py

*  代码使用
   pdf = SmartPdf(pdf_filename)
   text = pdf.extract_text()