"""
import binascii
import struct
import base64
import json
"""
from PIL import Image
import math
import types
import os
import chardet

from Crypto.Cipher import AES


def conver(file_path):
    print("PATH:"+file_path)
    #====Define====#
    f=readImage(file_path)
    debug=0
    if f==None:
        #====Binary====#
        f=readBinary(file_path)
        re=f.read()
        print("byte=type:"+str(type(re)))
        f.close()
        #==Operate Image==#
        width=int(math.sqrt(len(re)))
        while len(re)%width>0:
            if width>1:width=width-1
        height=int(len(re)//width)
        #==Create Image==#
        n_im=Image.new("RGBA",(width,height),(0,0,0,0))
        i=j=0
        for y in range(height):
            for x in range(width):
                for j in range(4):
                    if i<len(re):
                        if j==0: g=re[i]
                        elif j==1: b=re[i]
                        elif j==2: a=re[i]
                        else:
                            r=re[i]
                            #==Write Image==#
                            if debug:print(str((r,g,b,a))+" -> "+str((x,y)))
                            n_im.putpixel((x,y),(r,g,b,a))
                            lastY=y
                        i=i+1
        n_im=n_im.crop((0, 0,width,lastY+1))
        #==Show Image==#
        #Show Image
        #n_im.show()
        n_im.save(os.path.basename(file_path)+'.png')
        #print(n_im,n_im.format)
        print("Image generated!")
    else:
        #====Image====#
        print(f,f.format)
        width=f.size[0]
        height=f.size[1]
        result=[]
        for y in range(height):
            for x in range(width):
                try:
                    p=(x,y)
                    r,g,b,a=f.getpixel(p)
                    if debug:print(str(p)+" -> "+str(colorToUnicode(a,r,g,b)))
                    #char=colorToUnicode(r,g,b,a)
                    #result+=combineUnicode(char[1],char[0])
                    """
                    listApp(result,g,0)
                    listApp(result,b,0)
                    listApp(result,a,0)
                    listApp(result,r,0)
                    """
                    result.append(g)
                    result.append(b)
                    result.append(a)
                    result.append(r)
                except:
                    continue
        b=bytes(result)
        #Build Text
        full_path=os.path.basename(file_path)+'.txt'
        #encode=chardet.detect(result)['encoding']
        file=open(full_path,'wb',-1)#,"gb18030"
        file.write(b)
        #print("result=type:"+str(type(result))+",context="+str(result))
        #print("b=type:"+str(type(b))+",context="+str(b))
        #Show Text
        #Close
        file.close()
        #print(result)
        f.close()
        print("Text generated!")

def listApp(list,x,back):
    if x!=back: list.append(x)

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

#u1 <- a,r;u2 <- g,b;(r,g,b,a) -> (most,least)
def colorToUnicode(r,g,b,a):
    return ((a<<8)|r,(g<<8)|b)
    

#most -> a,r;least -> g,b; (most,least) -> (r,g,b,a)
def unicodeToColor(most,least):
    return (most&0xff,least>>24,least&0xff,most>>24)

#u1,u2 ->str
def combineUnicode(least,most):
    r1=r2=""
    if least!=0:
        try:
            r1=chr(least)
        except:
            pass
    if most!=0:
        try:
            r2=chr(most)
        except:
            pass
    return r1+r2

#Direct Function
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            conver(file_path)
    else:
        print("Usage: python IConver.py \"File Name\"")