import errno
import math
import os
import traceback

from PIL import Image
from tqdm import tqdm

'''
    2.0.0 核心(202003152029):
    引言：
        四字节转一像素的规定：四个字节(0x78,0xf1,0xd1,0x9a)按0->a,1->r,2->g,b->3转换为AARRGGBB颜色(0x78f1d19a)
        核心：在图片的像素列表中，取最后一个像素的最后一位当做末端像素的多余字节数，并删除末尾多余像素长度
        image.tobytes返回可枚举的、包含所有像素颜色的bytes列表
        例如image.bytes=b'0x7f/0x44/0xaf/0x7d/0x1a/0x89/0x11/0x56/0xac/0xcc/0xab/0x67/0xfa/0xda/0xcb/0x67/0x09/0x87/0x4a/0xc8/0x75/0x6d/0x00/0x02'
    关于图像转字节码的功能
        表示的原字节码总长为4之倍：
            -> 7f ad 1a 86 ab 6a 87 03 00 | 原像素列表,注1
            -> 7f ad 1a 86 ab 6a 87 03 00 00 00 04 | L=0，表示原字节码总长为4之倍数
            -> 7f ad 1a 86 ab 6a 87 03 | 因为L=3(bin:11)，删除最后一个像素
            -> 7fad1a86,ab6a8703 | 最终像素组，上一步的字节码将被存储为二进制文件
        表示的原字节码总长非4之倍（以上image）：
            -> 7f 44 af 7d 1a 89 11 56 ac cc ab 67 fa da cb 67 09 87 4a c8 75 6d 00 02 | 原像素列表，注2
            -> 7f 44 af 7d , 1a 89 11 56 , ac cc ab 67 , fa da cb 67 , 09 87 4a c8 75 6d 00 02 | L=01， 注3
            -> 7f 44 af 7d , 1a 89 11 56 , ac cc ab 67 , fa da cb 67 , 09 87 4a c8 75 6d | L=00 删除末端计数字节自身，并删除L个字节
            -> 7f 44 af 7d 1a 89 11 56 ac cc ab 67 fa da cb 67 09 87 4a c8 75 6d | 最终的二进制字节码将被存储为二进制文件
        注： 
            (1)默认将最后一位当做位数
            (2)本地图像的tobytes函数返回的字节码总长恒为4的倍数
            (3)末端无意义字节（不包括自身）的数目，正常的L值为0~3
        子IDEA 1:以最后一个像素的最后两个bit(00~11)作为长度
    关于字节码转图像的功能（示例，过程相当于上一个例子的逆过程）
        字节码总长非4之倍：
            ->8a 76 47 3f 4c 9b 7a 06 4b 7d 9a 4c 8e 67 00 f8 ff ca bd | 原字节码
            ->8a 76 47 3f,4c 9b 7a 06,4b 7d 9a 4c,8e 67 00 f8,ff ca bd 00 | 增1~3个字节以补全像素，计之为L=01（本例中）
            ->8a 76 47 3f,4c 9b 7a 06,4b 7d 9a 4c,8e 67 00 f8,ff ca bd 01 | 将最后一个字节修改为L（本例中"ff ca bd 01"）
            ->0x8a76473f,0x4c9b7a06,0x4b7d9a4c,0x8e6700f8,0xffcabd01 | 最终像素组，上一步的字节码将被等效存储为图片
        字节码总长为4之倍：
            ->8a 76 4f 4c 9b 7a 06 7d 9a 4e 67 00 f8 fa bd e5 ac 6d 9f 89 | 原字节码
            ->8a 76 4f 4c 9b 7a 06 7d 9a 4e 67 00 f8 fa bd e5 ac 6d 9f 89 00 00 00 00 |增加四个字节（代表一个空像素）
            ->8a764f4c,9b7a067d,9a4e6700,f8fabde5,ac6d9f89,00000000| 最终像素组，上一步的字节码将被等效存储为图片
    
    English Version:
    Introduction:
        Four-byte to one-pixel rule: Four bytes (0x78, 0xf1,0xd1,0x9a) are converted into AARRGGBB colors (0x78f1d19a) according to 0-> a, 1-> r, 2-> g, b-> 3
        Core: In the pixel list of the picture, take the last bit of the last pixel as the extra bytes of the end pixel and delete the extra pixel length at the end
        image.tobytes returns an enumerable list of bytes containing all pixel colors
        For example image.bytes = b'0x7f / 0x44 / 0xaf / 0x7d / 0x1a / 0x89 / 0x11 / 0x56 / 0xac / 0xcc / 0xab / 0x67 / 0xfa / 0xda / 0xcb / 0x67 / 0x09 / 0x87 / 0x4a / 0xc8 / 0x75 / 0x00 / 0x02 '
    About image to bytecode function
        The total length of the original bytecode represented is 4 times:
            -> 7f ad 1a 86 ab 6a 87 03 00 | Original pixel list, note 1
            -> 7f ad 1a 86 ab 6a 87 03 00 00 00 04 | L = 0, which means that the total length of the original bytecode is a multiple of 4.
            -> 7f ad 1a 86 ab 6a 87 03 | Because L = 3 (bin: 11), delete the last pixel
            -> 7fad1a86, ab6a8703 | The final pixel group, the bytecode from the previous step will be stored as a binary file
        The total length of the original bytecode represented is not 4 times (the above image):
            -> 7f 44 af 7d 1a 89 11 56 ac cc ab 67 fa da cb 67 09 87 4a c8 75 6d 00 02 | Original pixel list, note 2
            -> 7f 44 af 7d, 1a 89 11 56, ac cc ab 67, fa da cb 67, 09 87 4a c8 75 6d 00 02 | L = 01, Note 3
            -> 7f 44 af 7d, 1a 89 11 56, ac cc ab 67, fa da cb 67, 09 87 4a c8 75 6d | L = 00 delete the end count byte itself and delete L bytes
            -> 7f 44 af 7d 1a 89 11 56 ac cc ab 67 fa da cb 67 09 87 4a c8 75 6d | The final binary bytecode will be stored as a binary file
        Note: 
            (1) The last digit is regarded as the number of digits by default
            (2) The total length of the bytecode returned by the tobytes function of the local image is always a multiple of 4.
            (3) the number of meaningless bytes (excluding itself) at the end, the normal L value is 0 ~ 3
        Sub IDEA 1: Take the last two bits (00 ~ 11) of the last pixel as the length
    About the function of bytecode to image (example, the process is equivalent to the reverse process of the previous example)
        Total byte code length is not 4 times:
            -> 8a 76 47 3f 4c 9b 7a 06 4b 7d 9a 4c 8e 67 00 f8 ff ca bd | Original bytecode
            -> 8a 76 47 3f, 4c 9b 7a 06, 4b 7d 9a 4c, 8e 67 00 f8, ff ca bd 00 | Add 1 ~ 3 bytes to complete the pixel, which is L = 01 (in this example)
            -> 8a 76 47 3f, 4c 9b 7a 06,4b 7d 9a 4c, 8e 67 00 f8, ff ca bd 01 | Modify the last byte to L ("ff ca bd 01" in this example)
            -> 0x8a76473f, 0x4c9b7a06,0x4b7d9a4c, 0x8e6700f8,0xffcabd01 | In the final pixel group, the bytecode of the previous step will be equivalently stored as a picture
        The total length of the bytecode is 4 times:
            -> 8a 76 4f 4c 9b 7a 06 7d 9a 4e 67 00 f8 fa bd e5 ac 6d 9f 89 | Original bytecode
            -> 8a 76 4f 4c 9b 7a 06 7d 9a 4e 67 00 f8 fa bd e5 ac 6d 9f 89 00 00 00 00 | Add four bytes (representing an empty pixel)
            -> 8a764f4c, 9b7a067d, 9a4e6700, f8fabde5, ac6d9f89,00000000 | In the final pixel group, the bytecode of the previous step will be equivalently stored as a picture
'''

