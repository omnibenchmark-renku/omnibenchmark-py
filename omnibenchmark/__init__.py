# -*- coding: utf-8 -*-
#
# Copyright 2022-2022- University of Zuerich (UZH)
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

"""Omnibenchmark"""

# Version of the omnibenchmark package

__version__ = "0.0.42"


from omnibenchmark import core, management, renku_commands, utils
from omnibenchmark.core.omni_object import OmniObject
from omnibenchmark.core.output_classes import OmniOutput, OmniCommand, OmniPlan
from omnibenchmark.core.input_classes import OmniParameter, OmniInput
from omnibenchmark.utils.build_omni_object import get_omni_object_from_yaml
from omnibenchmark.renku_commands.general import renku_save
from omnibenchmark.management.data_commands import update_dataset_files
from omnibenchmark.management.data_commands import get_data_url_by_keyword

__all__ = (
    "core",
    "management",
    "renku_commands",
    "utils",
    "OmniObject",
    "OmniPlan",
    "OmniOutput",
    "OmniCommand",
    "OmniParameter",
    "OmniInput",
    "get_omni_object_from_yaml",
    "renku_save",
    "update_dataset_files",
    "get_data_url_by_keyword",
)
