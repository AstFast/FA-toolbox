import os
import binascii
import sys
import wave
import struct
import zlib
from PIL import Image
import soundfile
import ctypes
from tinytag import TinyTag
fpath=""
def PNG_decode(f):
	PngSignature = b'\x89PNG\r\n\x1a\n'
	if f.read(len(PngSignature)) != PngSignature:
		raise Exception('Invalid PNG Signature')
	def read_chunk(f):
		chunk_length, chunk_type = struct.unpack('>I4s', f.read(8))
		chunk_data = f.read(chunk_length)
		chunk_expected_crc, = struct.unpack('>I', f.read(4))
		chunk_actual_crc = zlib.crc32(chunk_data, zlib.crc32(struct.pack('>4s', chunk_type)))
		if chunk_expected_crc != chunk_actual_crc:
			raise Exception('chunk checksum failed')
		return chunk_type, chunk_data
	chunks = []
	while True:
		chunk_type, chunk_data = read_chunk(f)
		chunks.append((chunk_type, chunk_data))
		if chunk_type == b'IEND':
			break
	_, IHDR_data = chunks[0]
	width, height, bitd, colort, compm, filterm, interlacem = struct.unpack('>IIBBBBB', IHDR_data)
	if compm != 0:
		raise Exception('invalid compression method')
	if filterm != 0:
		raise Exception('invalid filter method')
	if colort != 6:
		raise Exception('we only support truecolor with alpha')
	if bitd != 8:
		raise Exception('we only support a bit depth of 8')
	if interlacem != 0:
		raise Exception('we only support no interlacing')
	IDAT_data = b''.join(chunk_data for chunk_type, chunk_data in chunks if chunk_type == b'IDAT')
	IDAT_data = zlib.decompress(IDAT_data)
	def PaethPredictor(a, b, c):
		p = a + b - c
		pa = abs(p - a)
		pb = abs(p - b)
		pc = abs(p - c)
		if pa <= pb and pa <= pc:
			Pr = a
		elif pb <= pc:
			Pr = b
		else:
			Pr = c
		return Pr
	Recon = []
	bytesPerPixel = 4
	stride = width * bytesPerPixel
	def Recon_a(r, c):
		return Recon[r * stride + c - bytesPerPixel] if c >= bytesPerPixel else 0
	def Recon_b(r, c):
		return Recon[(r-1) * stride + c] if r > 0 else 0
	def Recon_c(r, c):
		return Recon[(r-1) * stride + c - bytesPerPixel] if r > 0 and c >= bytesPerPixel else 0
	i = 0
	for r in range(height):
		filter_type = IDAT_data[i]
		i += 1
		for c in range(stride):
			Filt_x = IDAT_data[i]
			i += 1
			if filter_type == 0:
				Recon_x = Filt_x
			elif filter_type == 1:
				Recon_x = Filt_x + Recon_a(r, c)
			elif filter_type == 2:
				Recon_x = Filt_x + Recon_b(r, c)
			elif filter_type == 3:
				Recon_x = Filt_x + (Recon_a(r, c) + Recon_b(r, c)) // 2
			elif filter_type == 4:
				Recon_x = Filt_x + PaethPredictor(Recon_a(r, c), Recon_b(r, c), Recon_c(r, c))
			else:
				raise Exception('unknown filter type: ' + str(filter_type))
			Recon.append(Recon_x & 0xff)
	return Recon
def bytes_to_int(bytes):
	result = 0
	for b in bytes:
		result = result * 256 + int(b)
	return result
def readUInt32(stream):
	data=stream.read(4)
	data=struct.unpack('I',data)[0]
	return data
def readInt32(stream):
	data=stream.read(4)
	data=struct.unpack('i',data)[0]
	return data
def read_7Bit(stream):
    result = 0
    bitsRead = 0
    value = 0x80
    while value & 0x80:
        value = get("B", stream)[0]
        result |= (value & 0x7f) << bitsRead
        bitsRead += 7
    return result
def read7BitInt(stream):
	result=0
	bitsRead=0
	while True:
		value=stream.read(1)
		value=struct.unpack('B',value)[0]
		result|=(value&0x7f)<<bitsRead
		bitsRead+=7
		if value&0x80==0:
			break
	return result
