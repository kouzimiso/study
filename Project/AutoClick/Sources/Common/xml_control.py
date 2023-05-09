## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import xml.etree.ElementTree as ET
import xmltodict
import dicttoxml
import xml.dom.minidom

def XML_Read(file_path):
    information_dictionary={}
    
    #xmlデータを読み込みます
    tree = ET.parse(file_path)
    root = tree.getroot()
    #一番上の階層の要素を取り出します
    for child1 in root:
        information_dictionary[child1.tag] = child1.text
        print("child1.tag,child1.text")
        print(child1.tag)
        print(child1.text)
        for child2 in child1.iter():
            information_dictionary[child2.tag] = child2.text
            print("child2.tag,child2.text")
            print(child2.tag)
            print(child2.text)
            for child3 in child2:
                print("child3.tag,child3.text")
                print(child3.tag)
                print(child3.text)
                information_dictionary[child3.tag] = child3.attrib
    return information_dictionary

def XML_Write(file_path,xml_document, encoding='utf-8', newl='\n', indent='', addindent='  '):
    file = open(file_path, 'w')
    # エンコーディング、改行、全体のインデント、子要素の追加インデントを設定しつつファイルへ書き出し
    xml_document.writexml(file, encoding='utf-8', newl='\n', indent='', addindent='  ')
    file.close()

def Dictionary_XMLWrite(file_path,information_dictionary):
    root = ET.Element('root')
    tree = ET.ElementTree(element=root)
    
    element_data = ET.SubElement(root, 'Element')
    for key,value in information_dictionary.items():
        element_data_id = ET.SubElement(element_data, 'key')
        element_data_id.text = value
        element_data_id = ET.SubElement(element_data, 'value')
        element_data_id.text = value
    
    tree.write(file_path , encoding='utf-8', xml_declaration=True)

    # 文字列パースを介してminidomへ移す
    print("xml.dom.minidom.parseString")
    xml_document = xml.dom.minidom.parseString(ET.tostring(root, 'utf-8'))
    print("XML_Write")
    XML_Write(file_path,xml_document)


def Dictionary_ToXMLFile(file_path,information_dictionary):
    xml_tree = dicttoxml.dicttoxml(information_dictionary,attr_type=False,root=True)
    print("Dctionary_toXML:" + xml_tree.decode('utf-8'))
    xml_document = xml.dom.minidom.parseString(xml_tree.decode('utf-8'))
    XML_Write(file_path,xml_document)

def XML_ToDictionary(file_path):
    information_dictionary={}
    #xmlデータを読み込みます
    file = open(file_path)
    xml = file.read()
    information_dictionary=xmltodict.parse(xml)
    file.close()
    return information_dictionary

def RecognitionXML_Read(information_dictionary):
    #処理
    self.action = action
    #終了条件
    self.end_condition = end_condition
    #実行回数
    self.execute_number = execute_number
    #再試行回数
    self.retry_number = retry_number
    #終了処理
    self.end_action = end_action
    #クリックする画像を保存するフォルダ
    self.image_path = image_path
    #画像をClickした後の待ち時間(秒)
    self.interval_time = interval_time
    #画像認識のあいまい設定
    self.recognition_confidence = recognition_confidence
    #GrayScale設定(高速化)
    self.recognition_grayscale = recognition_grayscale

def Image_MouseAround(file_path,flag_overwrite=False,wide=0,height=0,dupplicate_format="{}({:0=3}){}"):
    x,y = pyautogui.position()
    
    Image_PointAround(file_path,flag_overwrite,x,y,wide,height,dupplicate_format)

def Image_PointAround(file_path,flag_overwrite=False,x=0,y=0,wide=0,height=0,dupplicate_format="{}({:0=3}){}"):
    if flag_overwrite == False:
        path = Rename.duplicate_rename(file_path,dupplicate_format)
    else:
        path=file_path
    if wide==0 or height==0 :
        PIL.ImageGrab.grab().save(path)
    else:
        bbox_w=wide
        bbox_h=height
        bbox_x=max(0,x - bbox_w/2)
        bbox_y=max(0,y - bbox_h/2)
        PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y,bbox_x + bbox_w , bbox_y + bbox_h)).save(path)
