import logging
import math

import torch
import torch.nn as nn


class RelationExtractorSimpleResnetCnnPosNetwork(nn.Module):
    """
     Attempt to  implement this papaer

     H. Zhang et al., "Deep Residual Convolutional Neural Network for Protein-Protein Interaction Extraction," in IEEE Access, vol. 7, pp. 89354-89365, 2019.
    doi: 10.1109/ACCESS.2019.2927253

    """

    def __init__(self, class_size, embedding_dim, feature_lengths, embed_vocab_size=0,
                 windows_size=3, dropout_rate_cnn=.5, cnn_output=64, cnn_num_layers=3, cnn_stride=1, pool_kernel=3,
                 pool_stride=2, fc_layer_size=256, fc_dropout_rate=.5, input_dropout_rate=.2, seed=777,
                 fine_tune_embeddings=True):

        super(RelationExtractorSimpleResnetCnnPosNetwork, self).__init__()

        self.embed_vocab_size = embed_vocab_size
        self.fine_tune_embeddings = fine_tune_embeddings
        self.feature_lengths = feature_lengths
        torch.manual_seed(seed)
        self.logger.info("Windows Size is {}".format(windows_size))
        # Use random weights if vocab size if passed in else load pretrained weights

        self.set_embeddings(None)
        self.embedding_dim = embedding_dim

        self.text_column_index = self.feature_lengths.argmax(axis=0)
        self.text_column_size = int(self.feature_lengths[self.text_column_index])

        self.logger.info("The text feature is index {}, the feature lengths are {}".format(self.text_column_index,
                                                                                           self.feature_lengths))

        self.windows_size = windows_size
        self.num_layers = cnn_num_layers

        total_cnn_out_size = 0
        # The total embedding size if the text column + position for the rest

        self.logger.info("Word embedding size is {},  cnn_output size {}".format(embedding_dim, cnn_output))
        cnn_kernel = min(self.windows_size, self.text_column_size)
        cnn_padding = cnn_kernel // 2
        pool_padding = 0

        self._class_size = class_size
        self.activation = nn.ReLU()

        first_cnn_kernel = 1
        self.input_block = nn.Sequential(nn.Dropout(input_dropout_rate),
                                         nn.Conv1d(embedding_dim, cnn_output, kernel_size=first_cnn_kernel,
                                                   stride=cnn_stride,
                                                   padding=cnn_padding),
                                         nn.MaxPool1d(kernel_size=pool_kernel, stride=pool_stride,
                                                      padding=pool_padding)
                                         )
        self.resnet_blocks = nn.ModuleList()

        cnn_out_length = math.ceil(
            (self.text_column_size + 2 * cnn_padding - first_cnn_kernel + 1) / cnn_stride)

        pool_out_length = math.ceil(
            (cnn_out_length + 2 * pool_padding - pool_kernel + 1) / pool_stride)

        pool_out_length = pool_out_length

        self.pooling_blocks = nn.ModuleList()
        for k in range(1, self.num_layers + 1):
            cnn_out_length = math.ceil(
                (pool_out_length + 2 * cnn_padding - cnn_kernel + 1) / cnn_stride)
            # twice for 2 layers of CNN
            cnn_out_length = math.ceil(
                (cnn_out_length + 2 * cnn_padding - cnn_kernel + 1) / cnn_stride)

            resnetblock = nn.Sequential(
                nn.Conv1d(cnn_output, cnn_output, kernel_size=cnn_kernel, stride=cnn_stride, padding=cnn_padding),
                #  nn.Dropout(p=dropout_rate_cnn),
                nn.BatchNorm1d(cnn_output),
                nn.ReLU(),
                nn.Conv1d(cnn_output, cnn_output, kernel_size=cnn_kernel, stride=cnn_stride, padding=cnn_padding),
                #     nn.Dropout(p=dropout_rate_cnn),
                nn.BatchNorm1d(cnn_output)
            )

            self.resnet_blocks.add_module("ResidualBlock_{}".format(k), resnetblock)

            poollayer = nn.MaxPool1d(kernel_size=pool_kernel, stride=pool_stride,
                                     padding=pool_padding)

            pool_out_length = math.ceil(
                (cnn_out_length + 2 * pool_padding - pool_kernel + 1) / pool_stride)

            self.pooling_blocks.add_module("poolinglayer{}".format(k), poollayer)

        self.fc = nn.Sequential(nn.Linear(cnn_output * pool_out_length,
                                          fc_layer_size),
                                nn.Dropout(fc_dropout_rate),
                                nn.ReLU(),
                                nn.Linear(fc_layer_size, class_size))

    @property
    def embeddings(self):
        if self.__embeddings is None:
            assert self.embed_vocab_size > 0, "Please set the vocab size for using random embeddings "
            self.__embeddings = nn.Embedding(self.embed_vocab_size, self.embedding_dim)
            self.__embeddings.weight.requires_grad = self.fine_tune_embeddings

        return self.__embeddings

    def set_embeddings(self, value):
        self.__embeddings = value
        if self.__embeddings is not None:
            self.__embeddings.weight.requires_grad = self.fine_tune_embeddings

    @property
    def logger(self):
        return logging.getLogger(__name__)

    def forward(self, feature_tuples):

        # The input format is tuples of features.. where each item in tuple is a shape feature_len * batch_szie

        # Assume text is when the feature length is max..

        text_inputs = feature_tuples[self.text_column_index]

        embeded = self.embeddings(text_inputs)

        # Final output
        # Conv1d takes in (batch, channels, seq_len), but raw embedded is (batch, seq_len, channels)
        final_input = embeded.permute(0, 2, 1)

        self.logger.debug("Running input block")
        x = self.input_block(final_input)

        self.logger.debug("Running resnet block")
        for _, (m, p) in enumerate(zip(self.resnet_blocks, self.pooling_blocks)):
            x = self.activation(x + m(x))
            x = p(x)

        self.logger.debug("Running fc")

        out = x.reshape(x.size(0), -1)
        out = self.fc(out)

        return out
