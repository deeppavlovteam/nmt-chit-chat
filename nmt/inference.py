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

"""To perform inference on test set given a trained model."""
from __future__ import print_function

import codecs
import collections
import time
import heapq
import numpy as np

import tensorflow as tf

from . import attention_model
from . import gnmt_model
from . import model as nmt_model
from . import model_helper
from .utils import misc_utils as utils
from .utils import nmt_utils

__all__ = ["load_data", "inference",
           "single_worker_inference", "multi_worker_inference"]



def _decode_inference_indices(model, sess, output_infer,
                              output_infer_summary_prefix,
                              inference_indices,
                              tgt_eos,
                              bpe_delimiter):
  """Decoding only a specific set of sentences."""
  utils.print_out("  decoding to output %s , num sents %d." %
                  (output_infer, len(inference_indices)))
  start_time = time.time()
  with codecs.getwriter("utf-8")(
      tf.gfile.GFile(output_infer, mode="wb")) as trans_f:
    trans_f.write("")  # Write empty string to ensure file is created.
    for decode_id in inference_indices:
      nmt_outputs, infer_summary = model.decode(sess)
      # get text translation
      assert nmt_outputs.shape[0] == 1
      translation = nmt_utils.get_translation(
          nmt_outputs,
          sent_id=0,
          tgt_eos=tgt_eos,
          bpe_delimiter=bpe_delimiter)

      if infer_summary is not None:  # Attention models
        image_file = output_infer_summary_prefix + str(decode_id) + ".png"
        utils.print_out("  save attention image to %s*" % image_file)
        image_summ = tf.Summary()
        image_summ.ParseFromString(infer_summary)
        with tf.gfile.GFile(image_file, mode="w") as img_f:
          img_f.write(image_summ.value[0].image.encoded_image_string)

      trans_f.write("%s\n" % translation)
      utils.print_out(b"%s\n" % translation)
  utils.print_time("  done", start_time)


def load_data(inference_input_file, hparams=None):
  """Load inference data."""
  with codecs.getreader("utf-8")(
      tf.gfile.GFile(inference_input_file, mode="rb")) as f:
    inference_data = f.read().splitlines()

  if hparams and hparams.inference_indices:
    inference_data = [inference_data[i] for i in hparams.inference_indices]

  return inference_data


def inference(ckpt,
              inference_input_file,
              inference_output_file,
              hparams,
              num_workers=1,
              jobid=0,
              scope=None):
  """Perform translation."""
  if hparams.inference_indices:
    assert num_workers == 1

  # def get_vocab_size(vocab_file):
  #     with open(vocab_file) as vf:
  #         vocab_size = sum(1 for _ in vf)
  #     return vocab_size
  # if hparams.pretrain_enc_emb_path:
  #     hparams.src_vocab_size = get_vocab_size(hparams.src_vocab_file)
  #
  # if hparams.pretrain_dec_emb_path:
  #     hparams.tgt_vocab_size = get_vocab_size(hparams.tgt_vocab_file)


  if not hparams.attention:
    model_creator = nmt_model.Model
  elif hparams.attention_architecture == "standard":
    model_creator = attention_model.AttentionModel
  elif hparams.attention_architecture in ["gnmt", "gnmt_v2"]:
    model_creator = gnmt_model.GNMTModel
  else:
    raise ValueError("Unknown model architecture")
  infer_model = model_helper.create_infer_model(model_creator, hparams, scope)

  if num_workers == 1:
    single_worker_inference(
        infer_model,
        ckpt,
        inference_input_file,
        inference_output_file,
        hparams)
  else:
    multi_worker_inference(
        infer_model,
        ckpt,
        inference_input_file,
        inference_output_file,
        hparams,
        num_workers=num_workers,
        jobid=jobid)


