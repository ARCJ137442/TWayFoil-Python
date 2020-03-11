from PIL import Image
import math
import os
import traceback
from tqdm import tqdm

'''
Binary to image:
     1.Convert byte array to 32-bit pixel int array
         For example: [0xff,0x76,0x00,0x3a,0x98,0x1d,0xcb] (len=7)-> [0xff76003a,0x981dcb00] (len=2)
     2.Insert the length pixel (len (byte)% 4,0x1 in the example) in the first bit of the int array
     3. Create a picture from an int array
Image to binary:
     1.Convert image to array of length L and 32-bit pixel int
         For example: L=3,[0x998acb6a,0x6a634bde,0x87000000]
     2.Convert 32-bit pixel int array to byte array
         For example: [0x998acb6a,0x6a634bde,0x87000000]-> [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87,0x00,0x00,0x00]
     3. Delete the L elements at the end of the byte array
         For example: [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87,0x00,0x00,0x00]-> [0x99,0x8a,0xcb,0x6a,0x6a,0x63,0x4b,0xde,0x87]
     4. Create binary file based on byte array

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

DEBUG=False
NCOLS=70

#aa,rr,gg,bb -> 0xaarrggbb
def binaryToPixels(b):#bytes b
    global NCOLS
    lb=len(b)
    result=[(-lb)&3]#included length,4 bit in a pixel
    j=0
    pixel=0
    for i in tqdm(range(lb),desc='Converting: ',ncols=NCOLS):
        if j<4:pixel|=b[i]<<(j<<3)
        else:
            j=0
            result.append(pixel)
            pixel=b[i]
        j=j+1
    if j!=0:result.append(pixel)#Add the end of byte
    return result
#returns int[]

#0xaarrggbb -> aa,rr,gg,bb
def pixelsToBinary(pixels):#int[] pixels
    result=[]
    processBar=tqdm(total=len(pixels),desc='Converting: ',ncols=NCOLS)
    for pix in pixels:
        color=pixelToRGBA(pix)
        result.append(color[0])#a
        result.append(color[1])#r
        result.append(color[2])#g
        result.append(color[3])#b
        processBar.update(1)
    processBar.close()
    return result
#returns bytes

def autoConver(file_path):
    #====Define====#
    f=readImage(file_path)
    if f!=None:
        try:dealFromImage(f,file_path)
        except BaseException as e:printExcept(e,"autoConver()->")
        else:return
    if type(f)!='image':print("Faild to load image \""+file_path+"\",now try to load as binary")
    dealFromBinary(file_path)

def dealFromBinary(path):
    global DEBUG
    #========From Binary========#
    f=readBinary(path)
    if f==None:
        print("Faild to load binary \""+path+"\"")
        return
    print("PATH:"+path+",FILE:",f)
    #====1 Convert Binary and 2 Insert Pixel====#
    pixels=binaryToPixels(f.read())
    #====Close File====#
    f.close()
    #====3 Create Image====#
    createImage(path,pixels)

def dealFromImage(f,path):
    print("PATH:"+path+",FILE:",f,f.format)
    global DEBUG
    #========From Image========#
    #====1 Convert Image to Pixel,and Get Length====#
    PaL=getPixelsAndLength(f)
    length=PaL[0]
    pixels=PaL[1]
    print(">-Pal:","length="+str(length),"len(pixels) =",len(pixels))
    #====2 Convert Pixel to Binary and 3 Delete the L Byte====#
    binary=pixelsToBinary(pixels)
    print(">-len(binery) =",len(binary))
    if length>0:
        for i in range(length):binary.pop()
    #====4 Create Binary File====#
    f.close()
    createBinaryFile(bytes(binary),path)

def getPixelsAndLength(image):
    global NCOLS
    result=[0,[]]
    t=True
    plist=list(image.getdata())
    processBar=tqdm(total=len(plist),desc='Scanning: ',ncols=NCOLS)
    for pixel in plist:
        color=ARGBtoPixel(pixel)
        if t:
            print("\n>-getPixelsAndLength(",pixel,")->",color)
            result[0]=color
            t=False
        else:result[1].append(color)
        processBar.update(1)
    processBar.close()
    return result
#returns (int,int[])

def createImage(sourcePath,pixels):
    global DEBUG
    global NCOLS
    #==Operate Image==#
    lpx=len(pixels)
    width=int(math.sqrt(lpx))
    while lpx%width>0:width=width-1
    height=int(lpx/width)
    nim=Image.new("RGBA",(width,height),(0,0,0,0))
    i=0
    imL=nim.load()
    processBar=tqdm(total=lpx,desc='Creating: ',ncols=NCOLS)
    for y in range(height):
        for x in range(width):
            #==Write Image==#
            #nim.putpixel((x,y),pixelToRGBA(pixels[i]))
            if i==0:
                print("\n>-createImage(",x,y,")->",hex(pixels[i]))
            imL[x,y]=pixels[i]
            if i==0:
                print(">-createImage#detect(",x,y,")->",hex(pixels[i]),imL[x,y],nim.getpixel((x,y)))
            i=i+1
            processBar.update(1)
    processBar.close()
    #==Save Image==#
    #Show Image(Unused) #nim.show()
    nim.save(os.path.basename(sourcePath)+'.png')
    print(nim,nim.format)
    print("Image File created!")

def createBinaryFile(b,path):#bytes b,str path
    #Build Text
    print("Writing...")
    try:
        file=open(generateFileName(path),'wb',-1)
        file.write(b)
    except BaseException as e:printExcept(e,"createBinaryFile()->")
    #==Close File==#
    file.close()
    print("Binary File generated!")

#pixel(0xaarrggbb) -> RGBA(r,g,b,a)
def pixelToRGBA(pixel):return ((pixel>>16)&0xff,(pixel>>8)&0xff,pixel&0xff,(pixel>>24))

#RGBA(a,r,g,b)<Tuple/List> -> pixel(0xaarrggbb)
def ARGBtoPixel(color):
    #For Image uses RGB:
    if len(color)<4:alpha=0xff000000
    else:alpha=color[0]<<24
    return alpha|(color[1]<<16)|(color[2]<<8)|color[3]

def generateFileName(originPath):
    bn=os.path.basename(originPath)
    if bn.count('.')>1:return bn[0:bn.rindex('.')]
    return bn+'.txt'

def readImage(path):
    try:return Image.open(path)
    except:return None

def readBinary(path):
    try:f=open(path,'rb')
    except BaseException as e:printExcept(e,"readBinary()->")
    else:return f
    try:f.close()
    except:pass
    return None

def printExcept(exc,head):
    global DEBUG
    tb=""
    if DEBUG:tb+="\n"+traceback.format_exc()
    print(head+"Find a exception:",exc,tb)

def InputYN(head):
    print(head,end='')
    yn=input()
    return yn.lower()=="y" or yn.lower()=="yes" or yn.lower()=="true"

#Function Main
if __name__=='__main__':
    import sys
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            autoConver(file_path)
            print()
    else:
        print("<====IConver====>")
        #print("Now in Command Line Mode!")
        while(True):
            try:
                #print("Usage: python IConver.py \"File Name\"")
                path=input("Please choose PATH:")
                if InputYN("Force compress to Image?Y/N:"):dealFromBinary(path)
                else: autoConver(path)
            except BaseException as e:
                printExcept(e,"readText()->")
                if InputYN("Do you want to terminate the program?Y/N:"):break
            print()