NCOLS=70
SELF_NAME='TWayFoil'
VERSION='1.0.0'

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

#0=binary,1=image,-1=exception
def readFile(path):
    try:
        file0=readImage(path)
        if file0==None:
            file0=readBinary(path)
            if file0==None:
                return (-1,FileNotFoundError(path),None)
            return (0,file0,None)
        else:return (1,readBinary(path),file0)
    except BaseException as error:return (-1,error,None)
#return (code,binary or error,image or None)

def autoReadFile(path,forceImage=False):
    try:
        file0=readImage(path)
        if forceImage:file0=readImage(path)
        elif file0==None:file0=readBinary(path)
        return file0
    except BaseException as e:
        printExcept(e,"autoReadFile()->")
        return None
#return image or binary or None

def autoConver(path,forceImage=False):
    #====Define====#
    currentFile=autoReadFile(path,forceImage=forceImage)
    if Image.isImageType(currentFile):
        prbl(en="Image file read successfully!",zh="\u56fe\u50cf\u6587\u4ef6\u8bfb\u53d6\u6210\u529f\uff01")
        try:
            result=converImageToBinary(imageFile=currentFile,path=path,compressMode=False,message=True)
            result[1].close()
        except BaseException as e:printExcept(e,"autoConver()->")
        else:return
    if (not forceImage) and not Image.isImageType(currentFile):
        printPathBL(en="Now try to load {} as binary",zh="\u73b0\u5728\u5c1d\u8bd5\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6570\u636e {}",path=path)
    converBinaryToImage(path=path,binaryFile=readBinary(path),returnBytes=False,compressMode=False,message=True)

