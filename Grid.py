# -*- coding: utf-8 -*-
"""
Created on Sat Mar 04 16:46:24 2017

RyIP v1.1， Ranyu's Image Process
@author: Ranyu YIN
@作者：尹然宇
 
Hosted in GitHub: https://github.com/ranyuyin/RyIP
托管于GitHub：https://github.com/ranyuyin/RyIP

使用方法：
CMD：
Python Grid.py [Source_File_Name] [top_from] [down_end] [left_from] [right_end] [Destination_Filename]

Example: Python Grid.py fdem.tif 50 100 50 100 fdemSub1_1.tif
表示裁剪出原始图像fdem.tif中的第50到100行，共51行；60到110列，共51列。并将结果写入fdemSub1_1.tif。
文件名参数可以是相对路径或绝对路径，使用相对路径时需注意当前工作路径设置。
"""
import gdal
import numpy as np
class Grid:
    def __init__(self,filename):
        self.FileName=filename
        self.Dataset=gdal.Open(self.FileName)
        self.FileType=(self.Dataset.GetDriver()).LongName
        self.DataType=self.Dataset.GetRasterBand(1).DataType
        self.DataTypeStr=gdal.GetDataTypeName(self.DataType)
        self.im_proj = self.Dataset.GetProjection()
        self.im_geotrans = self.Dataset.GetGeoTransform()
        self.XStart=0
        self.YStart=0
        self.XSize=self.Dataset.RasterXSize
        self.YSize=self.Dataset.RasterYSize
        self.im_bands=self.Dataset.RasterCount

    def ClipbyBox(self,box,dstname):
        if self.__ValidateBox(box):#验证所给的box范围是否正确
            print 'invalidate box'
            return
        else:
            
            dst_im_geotrans=list(self.im_geotrans)
            dst_im_geotrans[0]=self.im_geotrans[0]+(box[2]-1)*self.im_geotrans[1]
            dst_im_geotrans[3]=self.im_geotrans[3]+(box[0]-1)*self.im_geotrans[5]
            self.im_geotrans=tuple(dst_im_geotrans)
            self.XStart=box[2]-1
            self.YStart=box[0]-1
            self.XSize=box[3]-box[2]+1
            self.YSize=box[1]-box[0]+1
            self.__Read()
            self.__SaveAs(dstname)
    """
    box定义为(top,down,left,right),索引从1开始而不是0.
    例如(50,100,60,110)表示裁剪出原始图像中的第50到100行，共51行；60到110列，共51列。
    """
    def __SaveAs(self,dstname):#保存当前对象
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
		self.DataArray=self.Dataset.ReadAsArray(self.XStart,self.YStart,self.XSize,self.YSize)
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
        grid=Grid(filename)
        grid.ClipbyBox((up,down,left,right),sys.argv[6])
    else:
        os.chdir(r'I:\ucas\Python_Geo_Process\chapter_02')
        grid=Grid("fdem.tif")
        grid.ClipbyBox((50,100,50,100))
        grid.SaveAs('fdem_class_clip_submit.tif')