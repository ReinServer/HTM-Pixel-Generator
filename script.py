import os
import re
from PIL import Image
import pytesseract
import cv2

# config
INPUT_FOLDER = "images"
OUTPUT_FOLDER = "output"

OCR_FILE = os.path.join(OUTPUT_FOLDER, "all_hints.txt")
FIXED_FILE = os.path.join(OUTPUT_FOLDER, "fixed_hints.txt")

ERROR_LOG = os.path.join(OUTPUT_FOLDER, "errors.txt")
OVERWRITE_LOG = os.path.join(OUTPUT_FOLDER, "overwrites.txt")

FINAL_IMAGE_NAME = "final_coin_image.png"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PIXEL_REGEX = r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*#([0-9A-Fa-f]{6})\s*\)"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
open(ERROR_LOG, "w", encoding="utf-8").close()
open(OVERWRITE_LOG, "w", encoding="utf-8").close()

# hardcoded character replacements based on common OCR mistakes observed
CHAR_REPLACE = {
    "@": "#",
    "G": "6",
    "H": "#",
    "I": "1",
    "O": "0",
    "Q": "0",
    "S": "5",
    "Z": "2",
    "l": "1",
    ".": ","
}

# normalize text
def normalize_text(text):
    text = re.sub(r"(?<![\s,])\(", " (", text)
    text = re.sub(r"\)\)+", ")", text)
    for k, v in CHAR_REPLACE.items():
        text = text.replace(k, v)
    text = re.sub(r"\(\s*(\d+),(\d+),", r"(\1, \2,", text)
    text = re.sub(r"\(\s*(\d+),\s*(\d+),\s*#([0-9A-Fa-f]{6})\s*\)\s*\n\s*\(", r"(\1, \2, #\3) (", text)
    def fix_hex(m):
        h = m.group(1).replace("O","0").replace("I","1").replace("l","1")
        return "#" + h
    text = re.sub(r"#([0-9OIl]{6})", fix_hex, text)
    text = "".join(c for c in text if c.isprintable())
    return text

# ocr images if fixed_hints.txt isn't found
def run_ocr_and_generate_files():
    print("fixed_hints.txt not found. Running OCR...")
    ocr_entries = []
    for file in sorted(os.listdir(INPUT_FOLDER)):
        if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            continue
        path = os.path.join(INPUT_FOLDER, file)
        print(f"[+] OCRing {file}")
        try:
            img = cv2.imread(path)
            if img is None: raise Exception("cv2.imread returned None")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
            temp_path = os.path.join(OUTPUT_FOLDER, "temp_processed.png")
            cv2.imwrite(temp_path, thresh)
            text = pytesseract.image_to_string(Image.open(temp_path))
            cleaned = normalize_text(text)
            matches = re.findall(PIXEL_REGEX, cleaned)
            has_valid = len(matches) > 0
            malformed = False
            all_paren = re.findall(r"\((.*?)\)", cleaned)
            for p in all_paren:
                if "," in p and "#" in p:
                    if not re.match(r"\s*\d+\s*,\s*\d+\s*,\s*#[0-9A-Fa-f]{6}\s*$", p):
                        malformed = True
                        break
        except Exception as e:
            print(f"[!] ERROR OCR {file}: {e}")
            cleaned=""
            has_valid=False
            malformed=True
        is_broken = (not has_valid) or malformed
        if not has_valid:
            with open(ERROR_LOG,"a",encoding="utf-8") as ef:
                ef.write(f"[NO VALID TUPLES] {file}\n{cleaned}\n\n")
        if malformed:
            with open(ERROR_LOG,"a",encoding="utf-8") as ef:
                ef.write(f"[MALFORMED OCR] {file}\n{cleaned}\n\n")
        ocr_entries.append((is_broken,file,cleaned))
    # Sort broken first
    broken = [e for e in ocr_entries if e[0]]
    good = [e for e in ocr_entries if not e[0]]
    output=""
    output+="#########################################\n############ BROKEN HINTS ###############\n#########################################\n\n"
    for _,f,t in broken: output+=f"### {f} ###\n{t}\n\n"
    output+="#########################################\n############   GOOD HINTS   #############\n#########################################\n\n"
    for _,f,t in good: output+=f"### {f} ###\n{t}\n\n"
    with open(OCR_FILE,"w",encoding="utf-8") as f:
        f.write(output)
    print(f"All hints saved to {OCR_FILE}")
    revalidate_and_write_fixed(OCR_FILE,FIXED_FILE)