def readString(stream):
	length=read7BitInt(stream)
	if length<0:
		return None
	if length==0:
		return ''
	data=stream.read(length)
	return data.decode()
def int_to_bytes(value, length):
	result = []
	for i in range(0, length):
		result.append(value >> (i * 8) & 0xff)
	result.reverse()
	return result
def cut(obj, sec):
	return [obj[i:i+sec] for i in range(0,len(obj),sec)]
def hexQ(text):
	return str(text,"utf-8")
def Platform_judgment(text):
	temp=hexQ(text)
	if temp.upper()=='W':
		return 'Windows platform'
	if temp.upper()=='M':
		return 'Windows Phone'
	if temp.upper()=='X':
		return 'Xbox360'
def Version_judgment(text):
	temp1=bytes_to_int(text)
	if temp1==1:
		return 'XNA1.0'
	if temp1==2:
		return 'XNA2.0'
	if temp1==3:
		return 'XNA3.0'
	if temp1==4:
		return 'XNA3.1'
	if temp1==5:
		return 'XNA4.0'
def Compression_judgment(text):
	temp2=bytes_to_int(text)
	if temp2==0:
		return 'Reach'
	elif temp2==1:
		return 'HiDef'
	elif temp2==80:
		return 'Reach'
	elif temp2==81:
		return 'HiDef'
	else:
		return 'unknown'
def bytes_to_number(text):
	temp1=str(binascii.hexlify(text),"utf-8")
	temp2=""
	for i in range(4):
		temp2=temp2 + temp1[-2:-1] +temp1[-1:]
		temp1=temp1[:-2]
	temp2=temp2+""
	return int(temp2,16)
def Identification_identifier(data):
	if data==b"\x03":
		return "System.Collections.Generic.List`1[[Microsoft.Xna.Framework.Rectangle]]"
	elif data==b"\x05":
		return "System.Collections.Generic.List`1[[System.Char]]"
	elif data==b"\x07":
		return "System.Collections.Generic.List`1[[Microsoft.Xna.Framework.Vector3]]"

def XNAUniversalRead(f):
	print(f.name[:-3])
	temp=f.read(3)
	print(hexQ(temp))
	temp=f.read(1)
	print("Target platform:",Platform_judgment(temp))
	temp=f.read(1)
	print("Version:",Version_judgment(temp))
	temp=f.read(1)
	print("Graphics profile:",Compression_judgment(temp))
def XNBConvertWAV_Sound(f):
	XNAUniversalRead(f)
	size=f.read(4)
	print("size:",int.from_bytes(size,'little'))
	temp=f.read(1)
	for i in range(int.from_bytes(temp,'little')):
		temp=f.read(1)
		number1=int.from_bytes(temp,'little')
		temp=f.read(number1)
		Verson=readInt32(f)
		print("Type readers:",hexQ(temp),"Verson:",Verson)
	#
	temp=f.read(1)
	temp=f.read(1)
	#Format
	number2=f.read(4)
	print("Format size:",int.from_bytes(number2,'little'))
	Format_temp=f.read(int.from_bytes(number2,'little'))
	print("Format:",Format_temp)
	number3=f.read(4)
	print("Date size:",int.from_bytes(number3,'little'))
	#Date
	date_temp=f.read(int.from_bytes(number3,'little'))
	#尾部信息
	number4=f.read(4)
	print("Loop start:",int.from_bytes(number4,'little'))
	number5=f.read(4)
	print("Loop length:",int.from_bytes(number5,'little'))
	numbern=f.read(4)
	print("Duration:",int.from_bytes(numbern,'little'),"ms")
	f.close()
	XNA2WAV(size,number2,Format_temp,number3,date_temp)
	#soundfile.write(sys.argv[2],data,samplerate,subtype="MS_ADPCM")
	#Excess(This only serves as a comment)
