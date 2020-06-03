# =============================================================================
# Copyright 2020 NVIDIA. All Rights Reserved.
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
# =============================================================================

'''
This file contains code artifacts adapted from the original implementation:
https://github.com/thu-coai/ConvLab-2/
'''
import torch

from nemo.backends.pytorch.nm import NonTrainableNM
from nemo.core import AxisKind, AxisType, ChannelType, LengthsType, NeuralType, StringType
from nemo.utils import logging
from nemo.utils.decorators import add_port_docs

__all__ = ['UtteranceEncoderNM']


class UtteranceEncoderNM(NonTrainableNM):
    """
    Encodes dialogue history (system and user utterances) into a Multiwoz dataset format
    Args:
        data_desc (obj): data descriptor for MultiWOZ dataset, contains information about domains, slots, 
            and associated vocabulary
    """

    @property
    @add_port_docs()
    def input_ports(self):
        """Returns definitions of module input ports.
        history (list): dialogue history, list of system and diaglogue utterances
        user_uttr (str): user utterance
        sys_uttr (str): system utterace
        """
        return {
            'dial_history': NeuralType(axes=(AxisType(kind=AxisKind.Time, is_list=True)), elements_type=StringType()),
            'user_uttr': NeuralType(axes=(AxisType(kind=AxisKind.Time)), elements_type=StringType()),
            'sys_uttr': NeuralType(axes=(AxisType(kind=AxisKind.Time)), elements_type=StringType()),
        }

    @property
    @add_port_docs()
    def output_ports(self):
        """Returns definitions of module output ports.
        src_ids (int): token ids for dialogue history
        src_lens (int): length of the tokenized dialogue history
        dial_history (list): dialogue history, list of system and diaglogue utterances 
        """
        return {
            'src_ids': NeuralType(('B', 'T'), elements_type=ChannelType()),
            'src_lens': NeuralType(tuple('B'), elements_type=LengthsType()),
            'dial_history': NeuralType(axes=(AxisType(kind=AxisKind.Time, is_list=True)), elements_type=StringType()),
        }

    def __init__(self, data_desc):
        """
        Initializes the object
        Args:
            data_desc (obj): data descriptor for MultiWOZ dataset, contains information about domains, slots, 
                    and associated vocabulary
        """
        super().__init__()
        self.data_desc = data_desc

    def forward(self, dial_history, user_uttr, sys_uttr):
        """
        Returns dialogue utterances in the format accepted by the TRADE Dialogue state tracking model
        Args:
            dial_history (list): dialogue history, list of system and diaglogue utterances
            user_uttr (str): user utterance
            sys_uttr (str): system utterace
        Returns:
            src_ids (int): token ids for dialogue history
            src_lens (int): length of the tokenized dialogue history
            dial_history (list): updated dialogue history, list of system and diaglogue utterances
        """
        dial_history.append(["sys", sys_uttr])
        dial_history.append(["user", user_uttr])
        logging.debug("Dialogue history: %s", dial_history)

        context = ' ; '.join([item[1].strip().lower() for item in dial_history]).strip() + ' ;'
        context_ids = self.data_desc.vocab.tokens2ids(context.split())
        src_ids = torch.tensor(context_ids).unsqueeze(0).to(self._device)
        src_lens = torch.tensor(len(context_ids)).unsqueeze(0).to(self._device)
        return src_ids, src_lens, dial_history