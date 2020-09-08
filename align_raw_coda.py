"""Produce word alignment within aligned sentences.

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
"""

from alignment import align_words
import itertools as itr
import editdistance
from docopt import docopt
import sys
import re


def _detect_i_d_seuqnces(alignments):
    
    seq_align = {}
    operation_strings = ''
    for alignment in alignments:
        operation_strings += alignment[2]
    
    # if list(re.finditer('(?<!e)i+d+(?!e)', operation_strings)) != []:
    #     print(operation_strings)
    #     for match in re.finditer('(?<!e)i+d+(?!e)', operation_strings):
    #         print('\t', match.group())
    if list(re.finditer('d+i+', operation_strings)) != []:
        print('True')
    for match in re.finditer('i+d+', operation_strings):
        str_span = match.span()
        raw_idx = []
        coda_idx = []
        for i in range(str_span[0], str_span[1]):
            if alignments[i][2] == 'i':
                coda_idx.append(alignments[i][1]-1)
            elif alignments[i][2] == 'd':
                raw_idx.append(alignments[i][0]-1)
            else:
                print('wth man')
        #print(raw_idx, coda_idx)
        prev_r = 0
        for r,c in itr.zip_longest(raw_idx, coda_idx):        
            if r is not None:
                seq_align[r] = []
                seq_align[r].append(c)
                prev_r = r
            else:
                seq_align[prev_r].append(c)
            
    return seq_align



def write_exact_alignment_only(alignments, raw_sent, coda_sent, raw_stream, coda_stream, col_align_stream):
    seqs = _detect_i_d_seuqnces(alignments)

    keys = list(range(max(len(raw_sent), len(coda_sent))))
    words = dict.fromkeys(keys)
    
    for key in words:
        words[key] = {}
        words[key]['raw'] = []
        words[key]['coda'] = []

    visited_coda = []
    for seq in seqs:
        if len(seqs[seq]) == 1:
            words[seq]['raw'].append(raw_sent[seq])
            if seqs[seq][0] is not None:
                words[seq]['coda'].append(coda_sent[seqs[seq][0]])
                visited_coda.append(seqs[seq][0])
            else:
                words[seq-1]['raw'].append(raw_sent[seq-1])
        elif len(seqs[seq]) > 1:
            words[seq]['raw'].append(raw_sent[seq])
            for x in seqs[seq]:
                words[seq]['coda'].append(coda_sent[x])
                visited_coda.append(x)
        else:
            print('why')


    for alignment in alignments:
        current_op = alignment[2]
        prev_idx = alignments.index(alignment)-1
        next_idx = alignments.index(alignment)+1
        if next_idx >= len(alignments):
            next_op = ''
            next_align = (-1,-1,'x',1)
        else:
            next_op = alignments[next_idx][2]
            next_align = alignments[next_idx]

        if prev_idx < 0:
            prev_op = ''
            prev_align = (-1,-1,'x',1)
        else:
            prev_op = alignments[prev_idx][2]
            prev_align = alignments[prev_idx]

        if alignment[0] is None:

            if (prev_op == 'e' and current_op == 'i' and next_op == 'e'):

                hypoth_1 = coda_sent[alignment[1]-2]+coda_sent[alignment[1]-1] #go with e+i
                hypoth_2 = coda_sent[alignment[1]-1]+coda_sent[alignment[1]] # go with i+e
                raw_1 = raw_sent[prev_align[0]-1] #e+i
                raw_2 = raw_sent[next_align[0]-1] #i+e

                dist_1 = editdistance.eval(hypoth_1, raw_1)
                dist_2 = editdistance.eval(hypoth_2, raw_2)

                if dist_1 < dist_2:
                    words[prev_align[0]-1]['coda'].append(coda_sent[alignment[1]-1])
                else:
                    words[next_align[0]-1]['coda'].append(coda_sent[alignment[1]-1])


            elif (prev_op == 'e' and current_op == 'i'):
                if (prev_align[0]-1) in seqs:
                    continue
                elif (alignment[1]-1) in visited_coda:
                    continue
                words[prev_align[0]-1]['coda'].append(coda_sent[alignment[1]-1])
                
            elif next_op not in ['i', 'd']:

                if (next_align[0]-1) in seqs or ((next_align[0]-1) == -2):
                    continue
                elif (alignment[1]-1) in visited_coda:
                    continue
                words[next_align[0]-1]['coda'].append(coda_sent[alignment[1]-1])
            else:
                continue

        elif alignment[1] is None:
            if current_op == 'd' and next_op == 'e':
                if (alignment[0]) in seqs:
                    continue
                elif (alignment[0]-1) in seqs:
                    continue
                words[alignment[0]]['raw'].append(raw_sent[alignment[0]-1])
            elif current_op == 'd' and prev_op == 'e':
                if (alignment[0]-2) in seqs:
                    continue
                elif (alignment[0]-1) in seqs:
                    continue
                words[alignment[0]-2]['raw'].append(raw_sent[alignment[0]-1])
            else:
                continue
        elif (alignment[0] is not None) and (alignment[1] is not None):

            words[alignment[0] - 1]['raw'].append(raw_sent[alignment[0] - 1])
            words[alignment[0] - 1]['coda'].append(coda_sent[alignment[1] - 1])
        else:
            continue

    for key in words:
        if words[key]['raw'] == [] and words[key]['coda'] == []:
            continue
        if words[key]["raw"] == []:
            words[key]["raw"].append('NULL')
        elif words[key]["coda"] == []:
            words[key]["coda"].append('NULL')

        raw_stream.write(f'{" ".join(words[key]["raw"])}\n')
        coda_stream.write(f'{" ".join(words[key]["coda"])}\n')
        col_align_stream.write(f'{" ".join(words[key]["raw"])}\t{" ".join(words[key]["coda"])}\n')

    raw_stream.write('\n')
    coda_stream.write('\n')
    col_align_stream.write('\n')
        


