# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Utility functions specifically for NMT."""
from __future__ import print_function

import codecs
import time

import tensorflow as tf
import numpy as np
import heapq

from ..utils import evaluation_utils
from ..utils import misc_utils as utils

MAGNITUDE = 1000

__all__ = ["decode_and_evaluate", "get_translation"]


def decode_and_evaluate(name,
                        model,
                        sess,
                        trans_file,
                        ref_file,
                        metrics,
                        bpe_delimiter,
                        beam_width,
                        tgt_eos,
                        decode=True):
  """Decode a test set and compute a score according to the evaluation task."""
  # Decode
  if decode:
    utils.print_out("  decoding to output %s." % trans_file)
    #############
    def get_vocab(filename):
        vocab = []
        with open(filename) as f:
            for line in f.readlines():
                word = line.strip().split()[0]
                vocab.append(word)
        return vocab
    def words_probability(prob, vocab):
        confidences = []
        words = []
        # mean = np.mean(prob)
        std = np.std(prob)
        for most_n in range(1,5):
            variants = np.array(heapq.nlargest(most_n, prob))
            dev = np.sqrt((variants[-1] - variants[0])**2)
            confidences.append(dev)
            index = np.where(prob == variants[-1])[0][0]
            words.append(vocab[index])
        return confidences, words, std

    def words_probability_for_2(words):
        word_probs0 = []
        word_probs1 = []
        for word in words:
            variant = np.array(heapq.nlargest(2, word))
            word_probs0.append(variant[0]-MAGNITUDE)
            word_probs1.append(variant[1])
        return word_probs0, word_probs1
    ###########
    start_time = time.time()
    num_sentences = 0
    with codecs.getwriter("utf-8")(
        tf.gfile.GFile(trans_file, mode="wb")) as trans_f:
      trans_f.write("")  # Write empty string to ensure file is created.

      while True:
        try:
          nmt_outputs, _, sample_words = model.decode(sess)

          words = np.squeeze(sample_words)

          if beam_width > 0:
            # get the top translation.
            nmt_outputs = nmt_outputs[0]

          pr0, pr1 = words_probability_for_2(words)
          print(pr0)
          print(pr1)
          num_sentences += len(nmt_outputs)
          for sent_id in range(len(nmt_outputs)):
            translation = get_translation(
                nmt_outputs,
                sent_id,
                tgt_eos=tgt_eos,
                bpe_delimiter=bpe_delimiter)
            trans_f.write((translation + b"\n").decode("utf-8"))
        except tf.errors.OutOfRangeError:
          utils.print_time("  done, num sentences %d" % num_sentences,
                           start_time)
          break

  # Evaluation
  evaluation_scores = {}
  if ref_file and tf.gfile.Exists(trans_file):
    for metric in metrics:
      score = evaluation_utils.evaluate(
          ref_file,
          trans_file,
          metric,
          bpe_delimiter=bpe_delimiter)
      evaluation_scores[metric] = score
      utils.print_out("  %s %s: %.1f" % (metric, name, score))

  return evaluation_scores


def get_translation(nmt_outputs, sent_id, tgt_eos, bpe_delimiter):
  """Given batch decoding outputs, select a sentence and turn to text."""
  if tgt_eos: tgt_eos = tgt_eos.encode("utf-8")
  if bpe_delimiter: bpe_delimiter = bpe_delimiter.encode("utf-8")
  # Select a sentence
  output = nmt_outputs[sent_id, :].tolist()

  # If there is an eos symbol in outputs, cut them at that point.
  if tgt_eos and tgt_eos in output:
    output = output[:output.index(tgt_eos)]

  if not bpe_delimiter:
    translation = utils.format_text(output)
  else:  # BPE
    translation = utils.format_bpe_text(output, delimiter=bpe_delimiter)

  return translation
