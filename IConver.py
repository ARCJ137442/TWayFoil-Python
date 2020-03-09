"""
import json
import chardet
"""
from PIL import Image
import math
import types
import os

from Crypto.Cipher import AES

'''
Binary to image:
     1.Convert byte array to 32-bit pixel int array
         For example: [0xff,0x76,0x00,0x3a,0x98,0x1d,0xcb] (len = 7)-> [0xff76003a,0x981dcb00] (len = 2)
     2.Insert the length pixel (len (byte)% 4,0x1 in the example) in the first bit of the int array
     3. Create a picture from an int array
Image to binary:
     1.Convert image to array of length L and 32-bit pixel int
         For example: L = 3,[0x998acb6a,0x6a634bde,0x87000000]
     2.Convert 32-bit pixel int array to byte array
         For example: [0x998acb6a,0x6a634bde,0x87000000]-> [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87,0x00,0x00,0x00]
     3. Delete the L elements at the end of the byte array
         For example: [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87,0x00,0x00,0x00]-> [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87]
     4. Create binary file based on byte array
'''
'''
二进制转图像：
    1.把byte数组转换为32位像素int数组
        例如：[0xff,0x76,0x00,0x3a,0x98,0x1d,0xcb](len=7) -> [0xff76003a,0x981dcb00](len=2)
    2.在int数组第一位插入长度像素(len(byte)%4,例中为0x1)
    3.根据int数组创建图片
图像转二进制：
    1.把图像转换为长度L和32位像素int数组
        例如：L=3,[0x998acb6a,0x6a634bde,0x87000000]
    2.把32位像素int数组转换为byte数组
        例如：[0x998acb6a,0x6a634bde,0x87000000] -> [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87,0x00,0x00,0x00]
    3.删除byte数组末尾的L个元素
        例如：[0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87,0x00,0x00,0x00] -> [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87]
    4.根据byte数组创建二进制文件
'''

debug=0

#aa,rr,gg,bb -> 0xaarrggbb
def converBinaryToPixels(b):#bytes b
    result=[4-(len(b)%4)]#included length
    j=0
    pixel=0
    for i in range(len(b)):
        if j<4:
            pixel|=b[i]<<(j*8)
        else:
            j=0
            result.append(pixel)
            #print("converBinaryToPixels:"+str((i,j))+" "+hex(pixel)+" -> result["+str(i)+"]")
            pixel=b[i]
        j=j+1
    if j!=0:result.append(pixel)
    print("converBinaryToPixels:b="+str(list(b)))
    #print("converBinaryToPixels:result="+str(result))
    return result
#returns int[]

def getPixelsAndLength(image):
    result=[0,[]]
    i=0
    for y in range(image.height):
        for x in range(image.width):
            r,g,b,a=image.getpixel((x,y))
            color=RGBAtoPixel(r,g,b,a)
            if i==0:
                result[0]=color
            else:
                result[1].append(color)
                #print("getPixelsAndLength:"+str((x,y))+" "+hex(color)+" -> result["+str(i)+"]")
            i=i+1
    #print("getPixelsAndLength:result="+str(result))
    return result
#returns (int,int[])

#0xaarrggbb -> aa,rr,gg,bb
def pixelsToBinary(pixels):#int[] pixels
    result=[]
    for pix in pixels:
        color=pixelToRGBA(pix)
        result.append(color[2])#g
        result.append(color[1])#r
        result.append(color[0])#a
        result.append(color[3])#b
    #print("pixelsToBinary:result="+str(result))
    return result
#returns bytes

def conver(file_path):
    print("PATH:"+file_path)
    global debug
    #====Define====#
    f=readImage(file_path)
    if f==None:
        #========From Binary========#
        f=readBinary(file_path)
        #====1 Convert Binary and 2 Insert Pixel====#
        r=f.read()
        print(str(r))
        pixels=converBinaryToPixels(r)
        #====Close File====#
        f.close()
        #====3 Create Image====#
        createImage(pixels)
    else:
        #========From Image========#
        #====1 Convert Image to Pixel,and Get Length====#
        PaL=getPixelsAndLength(f)
        length=PaL[0]
        pixels=PaL[1]
        print("Pal:","pixels="+str(pixels),"length="+str(length))
        #====2 Convert Pixel to Binary and 3 Delete the L Byte====#
        binary=pixelsToBinary(pixels)
        if length>0:
            for i in range(length):
                binary.pop()
        #====4 Create Binary File====#
        print(f,f.format)
        b=bytes(binary)
        f.close()
        print("conver:b="+str(list(b)))
        createBinaryFile(b,file_path)

def createImage(pixels):
    global debug
    #==Operate Image==#
    lpx=len(pixels)
    width=int(math.sqrt(lpx)/2)
    if width>1:
        while lpx%width>0:
            if width>1:width=width-1
    while width<1:width=width+1
    height=int(lpx/width)
    n_im=Image.new("RGBA",(width,height),(0,0,0,0))
    i=0
    j=0
    for y in range(height):
        for x in range(width):
            if i<lpx:
                r,g,b,a=pixelToRGBA(pixels[i])
                #==Write Image==#
                if debug:print(str((r,g,b,a))+" -> "+str((x,y)))
                n_im.putpixel((x,y),(r,g,b,a))
                lastY=y
                i=i+1
    #print("height:",lastY,height,y)
    #n_im=n_im.crop((0,0,width,lastY+1))
    #==Show Image==#
    #Show Image
    #n_im.show()
    n_im.save(os.path.basename(file_path)+'.png')
    print(n_im,n_im.format)
    print("Image created!")

def createBinaryFile(b,path):#bytes b,str path
    #Build Text
    full_path=os.path.basename(path)+'.txt'
    file=open(full_path,'wb',-1)
    file.write(b)
    #==Close File==#
    file.close()
    print("Text generated!")

def readImage(path):
    try:
        return Image.open(path)
    except:
        return None

def readBinary(path):
    try:
        f=open(path,'rb')
        return f
    except:
        print("readBinary:error!")
    f.close()
    return None

#Unused
def readText(path):
    try:
        f=open(path,'rt')
        r=f.read()
        return r
    except:
        print("readText:error!")
        return None
    f.close()
    return r

#pixel(0xaarrggbb) -> RGBA(r,g,b,a)
def pixelToRGBA(pixel):
    return ((pixel>>16)&0xff,(pixel>>8)&0xff,pixel&0xff,(pixel>>24))

#RGBA(r,g,b,a) -> pixel(0xaarrggbb)
def RGBAtoPixel(r,g,b,a):
    return (a<<24)|(r<<16)|(g<<8)|b

#Direct Function
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            conver(file_path)
    else:
        print("Usage: python IConver.py \"File Name\"")