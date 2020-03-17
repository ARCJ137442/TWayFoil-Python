import errno
import os
import traceback

from PIL import Image
from tqdm import tqdm

'''For The Core,see README'''

NCOLS=70
SELF_NAME='TWayFoil'
VERSION='2.0.0'

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
def printPath(message,path):return print(message%('\"'+path+'\"'))
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
        else:
            return (1,readBinary(path),file0)
    except BaseException as error:return (-1,error,None)
#return (code,binary or error,image or None)

def autoReadFile(path,forceImage=False):
    try:
        file0=readImage(path)
        if forceImage:
            file0=readImage(path)
        elif file0==None:
            file0=readBinary(path)
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
        except BaseException as e:
            printExcept(e,"autoConver()->")
        else:return
    if (not forceImage) and not Image.isImageType(currentFile):
        printPathBL(en="Now try to load %s as binary",zh="\u73b0\u5728\u5c1d\u8bd5\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6570\u636e %s",path=path)
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

#binaryFile:A BufferedReader or bytes(will set to bRead),Image(will convert to bytes)
def converBinaryToImage(path,binaryFile,returnBytes=False,message=None,compressMode=False):
    #========Auto Refer========#
    if message==None:message=not returnBytes
    #========From Binary========#
    if binaryFile==None:
        printPathBL(en="Faild to load binary %s",zh="\u8bfb\u53d6\u4e8c\u8fdb\u5236\u6587\u4ef6%s\u5931\u8d25",path=path)
        return
    elif type(binaryFile)==bytes:
        bReadBytes=binaryFile
    elif isinstance(binaryFile,Image.Image):
        bReadBytes=binaryFile.tobytes()
    else:
        bReadBytes=binaryFile.read()
    #====Convert Binary and Insert Pixel====#
    if bReadBytes!=None:
        if compressMode:
            return compressFromBinary(path,bReadBytes)
        prbl(en="Binary file read successfully!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6\u8bfb\u53d6\u6210\u529f\uff01")
        pixelBytes=binaryToPixelBytes(bReadBytes)
    #====Close File====#
    if (not returnBytes) and type(binaryFile)!=bytes:
        binaryFile.close()
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
        printPathBL(en="Deleting temp file %s...",zh="\u6b63\u5728\u5220\u9664\u4e34\u65f6\u6587\u4ef6%s\u3002\u3002\u3002",path=tPath)
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
    width=int(lenPixel**0.5)
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
    if message:
        prbl(en="Image File created!",zh="\u56fe\u7247\u6587\u4ef6\u5df2\u521b\u5efa\uff01")
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
        printPathBL(path=fileName,en="Binary File %s generated!",zh="\u4e8c\u8fdb\u5236\u6587\u4ef6%s\u5df2\u751f\u6210\uff01")
    file=open(fileName,'rb+',-1)
    return (image,file,file.read())
#return tuple(image,file,fileBytes)

def generateFileNameFromImage(originPath,removeDotPngs=False):
    baseName=os.path.basename(originPath)
    result=baseName
    if result.count('.')>1:
        result=result[:result.rindex('.')]
    if removeDotPngs:
        while result[-4:]=='.png':
            result=result[:-4]
    if ('.png' in result) or result==baseName:
        result+='.txt'
    return result

def readImage(path):
    ima=None
    try:
        ima=Image.open(path)
    except BaseException as e:
        if ima!=None:ima.close()
    return ima

def readBinary(path):
    return open(path,'rb')#raises error

def printExcept(exc,funcPointer):
    print(funcPointer+gsbl(en="A exception was found:",zh="\u53d1\u73b0\u5f02\u5e38\uff1a"),exc,"\n"+traceback.format_exc())

def InputYN(head,defaultFalse=True):
    yn=input(head)
    if not bool(yn):
        return False
    elif defaultFalse and (yn.lower()=='n' or yn.lower()=="no" or yn.lower()=="false" or yn in '\u5426\u9634\u9682\u9519\u53cd\u5047'):
        return False
    return yn.lower()=='y' or yn.lower()=="yes" or yn.lower()=="true" or yn in '\u662f\u9633\u967d\u5bf9\u6b63\u771f'

#BANDING to main and cmdLinemode
def catchExcept(err,path,head):
    global numExcept
    numExcept=numExcept+1
    if isinstance(err,FileNotFoundError):
        printPathBL(en="%s not found!",zh="\u672a\u627e\u5230%s\uff01",path=path)
    elif isinstance(err,OSError):
        if err.errno==errno.ENOENT:printPathBL(en="%s read/write faild!",zh="\u8bfb\u5199%s\u5931\u8d25\uff01",path=path)
        elif err.errno==errno.EPERM:printPathBL(en="Permission denied!",zh="\u8bbf\u95ee\u88ab\u62d2\u7edd\uff01",path=path)
        elif err.errno==errno.EISDIR:printPathBL(en="%s is a directory!",zh="%s\u662f\u4e00\u4e2a\u76ee\u5f55\uff01",path=path)
        elif err.errno==errno.ENOSPC:printPathBL(en="Not enough equipment space!",zh="\u8bbe\u5907\u7a7a\u95f4\u4e0d\u8db3\uff01",path=path)
        elif err.errno==errno.ENAMETOOLONG:printPathBL(en="The File name is too long!",zh="\u6587\u4ef6\u540d\u8fc7\u957f\uff01",path=path)
        elif err.errno==errno.EINVAL:printPathBL(en="Invalid File name: %s",zh="\u6587\u4ef6\u540d\u65e0\u6548\uff1a%s",path=path)
        else:printPathBL(en="Reading/Writeing %s error!",zh="\u8bfb\u5199\u6587\u4ef6%s\u9519\u8bef\uff01",path=path)
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
                if result!=None and result[1]!=None:
                    result[1].close()
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
if numExcept>0 and InputYN((gsbl(en="%s exceptions found.\nDo you need to switch to command line mode?",zh="\u53d1\u73b0\u4e86%s\u4e2a\u5f02\u5e38\u3002\u4f60\u9700\u8981\u5207\u6362\u5230\u547d\u4ee4\u884c\u6a21\u5f0f\u5417\uff1f")+"Y/N:").format(numExcept)):
    cmdLineMode()