#aa,rr,gg,bb -> 0xaarrggbb
def binaryToPixelBytes(binary):#bytes binary
    global NCOLS
    result=binary
    processBar=tqdm(range(3),desc=gsbl('Converting','\u8f6c\u6362\u4e2d'))
    binaryLength=len(binary)
    processBar.update(1)
    lenMod4m3=3-binaryLength%4
    processBar.update(1)
    if lenMod4m3<0:
        result=result+b'\x00\x00\x00\x03'
    else:
        result=result+(lenMod4m3)*b'\x00'+bytes((lenMod4m3,))
    processBar.update(1)
    processBar.close()
    return result
#returns bytes

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

#binaryFile:A BufferedReader or bytes(will set to bRead),Image(will convert to bytes)
def converBinaryToImage(path,binaryFile,returnBytes=False,message=None,compressMode=False):
    #========Auto Refer========#
    if message==None:message=not returnBytes
    #========From Binary========#
    if binaryFile==None:
        printPathBL(en="Faild to load binary {}",zh="\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6587\u4ef6{}\u5931\u8d25",path=path)
        return
    elif type(binaryFile)==bytes:bReadBytes=binaryFile
    elif isinstance(binaryFile,Image.Image):bReadBytes=binaryFile.tobytes()
    else:bReadBytes=binaryFile.read()
    #====Convert Binary and Insert Pixel====#
    if bReadBytes!=None:
        if compressMode:return compressFromBinary(path,bReadBytes)
        prbl(en="Binary file read successfully!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6\u8bfb\u53d6\u6210\u529f\uff01")
        pixelBytes=binaryToPixelBytes(bReadBytes)
    #====Close File====#
    if (not returnBytes) and type(binaryFile)!=bytes:binaryFile.close()
    #====Create Image and Return Tuple====#
    return createImageFromPixelBytes(path,pixelBytes,message=message)
#return (image,bytes)

#imageFile is FileReader
def converImageToBinary(imageFile,path,compressMode=False,message=True):
    #========From Image========#
    #====1 Convert Image to Pixel,and Get Length====#
    #====2 Convert Pixel to Binary and 3 Delete the L Byte====#
    if compressMode:
        result=releaseFromImage(path,imageFile)
        imageFile.close()
        return (None,imageFile,None)
    pixelBytes=getFormedPixelBytes(imageFile)
    #====4 Create Binary File and Return====#
    imageFile.close()
    return createBinaryFile(pixelBytes,path,message=message,compressMode=compressMode)
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
    prbl(en="Binary File compressed!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6\u5df2\u538b\u7f29\uff01")
    return None
#return (pixels,path)

def releaseFromImage(path,image):
    tPath='temp_'+path
    oResult=converImageToBinary(imageFile=image,path=tPath,message=False,compressMode=False)#(image,bytes)
    while True:
        try:nResult=converImageToBinary(imageFile=oResult[0],path=tPath,compressMode=False,message=False)
        except BaseException as e:
            #printExcept(e,"releaseFromImage/while()->")
            break
        if len(nResult[2])<1:break
        oResult=nResult
        if nResult!=None and nResult[1]!=None:nResult[1].close()
    oResult=createBinaryFile(oResult[2],generateFileNameFromImage(path,removeDotPngs=True),message=True,compressMode=False)#required not closed file
    oResult[1].close()#close at there
    try:
        printPathBL(en="Deleting temp file {}...",zh="\u6b63\u5728\u5220\u9664\u4e34\u65f6\u6587\u4ef6{}\u3002\u3002\u3002",path=tPath)
        os.remove(tPath)
    except BaseException as e:
        printExcept(e,"releaseFromImage()->")
    else:prbl(en="Delete temp file successed!",zh="\u5220\u9664\u4e34\u65f6\u6587\u4ef6\u6210\u529f\uff01")
    prbl(en="Image file unzipped!",zh="\u56fe\u7247\u6587\u4ef6\u5df2\u89e3\u538b\uff01")
    return None

#image is Image.Image,alse can be a list of pixels
def getFormedPixelBytes(image):
    global NCOLS
    processBar=tqdm(total=2,desc=gsbl('Scanning','\u626b\u63cf\u4e2d')+': ',ncols=NCOLS)
    result=image.tobytes()
    processBar.update(1)
    length=int(result[-1])
    processBar.update(1)
    result=result[:-(1+length)]
    processBar.close()
    return result
#returns bytes

