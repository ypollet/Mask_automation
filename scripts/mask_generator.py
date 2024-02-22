import numpy as np
import glob
import matplotlib.pyplot as plt
import cv2 as cv
import os

import torch
from segment_anything import SamPredictor, sam_model_registry

class MaskGenerator():
    def __init__(self, blur : int, morpho : int):
        self.blur = blur
        self.morpho = morpho

    def remove_noise(self, img):

        img = cv.morphologyEx(img, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_ELLIPSE, (self.morpho, self.morpho)))
        img = cv.morphologyEx(img, cv.MORPH_OPEN, cv.getStructuringElement(cv.MORPH_ELLIPSE, (self.morpho, self.morpho)))

        return img
    
    def prepare_image(self, img_path):
        img = cv.imread(img_path)
        # Convert to graycsale
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Blur the image for better edge detection
        img = cv.GaussianBlur(img, (self.blur, self.blur), 0) 

        return img
    
    def findSignificantContour(self, edgeImg):
        try:
            image, contours, hierarchy = cv.findContours(
                edgeImg,
                cv.RETR_TREE,
                cv.CHAIN_APPROX_SIMPLE)
        except ValueError:
            contours, hierarchy = cv.findContours(
                edgeImg,
                cv.RETR_TREE,
                cv.CHAIN_APPROX_SIMPLE)
        # Find level 1 contours (i.e. largest contours)
        level1Meta = []
        for contourIndex, tupl in enumerate(hierarchy[0]):
            # Each array is in format (Next, Prev, First child, Parent)
            # Filter the ones without parent
            if tupl[3] == -1:
                tupl = np.insert(tupl.copy(), 0, [contourIndex])
                level1Meta.append(tupl)
                #  # From among them, find the contours with large surface area.
        contoursWithArea = []
        for tupl in level1Meta:
            contourIndex = tupl[0]
            contour = contours[contourIndex]
            area = cv.contourArea(contour)
            contoursWithArea.append([contour, area, contourIndex])

    
        contoursWithArea.sort(key=lambda meta: meta[1], reverse=True)
        largestContour = contoursWithArea[0][0]
        return largestContour
    
    def generate_mask(self, img_path) -> np.ndarray:
        pass

class CannyGenerator(MaskGenerator):
    def __init__(self, thresh_min : int, thresh_max : int, blur : int, morpho : int, floodfill : bool, draw_contour : bool):
        super(CannyGenerator, self).__init__(blur, morpho)
        self.thresh_min = thresh_min
        self.thresh_max = thresh_max
        self.floodfill = floodfill
        self.draw_contour = draw_contour
        
    def generate_mask(self, img_path) -> np.ndarray:
        if img_path is None:
            return None
        
        img = self.prepare_image(img_path)

        canny_output = cv.Canny(img, self.thresh_min, self.thresh_max, L2gradient=True)
        result = self.remove_noise(canny_output)

        if self.floodfill:
            # Copy the thresholded image.
            im_floodfill = result.copy()
            
            # Mask used to flood filling.
            # Notice the size needs to be 2 pixels than the image.
            h, w = result.shape[:2]
            mask = np.zeros((h+2, w+2), np.uint8)
            
            # Floodfill from point (0, 0)
            cv.floodFill(im_floodfill, mask, (0,0), 255)

            im_floodfill_inv = cv.bitwise_not(im_floodfill)

            result = result | im_floodfill_inv

        if self.draw_contour:
            big_contour = self.findSignificantContour(result)

            # draw white filled contour on black background
            result = np.zeros_like(img)
            cv.drawContours(result, [big_contour], 0, (255,255,255), cv.FILLED)

        result = cv.dilate(result, (20, 20),iterations = 1)
        return result
    