def single_worker_inference(infer_model,
                            ckpt,
                            inference_input_file,
                            inference_output_file,
                            hparams):
  """Inference with a single worker."""
  output_infer = inference_output_file

  # Read data
  infer_data = load_data(inference_input_file, hparams)

  with tf.Session(
      graph=infer_model.graph, config=utils.get_config_proto()) as sess:
    loaded_infer_model = model_helper.load_model(
        infer_model.model, ckpt, sess, "infer")


    if hparams.pretrain_enc_emb_path:
      sess.run(
          infer_model.init_enc_emb,
          feed_dict={infer_model.enc_emb_placeholder: model_helper.load_embeddings(hparams.pretrain_enc_emb_path,hparams.src_vocab_size)})

    if hparams.pretrain_dec_emb_path:
      sess.run(
          infer_model.init_dec_emb,
          feed_dict={infer_model.dec_emb_placeholder: model_helper.load_embeddings(hparams.pretrain_dec_emb_path,hparams.tgt_vocab_size)})

    # sess.run(
    #     infer_model.iterator.initializer,
    #     feed_dict={
    #         infer_model.src_placeholder: infer_data,
    #         infer_model.batch_size_placeholder: hparams.infer_batch_size
    #     })
    # output_layer = sess.run(infer_model.model.model_outputs)
    # print(output_layer)

    # sess.run(
    #     infer_model.iterator.initializer,
    #     feed_dict={
    #         infer_model.src_placeholder: infer_data,
    #         infer_model.batch_size_placeholder: hparams.infer_batch_size
    #     })
    # output_layer = sess.run(infer_model.model.model_outputs)
    # print(output_layer)
    # print(output_layer/100)
    # output_layer = np.squeeze(output_layer)
    # def get_vocab(filename):
    #     vocab = []
    #     with open(filename) as f:
    #         for line in f.readlines():
    #             word = line.strip().split()[0]
    #             vocab.append(word)
    #     return vocab
    # def words_probability(prob, vocab):
    #     confidences = []
    #     words = []
    #     # mean = np.mean(prob)
    #     std = np.std(prob)
    #     for most_n in range(1,5):
    #         variants = np.array(heapq.nlargest(most_n, prob))
    #         dev = np.sqrt((variants[-1] - variants[0])**2)
    #         confidences.append(dev)
    #         index = np.where(prob == variants[-1])[0][0]
    #         words.append(vocab[index])
    #     return confidences, words, std
#         print(
# """
# Confidences mean deviation = {0}
# Words = {1}
# STD = {2}
# """.format(confidences, words, std))

    # # vocab = get_vocab(hparams.tgt_vocab_file)
    # # word_confs = []
    # # for word in output_layer:
    # #     confidences, _, _ = words_probability(word,vocab)
    # #     word_confs.append(confidences[1])
    # word_probs0 = []
    # word_probs1 = []
    # for word in output_layer:
    #     variant = np.array(heapq.nlargest(2, word))
    #     word_probs0.append(variant[0])
    #     word_probs1.append(variant[1])
    # word_confs
    # first_word = np.arange(len(word_confs)//3)
    # first_word.fill(word_confs[0])
    # result_vect1 = np.concatenate([first_word,word_confs])
    # indices = np.where(word_confs<(word_confs[0]*5))
    # # result_vect2 = np.take(word_confs, indices)
    # # result_vect3 = np.concatenate([first_word,result_vect2])
    #
    # mediana = np.median(word_confs)
    # moded_mediana1 = np.median(result_vect1)
    # # moded_mediana2 = np.median(result_vect2)
    # # moded_mediana3 = np.median(result_vect3)
    # # print("Confidences mean deviation = {0}".format(word_confs))
    # print("Probability of first words = {0}".format(word_probs0))
    # print("Probability of seconds words = {0}".format(word_probs1))
    # print("Mediana = {0}".format(mediana))
    # print("Moded mediana1 = {0}".format(moded_mediana1))
    # # print("Moded mediana2 = {0}".format(moded_mediana2))
    # # print("Moded mediana3 = {0}".format(moded_mediana3))


    sess.run(
        infer_model.iterator.initializer,
        feed_dict={
            infer_model.src_placeholder: infer_data,
            infer_model.batch_size_placeholder: hparams.infer_batch_size
        })

    # Decode
    utils.print_out("# Start decoding")
    if hparams.inference_indices:
      _decode_inference_indices(
          loaded_infer_model,
          sess,
          output_infer=output_infer,
          output_infer_summary_prefix=output_infer,
          inference_indices=hparams.inference_indices,
          tgt_eos=hparams.eos,
          bpe_delimiter=hparams.bpe_delimiter)
    else:
      nmt_utils.decode_and_evaluate(
          "infer",
          loaded_infer_model,
          sess,
          output_infer,
          ref_file=None,
          metrics=hparams.metrics,
          bpe_delimiter=hparams.bpe_delimiter,
          beam_width=hparams.beam_width,
          tgt_eos=hparams.eos)


