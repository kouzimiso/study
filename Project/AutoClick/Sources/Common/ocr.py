import cv2
import pyocr
import pyocr.builders
import PIL

class OCR:
    #Optical Character Recognition(光学的文字認識)
    #tesseract(ocr)のディレクトリ
    pyocr.tesseract.TESSERACT_CMD = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    tool = pyocr.get_available_tools()[0]
    builder=pyocr.builders.TextBuilder(tesseract_layout=6)
    builder.tesseract_configs.append("-c")
    builder.tesseract_configs.append("preserve_interword_spaces=1")

    def Setting_TesseractPath(self,application_path):
        pyocr.tesseract.TESSERACT_CMD=application_path

    def Setting_BuilderText(self,layout=6):
        self.builder=pyocr.builders.TextBuilder(tesseract_layout=layout)

    def Setting_BuilderDigits(self,layout=6):
        self.builder=pyocr.builders.DigitBuilder(tesseract_layout=layout)
        self.builder.tesseract_configs.append("digits")
    
    def Recognition_ByFilePath(self,file_path,language="jpn"):
        image=PIL.Image.open(file_path)
        text=self.Recognition(image,language)
        return text

    def Recognition(self,image,language="jpn"):
        text=self.tool.image_to_string(
                image,
                lang=language,
                builder=self.builder
                )#.replace(".", "")
        return text
