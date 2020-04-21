# TWayFoil

## What is `TWayFoil`?
* TWayFoil is an image-to-binary converter.

## How to use `TWayFoil`?
* You can drag the file to TWayFoil.exe, or execute the command `python TWayFoil.exe <PATH_TO_FILE>`
* You can directly open the executable file, enter the command line mode and enter the specified path to convert the file

## What is the principle of `TWayFoil`?
* Long text warning
### 2.0.0 core (202003152029):
* Introduction:
    * Four bytes to one pixel: four bytes (0x78,0xf1,0xd1,0x9a) are converted into AARRGGBB color (0x78f1d19a) according to 0-> a, 1-> r, 2-> g, b-> 3
    * Core: In the picture's pixel list, take the last bit of the last pixel as the extra bytes of the end pixel and delete the extra pixel length at the end
    * image.tobytes returns an enumerable list of bytes containing all pixel colors
    * For example image.bytes = b'0x7f / 0x44 / 0xaf / 0x7d / 0x1a / 0x89 / 0x11 / 0x56 / 0xac / 0xcc / 0xab / 0x67 / 0xfa / 0xda / 0xcb / 0x67 / 0x09 / 0x87 / 0x4a / 0xc8 / 0 0x6d / 0x00 / 0x02 '
* About the function of image to byte code
    * The total length of the original bytecode indicated is 4 times:
        *-> 7f ad 1a 86 ab 6a 87 03 00 | original pixel list, note 1
        *-> 7f ad 1a 86 ab 6a 87 03 00 00 00 04 | L = 0, which means that the total length of the original bytecode is a multiple of 4.
        *-> 7f ad 1a 86 ab 6a 87 03 | Because L = 3 (bin: 11), delete the last pixel
        *-> 7fad1a86, ab6a8703 | The final pixel group, the bytecode of the previous step will be stored as a binary file
    * The total length of the original bytecode is not 4 times (the above image):
        *-> 7f 44 af 7d 1a 89 11 56 ac cc ab 67 fa da cb 67 09 87 4a c8 75 6d 00 02 | Original pixel list, note 2
        *-> 7f 44 af 7d, 1a 89 11 56, ac cc ab 67, fa da cb 67, 09 87 4a c8 75 6d 00 02 | L = 01, Note 3
        *-> 7f 44 af 7d, 1a 89 11 56, ac cc ab 67, fa da cb 67, 09 87 4a c8 75 6d | L = 00 delete the end count byte itself and delete L bytes
        *-> 7f 44 af 7d 1a 89 11 56 ac cc ab 67 fa da cb 67 09 87 4a c8 75 6d | The final binary bytecode will be stored as a binary file
    * Note: 
        * (1) The last digit is regarded as the number of digits by default
        * (2) The total length of the bytecode returned by the tobytes function of the local image is always a multiple of 4.
        * (3) the number of meaningless bytes at the end (excluding itself), the normal L value is 0 ~ 3
    * Sub IDEA 1: Take the last two bits (00 ~ 11) of the last pixel as the length
* About the function of bytecode to image (example, the process is equivalent to the reverse process of the previous example)
    * Total length of byte code is not 4 times:
        *-> 8a 76 47 3f 4c 9b 7a 06 4b 7d 9a 4c 8e 67 00 f8 ff ca bd | original bytecode
        *-> 8a 76 47 3f, 4c 9b 7a 06, 4b 7d 9a 4c, 8e 67 00 f8, ff ca bd 00 | Add 1 ~ 3 bytes to complete the pixel, which is L = 01 (in this example )
        *-> 8a 76 47 3f, 4c 9b 7a 06, 4b 7d 9a 4c, 8e 67 00 f8, ff ca bd 01 | Modify the last byte to L ("ff ca bd 01" in this example)
        *-> 0x8a76473f, 0x4c9b7a06,0x4b7d9a4c, 0x8e6700f8,0xffcabd01 | In the final pixel group, the byte code of the previous step will be equivalently stored as a picture
    * The total length of the bytecode is 4 times:
        *-> 8a 76 4f 4c 9b 7a 06 7d 9a 4e 67 00 f8 fa bd e5 ac 6d 9f 89 | original bytecode
        *-> 8a 76 4f 4c 9b 7a 06 7d 9a 4e 67 00 f8 fa bd e5 ac 6d 9f 89 00 00 00 00 | Add four bytes (representing an empty pixel)
        *-> 8a764f4c, 9b7a067d, 9a4e6700, f8fabde5, ac6d9f89,00000000 | In the final pixel group, the bytecode of the previous step will be equivalently stored as a picture

## Does `TWayFoil` have an open source license?
* `TWayFoil` is now used * MIT [License] (LICENCE) *