def multi_worker_inference(infer_model,
                           ckpt,
                           inference_input_file,
                           inference_output_file,
                           hparams,
                           num_workers,
                           jobid):
  """Inference using multiple workers."""
  assert num_workers > 1

  final_output_infer = inference_output_file
  output_infer = "%s_%d" % (inference_output_file, jobid)
  output_infer_done = "%s_done_%d" % (inference_output_file, jobid)

  # Read data
  infer_data = load_data(inference_input_file, hparams)

  # Split data to multiple workers
  total_load = len(infer_data)
  load_per_worker = int((total_load - 1) / num_workers) + 1
  start_position = jobid * load_per_worker
  end_position = min(start_position + load_per_worker, total_load)
  infer_data = infer_data[start_position:end_position]

  with tf.Session(
      graph=infer_model.graph, config=utils.get_config_proto()) as sess:



      #This part is not debuged
    if hparams.pretrain_enc_emb_path:
        sess.run(
          infer_model.init_enc_emb,
          feed_dict={infer_model.enc_emb_placeholder: model_helper.load_embeddings(hparams.pretrain_enc_emb_path,hparams.src_vocab_size)})

    if hparams.pretrain_dec_emb_path:
        sess.run(
          infer_model.init_dec_emb,
          feed_dict={infer_model.dec_emb_placeholder: model_helper.load_embeddings(hparams.pretrain_dec_emb_path,hparams.tgt_vocab_size)})


    loaded_infer_model = model_helper.load_model(
        infer_model.model, ckpt, sess, "infer")



    sess.run(infer_model.iterator.initializer,
             {
                 infer_model.src_placeholder: infer_data,
                 infer_model.batch_size_placeholder: hparams.infer_batch_size
             })
    # Decode
    utils.print_out("# Start decoding")
    nmt_utils.decode_and_evaluate(
        "infer",
        loaded_infer_model,
        sess,
        output_infer,
        ref_file=None,
        metrics=hparams.metrics,
        bpe_delimiter=hparams.bpe_delimiter,
        beam_width=hparams.beam_width,
        tgt_eos=hparams.eos)

    # Change file name to indicate the file writing is completed.
    tf.gfile.Rename(output_infer, output_infer_done, overwrite=True)

    # Job 0 is responsible for the clean up.
    if jobid != 0: return

    # Now write all translations
    with codecs.getwriter("utf-8")(
        tf.gfile.GFile(final_output_infer, mode="wb")) as final_f:
      for worker_id in range(num_workers):
        worker_infer_done = "%s_done_%d" % (inference_output_file, worker_id)
        while not tf.gfile.Exists(worker_infer_done):
          utils.print_out("  waitting job %d to complete." % worker_id)
          time.sleep(10)

        with codecs.getreader("utf-8")(
            tf.gfile.GFile(worker_infer_done, mode="rb")) as f:
          for translation in f:
            final_f.write("%s" % translation)
        tf.gfile.Remove(worker_infer_done)
