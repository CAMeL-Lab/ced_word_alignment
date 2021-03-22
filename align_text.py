"""Produce word alignment within aligned sentences.

Usage:
    align_text.py (-s SOURCE | --source=SOURCE)
               (-t TARGET | --target=TARGET)
               (-m MODE | --mode=MODE)
               (-o OUTPUT | --out OUTPUT)
    align_text.py (-h | --help) 

Options:
  -s SOURCE --source=SOURCE
        source/reference/gold sentences file
  -t TARGET --target=TARGET
        target/hypothesis/prediction sentences file
  -m MODE --mode=MODE
        Two modes to choose from: 
            1- 'align' To produce full alignments (one-to-many and many-to-one)
            2- 'basic' To produce basic alignments with operation and distance details (one-to-one)
  -o OUTPUT --output=OUTPUT
        Prefix for single output files
  -h --help
        Show this screen.
"""


import sys
import re
import itertools as itr
import editdistance
from docopt import docopt
from alignment import align_words


def _detect_i_d_seuqnces(alignments):
    seq_align = {}
    operation_strings = ''
    for alignment in alignments:
        operation_strings += alignment[2]

    if list(re.finditer('d+i+', operation_strings)) != []:
        print('True')
    for match in re.finditer('i+d+', operation_strings):
        str_span = match.span()
        src_idx = []
        trg_idx = []
        for i in range(str_span[0], str_span[1]):
            if alignments[i][2] == 'i':
                trg_idx.append(alignments[i][1]-1)
            elif alignments[i][2] == 'd':
                src_idx.append(alignments[i][0]-1)
            else:
                print('wth man')
        prev_r = 0
        for r,c in itr.zip_longest(src_idx, trg_idx):        
            if r is not None:
                seq_align[r] = []
                seq_align[r].append(c)
                prev_r = r
            else:
                seq_align[prev_r].append(c)

    return seq_align


def write_exact_alignment_only(alignments, src_sent, trg_sent, src_stream, trg_stream, col_align_stream):
    seqs = _detect_i_d_seuqnces(alignments)

    keys = list(range(max(len(src_sent), len(trg_sent))))
    words = dict.fromkeys(keys)

    for key in words:
        words[key] = {}
        words[key]['src'] = []
        words[key]['trg'] = []

    visited_target = []
    for seq in seqs:
        if len(seqs[seq]) == 1:
            words[seq]['src'].append(src_sent[seq])
            if seqs[seq][0] is not None:
                words[seq]['trg'].append(trg_sent[seqs[seq][0]])
                visited_target.append(seqs[seq][0])
            else:
                words[seq-1]['src'].append(src_sent[seq-1])
        elif len(seqs[seq]) > 1:
            words[seq]['src'].append(src_sent[seq])
            for x in seqs[seq]:
                words[seq]['trg'].append(trg_sent[x])
                visited_target.append(x)
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

            if (prev_op == 's' and current_op == 'i' and next_op == 's'):

                hypoth_1 = trg_sent[alignment[1]-2]+trg_sent[alignment[1]-1] #go with e+i
                hypoth_2 = trg_sent[alignment[1]-1]+trg_sent[alignment[1]] # go with i+e
                src_1 = src_sent[prev_align[0]-1] #e+i
                src_2 = src_sent[next_align[0]-1] #i+e

                dist_1 = editdistance.eval(hypoth_1, src_1)
                dist_2 = editdistance.eval(hypoth_2, src_2)

                if dist_1 < dist_2:
                    words[prev_align[0]-1]['trg'].append(trg_sent[alignment[1]-1])
                else:
                    words[next_align[0]-1]['trg'].append(trg_sent[alignment[1]-1])

            elif (prev_op == 's' and current_op == 'i'):
                if (prev_align[0]-1) in seqs:
                    continue
                elif (alignment[1]-1) in visited_target:
                    continue
                words[prev_align[0]-1]['trg'].append(trg_sent[alignment[1]-1])

            elif next_op not in ['i', 'd']:

                if (next_align[0]-1) in seqs or ((next_align[0]-1) == -2):
                    continue
                elif (alignment[1]-1) in visited_target:
                    continue
                words[next_align[0]-1]['trg'].append(trg_sent[alignment[1]-1])
            else:
                continue

        elif alignment[1] is None:
            if current_op == 'd' and next_op == 's':
                if (alignment[0]) in seqs:
                    continue
                elif (alignment[0]-1) in seqs:
                    continue
                words[alignment[0]]['src'].append(src_sent[alignment[0]-1])
            elif current_op == 'd' and prev_op == 's':
                if (alignment[0]-2) in seqs:
                    continue
                elif (alignment[0]-1) in seqs:
                    continue
                words[alignment[0]-2]['src'].append(src_sent[alignment[0]-1])
            else:
                continue
        elif (alignment[0] is not None) and (alignment[1] is not None):

            words[alignment[0] - 1]['src'].append(src_sent[alignment[0] - 1])
            words[alignment[0] - 1]['trg'].append(trg_sent[alignment[1] - 1])
        else:
            continue

    for key in words:
        if words[key]['src'] == [] and words[key]['trg'] == []:
            continue
        if words[key]['src'] == []:
            words[key]['src'].append('NULL')
        elif words[key]['trg'] == []:
            words[key]['trg'].append('NULL')

        src_stream.write(f'{" ".join(words[key]["src"])}\n')
        trg_stream.write(f'{" ".join(words[key]["trg"])}\n')
        col_align_stream.write(f'{" ".join(words[key]["src"])}\t{" ".join(words[key]["trg"])}\n')

    src_stream.write('\n')
    trg_stream.write('\n')
    col_align_stream.write('\n')