class ThreshGenerator(MaskGenerator):
    def __init__(self, thresh : int, max_val : int, blur : int, morpho : int, white_background : bool, auto_thresh : bool, floodfill : bool, draw_contour : bool):
        super(ThreshGenerator, self).__init__(blur, morpho)
        self.thresh = thresh
        self.max_val = max_val
        self.white_background = white_background
        self.auto_thresh = auto_thresh
        self.floodfill = floodfill
        self.draw_contour = draw_contour
        
    def generate_mask(self, img_path):
        if img_path is None:
            return None
        
        img = self.prepare_image(img_path)

        flags = cv.THRESH_BINARY_INV if self.white_background else cv.THRESH_BINARY
        if self.auto_thresh :
            flags += cv.THRESH_OTSU
        
        _, th_h = cv.threshold(img,self.thresh, self.max_val, flags)
        result = self.remove_noise(th_h)

        if self.floodfill:

            # Copy the thresholded image.
            im_floodfill = result.copy()
            
            # Mask used to flood filling.
            # Notice the size needs to be 2 pixels than the image.
            h, w = result.shape[:2]
            mask = np.zeros((h+2, w+2), np.uint8)
            
            # Floodfill from point (0, 0)
            cv.floodFill(im_floodfill, mask, (0,0), 255)

            im_floodfill_inv = cv.bitwise_not(im_floodfill)

            result = result | im_floodfill_inv
        
        if self.draw_contour:
            big_contour = self.findSignificantContour(result)

            # draw white filled contour on black background
            result = np.zeros_like(img)
            cv.drawContours(result, [big_contour], 0, (255,255,255), cv.FILLED)

        return result

'''# TODO adapt variables
def get_bounding_box(threshold_min, threshold_max, img):

    # Convert to graycsale
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Blur the image for better edge detection
    img_blur = cv.GaussianBlur(img_gray, (3,3), 0) 

    canny_output = cv.Canny(img_blur, threshold_min, threshold_max)
    canny_output = cv.morphologyEx(canny_output, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3)))
    canny_output = cv.morphologyEx(canny_output, cv.MORPH_OPEN, cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3)))
    cv.imwrite(f"../images/test/masks/{os.path.splitext(os.path.basename(image_path))[0]}_canny.jpg", canny_output)

    x,y,w,h = cv.boundingRect(canny_output)
    

    _, th_h = cv.threshold(img_blur,threshold_min,threshold_max ,cv.THRESH_BINARY+cv.THRESH_OTSU)

    cv.imwrite(f"../images/test/masks/{os.path.splitext(os.path.basename(image_path))[0]}_treshold.jpg", th_h)

    largestCountour = findSignificantContour(th_h)

    contour_copy = img.copy()

    cv.drawContours(contour_copy, [largestCountour], 0, (255,0,0), 3, lineType=cv.FILLED)

    cv.imwrite(f"../images/test/masks/{os.path.splitext(os.path.basename(image_path))[0]}_contours.jpg", contour_copy)

    x,y,w,h = cv.boundingRect(largestCountour)
    
    img_copy = img.copy()
    cv.rectangle(img_copy,(x,y),(x+w,y+h),(0,0,255),3)
    cv.imwrite(f"../images/test/masks/{os.path.splitext(os.path.basename(image_path))[0]}_box.jpg", img_copy)
    
    print(f"{x,y,w,h}")
    return np.array([x,y, x+w, y+h])
    '''
        




np.random.seed(12345)

'''CHECKPOINT_PATH = "sam_vit_h_4b8939.pth"
MODEL_TYPE = "vit_h"

DEVICE = torch.device('cuda')

sam = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT_PATH)
sam.to(device=DEVICE)

mask_predictor = SamPredictor(sam)


images = glob.glob("../images/test/*.jpg")
images = sorted(images)
id = 0
for image_path in images:
    print(f"{id} = {image_path}")
    img = cv.imread(image_path)
    image_rgb = cv.cvtColor(img, cv.COLOR_BGRA2RGB)
    
    mask_predictor.set_image(image_rgb)

    max_thresh = 255
    thresh = 50 # initial threshold
    box = get_bounding_box(thresh, thresh*4, img)

    masks, scores, logits = mask_predictor.predict(
        box=box,
        multimask_output=True
    )

    max_score = -1
    ref_mask = None
    for i, (mask, score) in enumerate(zip(masks, scores)):
        if max_score < score:
            ref_mask = mask

    id+=1
    
    mask_image = (ref_mask * 255).astype(np.uint8)  # Convert to uint8 format
    cv.imwrite(f"../images/test/masks/{os.path.basename(image_path)}", mask_image)
'''