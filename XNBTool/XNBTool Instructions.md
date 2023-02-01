# XNBTool Instructions

## Detailed function

| Content | Folder    | Whether it can be converted |
| ------- |:---------:|:---------------------------:|
|         | fonts     | Incomplete                  |
|         | images    | YES                         |
|         | music     | Incomplete                  |
|         | particles | No                          |
|         | reanim    | No                          |
|         | sound     | YES                         |
|         | video     | No                          |

## Requirements

Python version 3.7 or above is required

```
pip install Pillow
pip install soundfile
pip install tinytag
```

## Matters needing attention

The generated file will be generated in the XNBTool directory

Since no error feedback is written, it may be forced to write

## Getting Started

- XNBTool.py    <Option>    <input file>

```
    
-WX
    {
    WAV->XNB
    Only WAV without encryption is supported
    The encryption used by the converted XNB is Microsoft ADPCM
    You can try to import music files in other formats but most will not succeed
    Example:
        XNBTool -WX dancer.wav
    }
-XW
    {
    XNB->WAV
    Note: The default player of the system may not play
    }
-WX_16
    {
    WAV->XNB
    The converted XNB is encrypted to PCM_16
    A special conversion
    It is only necessary to be born
    }
-XSR
    {
    read sound xnb
    Print only the information of songs on XNA
    }
-SWW
    {
    WMA--Create-->XNB
    Store song information in XNB
    }
-XPI
    {
    XNB->PNG
    Used to convert XNB files in the images folder
    }
-PXI
    {
    PNG->XNB
    Used to convert to XNB files in the images folder
    }
-XF
    {
    XNB->Font PNG
    Used to convert XNB in the fonts folder
    }
```

## Use platform

In theory, these three platforms are compatible, but I haven't tested them

| ***Windwos*** | ***Android*** | ***Linux*** |
| ------------- | ------------- | ----------- |

## Recommended player

###### Windows:    Foobar2000+vgmstream

Foobar2000:[https://www.foobar2000.org/]()

Vgmstream:[GitHub - vgmstream/vgmstream: vgmstream - A library for playback of various streamed audio formats used in video games.](https://github.com/vgmstream/vgmstream)

##### Android:

##### Linux:

## Contact

You can visit Baidu Post Bar to find me

Post Bar ID:565402835

## Author(Initial)

###### Chinese net name:冬日-春上

(English) net name:SFDA-冬( SFDA-Dong )

## Original intention

Just for your own use
