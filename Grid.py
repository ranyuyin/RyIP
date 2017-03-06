# -*- coding: utf-8 -*-
"""
Created on Sat Mar 04 16:46:24 2017

RyIP v1.11， Ranyu's Image Process
@author: Ranyu YIN
@作者：尹然宇
 
Hosted in GitHub: https://github.com/ranyuyin/RyIP
托管于GitHub：https://github.com/ranyuyin/RyIP

使用方法：
裁剪影像：
CMD：Python Grid.py clip [Source_File_Name] [top_from] [down_end] [left_from] [right_end] [Destination_Filename]
Example: Python Grid.py clip fdem.tif 50 100 50 100 fdemSub1_1.tif
表示裁剪出原始图像fdem.tif中的第50到100行，共51行；60到110列，共51列。并将结果写入fdemSub1_1.tif。
文件名参数可以是相对路径或绝对路径，使用相对路径时需注意当前工作路径设置。

修改日志
v1.0
    完成程序主体
v1.1
    优化内存，将初始化时读取数据到内存调整为按需读取。
v1.11
    调整API，调用时需指定模式，而不是默认使用裁剪功能
    
"""
import gdal
import numpy as np
import ConvTrans
class Grid:
    def __init__(self,filename):
        self.FileName=filename
        self.Dataset=gdal.Open(self.FileName)
        self.ReadXStart=0
        self.ReadYStart=0
        self.DstXStart=0
        self.DstYStart=0
        self.ReadXSize=self.Dataset.RasterXSize
        self.ReadYSize=self.Dataset.RasterYSize
        self.FileType=(self.Dataset.GetDriver()).LongName
        self.DataType=self.Dataset.GetRasterBand(1).DataType
        self.DataTypeStr=gdal.GetDataTypeName(self.DataType)
        self.im_proj = self.Dataset.GetProjection()
        self.im_geotrans = self.Dataset.GetGeoTransform()
        GeoUp=self.im_geotrans[3]
        GeoDown=self.im_geotrans[3] + self.ReadYSize*self.im_geotrans[4] + self.ReadXSize*im_geotrans[5]
        GeoLeft=im_geotrans[0]
        GeoRight=im_geotrans[0] + self.ReadYSize*im_geotrans[1] + self.ReadXSize*im_geotrans[2]
        self.GeoBox=(GeoUp,GeoDown,GeoLeft,GeoRight)
        
        self.im_bands=self.Dataset.RasterCount
        DataArray=self.Dataset.ReadAsArray(0,0,1,1)
        #待优化点：可以使用Dataset中读取的GDT来确定
        self.npdtype=DataArray.dtype
    def ClipbyBox(self,box,dstname):
        if self.__ValidateBox(box):#验证所给的box范围是否正确
            print 'invalidate box'
            return
        else:
            
            dst_im_geotrans=list(self.im_geotrans)
            dst_im_geotrans[0]=self.im_geotrans[0]+(box[2]-1)*self.im_geotrans[1]
            dst_im_geotrans[3]=self.im_geotrans[3]+(box[0]-1)*self.im_geotrans[5]
            self.im_geotrans=tuple(dst_im_geotrans)
            self.ReadXStart=box[2]-1
            self.ReadYStart=box[0]-1
            self.DstXStart=self.ReadXStart
            self.DstYStart=self.ReadYStart
            self.ReadXSize=box[3]-box[2]+1
            self.ReadYSize=box[1]-box[0]+1
            self.DstXSize=self.ReadXSize
            self.DstYSize=self.ReadYSize
            self.__Read()
            self.__SaveAs(dstname)
    """
    box定义为(top,down,left,right),索引从1开始而不是0.
    例如(50,100,60,110)表示裁剪出原始图像中的第50到100行，共51行；60到110列，共51列。
    """
    def __SaveAs(self,dstname):#保存当前对象
        driver = self.Dataset.GetDriver()
        dst_dataset = driver.Create(dstname, self.ReadXSize,self.ReadYSize, self.im_bands, self.DataType)
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
        if box[1]>self.Dataset.RasterYSize|box[3]>self.Dataset.RasterXSize:
            return 2
        return 0
    
    def __Read(self):
        self.DataArray=self.Dataset.ReadAsArray(self.ReadXStart,self.ReadYStart,self.ReadXSize,self.ReadYSize)
    def ClipbyGeoBox(self,GeoBox,dstname,NoData=-9999,ToggleThreshold=0.001):#调整为与地理范围相交的最小栅格范围
    '''
    待优化点：
    可以先对输入的范围调整到对应投影的格网的整数边界处（也可能不是根据投影确定的，或许不同数据的格网都不一样），
    然后根据匹配后的格网确定输出的栅格大小；
    最后计算原始栅格到输出栅格的对应关系，并映射到输出栅格
    '''
        (Left,Up)=ConvTrans.map2pix(self.Dataset,GeoBox[2],GeoBox[0])
        (Right,Down)=ConvTrans.map2pix(self.Dataset,GeoBox[3],GeoBox[1])
        #处理恰好在像元边界附近的情况
        if (ConvTrans.IsLikeInt(Up,ToggleThreshold)):
            Up=int(round(Up))
        if (ConvTrans.IsLikeInt(Down,ToggleThreshold)):
            Down=int(round(Down))-1
        if (ConvTrans.IsLikeInt(Left,ToggleThreshold)):
            Left=int(round(Left))
        if (ConvTrans.IsLikeInt(Right,ToggleThreshold)):
            Right=int(round(Right))-1       
        #确定输出与原始图像的交集,以确定从何处开始读取
        OriginYSize=self.Dataset.RasterYSize
        OriginXSize=self.Dataset.RasterXSize
        OriginBox=np.array([0,self.Dataset.RasterYSize-1,0,self.Dataset.RasterXSize])#上下左右的矩阵索引
        AimBox=np.array([Up,Down,Left,Right])
        AimBox=np.floor(AimBox).astype('int')
        self.DstXSize=AimBox[3]-AimBox[2]+1
        self.DstYSize=AimBox[1]-AimBox[0]+1
        #此处为图像像素行列值，因此对于起始像元，寻找最大的，终止像元寻找最小的
        self.ReadXStart=max([AimBox[2],OriginBox[2]])
        self.ReadYStart=max([AimBox[0],OriginBox[0]])
        self.ReadXSize=min([AimBox[3],OriginBox[3]])-self.ReadXStart+1
        self.ReadYSize=min([AimBox[1],OriginBox[1]])-self.ReadYStart+1
        self.__Read()
        DstArray=np.ndarray((self.im_bands,self.DstYSize,self.DstXSize),self.npdtype)
        DstArray.fill(NoData)
        #source中的对应角标平移到0起始
        if AimBox[2]<0:
            DstOffX=abs(AimBox[2])
        else:
            DstOffX=0
        if AimBox[0]<0:
            DstOffY=abs(AimBox[0])
        else:
            DstOffY=0
        DstEndY=DstOffY+self.ReadYSize-1
        DstEndX=DstOffX+self.ReadXSize-1
        if self.im_bands == 1:
            DstArray[DstOffY:DstEndY,DstOffX:DstEndX]= self.DataArray[:]
        else:
            DstArray[:,DstOffY:DstEndY,DstOffX:DstEndX]=self.DataArray[:]
        self.DataArray=DstArray
        __SaveAs(dstname)
        
        '''
        
        intsect==np.min(np.stack((OriginBox,AimBox)),0)
        '''
    def __Align(self,MapLeftX,MapUpY,XSize,YSize):#暂时仅考虑UTM投影
#main
if __name__=="__main__":
    import os,sys
    #判断cmd中是否给了足够的参数，若给了正确的参数，则按给出的参数运行
    if (len(sys.argv)==8)&(sys.argv[1].lower()=='clip'):
        filename=sys.argv[2]
        up=int(sys.argv[3])
        down=int(sys.argv[4])
        left=int(sys.argv[5])
        right=int(sys.argv[6])
        grid=Grid(filename)
        grid.ClipbyBox((up,down,left,right),sys.argv[7])
    else:#测试代码
        print '参数错误，执行测试代码！'
        os.chdir(r'I:\ucas\Python_Geo_Process\chapter_02')
        grid=Grid("fdem.tif")
        grid.ClipbyBox((50,100,50,100),'test.tif')