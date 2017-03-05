# -*- coding: utf-8 -*-
"""
Created on Sat Mar 04 16:46:24 2017

@author: catfi
"""
import gdal
import numpy as np
class Grid_Modify:
    def __init__(self,filename):
        self.FileName=filename
        self.Dataset=gdal.Open(self.FileName)
        self.FileType=(self.Dataset.GetDriver()).LongName
        self.DataType=self.Dataset.GetRasterBand(1).DataType
        self.DataTypeStr=gdal.GetDataTypeName(self.DataType)
        self.im_proj = self.Dataset.GetProjection()
        self.im_geotrans = self.Dataset.GetGeoTransform()
        self.XSize=self.Dataset.RasterXSize
        self.YSize=self.Dataset.RasterYSize
        self.im_bands=self.Dataset.RasterCount

    def ClipbyBox(self,box):
        if self.__ValidateBox(box):#验证所给的box范围是否正确
            print 'invalidate box'
            return
        else:
            
            dst_im_geotrans=list(self.im_geotrans)
            dst_im_geotrans[0]=self.im_geotrans[0]+(box[2]-1)*self.im_geotrans[1]
            dst_im_geotrans[3]=self.im_geotrans[3]+(box[0]-1)*self.im_geotrans[5]
            self.im_geotrans=tuple(dst_im_geotrans)
            self.XSize=box[3]-box[2]+1
            self.YSize=box[1]-box[0]+1
            if self.im_bands == 1:
                self.DataArray=self.DataArray[box[0]:(box[1]+1),box[2]:(box[3]+1)]
            else:
                self.DataArray=self.DataArray[:,box[0]:(box[1]+1),box[2]:(box[3]+1)]
    """
    box定义为(top,down,left,right),索引从1开始而不是0.
    例如(50,100,60,110)表示裁剪出原始图像中的第50到100行，共51行；60到110列，共51列。
    """
    def SaveAs(self,dstname):
        driver = self.Dataset.GetDriver()
        dst_dataset = driver.Create(dstname, self.XSize,self.YSize, self.im_bands, self.DataType)
        dst_dataset.SetGeoTransform(self.im_geotrans)
        dst_dataset.SetProjection(self.im_proj)
        if self.im_bands == 1:
            dst_dataset.GetRasterBand(1).WriteArray(self.DataArray) #写入数组数
        else:
            for i in range(self.im_bands):
                dst_dataset.GetRasterBand(i+1).WriteArray(self.DataArray[i])
        print 'Done!!!' 
    def __ValidateBox(self,box):#验证所给的box范围是否正确
        if box[0]>box[1]|box[2]>box[3]:
            return 1
        if min(box)<0:
            return 1
        if box[1]>self.YSize|box[3]>self.XSize:
            return 2
        return 0
	def __Read(self):
		self.DataArray=self.Dataset.ReadAsArray(0,0,self.XSize,self.YSize)
#main
if __name__=="__main__":
    import os,sys
    #判断cmd中是否给了足够的参数，若给了正确的参数，则按给出的参数运行
    if len(sys.argv)==7:
        filename=sys.argv[1]
        up=int(sys.argv[2])
        down=int(sys.argv[3])
        left=int(sys.argv[4])
        right=int(sys.argv[5])
        Grid=Grid_Modify(filename)
        Grid.ClipbyBox((up,down,left,right))
        Grid.SaveAs(sys.argv[6])
    else:
        os.chdir(r'I:\ucas\Python_Geo_Process\chapter_02')
        Grid=Grid_Modify("fdem.tif")
        Grid.ClipbyBox((50,100,50,100))
        Grid.SaveAs('fdem_class_clip_submit.tif')