import os
import cv2
import numpy as np
import pytesseract as pt

from skimage import io

folder_Video_detection = os.path.dirname(__file__)
folder_WebbApp2 = os.path.dirname(folder_Video_detection)
folder_Project = os.path.dirname(folder_WebbApp2)

# settings
INPUT_WIDTH =  640
INPUT_HEIGHT = 640


# LOAD YOLO MODEL
net = cv2.dnn.readNetFromONNX(f'{folder_WebbApp2}/Model/weights/best.onnx')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def get_detections(img,net):
    # 1.CONVERT IMAGE TO YOLO FORMAT
    image = img.copy()
    row, col, d = image.shape

    max_rc = max(row,col)
    input_image = np.zeros((max_rc,max_rc,3),dtype=np.uint8)
    input_image[0:row,0:col] = image

    # 2. GET PREDICTION FROM YOLO MODEL
    blob = cv2.dnn.blobFromImage(input_image,1/255,(INPUT_WIDTH,INPUT_HEIGHT),swapRB=True,crop=False)
    net.setInput(blob)
    preds = net.forward()
    detections = preds[0]
    # print('Detection', detections)
    # print('InpIma',input_image)

    return input_image, detections

def non_maximum_supression(input_image,detections):

    # 3. FILTER DETECTIONS BASED ON CONFIDENCE AND PROBABILIY SCORE

    # center x, center y, w , h, conf, proba
    boxes = []
    confidences = []
    
    image_w, image_h = input_image.shape[:2]
    x_factor = image_w/INPUT_WIDTH
    y_factor = image_h/INPUT_HEIGHT
    
    confi_rate = 0.4
    nice_rate = False
    for i in range(len(detections)):
        row = detections[i]
        confidence = row[4] # confidence of detecting license plate
        if nice_rate is False:
            while confidence <= confi_rate:
                confi_rate *= 0.9
            nice_rate = True
        if confidence > confi_rate: ###Ban đầu 0.4
            class_score = row[5] # probability score of license plate
            if class_score > 0.25: ###Ban đầu 0.25
                cx, cy , w, h = row[0:4]

                left = int((cx - 0.5*w)*x_factor)
                top = int((cy-0.5*h)*y_factor)
                width = int(w*x_factor)
                height = int(h*y_factor)
                box = np.array([left,top,width,height])

                confidences.append(confidence)
                boxes.append(box)

    # 4.1 CLEAN
    boxes_np = np.array(boxes).tolist()
    confidences_np = np.array(confidences).tolist()

    # 4.2 NMS
    score_threshold = 0.25
    NMS_threshold = 0.45
    while True:
        index = cv2.dnn.NMSBoxes(boxes_np,confidences_np,score_threshold,NMS_threshold) ###0.25, 0.45
        if len(index) == 0:
            score_threshold *= 0.9
        else:
            break
    
    return boxes_np, confidences_np, index

def save_text(filename, text):
    name, ext = os.path.splitext(filename)
    with open('{}\static\predict/{}.txt'.format(folder_WebbApp2, name), mode='w') as f:
        f.write(text)
    f.close()

def apply_brightness_contrast(input_img, brightness=0, contrast=0):

    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow

        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()

    if contrast != 0:
        f = 131*(contrast + 127)/(127*(131-contrast))
        alpha_c = f
        gamma_c = 127*(1-f)

        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf


def drawings(image,boxes_np,confidences_np,index, filename):
    # 5. Drawings
    for ind in index:
        x,y,w,h =  boxes_np[ind]
        
        # bb_conf = confidences_np[ind]
        # conf_text = 'plate: {:.0f}%'.format(bb_conf*100)

        # license_text = extract_text(image,boxes_np[ind])
        # # print("Plate is:" + license_text)
        # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        ymax = y + h
        xmax = x + w
        roi = image[y:ymax, x:xmax]
        
        roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        magic_color = apply_brightness_contrast(gray, brightness=40, contrast=70)
        text = pt.image_to_string(magic_color, lang='eng', config='--psm 6')

        cv2.rectangle(image,(x,y),(x+w,y+h),(0, 255, 0),2) ##Ban đầu màu là: 255, 0 ,255
        # cv2.rectangle(image,(x,y-30),(x+w,y),(255,0,255),-1)
        # cv2.rectangle(image,(x,y+h),(x+w,y+h+25),(0,0,0),-1)

        # cv2.putText(image,conf_text,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),1)
        cv2.putText(image,text,(x,y+h+27),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,0),2)
        
        ##########################
        
    return image
#### -> Trả ra file ảnh sau khi vẽ và vẽ lên hình luôn


# predictions flow with return result
def yolo_predictions(img,net, filename):
    # step-1: detections
    input_image, detections = get_detections(img,net)
    # step-2: NMS
    boxes_np, confidences_np, index = non_maximum_supression(input_image, detections)
    # step-3: Drawings
    image = drawings(img,boxes_np,confidences_np,index, filename)
    return image
    
cap = cv2.VideoCapture(f'{folder_Video_detection}/TEST.mov')

nFrame = 500 # Show nFrame only
cFrame = 0
while cap.isOpened():
    # cv2.namedWindow('YOLO',cv2.WINDOW_KEEPRATIO)
    ret, frame = cap.read()

    if ret == False:
        print('Unable to read video')
        break

    results = yolo_predictions(frame,net, 'a')
    cv2.imshow('Results', results)
    if cv2.waitKey(1) == 27 : ####### Bấm ESC để dừng
        break
    cFrame = cFrame + 1

    # if (cFrame > nFrame):
    #     break
cv2.destroyAllWindows()
cap.release()