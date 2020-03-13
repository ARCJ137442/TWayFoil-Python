import errno
import math
import os
import traceback

from PIL import Image
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

NCOLS=70
SELF_NAME='IKonverti'
VERSION='1.3.1'

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
def printPath(message,path):return print(message.format('\"'+path+'\"'))
def printPathBL(path,en,zh):return printPath(gsbl(en=en,zh=zh),path=path)

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
        if not asBinary:file0=readImage(path)
        elif file0==None:file0=readBinary(path)
        return file0
    except BaseException as e:
        printExcept(e,"autoReadFile()->")
        return None

def autoConver(path,forceImage=False):
    #====Define====#
    currentFile=autoReadFile(path,forceImage)
    print(path,forceImage,type(currentFile),Image.isImageType(currentFile))
    if Image.isImageType(currentFile):
        print(gsbl(en="Image file read successfully!",zh="\u56fe\u50cf\u6587\u4ef6\u8bfb\u53d6\u6210\u529f\uff01"))
        try:
            result=converImageToBinary(currentFile,path)
            result[1].close()
        except BaseException as e:printExcept(e,"autoConver()->")
        else:return
    if (not forceImage) and not Image.isImageType(currentFile):
        print(gsbl(en="Faild to load image {},now try to load as binary",zh="\u8bfb\u53d6\u56fe\u50cf{}\u5931\u8d25\uff0c\u73b0\u5728\u5c1d\u8bd5\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6570\u636e").format("\""+path+"\""))
    converBinaryToImage(path,readBinary(path))

#binaryFile:A BufferedReader or bytes(will set to bRead),Image(will convert to bytes)
def converBinaryToImage(path,binaryFile,returnBytes=False,compressMode=False):
    #========From Binary========#
    if binaryFile==None:
        print(gsbl(en="Faild to load binary {}",zh="\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6587\u4ef6{}\u5931\u8d25").format("\""+path+"\""))
        return
    elif type(binaryFile)==bytes:bRead=binaryFile
    elif isinstance(binaryFile,Image.Image):bRead=binaryFile.tobytes()
    else:bRead=binaryFile.read()
    #====Convert Binary and Insert Pixel====#
    if bRead!=None:
        if compressMode:return compressFromBinary(path,bRead)
        print(gsbl(en="Binary file read successfully!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6\u8bfb\u53d6\u6210\u529f\uff01"))
        pixels=binaryToPixels(bRead)
    #====Close File====#
    if (not returnBytes) and type(binaryFile)!=bytes:binaryFile.close()
    #====Create Image and Return Tuple====#
    return createImageFromPixels(path,pixels,message=returnBytes)
#return (image,bytes)

#imageFile
def converImageToBinary(imageFile,path,compressMode=False):
    #========From Image========#
    #====1 Convert Image to Pixel,and Get Length====#
    PaL=getPixelsAndLength(imageFile)
    tailLength=PaL[0]&3#Limit the length lower than 4
    pixels=PaL[1]
    #====2 Convert Pixel to Binary and 3 Delete the L Byte====#
    binary=pixelsToBinary(pixels)
    if compressMode:return releaseFromImage(path,imageFile)
    if tailLength>0:
        for i in range(tailLength):binary.pop()
    #====4 Create Binary File and Return====#
    imageFile.close()
    return createBinaryFile(bytes(binary),path,message=not compressMode)
#return (image,file,fileBytes) the file in returns[1] need to close!

def compressFromBinary(path,binary):
    oResult=converBinaryToImage(binaryFile=binary,path=path)#(image,bytes)
    lengthN=-1
    while True:
        lengthO=len(oResult[1])
        nResult=converBinaryToImage(binaryFile=oResult[1],path=path)
        lengthN=len(nResult[1])
        if lengthN>lengthO:
            nResult[0].close()
            break
        oResult=nResult
    oResult[0].save(path+'.png')#required not closed image
    oResult[0].close()#close at there
    print(gsbl(en="Binary File compressed!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6\u5df2\u538b\u7f29\uff01"))
    return None
#return (pixels,path)