def write_distances_only(distances, raw_sent, coda_sent, file_stream):
    for distance in distances:
        if distance[0] is None:
            file_stream.write('\t<\t')
            file_stream.write(coda_sent[distance[1] - 1])
            file_stream.write(f'{distance}\n')
        elif distance[1] is None:
            file_stream.write(raw_sent[distance[0] - 1])
            file_stream.write('\t>\t')
            file_stream.write(f'{distance}\n')
        else:
            file_stream.write(raw_sent[distance[0] - 1])
            file_stream.write('\t')
            file_stream.write('=' if distance[2] == 'n' else '|')
            file_stream.write('\t')
            file_stream.write(coda_sent[distance[1] - 1])
            file_stream.write(f'\t{distance}\n')
    file_stream.write('\n')


if __name__ == "__main__":
    arguments = docopt(__doc__)
    raw_sentences = open(arguments['--raw'], 'r').readlines()
    coda_sentences = open(arguments['--coda'], 'r').readlines()
    mode = arguments['--mode']

    if mode == 'align':
        raw_output = open(arguments['--raw']+'.align', 'w')
        coda_output = open(arguments['--coda']+'.align', 'w')
        col_align_out = open(arguments['--out']+'.colAlign', 'w')
        col_align_out.write(f'RAW\tCODA\n')
    elif mode == 'basic':
        output = open(arguments['--out']+'.basic', 'w')
    else:
        print(f"Warning: mode: [{arguments['--mode']}] is not valid, falling back to default mode: [align]")
        mode = 'align'
        raw_output = open(arguments['--raw']+'.align', 'w')
        coda_output = open(arguments['--coda']+'.align', 'w')
        col_align_out = open(arguments['--out']+'.colAlign', 'w')
        col_align_out.write(f'RAW\tCODA\n')
    
    for raw,coda in zip(raw_sentences, coda_sentences):

        alignments = align_words(raw.strip(), coda.strip())
        raw_sent = raw.strip().split()
        coda_sent = coda.strip().split()

        if mode == 'align':
            write_exact_alignment_only(alignments, raw_sent, coda_sent, raw_output, coda_output, col_align_out)
            
        elif mode == 'basic':
            write_distances_only(alignments, raw_sent, coda_sent, output)
    
    if mode == 'align':
        print(f'RAW alignments are saved to: {arguments["--raw"]}.align')
        raw_output.close()
        print(f'CODA alignments are saved to: {arguments["--coda"]}.align')
        coda_output.close()
        print(f'Side by side alignments are saved to: {arguments["--out"]}.colAlign')
        col_align_out.close()
    elif mode == 'basic':
        print(f'Basic alignments are saved to: {arguments["--out"]}.basic')
        output.close()