def XNA2WAV(size,number2,Format_temp,number3,date_temp):
	fnameW=f.name[:-3] + "wav"
	fW=open(fnameW,"wb+")
	fW.write(b"RIFF")
	fW.write(size)
	fW.write(b"WAVE")
	fW.write(b'\x66\x6D\x74\x20')
	fW.write(number2)
	fW.write(Format_temp)
	fW.write(b"data")
	fW.write(number3)
	fW.write(date_temp)
	"""
	#There are some small problems
	fW.write(b"LIST")
	number6=4+4+4+len(os.path.basename(sys.argv[2])[:-4])+1+1
	fW.write(number6.to_bytes(4,byteorder='little', signed=False))
	fW.write(b"INFO")
	fW.write(b"INAM")
	number7=len((sys.argv[2])[:-3])
	fW.write(number7.to_bytes(4,byteorder='little', signed=False))
	fW.write(str.encode(os.path.basename(sys.argv[2])[:-4]))
	fW.write(b'\x00')
	#uchar padding
	fW.write(b'\x00')
	"""
	fW.close()
	
def findchuck(f,string,number):
	#Inefficient solutions
	while True:
		a=f.read(number)
		if a==string:
			break
		f.seek(-3,1)
	return f.tell()


def WAVConvertXNB_Sound(f,sign=None):
	name_AD="AD_" + os.path.basename(sys.argv[2])[:-4] + ".wav"
	if sign==None:
		data, samplerate = soundfile.read(sys.argv[2])
		soundfile.write(name_AD,data,samplerate,subtype="PCM_16")
	f.close()
	fa=wave.open(("./" + name_AD),"rb")
	rate = fa.getframerate()
	nframes = fa.getnframes()
	params = fa.getparams()
	duration = nframes/float(rate)
	duration = int(duration*1000)
	fa.close()
	f=open(fpath,"rb+")
	if sign==None:	
		data, samplerate = soundfile.read(sys.argv[2])
		soundfile.write(name_AD,data,samplerate,subtype="MS_ADPCM")
	f.seek(0,0)
	temp=f.read(4)
	if temp!=b"\x52\x49\x46\x46":
		print("Fail !")
	filesize=f.read(4)
	filesize_str=int.from_bytes(temp,'little')
	temp=f.read(4)
	findchuck(f,b"\x66\x6d\x74\x20",4)
	format_length=f.read(4)
	format=f.read(int.from_bytes(format_length,'little'))
	findchuck(f,b"\x64\x61\x74\x61",4)
	data_length=f.read(4)
	data=f.read(int.from_bytes(data_length,'little'))
	f.close()
	if os.path.isfile(("./" + name_AD)):
		os.remove(("./" + name_AD))
	else:
		print("Suspected read error")
	fnameW=os.path.basename(sys.argv[2])[:-3] + "xnb"
	fW=open(fnameW,"wb+")
	fW.write(b"XNB")
	fW.write(b"m")
	fW.write(b"\x05")
	fW.write(b"\x00")
	fW.write(filesize)
	fW.write(b"\x01")
	fW.write(b"\x31")
	fW.write(b"Microsoft.Xna.Framework.Content.SoundEffectReader")
	temp=0
	fW.write(temp.to_bytes(4,byteorder='little', signed=False))
	fW.write(b"\x00")
	fW.write(b"\x01")
	fW.write(format_length)
	fW.write(format)
	fW.write(data_length)
	fW.write(data)
	fW.write(temp.to_bytes(4,byteorder='little', signed=False))
	fW.write(nframes.to_bytes(4,byteorder='little', signed=False))
	fW.write(duration.to_bytes(4,byteorder='little', signed=False))
	fW.close()
def ReadSong(f):
	XNAUniversalRead(f)
	#size
	temp=readUInt32(f)
	print("XNAsize:",temp)
	number=f.read(1)
	for i in range(int.from_bytes(number,'little')):
		temp=f.read(1)
		number2=int.from_bytes(temp,'little')
		temp=f.read(number2)
		print("Type reader name:",hexQ(temp))
		number2=readUInt32(f)
		print("Verson:",number2)
	temp=f.read(2)
	temp=f.read(1)
	number3=int.from_bytes(temp,'little')
	temp=f.read(number3)
	print("File name:",hexQ(temp))
	temp=f.read(1)
	temp=readInt32(f)
	print("Duration(uncertain):",temp,"ms")
	f.close()