def createImageFromPixelBytes(sourcePath,pixelBytes,message=True):
    global NCOLS
    #==Operate Image==#
    #Operate pixel count
    lenPixel=len(pixelBytes)
    if lenPixel&3>0:
        lenPixel=(lenPixel//4)+1
    else:
        lenPixel=lenPixel//4
    #Determine size
    processBar=tqdm(total=4,desc=gsbl('Creating','\u521b\u5efa\u4e2d')+': ',ncols=NCOLS)
    width=int(math.sqrt(lenPixel))
    while lenPixel%width>0:
        width=width-1
    height=int(lenPixel/width)
    processBar.update(1)
    #Generate image
    nImage=Image.frombytes(data=pixelBytes,size=(width,height),mode="RGBA")
    processBar.update(1)
    niLoad=nImage.load()
    processBar.update(1)
    #==Save Image==#
    nImage.save(sourcePath+'.png')
    processBar.update(1)
    processBar.close()
    if message:prbl(en="Image File created!",zh="\u56fe\u7247\u6587\u4ef6\u5df2\u521b\u5efa\uff01")
    return (nImage,open(sourcePath+'.png','rb').read())
#return (image,imageBytes) imageBytes is (compressed png file)'s bytes!!!

def createBinaryFile(binary,path,message=True,compressMode=False):#bytes binary,str path
    #TO DEBUG
    processBar=tqdm(total=3,desc=gsbl('Generating','\u751f\u6210\u4e2d')+': ',ncols=NCOLS)
    try:
        if message and not compressMode:
            fileName=generateFileNameFromImage(path,removeDotPngs=not compressMode)#Auto Mode
        else:
            fileName=path
        file=open(fileName,'wb',-1)
        processBar.update()
        file.write(binary)
        file.close()
        processBar.update()
        try:image=Image.open(fileName)
        except:image=None
    except BaseException as exception:
        printExcept(exception,"createBinaryFile()->")
        return (None,None,None)
    #==Return,may Close File==#
    processBar.update()
    processBar.close()
    if message:#not close
        printPathBL(path=fileName,en="Binary File {} generated!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6{}\u5df2\u751f\u6210\uff01")
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
    result=baseName
    if result.count('.')>1:
        result=result[:result.rindex('.')]
    if ('.png' in result) or result==baseName:
        result+='.txt'
    if removeDotPngs:
        while result[-4:]=='.png':
            result=result[:-4]
    return result

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

#BANDING to main and cmdLinemode
def catchExcept(err,path,head):
    global numExcept
    numExcept=numExcept+1
    if isinstance(err,FileNotFoundError):
        printPathBL(en="{} not found!",zh="\u672a\u627e\u5230{}\uff01",path=path)
    elif isinstance(err,OSError):
        if err.errno==errno.ENOENT:printPathBL(en="{} read/write faild!",zh="\u8bfb\u5199{}\u5931\u8d25\uff01",path=path)
        elif err.errno==errno.EPERM:printPathBL(en="Permission denied!",zh="\u8bbf\u95ee\u88ab\u62d2\u7edd\uff01",path=path)
        elif err.errno==errno.EISDIR:printPathBL(en="{} is a directory!",zh="{}\u662f\u4e00\u4e2a\u76ee\u5f55\uff01",path=path)
        elif err.errno==errno.ENOSPC:printPathBL(en="Not enough equipment space!",zh="\u8bbe\u5907\u7a7a\u95f4\u4e0d\u8db3\uff01",path=path)
        elif err.errno==errno.ENAMETOOLONG:printPathBL(en="The File name is too long!",zh="\u6587\u4ef6\u540d\u8fc7\u957f\uff01",path=path)
        elif err.errno==errno.EINVAL:printPathBL(en="Invalid File name: {}",zh="\u6587\u4ef6\u540d\u65e0\u6548\uff1a{}",path=path)
        else:printPathBL(en="Reading/Writeing {} error!",zh="\u8bfb\u5199\u6587\u4ef6{}\u9519\u8bef\uff01",path=path)
    else:
        printExcept(err,head)

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
                converBinaryToImage(path=path,binaryFile=bina_,compressMode=compressMode,message=True)
            #Image -> Binary
            elif code_>0:
                result=converImageToBinary(imageFile=fileImf[2],path=path,compressMode=compressMode)
                if result!=None and result[1]!=None:result[1].close()
            else:
                raise bina_#exception at here
        except BaseException as e:
            catchExcept(e,path,"cmdLineMode()->")
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
                except BaseException as error:
                    catchExcept(error,file_path,"main->")
        else:
            cmdLineMode()
except BaseException as e:
    printExcept(e,"main->")
if numExcept>0 and InputYN((gsbl(en="{} exceptions found.\nDo you need to switch to command line mode?",zh="\u53d1\u73b0\u4e86{}\u4e2a\u5f02\u5e38\u3002\u4f60\u9700\u8981\u5207\u6362\u5230\u547d\u4ee4\u884c\u6a21\u5f0f\u5417\uff1f")+"Y/N:").format(numExcept)):
    cmdLineMode()