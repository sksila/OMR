# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.modules.module import get_module_resource
from imutils.perspective import four_point_transform
from imutils import contours

import numpy as np
import imutils
import cv2
import os


class Survey(models.Model):
    _inherit = 'survey.survey'
    _description = "Exam's model"

    is_exam = fields.Boolean(string="Is an exam?")
    teacher_id = fields.Many2one('res.users', string='Teacher')
    class_name = fields.Char(string='Class')
    date_exam = fields.Date(string='Date of exam')
    current_date = fields.Date(string='Date')
    answer_student_ids = fields.Many2many('ir.attachment', 'answer_attachment_rel', 'answer_student_id',
                                          'attachment_id', "Student's answer")


    def compute_result(self):
        print("begin")
        # define the answer key which maps the question number
        # to the correct answer
        ANSWER_KEY = {0: 1, 1: 4, 2: 0, 3: 3, 4: 1}

        # load the image, convert it to grayscale, blur it
        # slightly, then find edges
        path = get_module_resource('ajw_omr', 'static/src/img/student_papers/')
        data = os.listdir(path)
        sheet_list = []
        for file in data:
            data_name = os.path.splitext(file)  # split extension
            sheet_list.append(data_name[0])  # add id_name_code into a list

        path_array = []
        for sheet in range(len(sheet_list)):
            repo_path = get_module_resource('ajw_omr', 'static/src/img/student_papers/')
            path_answer_st = sheet_list[sheet]
            absolute_path_answer_st = repo_path + path_answer_st + '.png'


            path_array.append(absolute_path_answer_st)  # adding paths into an array
        for sheet in range(len(path_array)):
            image = cv2.imread(path_array[sheet])  # read image
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 75, 200)
            # cv2.imshow('edged',edged)
            # cv2.waitKey(0)

            # find contours in the edge map, then initialize
            # the contour that corresponds to the document
            cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            docCnt = None
            # ensure that at least one contour was found
            if len(cnts) > 0:
                # sort the contours according to their size in
                # descending order
                cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
                # loop over the sorted contours
                for c in cnts:
                    # approximate the contour
                    peri = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                    # if our approximated contour has four points,
                    # then we can assume we have found the paper
                    if len(approx) == 4:
                        docCnt = approx
                        break
                # apply a four point perspective transform to both the
                # original image and grayscale image to obtain a top-down
                # birds eye view of the paper
                paper = four_point_transform(image, docCnt.reshape(4, 2))
                warped = four_point_transform(gray, docCnt.reshape(4, 2))

                # apply Otsu's thresholding method to binarize the warped
                # piece of paper
                thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
                # cv2.imshow('warped', thresh)
                # cv2.waitKey(0)

                # find contours in the thresholded image, then initialize
                # the list of contours that correspond to questions
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                # print('cnts ', cnts)

                questionCnts = []
                # loop over the contours
                for c in cnts:
                    # compute the bounding box of the contour, then use the
                    # bounding box to derive the aspect ratio
                    (x, y, w, h) = cv2.boundingRect(c)
                    ar = w / float(h)
                    # in order to label the contour as a question, region
                    # should be sufficiently wide, sufficiently tall, and
                    # have an aspect ratio approximately equal to 1
                    if w >= 20 and h >= 20 and ar >= 0.9 and ar <= 1.1:
                        questionCnts.append(c)

                # sort the question contours top-to-bottom, then initialize
                # the total number of correct answers
                questionCnts = contours.sort_contours(questionCnts,
                                                      method="top-to-bottom")[0]
                correct = 0
                # each question has 5 possible answers, to loop over the
                # question in batches of 5
                for (q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
                    # sort the contours for the current question from
                    # left to right, then initialize the index of the
                    # bubbled answer
                    cnts = contours.sort_contours(questionCnts[i:i + 5])[0]
                    bubbled = None

                    # loop over the sorted contours
                    for (j, c) in enumerate(cnts):
                        # construct a mask that reveals only the current
                        # "bubble" for the question
                        mask = np.zeros(thresh.shape, dtype="uint8")
                        cv2.drawContours(mask, [c], -1, 255, -1)
                        # apply the mask to the thresholded image, then
                        # count the number of non-zero pixels in the
                        # bubble area
                        mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                        total = cv2.countNonZero(mask)
                        # if the current total has a larger number of total
                        # non-zero pixels, then we are examining the currently
                        # bubbled-in answer
                        if bubbled is None or total > bubbled[0]:
                            bubbled = (total, j)

                    # initialize the contour color and the index of the
                    # *correct* answer
                    color = (0, 0, 255)
                    k = ANSWER_KEY[q]
                    # check to see if the bubbled answer is correct
                    if k == bubbled[1]:
                        color = (0, 255, 0)
                        correct += 1
                    # draw the outline of the correct answer on the test
                    cv2.drawContours(paper, [cnts[k]], -1, color, 3)

                # grab the test taker
                score = (correct / 5.0) * 100
                print("[INFO] score: {:.2f}%".format(score))
                cv2.putText(paper, "{:.2f}%".format(score), (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
