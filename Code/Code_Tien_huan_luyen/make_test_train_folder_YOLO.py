import os
import pandas as pd
import xml.etree.ElementTree as xet
import shutil

from glob import glob
from shutil import copy


#Dẫn đến thư mục chứa thư mục DataSet của chúng ta:
"""Cách 1: Dùng khi tải tập tin về máy, chỉnh sửa lại sao cho phù hợp"""
# folder_Code = os.path.dirname(__file__)
# folder_Project = os.path.dirname(folder_Code)

"""Cách 2: Dùng khi chạy đoạn mã trên GG Colab, chỉnh sửa đường dẫn lại cho phù hợp"""
folder_Project = '/content/drive/MyDrive/Project'
from google.colab import drive
drive.mount('/content/drive', force_remount=True)

#Sử dụng file labels.csv đã được tạo trong quá trình train model Inception-ResNet
df = pd.read_csv(f'{folder_Project}/labels.csv')

# parsing
def parsing(path):
    parser = xet.parse(path).getroot()
    name = parser.find('filename').text
    filename = f'{folder_Project}/DataSet/images/{name}'

    # width and height
    parser_size = parser.find('size')
    width = int(parser_size.find('width').text)
    height = int(parser_size.find('height').text)

    return filename, width, height
df[['filename','width','height']] = df['filepath'].apply(parsing).apply(pd.Series)

# center_x, center_y, width , height
df['center_x'] = (df['xmax'] + df['xmin'])/(2*df['width'])
df['center_y'] = (df['ymax'] + df['ymin'])/(2*df['height'])

df['bb_width'] = (df['xmax'] - df['xmin'])/df['width']
df['bb_height'] = (df['ymax'] - df['ymin'])/df['height']


###Đoạn code trên giúp tiền xử lí dữ liệu
###Sau khi chạy xong trên GG Colab thì cần chạy các câu lệnh sau:
"""----------------------------------------"""
#!git clone https://github.com/ultralytics/yolov5
"""----------------------------------------"""
#!pip install -qr ./yolov5/requirements.txt comet_ml
"""----------------------------------------"""
#mkdir yolov5/data_images/
"""----------------------------------------"""
#mkdir yolov5/data_images/test/
"""----------------------------------------"""
#mkdir yolov5/data_images/train/
"""----------------------------------------"""
#Tiếp tục chạy đoạn code phía dưới trên GG Colab



### split the data into train and test
df_train = df.iloc[:2000]
df_test = df.iloc[2000:]
#Vì DataSet của chúng ta có 2500 ảnh nên khi chia 80:20 sẽ là 2000 ảnh: 500 ảnh

############

train_folder = 'yolov5/data_images/train'
values = df_train[['filename','center_x','center_y','bb_width','bb_height']].values
for fname, x,y, w, h in values:
    image_name = os.path.split(fname)[-1]
    txt_name = os.path.splitext(image_name)[0]

    dst_image_path = os.path.join(train_folder,image_name)
    dst_label_file = os.path.join(train_folder,txt_name+'.txt')
    print(fname)
    print(dst_image_path)
    # copy each image into the folder
    shutil.copy(fname,dst_image_path)

    # generate .txt which has label info
    label_txt = f'0 {x} {y} {w} {h}'
    with open(dst_label_file,mode='w') as f:
        f.write(label_txt)

        f.close()


test_folder = 'yolov5/data_images/test'
values = df_test[['filename','center_x','center_y','bb_width','bb_height']].values
for fname, x,y, w, h in values:
    image_name = os.path.split(fname)[-1]
    txt_name = os.path.splitext(image_name)[0]

    dst_image_path = os.path.join(test_folder,image_name)
    dst_label_file = os.path.join(test_folder,txt_name+'.txt')

    # copy each image into the folder
    copy(fname,dst_image_path)

    # generate .txt which has label info
    label_txt = f'0 {x} {y} {w} {h}'
    with open(dst_label_file,mode='w') as f:
        f.write(label_txt)

        f.close()
        
###Sau khi chạy xong code chia folder thì tiếp tục chạy các câu lệnh trong GG Colab:
"""----------------------------------------"""
#!python ./yolov5/train.py --data /content/drive/MyDrive/Project/data.yaml --cfg ./yolov5/models/yolov5s.yaml --batch-size 8 --name Model --epochs 5
"""----------------------------------------"""
#!python ./yolov5/export.py --weight ./yolov5/runs/train/Model/weights/best.pt --include torchscript onnx
"""----------------------------------------"""
"""----------------------------------------"""
#Lúc này tệp huấn luyện đã được lưu lại trên folder clone GitHub, bạn có thể tải về máy bằng cách thực hiện tiếp:
"""----------------------------------------"""
#!ls /content/yolov5/runs    -> Đi đến thư mục 'runs' chứa các dữ liệu sau khi train.
"""----------------------------------------"""
#!zip -r runs.zip /runs     -> Nén các thư mục lại vào file runs.zip
"""----------------------------------------"""
#from google.colab import files
#files.download('/content/runs.zip')    -> Tải tệp runs.zip về máy