def WriteSong():
	tag=TinyTag.get(sys.argv[2])
	fnameW=os.path.basename(sys.argv[2])[:-3] + "xnb"
	fW=open(fnameW,"wb+")
	fW.write(b"XNB")
	fW.write(b"m")
	fW.write(b"\x05")
	fW.write(b"\x00")
	temp=len(str.encode(os.path.basename(sys.argv[2])))
	number=114+temp
	fW.write(number.to_bytes(4,byteorder='little', signed=False))
	fW.write(b"\x02")
	fW.write(b"\x2a")
	fW.write(b"Microsoft.Xna.Framework.Content.SongReader")
	fW.write(b"\x00\x00\x00\x00")
	fW.write(b"\x2a")
	fW.write(b"Microsoft.Xna.Framework.Content.Int32Reader")
	fW.write(b"\x00\x00\x00\x00")
	fW.write(b"\x00")
	fW.write(b"\x01")
	fW.write(temp.to_bytes(1,byteorder='little', signed=False))
	fW.write(str.encode(os.path.basename(sys.argv[2])))
	fW.write(b"\x02")
	fW.write(int(tag.duration*1000).to_bytes(4,byteorder='little', signed=False))

def XNBConvertPNG_image(f):
	XNAUniversalRead(f)
	filesize=readUInt32(f)
	print("FileSize:",filesize)
	temp=f.read(1)
	for i in range(int.from_bytes(temp,'little')):
		temp1=f.read(1)
		temp=f.read(1)
		if temp==b"\x4d":
			f.seek(-1, 1)
		temp1=int.from_bytes(temp1,'little')
		temp=f.read(temp1)
		temp1=readInt32(f)
		print("Type:",hexQ(temp),"Verson:",temp)
	temp=f.read(2)
	Surface_format=readInt32(f)
	print("Surface format",Surface_format)
	Width=readUInt32(f)
	print("Width:",Width)
	Height=readUInt32(f)
	print("Height:",Height)
	Mip_count=readUInt32(f)
	print("Mip count:",Mip_count)
	for i in range(Mip_count):
		size=readUInt32(f)
		data=f.read(size)
		im=Image.frombytes("RGBA", (Width, Height), data)
		im.save("./"+os.path.basename(sys.argv[2])[:-4]+".png")
def PNGConvertXNB_image(f):
	data_array=PNG_decode(f)
	data_length=len(data_array)
	f.seek(12, 0)
	temp=f.read(1)
	fnameW=os.path.basename(sys.argv[2])[:-3] + "xnb"
	fW=open(fnameW,"wb+")
	fW.write(b"XNB")
	fW.write(b"m")
	fW.write(b"\x05")
	fW.write(b"\x00")
	number=187+data_length
	fW.write(number.to_bytes(4,byteorder='little', signed=False))
	fW.write(b"\x01")
	fW.write(b"\x94")
	fW.write(b"\x01")
	fW.write(b"Microsoft.Xna.Framework.Content.Texture2DReader, Microsoft.Xna.Framework.Graphics, Version=4.0.0.0, Culture=neutral, PublicKeyToken=842cf8be1de50553")
	temp=0
	fW.write(temp.to_bytes(4,byteorder='little', signed=False))
	fW.write(b"\x00\x01")
	temp=0
	fW.write(temp.to_bytes(4,byteorder='little', signed=False))
	f.close()
	img=Image.open(sys.argv[2])
	w=img.width
	h=img.height
	fW.write(w.to_bytes(4,byteorder='little', signed=False))
	fW.write(h.to_bytes(4,byteorder='little', signed=False))
	temp=1
	fW.write(temp.to_bytes(4,byteorder='little', signed=False))
	fW.write(data_length.to_bytes(4,byteorder='little', signed=False))
	for i in data_array:
		fW.write(i.to_bytes(1,byteorder='little', signed=False))
	img.close()