def releaseFromImage(path,image):
    #TODO
    oResult=converImageToBinary(imageFile=image,path='temp_'+path)#(image,bytes)
    while True:
        print("路径：",'temp_'+path)
        try:nResult=converImageToBinary(imageFile=oResult[0],path='temp_'+path)
        except BaseException as e:
            #printExcept(e,"releaseFromImage/while()->")
            break
        if len(nResult[2])<1:
            nResult[1].close()
            break
        oResult=nResult
    oResult=createBinaryFile(oResult[2],generateFileNameFromImage(path,removeDotPngs=True),message=True,compressMode=False)#required not closed file
    oResult[1].close()#close at there
    print(gsbl(en="Image file unzipped!",zh="\u56fe\u7247\u6587\u4ef6\u5df2\u89e3\u538b\uff01"))
    return None

#image is Image.Image,alse can be a list of pixels
def getPixelsAndLength(image):
    global NCOLS
    result=[0,[]]
    isFirst=True
    if isinstance(image,list):pixList=image
    else:pixList=list(image.getdata())
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

def createImageFromPixels(sourcePath,pixels,message=True):
    global NCOLS
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
            #==Write Image==#
            niLoad[x,y]=RGBAtoBGRA(pixels[i])#The image's load need write pixel as 0xaabbggrr,I don't know why
            i=i+1
            processBar.update(1)
    processBar.close()
    #==Save Image==#
    nImage.save(sourcePath+'.png')
    return (nImage,open(sourcePath+'.png','rb').read())
    if message:print(gsbl(en="Image File created!",zh="\u56fe\u7247\u6587\u4ef6\u5df2\u521b\u5efa\uff01"))
#return (image,imageBytes)

def createBinaryFile(binary,path,message=True,compressMode=False):#bytes binary,str path
    try:
        if compressMode:fileName=generateFileNameFromImage(path)
        else:fileName=path
        file=open(fileName,'wb',-1)
        file.write(binary)
        file.close()
        try:image=Image.open(fileName)
        except:image=None
    except BaseException as exception:
        printExcept(exception,"createBinaryFile()->")
        return (None,None,None)
    #==Return,may Close File==#
    if message:#not close
        prbl(en="Binary File generated!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6\u5df2\u751f\u6210\uff01")
    file=open(fileName,'rb+',-1)
    return (image,file,file.read())
#return tuple(image,file,fileBytes)

#For pixel: 0xaarrggbb -> 0xaabbggrr
def RGBAtoBGRA(pixel):return ((pixel&0xff0000)>>16)|((pixel&0xff)<<16)|(pixel&0xff00ff00)

#pixel(0xaarrggbb) -> RGBA(r,g,b,a)
def pixelToRGBA(pixel):return ((pixel>>16)&0xff,(pixel>>8)&0xff,pixel&0xff,(pixel>>24))

#RGBA(a,r,g,b)<Tuple/List> -> pixel(0xaarrggbb)
def RGBAtoPixel(color):
    #For Image uses RGB:
    if len(color)<4:alpha=0xff000000
    else:alpha=color[3]<<24
    return alpha|(color[0]<<16)|(color[1]<<8)|color[2]

def generateFileNameFromImage(originPath,removeDotPngs=False):
    baseName=os.path.basename(originPath)
    if baseName.count('.')>1:
        baseName=baseName[0:baseName.rindex('.')]
    else:
        baseName+='.txt'
    if removeDotPngs:
        while baseName[-4:]=='.png':baseName=baseName[:-4]
    return baseName

def readImage(path):
    ima=None
    try:ima=Image.open(path)
    except BaseException as e:
        if ima!=None:ima.close()
    return ima

def readBinary(path):return open(path,'rb')#raises error

def printExcept(exc,funcPointer):print(funcPointer+gsbl(en="A exception was found:",zh="\u53d1\u73b0\u5f02\u5e38\uff1a"),exc,"\n"+traceback.format_exc())

def InputYN(head,defaultFalse=True):
    yn=input(head)
    if not bool(yn):return False
    elif defaultFalse and (yn.lower()=='n' or yn.lower()=="no" or yn.lower()=="false" or yn in '\u5426\u9634\u9682\u9519\u53cd\u5047'):return False
    return yn.lower()=='y' or yn.lower()=="yes" or yn.lower()=="true" or yn in '\u662f\u9633\u967d\u5bf9\u6b63\u771f'