# revalidate hints
def revalidate_and_write_fixed(source_file,target_file):
    with open(source_file,"r",encoding="utf-8") as f:
        src_text=f.read()
    blocks = re.split(r"(### .+? ###)",src_text)
    entries=[]
    for i in range(1,len(blocks),2):
        header = blocks[i].strip()
        body = blocks[i+1].strip()
        is_broken=False
        errors=[]
        matches = re.findall(PIXEL_REGEX,body)
        if len(matches)!=4:
            is_broken=True
            errors.append(f"{header}: {len(matches)} pixel tuples found (must be EXACTLY 4).")
        # malformed tuples
        all_paren = re.findall(r"\((.*?)\)",body)
        for p in all_paren:
            if "," in p and "#" in p:
                if not re.match(r"\s*\d+\s*,\s*\d+\s*,\s*#[0-9A-Fa-f]{6}\s*$",p):
                    is_broken=True
                    errors.append(f"{header}: Malformed tuple → ({p})")
        entries.append((is_broken,header,body,errors))
    # log errors
    with open(ERROR_LOG,"a",encoding="utf-8") as ef:
        for broken_flag,header,_,errs in entries:
            if broken_flag:
                for err in errs: ef.write(err+"\n")
    broken=[e for e in entries if e[0]]
    good=[e for e in entries if not e[0]]
    with open(target_file,"w",encoding="utf-8") as f:
        f.write("#########################################\n############ BROKEN HINTS ###############\n#########################################\n\n")
        for _,header,body,_ in broken: f.write(f"{header}\n{body}\n\n")
        f.write("#########################################\n############   GOOD HINTS   #############\n#########################################\n\n")
        for _,header,body,_ in good: f.write(f"{header}\n{body}\n\n")
    print(f"Revalidated hints written to {target_file}")

# build image and log overwrites
def build_image_from_fixed():
    if not os.path.exists(FIXED_FILE): raise FileNotFoundError(f"{FIXED_FILE} missing")
    with open(FIXED_FILE,"r",encoding="utf-8") as f: raw_text=f.read()
    text = normalize_text(raw_text)
    img32 = Image.new("RGB",(32,32),(0,0,0))
    pixels = img32.load()
    filled=0
    overwrites_count=0
    seen=set()
    pixel_source={}
    blocks = re.split(r"(### .+? ###)", text)
    for i in range(1,len(blocks),2):
        header=blocks[i].strip()
        body=blocks[i+1]
        current_file=header.replace("###","").strip()
        tuples_here = re.findall(PIXEL_REGEX, body)
        if len(tuples_here)==0:
            with open(ERROR_LOG,"a",encoding="utf-8") as ef:
                ef.write(f"[NO TUPLES IN BLOCK] {current_file}\n{body}\n\n")
            continue
        for x_str,y_str,hexcode in tuples_here:
            try:
                x=int(x_str); y=int(y_str)
                r=int(hexcode[0:2],16); g=int(hexcode[2:4],16); b=int(hexcode[4:6],16)
            except Exception:
                with open(ERROR_LOG,"a",encoding="utf-8") as ef:
                    ef.write(f"[MALFORMED TUPLE] {current_file}\nTUPLE: ({x_str},{y_str},#{hexcode})\n\n")
                continue
            if not (0<=x<32 and 0<=y<32):
                with open(ERROR_LOG,"a",encoding="utf-8") as ef:
                    ef.write(f"[OUT OF RANGE] {current_file}\n({x},{y},#{hexcode})\n\n")
                continue
            new_color=(r,g,b)
            old_color=pixels[x,y]
            if (x,y) in seen:
                overwrites_count+=1
                original_file=pixel_source[(x,y)]
                new_file=current_file
                if new_color!=old_color:
                    print(f"/!\\ REAL OVERWRITE at ({x},{y})")
                    print(f"    Originally from: {original_file}")
                    print(f"    Overwritten by : {new_file}")
                    print(f"    Old color: {old_color}, New color: {new_color}")
                    pixels[x,y]=(255,0,255)
                    pixel_source[(x,y)]=f"{original_file} -> {new_file}"
                else:
                    with open(OVERWRITE_LOG,"a",encoding="utf-8") as of:
                        of.write(f"IDENTICAL OVERWRITE at ({x},{y})\n  Original: {original_file}\n  Duplicate: {new_file}\n  Color: {old_color}\n\n")
                continue
            filled+=1
            seen.add((x,y))
            pixel_source[(x,y)]=current_file
            pixels[x,y]=new_color
    output_path=os.path.join(OUTPUT_FOLDER,FINAL_IMAGE_NAME)
    img32.save(output_path)
    percent=round(filled/1024*100,2)
    print("\nImage generation complete!")
    print(f"   Saved to: {output_path}")
    print(f"   Pixels filled: {filled}/1024 ({percent}%)")
    if overwrites_count>0:
        print(f"   /!\\ Overwritten pixels (count): {overwrites_count}")
    print(f"Errors logged: {ERROR_LOG}")
    print(f"Identical overwrites logged: {OVERWRITE_LOG}")

if not os.path.exists(FIXED_FILE):
    run_ocr_and_generate_files()
else:
    print("fixed_hints.txt exists > revalidating for EXACTLY 4 tuples.")
    revalidate_and_write_fixed(FIXED_FILE,FIXED_FILE)

build_image_from_fixed()

