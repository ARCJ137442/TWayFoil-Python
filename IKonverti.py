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

DEBUG=True
NCOLS=70
SELF_NAME='IKonverti'
VERSION='1.2.5'

#Language about
SYSTEM_LANGUAGE=0
try:
    import win32api
    SYSTEM_LANGUAGE=win32api.GetSystemDefaultLangID()
except:pass

#Language supports zh and en(default)
def getStrByLanguage(en='',zh=''):
    if SYSTEM_LANGUAGE==0x804:return zh
    return en
def gsbl(en='',zh=''):return getStrByLanguage(en=en,zh=zh)
def prbl(en='',zh=''):return print(gsbl(en=en,zh=zh))
def inputBL(en='',zh=''):return input(gsbl(en=en,zh=zh))

#aa,rr,gg,bb -> 0xaarrggbb
def binaryToPixels(binary):#bytes b
    global NCOLS
    binaryLength=len(binary)
    result=[(-binaryLength)&3]#included length,4 bit in a pixel
    j=0
    pixel=0
    for i in tqdm(range(binaryLength),desc=gsbl('Converting','\u8f6c\u6362\u4e2d')+': ',ncols=NCOLS):
        if j<4:pixel|=binary[i]<<(j<<3)
        else:
            j=0
            result.append(pixel)
            pixel=binary[i]
        j=j+1
    if j!=0:result.append(pixel)#Add the end of byte
    return result
#returns int[]

#0xaarrggbb -> aa,rr,gg,bb
def pixelsToBinary(pixels):#int[] pixels
    result=[]
    processBar=tqdm(total=len(pixels),desc=gsbl('Converting','\u8f6c\u6362\u4e2d')+': ',ncols=NCOLS)
    for pixel in pixels:
        result.append(pixel&0xff)#b
        result.append((pixel&0xff00)>>8)#g
        result.append((pixel&0xff0000)>>16)#r
        result.append((pixel&0xff000000)>>24)#a
        processBar.update(1)
    processBar.close()
    return result
#returns bytes

#0=binary,1=image,-1=exception
def readFile(path):
    try:
        file0=readImage(path)
        if file0==None:
            file0=readBinary(path)
            if file0==None:return (-1,FileNotFoundError(path),None)
            return (0,file0,None)
        else:return (1,readBinary(path),file0)
    except BaseException as error:return (-1,error,None)
#return (code,binary or error,image or None)

def autoReadFile(path,asBinary=False):
    try:
        file0=readImage(path)
        if file0==None:
            file0=readBinary(path)
            if file0==None:return None
            return file0
        elif asBinary:return readBinary(path)
        else:return file0
    except BaseException as e:return None

def autoConver(path,forceImage=False):
    #====Define====#
    currentFile=autoReadFile(path,forceImage)
    if type(currentFile)=="PIL.PngImagePlugin.PngImageFile":
        try:dealFromImage(currentFile,path)
        except BaseException as e:printExcept(e,"autoConver()->")
        else:return
    if (not forceImage) and type(currentFile)!='image':
        print(gsbl("Faild to load image ","\u8bfb\u53d6\u56fe\u50cf\u5931\u8d25")+"\""+path+"\","+gsbl("now try to load as binary","\u73b0\u5728\u5c1d\u8bd5\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6570\u636e"))
    dealFromBinary(path,readBinary(path))

def dealFromBinary(path,binaryFile):
    #========From Binary========#
    if binaryFile==None:
        print(gsbl("Faild to load binary","\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6570\u636e\u5931\u8d25")+" \""+path+"\"")
        return
    print(gsbl("PATH","\u8def\u5f84")+":"+path+","+gsbl("FILE","\u6587\u4ef6")+":",binaryFile)
    #====1 Convert Binary and 2 Insert Pixel====#
    pixels=binaryToPixels(binaryFile.read())
    #====Close File====#
    binaryFile.close()
    #====3 Create Image====#
    createImage(path,pixels)

def dealFromImage(imageFile,path):
    #========From Image========#
    #====1 Convert Image to Pixel,and Get Length====#
    PaL=getPixelsAndLength(imageFile)
    tailLength=PaL[0]&3#Limit the length lower than 4
    pixels=PaL[1]
    #====2 Convert Pixel to Binary and 3 Delete the L Byte====#
    binary=pixelsToBinary(pixels)
    if tailLength>0:
        for i in range(tailLength):binary.pop()
    #====4 Create Binary File====#
    imageFile.close()
    createBinaryFile(bytes(binary),path)

def getPixelsAndLength(image):
    global NCOLS
    result=[0,[]]
    isFirst=True
    pixList=list(image.getdata())
    processBar=tqdm(total=len(pixList),desc=gsbl('Scanning','\u626b\u63cf\u4e2d')+': ',ncols=NCOLS)
    for pixel in pixList:
        color=RGBAtoPixel(pixel)
        if isFirst:
            result[0]=color
            isFirst=False
        else:result[1].append(color)
        processBar.update(1)
    processBar.close()
    return result
