# Lists of PS1 SPU Tools

## SPUrm PS1 Audio Extractor (I apologise for the name...)
* Filename: ``spurm-extractor.py``

### *WARNING:* SHITTY CODE INSIDE THE FILE!!!

The **SPUrm PS1 Audio Extractor** can convert an entire SPU RAM dump (containing audio samples) or a .psf file into individual ``.wav`` files, which are the samples.
\

**Usage:** ``python spurm-extractor.py [inputfile]``

** **

* **Requires...**
  - [**Python**](https://www.python.org/)
  - (Optional) A PS1 emulator that has a feature where it dumps the SPU's ram, like [**DuckStation**](https://duckstation.org/), or some other emulator that has that specifc feature.

** **
 
* **Features to Add/Implement in Later...**
  - Option arguments, such as either wanting to export individual samples, or all of the samples in one ``.wav`` file.

Update (17-1-26): PSF support has been added!

** **

I used this for reference, while programming this: https://psx-spx.consoledev.net/soundprocessingunitspu/

The SPU is basically just an advanced version of the SNES's SPC audio chip. Which is very funny, considering that Sony worked with Nintendo on the first prototype of the PlayStation, as well as Ken Kutaragi being both the designer of the SNES's audio chip and the creator of the PlayStation.

** **

This thingamajig took me around 1-2 days to program, as this was my very first time programming with ADPCM.

Getting the PS1 ADPCM decoder to work was simple, but implementing the garbage data detection system (which eliminates the reverb bytes and the first 4 kb) and the loop point detection system was no easy task, haha.

Programming the complicated features was very hard, but fun. I guess I'm a masochist for nothing.
