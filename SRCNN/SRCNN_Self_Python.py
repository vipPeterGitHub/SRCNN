# -*- coding: UTF-8 -*-
import os
import numpy as np
import math
import scipy.misc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import h5py
# Make sure that caffe is on the python path:
caffe_root = '/home/peterhou/caffe-master/'
import sys
sys.path.append(caffe_root+'python')
sys.path.append(caffe_root+'python/caffe')
import caffe
sys.path.append('/usr/local/lib/python2.7/site-packages')
import cv2


# Parameters
scale = 3

def read_data(path):
  """
  Read h5 format data file
  
  Args:
    path: file path of desired file
    data: '.h5' file format that contains train data values
    label: '.h5' file format that contains train label values
  """
  with h5py.File(path, 'r') as hf:
    data = np.array(hf.get('dat'))
    label = np.array(hf.get('lab'))
    return data, label

def modcrop(image,scale):
    """
    To scale down and up the original image, first thing to do is to have no remainder while scaling operation.
  
    We need to find modulo of height (and width) and scale factor.
    Then, subtract the modulo from height (and width) of original image size.
    There would be no remainder even after scaling operation.
    """
    if len(image.shape) == 3:
        h, w, _ = image.shape
        h = h - np.mod(h, scale)
        w = w - np.mod(w, scale)
        image = image[0:h, 0:w, :]
    else:
        h, w = image.shape
        h = h - np.mod(h, scale)
        w = w - np.mod(w, scale)
        image = image[0:h, 0:w]
    return image

def colorize(y, ycrcb):
    y[y>255] = 255
    img = np.zeros((y.shape[0], y.shape[1], 3), np.uint8)
    img[:,:,0] = y
    img[:,:,1] = ycrcb[:,:,1]
    img[:,:,2] = ycrcb[:,:,2]
    img = cv2.cvtColor(img, cv2.COLOR_YCR_CB2BGR)
    
    return img

# PSNR measure, from ANR's code
def PSNR(pred, gt):
    f = pred.astype(float)
    g = gt.astype(float)
    e = (f - g).flatten()
    rmse = math.sqrt(np.mean(e ** 2.))
    return 20 * math.log10(255. / rmse)


def Predict(deploy_proto,caffe_model,test_image,h5_image,results_path):

	net = caffe.Net(deploy_proto,caffe_model,caffe.TEST)
	#read image
	image = cv2.imread(test_image)
	image = modcrop(image,scale)
	ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)

	lr_img,hr_img = read_data(h5_image)
	lr_img=lr_img.T #和matlab是行列相反
	hr_img=hr_img.T #和matlab是行列相反
	shape = hr_img.shape

	net.blobs['data'].reshape(1, 1, shape[0], shape[1])
	net.blobs['data'].data[...] = np.reshape(lr_img, (1, 1, shape[0], shape[1]))
	net.forward()
	out = net.blobs['conv3'].data[...]
	"""
	#e = 0	#edge crop
	#ep = e-6
	pred_img = np.squeeze(out)
	pred_img = np.lib.pad(pred_img,((6,6),(6,6)),'constant', constant_values=0)
	#pred_img = pred_img[ep:-ep,ep:-ep]
	pred_img = (np.rint(pred_img[:,:] * 255)).astype(np.uint8)
	#hr_img = hr_img[e:-e,e:-e]
	hr_img = (np.rint(hr_img[:,:]*255)).astype(np.uint8)
	#lr_img = lr_img[e:-e,e:-e]
	lr_img = (np.rint(lr_img[:,:]*255)).astype(np.uint8)

	#Show color image
	#ycrcb=ycrcb[e:-e,e:-e,:]
	pred_img = colorize(pred_img, ycrcb)
	lr_img = colorize(lr_img, ycrcb)
	hr_img =colorize(hr_img,ycrcb)

	"""

	pred_img = np.squeeze(out)
	pred_img = (np.rint(pred_img[:,:] * 255)).astype(np.uint8)
	#hr_img = hr_img[6:-6,6:-6]
	hr_img = (np.rint(hr_img[:,:]*255)).astype(np.uint8)
	#lr_img = lr_img[6:-6,6:-6]
	lr_img = (np.rint(lr_img[:,:]*255)).astype(np.uint8)
	
	#Show color image
	#ycrcb=ycrcb[6:-6,6:-6,:]
	pred_img = colorize(pred_img, ycrcb)
	lr_img = colorize(lr_img, ycrcb)
	hr_img =colorize(hr_img,ycrcb)

	#PSNR
	# print("SRCNN结果:")
	psnr_final=PSNR(pred_img,hr_img)
	# print("bicubic结果:")
	psnr_basic=PSNR(lr_img,hr_img)

	#save

	name = test_image.split("/")[-1]
	name = os.path.splitext(name)[0]
	cv2.imwrite(results_path+name+'_pred.png', pred_img)
	cv2.imwrite(results_path+name+'_hr.png', hr_img)
	cv2.imwrite(results_path+name+'_lr.png', lr_img)

	return psnr_basic , psnr_final

if __name__ == "__main__":
	deploy_proto=caffe_root + 'examples/SR1/SRCNN_deploy.prototxt'
	caffe_model=caffe_root + 'examples/SR1/SRCNN_pad_iter_5000000.caffemodel'
	test_path = caffe_root + 'examples/SR1/Test/Set5/'
	h5_path = caffe_root + 'examples/SR1/Test_h5/Set5/'
	results_path = caffe_root + 'examples/SR1/Result/'

	image_names = os.listdir(test_path)
	image_names = sorted(image_names)
	h5_names = os.listdir(h5_path)
    	h5_names = sorted(h5_names)
    	nums = image_names.__len__()
    	bicubic = []
    	srcnn = []
    	names =[]
	diff = []
    	for i in range(nums):
    		test_image = test_path + image_names[i]
    		h5_image = h5_path + h5_names[i]
		name = os.path.splitext(image_names[i])[0]
		bi,sr=Predict(deploy_proto,caffe_model,test_image,h5_image,results_path)
		bicubic.append(bi)
		srcnn.append(sr)
		names.append(name)
		diff.append(sr - bi)

	f = open(caffe_root + 'examples/SR1/result_pad_iter_5000000.txt','w')	
	f.write('Name of images: '+str(names)+'\rPSNR of bicubic: '+str(bicubic)+'\rPSNR of SRCNN: '+str(srcnn)+'\rdiff: '+ str(diff))
	print names 
	print bicubic 
	print srcnn
	print diff


		
