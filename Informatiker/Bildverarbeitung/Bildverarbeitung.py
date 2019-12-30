import os
import numpy as np
import cv2
from numpy.linalg import norm

SZ_PIXEL=20
bin_n = 16 # Number of bins
affine_flags = cv2.WARP_INVERSE_MAP|cv2.INTER_LINEAR

GAUSSIAN_SMOOTH_FILTER_SIZE = (5, 5)
ADAPTIVE_THRESH_BLOCK_SIZE = 9
ADAPTIVE_THRESH_WEIGHT = 9

GAMMA = 2
THRESHOLD_LOW = 25
THRESHOLD_HIGH = 250

pathToSVM = '/home/pi/Group38/Bildverarbeitung/svm_data.dat'

class Bildverarbeitung:
    def __init__(self):
        self.__svm = cv2.ml.SVM_load(pathToSVM)

    ## [deskew]
    ## Ausrichtung des Bildes mit Ziffer, so dass die Ziffer nicht verdreht ist.
    def __deskew(self,img):
        m = cv2.moments(img)
        if abs(m['mu02']) < 1e-2:
            return img.copy()
        skew = m['mu11'] / m['mu02']
        M = np.float32([[1, skew, -0.5 * SZ_PIXEL * skew], [0, 1, 0]])
        img = cv2.warpAffine(img, M, (SZ_PIXEL, SZ_PIXEL), flags=affine_flags)
        return img
    ## [deskew]

    ## [hog]
    ## Feature für die Input-Bilder um ihre Eigenschaften zu beschreiben.
    def __hog(self,img):
        gx = cv2.Sobel(img, cv2.CV_32F, 1, 0)
        gy = cv2.Sobel(img, cv2.CV_32F, 0, 1)
        mag, ang = cv2.cartToPolar(gx, gy)
        bins = np.int32(bin_n * ang / (2 * np.pi))  # quantizing binvalues in (0...16)
        bin_cells = bins[:10, :10], bins[10:, :10], bins[:10, 10:], bins[10:, 10:]
        mag_cells = mag[:10, :10], mag[10:, :10], mag[:10, 10:], mag[10:, 10:]
        hists = [np.bincount(b.ravel(), m.ravel(), bin_n) for b, m in zip(bin_cells, mag_cells)]
        hist = np.hstack(hists)  # hist is a 64 bit vector

        # transform to Hellinger kernel
        eps = 1e-7
        hist /= hist.sum() + eps
        hist = np.sqrt(hist)
        hist /= norm(hist) + eps
        return hist
    ## [hog]

    ## [detectShape]
    ## Mit Hilfe der Konturen wird geschaut, um welche geometrische Form es sich handelt.
    def __detectShape(self, c):
        shape = 'unknown'
        # calculate perimeter using
        peri = cv2.arcLength(c, True)
        # apply contour approximation and store the result in vertices
        vertices = cv2.approxPolyDP(c, 0.04 * peri, True)

        # If the shape it triangle, it will have 3 vertices
        if len(vertices) == 3:
            shape = 'triangle'

        # if the shape has 4 vertices, it is either a square or
        # a rectangle
        elif len(vertices) == 4:
            # using the boundingRect method calculate the width and height
            # of enclosing rectange and then calculte aspect ratio

            x, y, width, height = cv2.boundingRect(vertices)
            aspectRatio = float(width) / height

            # a square will have an aspect ratio that is approximately
            # equal to one, otherwise, the shape is a rectangle
            if aspectRatio >= 0.95 and aspectRatio <= 1.05:
                shape = "square"
            else:
                shape = "rectangle"

        # if the shape is a pentagon, it will have 5 vertices
        elif len(vertices) == 5:
            shape = "pentagon"

        # otherwise, we assume the shape is a circle
        else:
            shape = "circle"

        # return the name of the shape
        return shape
    ## [detectShape]

    ## [predictDigit]
    ## Vom Input-Bild wird mit Hilfe des erstellten SVM-Modells die Ziffer ermitellt.
    ## Input: img --> Bildausschnitt welcher das Signal enthält
    ## Input: x,y,w,h --> Positionen x & y mit Breite w und Höhe h für die genaue Lage des Schilds
    ## Return: Ermittelte
    def __predictDigit(self,img, x, y, w, h, border):
        zahl = img[y+border:y+h-border, x+border:x+w-border]
        thresh = cv2.resize(zahl, (SZ_PIXEL, SZ_PIXEL))

        # When the Background is white, invert the picture
        whitePixelCount = cv2.countNonZero(thresh)
        if whitePixelCount > (SZ_PIXEL*SZ_PIXEL)/2:
            thresh = 255-thresh

        if(np.median(thresh[0])>100):
            return -1
        desk = self.__deskew(thresh)
        hData = self.__hog(desk)
        tData = np.float32(hData).reshape(-1, bin_n * 4)
        return self.__svm.predict(tData)[1]
    ## [predictDigit]

    ## [isStartSignal]
    ## Im Bildausschnitt wird nach blauen Werten gesucht und bestimmt,
    ## ob es sich um das Startsignal handelt.
    ## Input: img --> Bildausschnitt
    ## Return: startsignal --> True falls es sich um das Startsignal handelt
    def isStartSignal(self, img):
        img = np.rot90(img, 3)

        # Konventierung in einen anderen Farbraum und erhöhen des Kontrast des Graubildes
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv_h, hsv_s, hsv_v = cv2.split(hsv)
        imgMaxContrast = self.__getMaxContrast(hsv_v)
        hsv = np.dstack([hsv_h, hsv_s, imgMaxContrast])

        # simple threshold in HSV for blue color
        blue_lower = np.array([80, 60, 0], np.uint8)
        blue_upper = np.array([120, 255, 255], np.uint8)
        thresh = cv2.inRange(hsv, blue_lower, blue_upper)

        # for better separation/combination of blue parts
        struct = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image_open = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, struct)

        # find possibles blue section of start signal
        (_, cnts, _) = cv2.findContours(image_open, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        positions = []
        for c in cnts:
            # compute the moment of contour
            M = cv2.moments(c)
            if (M['m00'] != 0.0):
                # From moment we can calculte area, centroid etc
                # The center or centroid can be calculated as follows
                cX = int(M['m10'] / M['m00'])
                cY = int(M['m01'] / M['m00'])

                if (M['m00'] > 10 and M['m00'] < 50 and (shape == 'rectangle' or shape == 'square')):
                    positions.append((cX, cY))

        if(np.size(positions) == 0):
            return False

        positions = np.sort(positions, axis=0)
        matched = False
        for i in range(1, np.size(positions, axis=0)):
            diffX, diffY = positions[i] - positions[i - 1]
            if (diffX <= 3):
                if (diffY <= 40 and diffY >= 10 or diffY<=-10 and diffY >= -40):
                    matched = True

        return matched
    ## [isStartSignal]

    def __preProcessImage(self, image):
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values
        invGamma = 1.0 / GAMMA
        table = np.array([((i / 255.0) ** invGamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")

        # apply gamma correction using the lookup table
        return cv2.LUT(image, table)

    def __segmentImage(self, image):
        return cv2.Canny(image, THRESHOLD_LOW, THRESHOLD_HIGH)

    ## [getDigitfromImage]
    ## Sucht in einem Bildausschnitt nach möglichen Signalen mit schwarzen Sigalen.
    ## Sobald die möglichen Stellen gefunden wurden, so wird für jede Stelle die Ziffer
    ## ermittelt. Dies geschieht über das trainierte SVM-Modell.
    ## Input: img --> Bildausschnitt
    ## Return: digits --> Liste von möglichen Ziffern (leer falls nichts gefunden)
    def getDigitfromImage(self, img):
        contours = []
        digits = []

        img = np.rot90(img, 3)
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgPreProcessed = self.__preProcessImage(imgGray)
        imgEdge = self.__segmentImage(imgPreProcessed)

        # Mit Hilfe der Konturen nach möglich Stellen suchen, wo sich Signal befinden könnte.
        # Bei dieser Stelle Ziffer ermitteln
        (_, cnts, _) = cv2.findContours(imgEdge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            # compute the moment of contour
            M = cv2.moments(c)
            if (M['m00'] != 0.0):
                # From moment we can calculte area, centroid etc
                # The center or centroid can be calculated as follows
                cX = int(M['m10'] / M['m00'])
                cY = int(M['m01'] / M['m00'])

                # call detectShape for contour c
                shape = self.__detectShape(c)

                if ((shape == "square" or shape == "rectangle" or shape == "circle")):

                    x, y, w, h = cv2.boundingRect(c)


                    ratio = w / h

                    if (shape == "circle"):
                        if (ratio > 0.3 and ratio < 0.7 and w > 3 and h > 6 and M['m00'] < (w * h) and M['m00'] > (
                                w * h * 0.01) and y > 2 and x > 2):
                            print(cX, cY, shape, x, y, w, h)
                            contours.append(c)
                            digits.append(self.__predictDigit(imgPreProcessed, x, y, w, h, -2))
                    else:
                        # Outline the contours
                        if (ratio > 0.75 and ratio < 1.25 and w > 10 and h > 10 and M['m00']>(w*h*0.5)):
                            print(cX, cY, shape, x, y, w, h)
                            contours.append(c)
                            digits.append(self.__predictDigit(imgPreProcessed, x, y, w, h, 1))
        return digits
    ## [getDigitfromImage]

    ## [getMaxContrast]
    ## Von einem Graustufenbild wird der Kontrast erhöht.
    ## Input: gray --> Graustufenbild
    ## Return: imgGrayscalePlusTopHatMinusBlackHat --> Kontrastbild
    def __getMaxContrast(self, gray):
        height, width = gray.shape
        imgTopHat = np.zeros((height, width, 1), np.uint8)
        imgBlackHat = np.zeros((height, width, 1), np.uint8)
        structuringElement = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        imgTopHat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, structuringElement)
        imgBlackHat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, structuringElement)
        imgGrayscalePlusTopHat = cv2.add(gray, imgTopHat)
        imgContrast = cv2.subtract(imgGrayscalePlusTopHat, imgBlackHat)
        return imgContrast
    ## [getMaxContrast]