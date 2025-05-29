import cv2
import numpy as np

def detect_cracks(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blurred, 50, 150)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=40, maxLineGap=30)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y2 - y1) < 20 and abs(x2 - x1) > 30:
                cv2.line(edges, (x1, y1), (x2, y2), 0, 6) 

    kernel_close = np.ones((7,7), np.uint8)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_close)

    kernel = np.ones((3,3), np.uint8)
    dilated = cv2.dilate(closed, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)   
    height, width = image.shape[:2]
    filtered_contours = []
    print("裂缝边界框坐标（起点 -> 终点）:")
    for idx, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        length = cv2.arcLength(cnt, False)
        if area < 350 or length < 200:
            continue 
        x, y, w, h = cv2.boundingRect(cnt)
        if x < 30 or y < 40 or (x + w) > (width - 40) or (y + h) > (height - 30):
            continue
        if len(cnt) >= 5:
            rect = cv2.minAreaRect(cnt)
            angle = rect[2]
            if angle < -45:
                angle = angle + 90
            if not (-5 <= angle <= 5):
                filtered_contours.append(cnt)
                # 输出边界框的起点和终点
                start_point = (x, y)
                end_point = (x + w, y + h)
                print(f"裂缝 {idx}: 起点 {start_point} -> 终点 {end_point}")
        else:
            filtered_contours.append(cnt)
            # 输出边界框的起点和终点
            start_point = (x, y)
            end_point = (x + w, y + h)
            print(f"裂缝 {idx}: 起点 {start_point} -> 终点 {end_point}") 
    
    result = image.copy()
    cv2.drawContours(result, filtered_contours, -1, (0, 255, 0), 2)

    output_path = 'detected_cracks.jpg'
    cv2.imwrite(output_path, result)
    print(f"结果已保存至: {output_path}")

if __name__ == "__main__":
    image_path = r".\images\1.jpg"
    detect_cracks(image_path)