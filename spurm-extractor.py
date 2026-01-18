import struct, sys, os, zlib

# hello sorry for the shitty code yet again

# filter coefficients for the ps1 adpcm shit
K0 = [0,60,115,98,122]
K1 = [0,0,-52,-55,-60]

def write_wav(p,s,r=22050,lstart=None,lend=None): # yes i had to program THIS without using any libraries related to wav files
    dsz = len(s)*2 # data size
    ssz = 60 if lstart is not None else 0 # samp size
    rsz = 4+(8+16)+(8+dsz)
    if lstart is not None and lend is not None: rsz += 8+60
    with open(p,"wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I",rsz))
        f.write(b"WAVE")

        f.write(b"fmt ")
        f.write(struct.pack("<IHHIIHH",
            16,     # chunk size
            1,      # PCM
            1,      # mono
            r,
            r*2,
            2,
            16
        ))
        # smpl chunk w/ loop
        if lstart is not None and lend is not None:
            f.write(b"smpl")
            f.write(struct.pack("<I",60))
            f.write(struct.pack("<9I",
                0,0,
                int(1_000_000_000//r),
                60,0,
                0,0,
                1,0
            ))
            f.write(struct.pack("<6I",
                0,
                0,
                lstart,
                lend,
                0,0
            ))
        f.write(b"data")
        f.write(struct.pack("<I",dsz))
        for i in s: f.write(struct.pack("<h",i))

def trimzeros(d,t=8):
    for i in range(len(d)):
        if abs(d[i]) > t: return d[i:],i
    return d,0

def detectsampend(d,s=0):
    bad = 0
    blm = 8
    for i in range(s,len(d),16):
        b = d[i:i+16]
        if len(b) < 16:
            return i

        h = b[0]
        shift = h & 0x0F
        pred  = (h>>4) & 0x0F

        invalid = False
        if shift > 12 or pred > 4: invalid = True
        if b[1] & 0xF0: invalid = True

        if invalid:
            bad += 1
            if bad >= blm: return i
        else: bad = 0
    return len(d)

def split(ind):
    samps = []
    cur = bytearray()
    bad_blocks = 0

    for i in range(0,len(ind),16):
        b = ind[i:i+16]
        if len(b) < 16:
            break
        h = b[0]
        shift = h & 0x0F
        pred  = (h>>4) & 0x0F
        f = b[1]
        # detect garbage shit
        if shift > 12 or pred > 4 or (f & 0xF0):
            bad_blocks += 1
            if bad_blocks >= 8:
                break
            continue
        else:
            bad_blocks = 0
        cur += b
        if f & 0x01:
            if len(cur) >= 16*3:  # min size
                samps.append(bytes(cur))
            cur = bytearray()
    return samps

def to16(x): 
    return max(-32768,min(32767,x))

def decPSX(ind):
    pcm = []
    hist1 = 0
    hist2 = 0
    lstart = None
    lend = None

    for i in range(0,len(ind),16):
        b = ind[i:i+16]
        # flag bits 7-0 (0000xRSE)
        # x = ignore bit
        # R = LOOP REPEAT
        # S = LOOP START
        # E = LOOP END
        if len(b) < 16:
            break
        f = b[1]
        if (f & 0x06) == 0x06 and lstart is None:
            lstart = len(pcm)

        h = b[0]
        shift = h & 0x0F
        fidx = (h>>4) & 0x07
        if fidx > 4: fidx = 0
        k0 = K0[fidx]
        k1 = K1[fidx]
        
        for i in b[2:]:
            for x in (0,4):
                nib = (i>>x) & 0x0F
                if nib >= 8: nib -= 16
                s = (nib<<12)>>shift
                s += (hist1*k0+hist2*k1)>>6
                s = to16(s)
                hist2 = hist1
                hist1 = s
                pcm.append(s)

        if f & 0x01:
            lend = len(pcm)-1
            break
    return pcm,lstart,lend

# first time handling adpcm haha

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    print(f"SPUrm PS1 Audio Extractor v0.1\n\nUsage: python {sys.argv[0]} [insert input file here!!!]")
    sys.exit(1)

try: 
    if path.lower().endswith('.bin') or path.lower().endswith('.psf'): f = open(path,"rb")
    else:
        print("INVALID: Not a .bin (PS1 SPU RAM dump) or a .psf (PlayStation Sound Format) file!")
        sys.exit(1)
except FileNotFoundError:
    print("INVALID: File not found!")
    sys.exit(1)

if os.path.splitext(path)[1] == '.bin': # converts ram dumps to wav files
    i = f.read()
    end = detectsampend(i,4096)
    smp = split(i[4096:end])
elif os.path.splitext(path)[1] == '.psf': # converts psf files to wav files
    f = open(path,"rb+")
    if f.read(3) != b"PSF":
        print("INVALID: PSF file header is incorrect!")
        f.close()
        sys.exit(1)
    elif f.read(1) != b"\x01":
        print("INVALID: PSF file is not a PS1-type file!")
        f.close()
        sys.exit(1)
    elif b'[TAG]' not in f.read():
        print("INVALID: PSF file lacks tags!")
        f.close()
        sys.exit(1)
    f.seek(0)

    # eliminates tag attributes at end
    i = f.read()[16:]
    f.close()
    f = open(f"{path}_tempdecomp.bin",'wb+')
    i = zlib.decompress(i.split(b'[TAG]')[0])
    f.write(i)

    if b"PS-X EXE\x00\x00\x00\x00\x00\x00\x00\x00" not in i:
        print("INVALID: Decompressed PSF data header is incorrect!")
        f.close()
        sys.exit(1)
    print("Successfully decompressed PSF data!")

    if b"pBAV" not in i:
        print("INVALID: Decompressed PSF data either lacks VAB sample data, or is invalid!")
        f.close()
        sys.exit(1)
    f.seek(i.index(b"pBAV")+4)

    print("===========================================")
    print(f"VAB Version: {int.from_bytes(f.read(4),"little")}")
    f.seek(f.tell()+8)
    if f.read(2) != b'\xEE\xEE':
        print("INVALID: VAB data may be invalid...")
        f.close()
        sys.exit(1)

    nprog = int.from_bytes(f.read(2),"little") # num of programs - 1 (midi related)
    ntons = int.from_bytes(f.read(2),"little")   # num of tones (max = 16 tones per program)
    nvags = int.from_bytes(f.read(2),"little")-1 # num of programs (midi related)

    print(f"# of VAGs/Samples: {nvags}") # haha VAGgot
    f.seek(f.tell()+8+(0x800)+((nprog)*0x200)+0x200)
    fst = f.tell()
    f.close()
    os.remove(f"{path}_tempdecomp.bin")

    end = detectsampend(i,fst)
    smp = split(i[fst:end])

ox = 0
for i,s in enumerate(smp):
    pcm,lstart,lend = decPSX(s)

    if os.path.splitext(path)[1] == '.psf':
        pcm,trim = trimzeros(pcm)
        if lstart is not None:
            lstart = max(0, lstart-trim)
        if lend is not None:
            lend = max(0, lend-trim)
    write_wav(f"{path}_sample{ox}.wav",pcm,22050,lstart,lend)
    #with open(f"{path}_sample{i}.bin","wb") as o:
    #    for v in pcm:
    #        o.write(struct.pack("<h",v))
    print(f"Wrote sample {ox}! ({len(pcm)} samples)")
    ox += 1
print("All finished! Note: Be aware that there might be some garbage data that got undetected.")
