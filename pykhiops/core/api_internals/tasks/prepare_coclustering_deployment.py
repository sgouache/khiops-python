######################################################################################
# Copyright (c) 2018 - 2023 Orange - All Rights Reserved                             #
# * This software is the confidential and proprietary information of Orange.         #
# * You shall not disclose such Restricted Information and shall use it only in      #
#   accordance with the terms of the license agreement you entered into with Orange  #
#   named the "Khiops - Python Library Evaluation License".                          #
# * Unauthorized copying of this file, via any medium is strictly prohibited.        #
# * See the "LICENSE.md" file for more details.                                      #
######################################################################################
"""prepare_coclustering_deployment task family"""
from pykhiops.core.api_internals import task as tm
from pykhiops.core.api_internals.types import (
    BoolType,
    DictType,
    IntType,
    StringLikeType,
)

# Disable long lines to have readable scenarios
# pylint: disable=line-too-long
TASKS = [
    tm.KhiopsTask(
        "prepare_coclustering_deployment",
        "khiops_coclustering",
        "9.0",
        [
            ("dictionary_file_path", StringLikeType),
            ("dictionary_name", StringLikeType),
            ("coclustering_file_path", StringLikeType),
            ("table_variable", StringLikeType),
            ("deployed_variable_name", StringLikeType),
            ("results_dir", StringLikeType),
        ],
        [
            ("max_preserved_information", IntType, 0),
            ("max_cells", IntType, 0),
            ("max_part_numbers", DictType(StringLikeType, IntType), None),
            ("build_cluster_variable", BoolType, True),
            ("build_distance_variables", BoolType, False),
            ("build_frequency_variables", BoolType, False),
            ("variables_prefix", StringLikeType, ""),
            ("results_prefix", StringLikeType, ""),
        ],
        [
            "dictionary_file_path",
            "coclustering_file_path",
            "results_dir",
        ],
        # fmt: off
        """
        // Dictionary file and class settings
        ClassManagement.OpenFile
        ClassFileName __dictionary_file_path__
        OK
        ClassManagement.ClassName __dictionary_name__

        // Prepare deployment window
        LearningTools.PrepareDeployment

        // Coclustering file
        SelectInputCoclustering
        InputCoclusteringFileName __coclustering_file_path__
        OK

        // Simplification settings
        PostProcessingSpec.MaxPreservedInformation __max_preserved_information__
        PostProcessingSpec.MaxCellNumber __max_cells__
        __DICT__
        __max_part_numbers__
        PostProcessingSpec.PostProcessedAttributes.List.Key
        PostProcessingSpec.PostProcessedAttributes.MaxPartNumber
        __END_DICT__

        // Deployment dictionary settings
        DeploymentSpec.InputObjectArrayAttributeName __table_variable__
        DeploymentSpec.DeployedAttributeName __deployed_variable_name__
        DeploymentSpec.BuildPredictedClusterAttribute __build_cluster_variable__
        DeploymentSpec.BuildClusterDistanceAttributes __build_distance_variables__
        DeploymentSpec.BuildFrequencyRecodingAttributes __build_frequency_variables__
        DeploymentSpec.OutputAttributesPrefix __variables_prefix__

        // Output settings
        AnalysisResults.ResultFilesDirectory __results_dir__
        AnalysisResults.ResultFilesPrefix __results_prefix__

        // Execute prepare deployment
        PrepareDeployment
        Exit
        """,
        # fmt: on
    ),
]