numExcept=0

def cmdLineMode():
    global numExcept
    print("<===="+SELF_NAME+" v"+VERSION+"====>")
    while(True):
        try:
            numExcept=0
            path=inputBL(en="Please insert PATH:",zh="\u8bf7\u8f93\u5165\u8def\u5f84\uff1a")
            fileImf=readFile(path)
            code_=fileImf[0]
            bina_=fileImf[1]
            #Binary -> Image
            if code_>=0:
                compressMode=InputYN(gsbl(en="Enable compression mode?",zh="\u542f\u7528\u538b\u7f29\u6a21\u5f0f\uff1f")+"Y/N:")
            if code_==0 or (code_>0 and InputYN(gsbl(en="Force compress to Image?",zh="\u5f3a\u5236\u8f6c\u6362\u6210\u56fe\u50cf\uff1f")+"Y/N:")):
                converBinaryToImage(path,bina_,compressMode=compressMode)
            #Image -> Binary
            elif code_>0:
                result=converImageToBinary(fileImf[2],path,compressMode=compressMode)
                if result!=None and result[1]!=None:result[1].close()
            else:
                raise bina_#exception at here
        except FileNotFoundError:
            printPathBL(en="{} not found!",zh="\u672a\u627e\u5230{}\uff01",path=path)
            numExcept=numExcept+1
        except OSError as err:
            if err.errno==errno.ENOENT:printPathBL(en="{} read/write faild!",zh="\u8bfb\u5199{}\u5931\u8d25\uff01",path=path)
            elif err.errno==errno.EPERM:printPathBL(en="Permission denied!",zh="\u8bbf\u95ee\u88ab\u62d2\u7edd\uff01",path=path)
            elif err.errno==errno.EISDIR:printPathBL(en="{} is a directory!",zh="{}\u662f\u4e00\u4e2a\u76ee\u5f55\uff01",path=path)
            elif err.errno==errno.ENOSPC:printPathBL(en="Not enough equipment space!",zh="\u8bbe\u5907\u7a7a\u95f4\u4e0d\u8db3\uff01",path=path)
            elif err.errno==errno.ENAMETOOLONG:printPathBL(en="The File name is too long!",zh="\u6587\u4ef6\u540d\u8fc7\u957f\uff01",path=path)
            elif err.errno==errno.EINVAL:printPathBL(en="Invalid File name: {}",zh="\u6587\u4ef6\u540d\u65e0\u6548\uff1a{}",path=path)
            else:printPathBL(en="Reading/Writeing {} error!",zh="\u8bfb\u5199\u6587\u4ef6{}\u9519\u8bef\uff01",path=path)
            numExcept=numExcept+1
        except BaseException as e:
            printExcept(e,"cmdLineMode()->")
            numExcept=numExcept+1
        if numExcept>0 and InputYN(gsbl(en="Do you want to terminate the program?",zh="\u4f60\u60f3\u7ec8\u6b62\u7a0b\u5e8f\u5417\uff1f")+"Y/N:"):
            break
        numExcept=0
        print()#new line

try:
    #Function Main
    if __name__=='__main__':
        import sys
        if len(sys.argv)>1:
            for file_path in sys.argv[1:]:
                try:
                    autoConver(file_path)
                    print()
                except FileNotFoundError:
                    printPathBL(en="{} not found!",zh="\u672a\u627e\u5230{}\uff01",path=file_path)
                    numExcept=numExcept+1
                except BaseException as error:
                    printExcept(error,"main->")
                    numExcept=numExcept+1
        else:
            cmdLineMode()
except BaseException as e:
    printExcept(e,"main->")
if numExcept>0 and InputYN((gsbl(en="{} exceptions found.\nDo you need to switch to command line mode?",zh="\u53d1\u73b0\u4e86{}\u4e2a\u5f02\u5e38\u3002\u4f60\u9700\u8981\u5207\u6362\u5230\u547d\u4ee4\u884c\u6a21\u5f0f\u5417\uff1f")+"Y/N:").format(numExcept)):
    cmdLineMode()