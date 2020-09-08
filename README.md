# Word Alignment

The purpose of this code is to find alignments two parallel sentences on the word level.

## Basic Approach
For each sentence, a basic edit distance based alignment is performed. This basic alignment is then followed by a post-processing step that looks at the context of the edit distance operations and decides the best match between the tokens.

## Assumptions
- Sentences are aligned.
- No change to the word order.
#
## Contents
- `align_raw_coda.py` main script that produces the alignments.
- `alignmnet.py` basic alignmnet script that is used in the initial step.
- `requirements.txt` necessary dependencies needed to run the scripts.

## Requirements
- Python 3.5 and above.

To use, you need to first install the necessary dependencies by running the following command:
```
pip install -r requirements.txt
```
#
## Usage
```
Usage:
    align_raw_coda (-r RAWSENT | --raw=RAWSENT)
                (-c CODASENT | --coda=CODASENT)
                (-m MODE | --mode=MODE)
                (-o OUTSTR | --out OUTSTR)
                [-h HELP]

Options:
  -r RAWSENT --raw=RAWSENT  RAW sentences file
  -c CODASENT --coda=CODASENT  CODA sentences file
  -m MODE --mode=MODE  
        Two modes to choose from: 
            1- 'align' To produce full alignments (one-to-many and many-to-one)
            2- 'basic' To produce basic alignments with operation and distance details (one-to-one)
            [default: align]
  -o OUTSTR --out=OUTSTR  Prefix for single output files
  -h --help  Show this screen.
```
#
## Examples

### Inputs
### Raw sentence
```
خالد : اممممممممممممممممم اذا بتروحون العصر اوكي ماعندي مانع بس لاتتأخرون
```
### CODA sentence
```
خالد : امم اذا بتروحون العصر اوكيه ما عندي مانع بس لا تتأخرون
```
#
### Full alignment
```
python align_raw_coda.py -r sample/sample.raw.txt -c sample/sample.coda.txt -m align -o sample/sample_text
```

### Output
```
RAW alignments are saved to: sample/sample.raw.txt.align
CODA alignments are saved to: sample/sample.coda.txt.align
Side by side alignments are saved to: sample/sample_text.colAlign
```
### Side by side view (found in the _.colAlign_ file)

|RAW| CODA|
|---|-----|
|خالد | خالد |
|: | : |
|اممممممممممممممممم | امم |
|اذا | اذا |
|بتروحون | بتروحون |
|العصر | العصر |
|اوكي | اوكيه |
|ماعندي | ما عندي |
|مانع | مانع |
|بس | بس |
|لاتتأخرون | لا تتأخرون |

### Notes on output
You can notice here whenever there is a _split_ or _merge_ on either side they are collapsed on the respective side, thus, we can have one-to-many, and many-to-one cases.

#

### Basic alignment
```
python align_raw_coda.py -r sample/sample.raw.txt -c sample/sample.coda.txt -m basic -o sample/sample_text
```
### Output
```
Basic alignments are saved to: sample/sample_text.basic
```
|RAW|op|CODA|Alignment Details|
|- |- |- |- |
|خالد| =| خالد| (1, 1, 'n', 0)|
|:| =| :| (2, 2, 'n', 0)|
|اممممممممممممممممم| \|| امم| (3, 3, 'e', 1.7)|
|اذا| =| اذا| (4, 4, 'n', 1.7)|
|بتروحون| =| بتروحون| (5, 5, 'n', 1.7)|
|العصر| =| العصر| (6, 6, 'n', 1.7)|
|اوكي| \|| اوكيه| (7, 7, 'e', 2.1)|
| |<| ما|(None, 8, 'i', 3.1)|
|ماعندي| \|| عندي| (8, 9, 'e', 3.7)|
|مانع| =| مانع| (9, 10, 'n', 3.7)|
|بس| =| بس| (10, 11, 'n', 3.7)|
| |<| لا|(None, 12, 'i', 4.7)|
|لاتتأخرون| \|| تتأخرون| (11, 13, 'e', 5.2)|

### Notes on output
- Operations (op) are defined as follows:

|op|Decription|
|-|-|
|=|  No change|
|\||  Edit|
|< | Insertion|
|> | Deletions|

- Alignment Details is a compact representation of the alignment:
```
(<source_idx>, <targe_idx>, op, editdistance_score)
```