def XNBConvertPNG(f):
	XNAUniversalRead(f)
	filesize=readUInt32(f)
	print("FileSize:",filesize)
	temp=f.read(1)
	for i in range(int.from_bytes(temp,'little')):
		temp=f.read(1)
		if temp==b"\x4d":
			f.seek(-1, 1)
		temp1=int.from_bytes(temp1,'little')
		temp=f.read(temp1)
		temp1=readInt32(f)
		print("Type:",hexQ(temp),"Verson:",temp)
	print("Incomplete")
	
def XNBConvertFonts(f):
	XNAUniversalRead(f)
	filesize=readUInt32(f)
	print("FileSize:",filesize)
	temp=f.read(1)
	for i in range(int.from_bytes(temp,'little')):
		temp1=f.read(1)
		temp=f.read(1)
		if temp==b"\x4d":
			f.seek(-1, 1)
		temp1=int.from_bytes(temp1,'little')
		temp=f.read(temp1)
		temp1=readInt32(f)
		print("Type:",hexQ(temp),"(Verson:",temp1,")")
	temp=f.read(3)
	Surface_format=readInt32(f)
	print("Surface format",Surface_format)
	Width=readUInt32(f)
	print("Width:",Width)
	Height=readUInt32(f)
	print("Height:",Height)
	Mip_count=readUInt32(f)
	print("Mip count:",Mip_count)
	for i in range(Mip_count):
		size=readUInt32(f)
		data=f.read(size)
		im=Image.frombytes("RGBA", (Width, Height), data)
		im.save("./"+os.path.basename(sys.argv[2])[:-4]+".png")
	f.close()

if __name__ == '__main__':
	dll_handle = ctypes.windll.kernel32
	sys_lang = hex(dll_handle.GetSystemDefaultUILanguage())
	if sys_lang=="0x804":
		a="""
	发生错误!
	帮助:
	XNBTool.py <选项> <输入文件>
	作者:冬日-春上 (或者叫SFDA-冬)
	当前版本：0.0.1
	选项:
		-WX  	WAV->XNB
		-XW  	XNB->WAV
		-WX_16 	特殊的转换,可以将PCM_16转换为XNB(PCM_16格式)
		-XSR 	仅打印歌曲在XNA上的信息
		-SWW 	传入.wma以生成XNB文件头
		-XPI 	XNB->PNG 仅能转换images文件夹中的XNB文件
		-PXI 	PNG->XNB 仅转换为images文件夹中的XNB文件
		-XF 	XNA->Font PNG
	注意：此程序可能无法完全转换
	"""
	else:
		a="""
	Error!
	Help:
	XNBTool.py <Option> <Input file>
	Author:Dong Ri Chun Shang (or SFDA-Dong)
	Current version:0.0.1
	Option:
		-WX  	WAV->XNB
		-XW  	XNB->WAV
		-WX_16 	A special conversion can convert the PCM_ 16 Convert to XNB(PCM_16 format)
		-XSR 	Print only the information of songs on XNA
		-SWW 	Pass in .wma to generate XNB file header
		-XPI 	XNB->PNG Only in the images folder
		-PXI 	PNG->XNB Only convert to XNB files in the images folder
		-XF 	XNA->Font PNG
	Note: This program may not be fully converted
	"""
	if len(sys.argv)<=1:
		print(a)
		exit(0)
	fpath=sys.argv[2]
	if not os.path.isfile(fpath):
		print("文件不存在")
		exit(0)
	f=open(fpath,"rb+")
	#file size
	fsize=os.path.getsize(fpath)
	print(os.path.basename(sys.argv[2]))
	Cinput=sys.argv[1][1:].upper()
	if Cinput=="WX_16":
		WAVConvertXNB_Sound(f,1)
	elif Cinput=="XW":
		XNBConvertWAV_Sound(f)
	elif Cinput=="XSR":
		ReadSong(f)
	elif Cinput=="XPI":
		XNBConvertPNG_image(f)
	elif Cinput=="XF":
		XNBConvertFonts(f)
	elif Cinput=="PXI":
		PNGConvertXNB_image(f)
	elif Cinput=="WX":
		WAVConvertXNB_Sound(f)
	elif Cinput=="SWW":
		WriteSong()
	else:
		print(a)
		exit(0)
	print("处理完成")