def write_distances_only(distances, src_sent, trg_sent, file_stream):
    for distance in distances:
        if distance[0] is None:
            file_stream.write('\t<\t')
            file_stream.write(trg_sent[distance[1] - 1])
            file_stream.write(f'\t{distance}\n')
        elif distance[1] is None:
            file_stream.write(src_sent[distance[0] - 1])
            file_stream.write('\t>\t')
            file_stream.write(f'\t{distance}\n')
        else:
            file_stream.write(src_sent[distance[0] - 1])
            file_stream.write('\t')
            file_stream.write('=' if distance[2] == 'n' else '|')
            file_stream.write('\t')
            file_stream.write(trg_sent[distance[1] - 1])
            file_stream.write(f'\t{distance}\n')
    file_stream.write('\n')


if __name__ == "__main__":
    arguments = docopt(__doc__)
    print(arguments)
    src_sentences = open(arguments['--source'], 'r').readlines()
    trg_sentences = open(arguments['--target'], 'r').readlines()
    mode = arguments['--mode']

    if mode == 'align':
        src_output = open(arguments['--source']+'.align', 'w')
        trg_output = open(arguments['--target']+'.align', 'w')
        col_align_out = open(arguments['--output']+'.coAlign', 'w')
        col_align_out.write(f'SOURCE\TARGET\n')
    elif mode == 'basic':
        output = open(arguments['--output']+'.basic', 'w')
    else:
        print(f"Warning: mode: [{arguments['--mode']}] is not valid, falling back to default mode: [align]")
        mode = 'align'
        src_output = open(arguments['--source']+'.align', 'w')
        trg_output = open(arguments['--target']+'.align', 'w')
        col_align_out = open(arguments['--output']+'.coAlign', 'w')
        col_align_out.write(f'SOURCE\TARGET\n')

    for src, trg in zip(src_sentences, trg_sentences):
        alignments = align_words(src.strip(), trg.strip())
        src_sent = src.strip().split()
        trg_sent = trg.strip().split()

        if mode == 'align':
            write_exact_alignment_only(alignments, src_sent, trg_sent,
                                       src_output, trg_output,
                                       col_align_out)
        elif mode == 'basic':
            write_distances_only(alignments, src_sent, trg_sent, output)

    if mode == 'align':
        print(f'SOURCE alignments are saved to: {arguments["--source"]}.align')
        src_output.close()
        print(f'TARGET alignments are saved to: {arguments["--target"]}.align')
        trg_output.close()
        print(f'Side by side alignments are saved to: {arguments["--output"]}.coAlign')
        col_align_out.close()
    elif mode == 'basic':
        print(f'Basic alignments are saved to: {arguments["--output"]}.basic')
        output.close()