#returns (int,int[])

def createImage(sourcePath,pixels):
    global NCOLS
    global DEBUG
    #==Operate Image==#
    lenPixel=len(pixels)
    width=int(math.sqrt(lenPixel))
    while lenPixel%width>0:width=width-1
    height=int(lenPixel/width)
    nImage=Image.new("RGBA",(width,height),(0,0,0,0))
    i=0
    niLoad=nImage.load()
    processBar=tqdm(total=lenPixel,desc=gsbl('Creating','\u521b\u5efa\u4e2d')+': ',ncols=NCOLS)
    for y in range(height):
        for x in range(width):
            #==Write Image==#old:nim.putpixel((x,y),pixelToRGBA(pixels[i]))
            niLoad[x,y]=RGBAtoBGRA(pixels[i])#The image's load need write pixel as 0xaabbggrr,I don't know why
            i=i+1
            processBar.update(1)
    processBar.close()
    #==Save Image==#
    #Show Image(Unused) #nim.show()
    nImage.save(os.path.basename(sourcePath)+'.png')
    if DEBUG:print(nImage,nImage.format)
    print(gsbl("Image File created!","\u56fe\u7247\u6587\u4ef6\u5df2\u521b\u5efa\uff01"))

#For pixel: 0xaarrggbb -> 0xaabbggrr
def RGBAtoBGRA(pixel):return ((pixel&0xff0000)>>16)|((pixel&0xff)<<16)|(pixel&0xff00ff00)

def createBinaryFile(binary,path):#bytes binary,str path
    #Build Text
    try:
        file=open(generateFileName(path),'wb',-1)
        file.write(binary)
    except BaseException as exception:printExcept(exception,"createBinaryFile()->")
    #==Close File==#
    file.close()
    print(gsbl("Binary File generated!","\u4e8c\u8fdb\u5236\u6587\u4ef6\u5df2\u751f\u6210\uff01"))

#pixel(0xaarrggbb) -> RGBA(r,g,b,a)
def pixelToRGBA(pixel):return ((pixel>>16)&0xff,(pixel>>8)&0xff,pixel&0xff,(pixel>>24))

#RGBA(a,r,g,b)<Tuple/List> -> pixel(0xaarrggbb)
def RGBAtoPixel(color):
    #For Image uses RGB:
    if len(color)<4:alpha=0xff000000
    else:alpha=color[3]<<24
    return alpha|(color[0]<<16)|(color[1]<<8)|color[2]

def generateFileName(originPath):
    baseName=os.path.basename(originPath)
    if baseName.count('.')>1:return baseName[0:baseName.rindex('.')]
    return baseName+'.txt'

def readImage(path):
    try:return Image.open(path)
    except:return None

def readBinary(path):return open(path,'rb')#raises error

def printExcept(exc,funcPointer):
    global DEBUG
    if DEBUG:print(funcPointer+"Find a exception:",exc,"\n"+traceback.format_exc())
    else: print(funcPointer+"Find a exception:",exc)

def InputYN(head):
    yn=input(head)
    if not bool(yn):return False
    return yn.lower()=='y' or yn.lower()=="yes" or yn.lower()=="true" or yn in '\u662f\u9633\u967d\u5bf9\u6b63\u771f'

def cmdLineMode():
    print("<===="+SELF_NAME+" v"+VERSION+"====>")
    while(True):
        try:
            path=inputBL("Please choose PATH:","\u8bf7\u8f93\u5165\u8def\u5f84\uff1f")
            fileImf=readFile(path)
            code_=fileImf[0]
            bina_=fileImf[1]
            if code_==0 or (code_>0 and InputYN(gsbl("Force compress to Image?","\u5f3a\u5236\u8f6c\u6362\u6210\u56fe\u50cf\uff1f")+"Y/N:")):dealFromBinary(path,bina_)
            elif code_>0:dealFromImage(fileImf[2],path)
            else:raise bina_#exception at here
        except BaseException as e:
            printExcept(e,"readText()->")
            if InputYN(gsbl("Do you want to terminate the program?","\u4f60\u9700\u8981\u7ec8\u6b62\u7a0b\u5e8f\u5417\uff1f")+"Y/N:"):break
        print()#new line

try:
    #Function Main
    if __name__=='__main__':
        import sys
        if len(sys.argv)>1:
                try:
                    for file_path in sys.argv[1:]:
                        autoConver(file_path)
                        print()
                except BaseException as error:
                    printExcept(error,"main->")
                    if(InputYN(gsbl("Do you need to switch to command line mode?","\u4f60\u9700\u8981\u5207\u6362\u5230\u547d\u4ee4\u884c\u6a21\u5f0f\u5417\uff1f")+"Y/N:")):cmdLineMode()
        else:cmdLineMode()
except BaseException as e:printExcept(e,"main->")